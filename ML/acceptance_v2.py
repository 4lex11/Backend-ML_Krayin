"""MEJ-06: aceptación exploratoria del candidato congelado."""

import argparse
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import average_precision_score

from ML.calibration_v2 import classification, exact_capacity_threshold
from ML.compare_v2 import estimator, scores, write_json
from ML.inference import ChurnPredictor
from ML.temporal_validation import FEATURE_SETS, ROOT, sha256


def verify_files(folder, manifest):
    for name, digest in manifest["files"].items():
        if sha256(folder / name) != digest:
            raise ValueError(f"Artefacto alterado: {name}")


def paired_bootstrap(frames, repeats=1000, seed=42):
    """Remuestrea clientes una vez por réplica y conserva todos sus cortes."""
    customers = sorted(set().union(*(set(f["Customer ID"]) for f in frames)))
    rng = np.random.default_rng(seed)
    deltas = {name: [] for name in ["recency", "recipe"]}
    for _ in range(repeats):
        sampled = rng.choice(customers, len(customers), replace=True)
        fold_metrics = []
        for frame in frames:
            indexed = frame.set_index("Customer ID")
            present = sampled[np.isin(sampled, indexed.index)]
            subset = indexed.loc[present].reset_index()
            if not len(subset) or subset["Churn"].nunique() < 2:
                break
            y = subset["Churn"].to_numpy()
            metrics = {}
            for name in ["candidate", "recency", "recipe"]:
                p = subset[name].to_numpy()
                order = np.lexsort((subset["Customer ID"].to_numpy(), -p))
                k = math.ceil(0.2 * len(y))
                metrics[name] = np.array(
                    [y[order[:k]].mean(), average_precision_score(y, p)]
                )
            fold_metrics.append(metrics)
        if len(fold_metrics) != len(frames):
            continue
        for name in deltas:
            deltas[name].append(
                np.mean([m["candidate"] - m[name] for m in fold_metrics], axis=0)
            )
    return {
        name: dict(
            valid_replicates=len(values),
            requested_replicates=repeats,
            precision_at_20_ci95=(
                np.quantile(values, [0.025, 0.975], axis=0)[:, 0].tolist()
                if len(values) >= repeats * 0.9
                else None
            ),
            ap_ci95=(
                np.quantile(values, [0.025, 0.975], axis=0)[:, 1].tolist()
                if len(values) >= repeats * 0.9
                else None
            ),
        )
        for name, values in deltas.items()
    }


def gates(metrics, intervals):
    def mean(name, metric):
        return float(np.mean([metrics[f][name][metric] for f in ["D1", "D2", "E1"]]))

    checks = {}
    for comparator in ["recency", "recipe"]:
        checks[f"precision_gain_{comparator}"] = (
            mean("candidate", "precision_at_20") - mean(comparator, "precision_at_20")
            >= 0.05
        )
        checks[f"wins_two_cuts_{comparator}"] = (
            sum(
                metrics[f]["candidate"]["precision_at_20"]
                > metrics[f][comparator]["precision_at_20"]
                for f in metrics
            )
            >= 2
        )
        checks[f"ap_gain_{comparator}"] = (
            mean("candidate", "average_precision")
            - mean(comparator, "average_precision")
            >= 0.02
        )
        checks[f"ap_stability_{comparator}"] = all(
            metrics[f]["candidate"]["average_precision"]
            >= metrics[f][comparator]["average_precision"] - 0.02
            for f in metrics
        )
        interval = intervals[comparator]["precision_at_20_ci95"]
        checks[f"positive_ci_{comparator}"] = interval is not None and interval[0] > 0
    for comparator in ["recency", "recipe", "installed"]:
        checks[f"E1_beats_{comparator}"] = all(
            metrics["E1"]["candidate"][m] > metrics["E1"][comparator][m]
            for m in ["precision_at_20", "average_precision"]
        )
    for comparator in ["constant", "recipe"]:
        checks[f"brier_{comparator}"] = (
            mean("candidate", "brier") <= mean(comparator, "brier") + 0.01
        )
    checks["E1_brier_installed"] = (
        metrics["E1"]["candidate"]["brier"]
        <= metrics["E1"]["installed"]["brier"] + 0.01
    )
    return checks


def run(output):
    if output.exists():
        raise FileExistsError("El destino debe ser nuevo.")
    prepared = ROOT / "docs/evidencias_mej03/preparacion"
    comparison = ROOT / "docs/evidencias_mej04/comparacion"
    calibration = ROOT / "docs/evidencias_mej05/calibracion"

    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    status = load(comparison / "status.json")
    verify_files(comparison, status)
    verify_files(calibration, load(calibration / "manifest.json"))
    policy = load(calibration / "frozen_policy.json")
    if (
        policy["selection_sha256"] != sha256(comparison / "selection.json")
        or policy["E1_used"]
    ):
        raise ValueError("Política no congelada correctamente.")
    if sha256(prepared / "manifest.json") != status["prepared_manifest_sha256"]:
        raise ValueError("Preparación alterada.")
    manifest = load(prepared / "manifest.json")
    protocol = load(prepared / "protocol.json")
    model_path = ROOT / "ML/artifacts/churn180-v1/model.joblib"
    before = sha256(model_path)
    if before != protocol["baseline"]["model_sha256"]:
        raise ValueError("Referencia v1 alterada.")
    output.mkdir(parents=True)
    write_json(output / "frozen_policy.json", policy)
    frames, metrics, thresholds = [], {}, []
    for fold in manifest["folds"]:
        data = {}
        for role, info in fold["roles"].items():
            path = prepared / info["file"]
            if sha256(path) != info["sha256"]:
                raise ValueError("CSV alterado.")
            data[role] = pd.read_csv(path)
        frame = data["evaluation"][["Customer ID", "cutoff", "Churn"]].copy()
        if fold["id"] in ["D1", "D2"]:
            candidate = pd.read_csv(
                calibration / f'{fold["id"]}_{policy["variant"]}.csv'
            )
            recipe = pd.read_csv(comparison / f'{fold["id"]}_baseline_v1_recipe.csv')
            for predictions in [candidate, recipe]:
                pd.testing.assert_frame_equal(frame, predictions[frame.columns])
            frame["candidate"] = candidate["probability"]
            frame["recipe"] = recipe["probability"]
        else:
            recipe_config = dict(
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
            for name, config in [
                ("candidate", policy["candidate"]),
                ("recipe", recipe_config),
            ]:
                columns = FEATURE_SETS[config["features"]]
                raw = estimator(config)
                raw.fit(data["train"][columns], data["train"]["Churn"])
                calibrated = CalibratedClassifierCV(
                    FrozenEstimator(raw), method="sigmoid"
                )
                calibrated.fit(
                    data["calibration"][columns], data["calibration"]["Churn"]
                )
                model = (
                    raw
                    if name == "candidate" and policy["variant"] == "raw"
                    else calibrated
                )
                frame[name] = model.predict_proba(data["evaluation"][columns])[:, 1]
                joblib.dump(
                    dict(
                        raw=raw, calibrated=calibrated, config=config, features=columns
                    ),
                    output / f"E1_{name}.joblib",
                )
                if name == "candidate":
                    cal_p = model.predict_proba(data["calibration"][columns])[:, 1]
                    for fraction in [0.1, 0.2, 0.3]:
                        threshold = exact_capacity_threshold(cal_p, fraction)
                        thresholds.append(
                            dict(
                                fraction=fraction,
                                threshold=threshold,
                                evaluation=(
                                    classification(
                                        frame["Churn"], frame[name], threshold
                                    )
                                    if threshold is not None
                                    else None
                                ),
                            )
                        )
            installed = ChurnPredictor.load()
            frame["installed"] = installed.predict_many(
                data["evaluation"][FEATURE_SETS["original"]].to_dict("records")
            )
        frame["recency"] = data["evaluation"]["Recency"] / 180
        frame["constant"] = data["train"]["Churn"].mean()
        metrics[fold["id"]] = {
            name: scores(frame, frame[name])
            for name in frame.columns
            if name not in ["Customer ID", "cutoff", "Churn"]
        }
        frame.to_csv(output / f'{fold["id"]}_predictions.csv', index=False)
        frames.append(frame)
    print("E1 evaluado; calculando 1000 remuestreos pareados de clientes.", flush=True)
    intervals = paired_bootstrap(frames)
    checks = gates(metrics, intervals)
    checks["v1_unchanged"] = sha256(model_path) == before
    checks["common_population_and_finite_predictions"] = True
    decision = dict(
        accepted=all(checks.values()),
        checks=checks,
        decision=(
            "eligible_for_experimental_integration"
            if all(checks.values())
            else "retain_v1"
        ),
        E1_is_independent_test=False,
    )
    for name, content in [
        ("metrics", metrics),
        ("bootstrap", intervals),
        ("thresholds", thresholds),
        ("decision", decision),
    ]:
        write_json(output / f"{name}.json", content)
    write_json(
        output / "manifest.json",
        dict(
            status="complete",
            code_sha256=sha256(Path(__file__)),
            policy_sha256=sha256(calibration / "frozen_policy.json"),
            files={p.name: sha256(p) for p in sorted(output.iterdir())},
        ),
    )
    return decision


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(run(parser.parse_args().output))
