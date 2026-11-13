"""MEJ-05: análisis del candidato congelado, sin consultar E1."""

import argparse
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

from ML.compare_v2 import scores, write_json
from ML.temporal_validation import ROOT, sha256


def exact_capacity_threshold(probability, fraction):
    """Umbral >= para exactamente ceil(fracción*N); None si hay empates."""
    p = np.asarray(probability, dtype=float)
    if not len(p) or not 0 < fraction <= 1 or not np.isfinite(p).all():
        raise ValueError("Cupo o probabilidades inválidos.")
    k = math.ceil(fraction * len(p))
    threshold = float(np.sort(p)[-k])
    return threshold if int((p >= threshold).sum()) == k else None


def classification(y, probability, threshold):
    predicted = np.asarray(probability) >= threshold
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    return dict(
        tn=int(tn),
        fp=int(fp),
        fn=int(fn),
        tp=int(tp),
        selected=int(tp + fp),
        precision=float(tp / (tp + fp)) if tp + fp else None,
        recall=float(tp / (tp + fn)) if tp + fn else None,
    )


def calibration_bins(y, probability):
    p = np.asarray(probability)
    bins = np.minimum((p * 10).astype(int), 9)
    return [
        dict(
            bin=i,
            lower=i / 10,
            upper=(i + 1) / 10,
            n=int((bins == i).sum()),
            mean_probability=float(p[bins == i].mean()) if (bins == i).any() else None,
            observed_rate=(
                float(np.asarray(y)[bins == i].mean()) if (bins == i).any() else None
            ),
        )
        for i in range(10)
    ]


def run(prepared, comparison, output):
    if output.exists():
        raise FileExistsError("El destino debe ser nuevo.")
    status = json.loads((comparison / "status.json").read_text())
    if status["status"] != "complete":
        raise ValueError("MEJ-04 no completada.")
    for name, digest in status["files"].items():
        if sha256(comparison / name) != digest:
            raise ValueError("Artefacto de MEJ-04 alterado.")
    selection = json.loads((comparison / "selection.json").read_text())
    candidate = selection["candidate"]
    manifest = json.loads((prepared / "manifest.json").read_text())
    if sha256(prepared / "manifest.json") != status["prepared_manifest_sha256"]:
        raise ValueError("Preparación alterada.")
    output.mkdir(parents=True)
    rule = dict(
        candidate=candidate,
        variants=["raw", "sigmoid"],
        selection_order=[
            "mean_precision_at_20_desc",
            "mean_AP_desc",
            "mean_Brier_asc",
            "variant_name_asc",
        ],
        fractions=[0.1, 0.2, 0.3],
        threshold_rule="exact ceil(fraction*N) with >=, derived from calibration only; null if ties",
        E1_used=False,
    )
    write_json(output / "analysis_plan.json", rule)
    rows, thresholds, bins = [], [], []
    for fold in manifest["folds"]:
        if fold["id"] not in ["D1", "D2"]:
            continue
        frames = {}
        for role in ["calibration", "evaluation"]:
            info = fold["roles"][role]
            path = prepared / info["file"]
            if sha256(path) != info["sha256"]:
                raise ValueError("CSV alterado.")
            frames[role] = pd.read_csv(path)
        bundle = joblib.load(comparison / f'{fold["id"]}_{candidate["id"]}.joblib')
        columns = bundle["features"]
        for variant, model in [
            ("raw", bundle["raw"]),
            ("sigmoid", bundle["calibrated"]),
        ]:
            cal = model.predict_proba(frames["calibration"][columns])[:, 1]
            evaluation = frames["evaluation"]
            probability = model.predict_proba(evaluation[columns])[:, 1]
            rows.append(
                dict(
                    fold=fold["id"],
                    variant=variant,
                    prevalence=float(evaluation["Churn"].mean()),
                    mean_probability=float(probability.mean()),
                    **scores(evaluation, probability),
                )
            )
            for item in calibration_bins(evaluation["Churn"], probability):
                bins.append(dict(fold=fold["id"], variant=variant, **item))
            prediction = evaluation[["Customer ID", "cutoff", "Churn"]].copy()
            prediction["probability"] = probability
            prediction.to_csv(output / f'{fold["id"]}_{variant}.csv', index=False)
            for fraction in rule["fractions"]:
                threshold = exact_capacity_threshold(cal, fraction)
                thresholds.append(
                    dict(
                        fold=fold["id"],
                        variant=variant,
                        fraction=fraction,
                        calibration_n=len(cal),
                        target_count=math.ceil(fraction * len(cal)),
                        threshold=threshold,
                        compatible=threshold is not None,
                        evaluation=(
                            classification(evaluation["Churn"], probability, threshold)
                            if threshold is not None
                            else None
                        ),
                    )
                )
    summary = []
    for variant in rule["variants"]:
        subset = [r for r in rows if r["variant"] == variant]
        summary.append(
            dict(
                variant=variant,
                **{
                    metric: float(np.mean([r[metric] for r in subset]))
                    for metric in [
                        "precision_at_20",
                        "average_precision",
                        "brier",
                        "log_loss",
                    ]
                },
            )
        )
    summary.sort(
        key=lambda r: (
            -r["precision_at_20"],
            -r["average_precision"],
            r["brier"],
            r["variant"],
        )
    )
    frozen = dict(
        candidate=candidate,
        variant=summary[0]["variant"],
        primary_policy="top_20_percent",
        ranking_ties="Customer ID ascending",
        k_rule="ceil(0.20*N)",
        threshold_policy=rule["threshold_rule"],
        E1_used=False,
        promoted=False,
        selection_sha256=sha256(comparison / "selection.json"),
        note="E1 debe ajustar el candidato congelado en su train y calibración; ningún umbral numérico de D1/D2 se traslada como umbral final.",
    )
    write_json(output / "metrics.json", rows)
    write_json(output / "thresholds.json", thresholds)
    write_json(output / "calibration_bins.json", bins)
    write_json(output / "summary.json", summary)
    write_json(output / "frozen_policy.json", frozen)
    write_json(
        output / "manifest.json",
        dict(
            status="complete",
            trained_models=0,
            E1_used=False,
            code_sha256=sha256(Path(__file__)),
            comparison_status_sha256=sha256(comparison / "status.json"),
            files={p.name: sha256(p) for p in sorted(output.iterdir())},
        ),
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepared", type=Path, default=ROOT / "docs/evidencias_mej03/preparacion"
    )
    parser.add_argument(
        "--comparison", type=Path, default=ROOT / "docs/evidencias_mej04/comparacion"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.prepared, args.comparison, args.output))
