"""ML-06: análisis retrospectivo de calibración, cupos y costos relativos."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss

from ML.features import FEATURE_NAMES
from ML.inference import ChurnPredictor

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def decision(y: np.ndarray, chosen: np.ndarray, fn_cost: float = 1) -> dict[str, Any]:
    """Costos de clasificación hipotéticos; no estiman efecto de una campaña."""
    tp = int(np.sum((y == 1) & chosen))
    fp = int(np.sum((y == 0) & chosen))
    fn = int(np.sum((y == 1) & ~chosen))
    tn = int(np.sum((y == 0) & ~chosen))
    return {
        "n": len(y),
        "selected": int(chosen.sum()),
        "selected_fraction": float(chosen.mean()),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "relative_loss": fp + fn_cost * fn,
    }


def ranking(frame: pd.DataFrame, score: str) -> np.ndarray:
    """Desempata por ID ascendente para no exceder cupo aun con probabilidades iguales."""
    return np.asarray(
        frame.sort_values([score, "Customer ID"], ascending=[False, True]).index,
        dtype=int,
    )


def select_fraction(frame: pd.DataFrame, capacity: float, fn_cost: float) -> float:
    """Elige el número de seleccionados solo en validación; empate favorece menor cupo."""
    if not 0 < capacity <= 1 or fn_cost <= 0:
        raise ValueError("Capacidad o costo relativo inválido.")
    y = frame["Churn"].to_numpy()
    order = ranking(frame, "probability")
    options = []
    for k in range(int(len(frame) * capacity) + 1):
        chosen = np.zeros(len(frame), dtype=bool)
        chosen[order[:k]] = True
        options.append((decision(y, chosen, fn_cost)["relative_loss"], k))
    return min(options)[1] / len(frame)


def run(folder: Path, output: Path) -> dict[str, Any]:
    """Conserva artefacto y umbrales originales; escribe en un directorio nuevo."""
    predictor = ChurnPredictor.load(folder / "model.joblib")
    output.mkdir(parents=True, exist_ok=False)
    metadata = predictor.metadata
    protocol = json.loads((folder / "protocol.json").read_text())
    frames = {}
    provenance = {}
    calibration_rows = []
    bin_rows = []
    threshold_rows = []
    for role in ["validation", "test"]:
        path = folder / f"snapshot_{protocol[role + '_cutoff']}.csv"
        provenance[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        frame = pd.read_csv(path).reset_index(drop=True)
        if frame["Customer ID"].duplicated().any() or set(frame["Churn"].unique()) != {
            0,
            1,
        }:
            raise ValueError("Snapshot incompatible.")
        predictor.predict_many(frame[list(FEATURE_NAMES)].to_dict("records"))
        x = frame[list(FEATURE_NAMES)]
        frame["probability"] = predictor.model.predict_proba(x)[:, 1]
        raw = predictor.model.calibrated_classifiers_[0].estimator.predict_proba(x)[
            :, 1
        ]
        y = frame["Churn"].to_numpy()
        for kind, p in [("raw", raw), ("sigmoid", frame["probability"].to_numpy())]:
            calibration_rows.append(
                {
                    "period": role,
                    "variant": kind,
                    "n": len(y),
                    "prevalence": float(y.mean()),
                    "mean_probability": float(p.mean()),
                    "brier": float(brier_score_loss(y, p)),
                    "log_loss": float(log_loss(y, p)),
                }
            )
            bins = np.minimum((p * 10).astype(int), 9)
            for b in range(10):
                mask = bins == b
                if mask.any():
                    bin_rows.append(
                        {
                            "period": role,
                            "variant": kind,
                            "bin_low": b / 10,
                            "n": int(mask.sum()),
                            "mean_probability": float(p[mask].mean()),
                            "observed_churn": float(y[mask].mean()),
                        }
                    )
        for label, threshold in {
            "medium_current": predictor.thresholds["medium"],
            "high_current": predictor.thresholds["high"],
            "legacy_035": 0.35,
            "legacy_070": 0.70,
            "reference_050": 0.50,
        }.items():
            threshold_rows.append(
                {
                    "period": role,
                    "policy": label,
                    "threshold": threshold,
                    **decision(y, frame["probability"].to_numpy() >= threshold),
                }
            )
        frames[role] = frame
    scenarios = []
    for capacity in [0.10, 0.20, 0.30]:
        for fn_cost in [1, 2, 5]:
            fraction = select_fraction(frames["validation"], capacity, fn_cost)
            for role, frame in frames.items():
                y = frame["Churn"].to_numpy()
                for policy, score, share in [
                    ("model_selected_on_validation", "probability", fraction),
                    ("model_full_capacity", "probability", capacity),
                    ("recency_same_selected_quota", "Recency", fraction),
                    ("recency_full_capacity", "Recency", capacity),
                    ("select_nobody", "probability", 0.0),
                ]:
                    k = min(
                        int(np.floor(len(frame) * share + 1e-9)),
                        int(len(frame) * capacity),
                    )
                    chosen = np.zeros(len(frame), dtype=bool)
                    chosen[ranking(frame, score)[:k]] = True
                    scenarios.append(
                        {
                            "period": role,
                            "capacity_fraction": capacity,
                            "false_negative_relative_cost": fn_cost,
                            "policy": policy,
                            "selected_fraction_validation": fraction,
                            **decision(y, chosen, fn_cost),
                        }
                    )
    pd.DataFrame(calibration_rows).to_csv(output / "calibration.csv", index=False)
    pd.DataFrame(bin_rows).to_csv(output / "calibration_bins.csv", index=False)
    pd.DataFrame(threshold_rows).to_csv(output / "thresholds.csv", index=False)
    pd.DataFrame(scenarios).to_csv(output / "capacity_scenarios.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    bins_frame = pd.DataFrame(bin_rows)
    for axis, role in zip(axes, ["validation", "test"]):
        axis.plot([0, 1], [0, 1], "--", color="gray")
        for variant in ["raw", "sigmoid"]:
            subset = bins_frame[
                (bins_frame.period == role) & (bins_frame.variant == variant)
            ]
            axis.plot(
                subset.mean_probability, subset.observed_churn, "o-", label=variant
            )
        axis.set(
            title=role,
            xlabel="Probabilidad media",
            ylabel="Fracción de abandono",
            xlim=(0, 1),
            ylim=(0, 1),
        )
        axis.legend()
    fig.suptitle(
        "ML-06: calibración retrospectiva; bins de 0,10 (no intervalos de confianza)"
    )
    fig.tight_layout()
    fig.savefig(output / "calibration.png", dpi=170)
    plt.close(fig)
    report = {
        "model_version": predictor.version,
        "model_sha256": metadata["model_sha256"],
        "snapshot_sha256": provenance,
        "thresholds_unchanged": predictor.thresholds,
        "calibration": calibration_rows,
        "scenarios_count": len(scenarios),
        "status": "academic_sensitivity_analysis_only",
        "commercially_validated": False,
        "automatic_action_allowed": False,
        "limitations": [
            "El test ya había sido observado: este análisis es retrospectivo, no nueva validación independiente.",
            "Costos FP=1 y FN=1/2/5 son unidades abstractas; no dinero, margen ni efecto causal.",
            "Cupos 10/20/30% son supuestos, no capacidad informada por un negocio.",
            "Se selecciona fracción en validación y se aplica sin optimizar en test; desempate por ID.",
            "Top-k es una política de análisis, no reemplaza las categorías de la API.",
            "Datos insuficientes para validar comercialmente umbrales o afirmar rentabilidad.",
        ],
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main() -> None:
    """Ejecuta el estudio con salida sin sobrescritura."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=ROOT / "ML/artifacts/churn180-v1"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.artifact, args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
