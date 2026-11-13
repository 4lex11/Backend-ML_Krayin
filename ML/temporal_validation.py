"""Preparación verificable de divisiones temporales v2; no entrena modelos."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ML.features import FEATURE_NAMES, clean_transactions, make_snapshot
from ML.features_v2 import TEMPORAL_FEATURE_NAMES, build_temporal_features

ROOT = Path(__file__).resolve().parents[1]
FEATURE_SETS = {
    "original": list(FEATURE_NAMES),
    "temporal": list(TEMPORAL_FEATURE_NAMES),
    "combined": list(FEATURE_NAMES + TEMPORAL_FEATURE_NAMES),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_protocol(protocol: dict[str, Any]) -> None:
    if protocol["schema_version"] != "churn180-v2-experimental":
        raise ValueError("Esquema incompatible.")
    definition = protocol["definition"]
    if any(
        definition[k] != v
        for k, v in {
            "lookback_days": 365,
            "horizon_days": 180,
            "eligible_recency_max_days": 180,
        }.items()
    ):
        raise ValueError("Ventanas incompatibles con las variables.")
    if protocol["baseline"]["features"] != list(FEATURE_NAMES) or protocol[
        "temporal_features"
    ] != list(TEMPORAL_FEATURE_NAMES):
        raise ValueError("Esquema de variables incompatible.")
    ids = [fold["id"] for fold in protocol["evaluations"]]
    if ids != ["D1", "D2", "E1"]:
        raise ValueError("Se requieren D1, D2 y E1 en orden.")
    for fold in protocol["evaluations"]:
        train = fold["train_cutoffs"]
        dates = [*train, fold["calibration_cutoff"], fold["evaluation_cutoff"]]
        if not train or dates != sorted(set(dates)):
            raise ValueError("Cortes duplicados o fuera de orden.")
        for before, after in zip(dates, dates[1:]):
            if pd.Timestamp(before) + pd.Timedelta(days=180) >= pd.Timestamp(after):
                raise ValueError(
                    "Etiquetas futuras no disponibles antes del siguiente corte."
                )


def build_snapshots(
    data: pd.DataFrame, protocol: dict[str, Any]
) -> dict[str, pd.DataFrame]:
    validate_protocol(protocol)
    cutoffs = sorted(
        {
            cutoff
            for fold in protocol["evaluations"]
            for cutoff in [
                *fold["train_cutoffs"],
                fold["calibration_cutoff"],
                fold["evaluation_cutoff"],
            ]
        }
    )
    snapshots = {}
    for cutoff in cutoffs:
        original = make_snapshot(data, cutoff)
        temporal = build_temporal_features(data, cutoff)
        if not original.index.equals(temporal.index) or not original.index.is_unique:
            raise ValueError("Poblaciones incompatibles entre conjuntos de variables.")
        frame = original.join(temporal)
        if not np.isfinite(frame[FEATURE_SETS["combined"]].to_numpy()).all():
            raise ValueError("Variables no finitas.")
        if frame["Churn"].nunique() != 2:
            raise ValueError("Cada corte requiere ambas clases.")
        if len(frame) < protocol["promotion_gate"]["minimum_customers_per_cutoff"]:
            raise ValueError("Población insuficiente; evaluación inconclusa.")
        snapshots[cutoff] = frame
    return snapshots


def prepare(dataset: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("El destino debe ser nuevo; no se sobrescriben ensayos.")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    if sha256(dataset) != protocol["source"]["dataset_csv_sha256"]:
        raise ValueError("Hash del dataset incompatible.")
    for name, path in {
        "model": ROOT / "ML/artifacts/churn180-v1/model.joblib",
        "metadata": ROOT / "ML/artifacts/churn180-v1/metadata.json",
        "protocol": ROOT / "ML/protocol.json",
    }.items():
        if sha256(path) != protocol["baseline"][f"{name}_sha256"]:
            raise ValueError("La referencia v1 cambió.")
    data, quality = clean_transactions(pd.read_csv(dataset))
    snapshots = build_snapshots(data, protocol)
    output.mkdir(parents=True)
    (output / "protocol.json").write_bytes(protocol_path.read_bytes())
    report: dict[str, Any] = {
        "stage": "MEJ-03",
        "trained_models": 0,
        "protocol_sha256": sha256(protocol_path),
        "dataset_sha256": sha256(dataset),
        "quality": quality,
        "feature_sets": FEATURE_SETS,
        "folds": [],
        "limitations": "E1 ya fue observado; aceptación exploratoria, no selección ni test independiente.",
        "code_sha256": {
            name: sha256(ROOT / name)
            for name in [
                "ML/features.py",
                "ML/features_v2.py",
                "ML/temporal_validation.py",
            ]
        },
    }
    for fold in protocol["evaluations"]:
        folder = output / fold["id"]
        folder.mkdir()
        roles = {
            "train": pd.concat([snapshots[c] for c in fold["train_cutoffs"]]),
            "calibration": snapshots[fold["calibration_cutoff"]],
            "evaluation": snapshots[fold["evaluation_cutoff"]],
        }
        detail = {
            "id": fold["id"],
            "usable_for_selection": fold["id"] != "E1",
            "roles": {},
        }
        for role, frame in roles.items():
            path = folder / f"{role}.csv"
            frame.reset_index().to_csv(path, index=False)
            detail["roles"][role] = {
                "rows": len(frame),
                "unique_customers": frame.index.nunique(),
                "churn": int(frame["Churn"].sum()),
                "cutoffs": sorted(frame["cutoff"].unique().tolist()),
                "file": path.relative_to(output).as_posix(),
                "sha256": sha256(path),
            }
        report["folds"].append(detail)
    (output / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "ML/Datasets/train.csv")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "ML/experiments/churn180-v2/protocol.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.dataset, args.protocol, args.output), indent=2))
