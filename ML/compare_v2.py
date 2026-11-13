"""Comparación de candidatos exclusivamente en D1/D2, con registro local."""

import argparse
import importlib.metadata
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ML.temporal_validation import FEATURE_SETS, ROOT, sha256, validate_protocol


def write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def plan():
    candidates = []
    for features in FEATURE_SETS:
        for family in ["logistic", "forest", "lightgbm"]:
            for variant in ["a", "b"]:
                if family == "logistic":
                    params = dict(
                        C=0.1 if variant == "a" else 1.0,
                        solver="lbfgs",
                        max_iter=3000,
                        random_state=42,
                    )
                elif family == "forest":
                    params = dict(
                        n_estimators=150,
                        max_depth=3 if variant == "a" else 5,
                        min_samples_leaf=10 if variant == "a" else 20,
                        random_state=42,
                        n_jobs=1,
                    )
                else:
                    params = dict(
                        n_estimators=100,
                        max_depth=2 if variant == "a" else 3,
                        num_leaves=4 if variant == "a" else 7,
                        min_child_samples=20,
                        reg_lambda=1.0,
                        learning_rate=0.03,
                        random_state=42,
                        n_jobs=1,
                        verbosity=-1,
                    )
                candidates.append(
                    dict(
                        id=f"{family}_{features}_{variant}",
                        family=family,
                        features=features,
                        params=params,
                    )
                )
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": 42,
        "calibration": "sigmoid",
        "candidates": candidates,
        "evaluation_folds": ["D1", "D2"],
        "E1_used": False,
    }


def estimator(config):
    if config["family"] == "logistic":
        return make_pipeline(StandardScaler(), LogisticRegression(**config["params"]))
    if config["family"] == "forest":
        return RandomForestClassifier(**config["params"])
    return LGBMClassifier(**config["params"])


def scores(frame, probability):
    p = np.asarray(probability)
    if (
        p.shape != (len(frame),)
        or not np.isfinite(p).all()
        or ((p < 0) | (p > 1)).any()
    ):
        raise ValueError("Probabilidades inválidas.")
    y = frame["Churn"].to_numpy()
    order = np.lexsort((frame["Customer ID"].astype(str).to_numpy(), -p))
    result = dict(
        average_precision=float(average_precision_score(y, p)),
        roc_auc=float(roc_auc_score(y, p)),
        brier=float(brier_score_loss(y, p)),
        log_loss=float(log_loss(y, p, labels=[0, 1])),
    )
    for percent in [10, 20, 30]:
        k = math.ceil(percent * len(y) / 100)
        tp = int(y[order[:k]].sum())
        result.update(
            {
                f"precision_at_{percent}": tp / k,
                f"recall_at_{percent}": tp / int(y.sum()),
                f"selected_{percent}": k,
                f"false_positives_{percent}": k - tp,
            }
        )
    return result


def rank_candidates(rows):
    return sorted(
        rows,
        key=lambda x: (
            -x["precision_at_20"],
            -x["average_precision"],
            x["brier"],
            x["feature_count"],
            x["id"],
        ),
    )


def run(prepared, manifest_path, output):
    if output.exists():
        raise FileExistsError("El destino debe ser nuevo.")
    protocol = json.loads((prepared / "protocol.json").read_text())
    validate_protocol(protocol)
    prepared_manifest = json.loads((prepared / "manifest.json").read_text())
    if sha256(prepared / "protocol.json") != prepared_manifest["protocol_sha256"]:
        raise ValueError("Protocolo alterado.")
    design = json.loads(manifest_path.read_text())
    configs = design["candidates"]
    if (
        not configs
        or len(configs) > protocol["candidate_budget_max"]
        or len({c["id"] for c in configs}) != len(configs)
    ):
        raise ValueError("Presupuesto o IDs inválidos.")
    if design["evaluation_folds"] != ["D1", "D2"] or design["E1_used"]:
        raise ValueError("E1 no puede utilizarse para selección.")
    baseline = dict(
        id="baseline_v1_recipe",
        family="lightgbm",
        features="original",
        params=dict(
            n_estimators=150,
            max_depth=3,
            num_leaves=7,
            learning_rate=0.05,
            verbosity=-1,
            random_state=42,
            n_jobs=1,
        ),
    )
    output.mkdir(parents=True)
    write_json(output / "design.json", design)
    write_json(
        output / "status.json",
        {"status": "running", "manifest_sha256": sha256(manifest_path)},
    )
    rows = []
    try:
        for fold in prepared_manifest["folds"]:
            if fold["id"] not in ["D1", "D2"]:
                continue
            frames = {}
            for role, info in fold["roles"].items():
                path = prepared / info["file"]
                if sha256(path) != info["sha256"]:
                    raise ValueError("CSV alterado.")
                frames[role] = pd.read_csv(path)
            train, calibration, evaluation = (
                frames[k] for k in ["train", "calibration", "evaluation"]
            )
            for config in [*configs, baseline]:
                columns = FEATURE_SETS[config["features"]]
                model = estimator(config)
                model.fit(train[columns], train["Churn"])
                calibrated = CalibratedClassifierCV(
                    FrozenEstimator(model), method="sigmoid"
                )
                calibrated.fit(calibration[columns], calibration["Churn"])
                probability = calibrated.predict_proba(evaluation[columns])[:, 1]
                raw = model.predict_proba(evaluation[columns])[:, 1]
                prefix = f'{fold["id"]}_{config["id"]}'
                joblib.dump(
                    {
                        "raw": model,
                        "calibrated": calibrated,
                        "features": columns,
                        "config": config,
                    },
                    output / f"{prefix}.joblib",
                )
                predictions = evaluation[["Customer ID", "cutoff", "Churn"]].copy()
                predictions["raw_probability"] = raw
                predictions["probability"] = probability
                predictions.to_csv(output / f"{prefix}.csv", index=False)
                rows.append(
                    dict(
                        id=config["id"],
                        fold=fold["id"],
                        feature_count=len(columns),
                        **scores(evaluation, probability),
                        raw_metrics=scores(evaluation, raw),
                    )
                )
            for name, p in [
                ("baseline_recency", evaluation["Recency"].to_numpy() / 180),
                ("baseline_constant", np.full(len(evaluation), train["Churn"].mean())),
            ]:
                rows.append(
                    dict(
                        id=name,
                        fold=fold["id"],
                        feature_count=1,
                        **scores(evaluation, p),
                    )
                )
            write_json(output / "metrics.json", rows)
            print(
                f'{fold["id"]}: 18 candidatos y 3 referencias completados.', flush=True
            )
        summary = []
        for name in sorted({row["id"] for row in rows}):
            selected = [row for row in rows if row["id"] == name]
            summary.append(
                dict(
                    id=name,
                    feature_count=selected[0]["feature_count"],
                    **{
                        metric: float(np.mean([row[metric] for row in selected]))
                        for metric in ["precision_at_20", "average_precision", "brier"]
                    },
                )
            )
        ranking = rank_candidates(
            [row for row in summary if not row["id"].startswith("baseline_")]
        )
        winner = next(c for c in configs if c["id"] == ranking[0]["id"])
        write_json(
            output / "selection.json",
            {
                "candidate": winner,
                "ranking": ranking,
                "comparators": [r for r in summary if r["id"].startswith("baseline_")],
                "E1_used": False,
                "promoted": False,
                "next": "MEJ-05: calibration and thresholds; MEJ-06: exploratory acceptance.",
            },
        )
        write_json(
            output / "status.json",
            {
                "status": "complete",
                "manifest_sha256": sha256(manifest_path),
                "prepared_manifest_sha256": sha256(prepared / "manifest.json"),
                "code_sha256": sha256(Path(__file__)),
                "versions": {
                    p: importlib.metadata.version(p)
                    for p in ["numpy", "pandas", "scikit-learn", "lightgbm", "joblib"]
                },
                "files": {
                    p.name: sha256(p)
                    for p in sorted(output.iterdir())
                    if p.name != "status.json"
                },
            },
        )
    except Exception as error:
        write_json(output / "status.json", {"status": "failed", "error": str(error)})
        raise
    return ranking[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-plan", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--prepared", type=Path, default=ROOT / "docs/evidencias_mej03/preparacion"
    )
    args = parser.parse_args()
    if args.freeze_plan:
        if args.freeze_plan.exists():
            raise FileExistsError("El manifiesto ya existe.")
        write_json(args.freeze_plan, plan())
    elif args.manifest and args.output:
        print(run(args.prepared, args.manifest, args.output))
    else:
        parser.error("Usar --freeze-plan o --manifest con --output")
