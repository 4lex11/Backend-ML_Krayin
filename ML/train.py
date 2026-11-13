"""Entrena y evalúa el protocolo temporal: python -m ML.train --output ML/artifacts/churn180-v1."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ML.evaluation import bootstrap_intervals, metrics, select_thresholds
from ML.features import FEATURE_NAMES, build_features, clean_transactions, make_snapshot

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: Any) -> None:
    """Escribe resultados legibles y sin NaN JSON."""
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    """Identifica exactamente un archivo."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidates() -> dict[str, Any]:
    """Seis candidatos prefijados; no se ajustan usando el periodo de prueba."""
    factories: dict[str, Callable[[], Any]] = {
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=150, max_depth=5, min_samples_leaf=5, random_state=42, n_jobs=1
        ),
        "XGBoost": lambda: XGBClassifier(
            n_estimators=150,
            max_depth=3,
            learning_rate=0.05,
            eval_metric="logloss",
            random_state=42,
            n_jobs=1,
        ),
        "LightGBM": lambda: LGBMClassifier(
            n_estimators=150,
            max_depth=3,
            num_leaves=7,
            learning_rate=0.05,
            verbosity=-1,
            random_state=42,
            n_jobs=1,
        ),
    }
    models: dict[str, Any] = {}
    for name, factory in factories.items():
        models[name] = factory()
        models[name + "_SMOTE"] = Pipeline(
            [
                ("scale", StandardScaler()),
                ("smote", SMOTE(random_state=42)),
                ("classifier", factory()),
            ]
        )
    return models


def run_training(dataset: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    """Ejecuta entrenamiento, calibración, selección y una prueba temporal final.

    El directorio debe ser nuevo: una evaluación anterior no se sobrescribe.
    El estimador final conserva el entrenamiento original; no se reentrena
    después de mirar el test, para que las métricas describan el artefacto servido.
    """
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    supported = {
        "schema_version": "churn180-v1",
        "seed": 42,
        "date_format": "%d/%m/%Y",
        "lookback_days": 365,
        "horizon_days": 180,
        "eligible_recency_max_days": 180,
        "high_risk_validation_quantile": 0.8,
        "selection": "validation_average_precision_then_lower_brier_then_name",
        "threshold_selection": "maximum_validation_F2_then_precision_then_threshold",
    }
    if any(protocol.get(key) != value for key, value in supported.items()):
        raise ValueError("Protocolo incompatible con la definición de churn180-v1.")
    if protocol["bootstrap_repetitions"] < 1:
        raise ValueError("Se requiere al menos una repetición bootstrap.")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "protocol.json", protocol)
    data, quality = clean_transactions(pd.read_csv(dataset))
    cutoffs = [
        *protocol["train_cutoffs"],
        protocol["calibration_cutoff"],
        protocol["validation_cutoff"],
        protocol["test_cutoff"],
    ]
    for previous, following in zip(cutoffs, cutoffs[1:]):
        if pd.Timestamp(previous) + pd.Timedelta(days=180) >= pd.Timestamp(following):
            raise ValueError(
                "Las ventanas de resultado deben cerrar antes del siguiente corte."
            )
    snapshots = {cutoff: make_snapshot(data, cutoff) for cutoff in cutoffs}
    roles = {cutoff: "train" for cutoff in protocol["train_cutoffs"]}
    roles.update(
        {
            protocol[f"{role}_cutoff"]: role
            for role in ["calibration", "validation", "test"]
        }
    )
    split_report = []
    for cutoff, snapshot in snapshots.items():
        if snapshot["Churn"].nunique() != 2:
            raise ValueError("Cada periodo debe contener ambas clases.")
        snapshot.reset_index().to_csv(output / f"snapshot_{cutoff}.csv", index=False)
        split_report.append(
            {
                "role": roles[cutoff],
                "cutoff": cutoff,
                "label_end": str(
                    (pd.Timestamp(cutoff) + pd.Timedelta(days=180)).date()
                ),
                "n": len(snapshot),
                "churn": int(snapshot["Churn"].sum()),
                "prevalence": float(snapshot["Churn"].mean()),
            }
        )
    train = pd.concat([snapshots[c] for c in protocol["train_cutoffs"]])
    calibration = snapshots[protocol["calibration_cutoff"]]
    validation = snapshots[protocol["validation_cutoff"]]
    test = snapshots[protocol["test_cutoff"]]
    columns = list(FEATURE_NAMES)
    models = candidates()
    fitted: dict[str, Any] = {}
    validation_rows: list[dict[str, Any]] = []
    for name, estimator in models.items():
        estimator.fit(train[columns], train["Churn"])
        calibrated = CalibratedClassifierCV(
            FrozenEstimator(estimator), method="sigmoid"
        )
        calibrated.fit(calibration[columns], calibration["Churn"])
        fitted[name] = calibrated
        raw = estimator.predict_proba(validation[columns])[:, 1]
        probability = calibrated.predict_proba(validation[columns])[:, 1]
        row = {
            "model": name,
            **metrics(validation["Churn"], probability),
            "raw_brier": metrics(validation["Churn"], raw)["brier"],
        }
        validation_rows.append(row)
        print(
            f"Validación {name}: AP={row['average_precision']:.4f}, Brier={row['brier']:.4f}",
            flush=True,
        )
    selected = sorted(
        validation_rows,
        key=lambda row: (-row["average_precision"], row["brier"], row["model"]),
    )[0]["model"]
    model = fitted[selected]
    val_prob = model.predict_proba(validation[columns])[:, 1]
    thresholds = select_thresholds(validation["Churn"].to_numpy(), val_prob)
    # La decisión y los límites se escriben antes de calcular predicciones de test.
    write_json(
        output / "selection_before_test.json",
        {
            "model": selected,
            "thresholds": thresholds,
            "protocol_sha256": sha256(protocol_path),
        },
    )
    pd.DataFrame(validation_rows).drop(columns="confusion_matrix").to_csv(
        output / "validation_comparison.csv", index=False
    )
    probability = model.predict_proba(test[columns])[:, 1]
    test_metrics = metrics(test["Churn"], probability, thresholds["medium"])
    baselines = {
        "prior_entrenamiento": metrics(
            test["Churn"], np.full(len(test), float(train["Churn"].mean()))
        ),
        "regla_recencia_90": metrics(test["Churn"], test["Recency"].to_numpy() / 180),
    }
    versions = {
        name: importlib.metadata.version(name)
        for name in [
            "numpy",
            "pandas",
            "scipy",
            "scikit-learn",
            "joblib",
            "imbalanced-learn",
            "xgboost",
            "lightgbm",
        ]
    }
    version = output.name
    report = {
        "model_version": version,
        "schema_version": protocol["schema_version"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": sha256(dataset),
        "protocol_sha256": sha256(protocol_path),
        "quality": quality,
        "splits": split_report,
        "selected_model": selected,
        "features": columns,
        "thresholds": thresholds,
        "validation": validation_rows,
        "test": test_metrics,
        "test_at_05": metrics(test["Churn"], probability),
        "test_at_high": metrics(test["Churn"], probability, thresholds["high"]),
        "test_at_legacy_035": metrics(test["Churn"], probability, 0.35),
        "test_at_legacy_070": metrics(test["Churn"], probability, 0.70),
        "test_baselines": baselines,
        "test_ci95": bootstrap_intervals(
            test["Churn"],
            probability,
            thresholds["medium"],
            protocol["bootstrap_repetitions"],
        ),
        "python": platform.python_version(),
        "versions": versions,
        "limitations": [
            "Dataset de ventas; abandono definido por ausencia de compra, no baja contractual.",
            "Mismos clientes pueden reaparecer en cortes posteriores; no demuestra generalización a una cartera nueva.",
            "Solo un periodo de test; intervalos bootstrap no capturan incertidumbre entre años.",
            "Umbral F2 y quintil superior son decisiones técnicas iniciales, sin costos ni capacidad comercial validados.",
            "No demuestra efecto causal en retención ni satisfacción.",
            "SMOTE interpola también conteos; se compara como candidato, no se asume que mejore.",
        ],
    }
    bundle = {
        "model": model,
        "metadata": report,
        "features": columns,
        "thresholds": thresholds,
        "version": version,
    }
    joblib.dump(bundle, output / "model.joblib")
    report["model_sha256"] = sha256(output / "model.joblib")
    write_json(output / "metadata.json", report)
    test_export = test.reset_index()
    test_export["probabilidad_churn"] = probability
    test_export["prediccion"] = (probability >= thresholds["medium"]).astype(int)
    test_export.to_csv(output / "test_predictions.csv", index=False)
    latest_date = str(data["Order Date"].max().date())
    latest = build_features(data, latest_date)
    latest_prob = model.predict_proba(latest)[:, 1]
    export = latest.reset_index().rename(columns={"Customer ID": "customer_id"})
    export["as_of"] = latest_date
    export["model_version"] = version
    export["probabilidad_churn"] = latest_prob
    export["categoria_riesgo"] = np.where(
        latest_prob >= thresholds["high"],
        "Alto",
        np.where(latest_prob >= thresholds["medium"], "Medio", "Bajo"),
    )
    export.to_csv(output / "crm_predictions.csv", index=False)
    export.to_json(
        output / "crm_predictions.json", orient="records", indent=2, force_ascii=False
    )
    from ML.figures import make_figures

    make_figures(report, test_export, models[selected], output)
    print(
        f"Modelo seleccionado: {selected}; test AP={test_metrics['average_precision']:.4f}",
        flush=True,
    )
    return report


def main() -> None:
    """Punto de entrada reproducible."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "ML/Datasets/train.csv")
    parser.add_argument("--protocol", type=Path, default=ROOT / "ML/protocol.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_training(args.dataset, args.protocol, args.output)


if __name__ == "__main__":
    main()
