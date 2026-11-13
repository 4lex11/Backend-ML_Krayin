"""Valida el esquema temporal de MEJ-02 sin entrenar modelos."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ML.features import clean_transactions  # noqa: E402
from ML.features_v2 import TEMPORAL_FEATURE_NAMES, build_temporal_features  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    protocol_path = ROOT / "ML/experiments/churn180-v2/protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    raw = pd.read_csv(ROOT / ".local/crm01-stage/train.csv")
    data, quality = clean_transactions(raw)
    reports = []
    for evaluation in protocol["evaluations"]:
        cutoff = evaluation["evaluation_cutoff"]
        frame = build_temporal_features(data, cutoff)
        changed = data.copy()
        changed.loc[changed["Order Date"].gt(cutoff), "Sales"] = 999999.0
        changed.loc[changed["Order Date"].gt(cutoff), "Order ID"] = "future-only"
        pd.testing.assert_frame_equal(frame, build_temporal_features(changed, cutoff))
        reports.append(
            {
                "id": evaluation["id"],
                "cutoff": cutoff,
                "customers": int(len(frame)),
                "columns": list(frame.columns),
                "all_finite": bool(np.isfinite(frame.to_numpy()).all()),
                "single_order_customers": int((frame["HasMultipleOrders"] == 0).sum()),
                "future_mutation_does_not_change_features": True,
            }
        )
    checks = {
        "dataset_hash": sha256(ROOT / ".local/crm01-stage/train.csv")
        == protocol["source"]["dataset_csv_sha256"],
        "clean_rows": quality["clean_rows"] == protocol["source"]["expected_rows"],
        "feature_schema": tuple(protocol["temporal_features"])
        == TEMPORAL_FEATURE_NAMES,
        "all_cutoffs_have_customers": all(row["customers"] > 0 for row in reports),
        "all_cutoffs_are_finite": all(row["all_finite"] for row in reports),
        "all_cutoffs_ignore_future_rows": all(
            row["future_mutation_does_not_change_features"] for row in reports
        ),
    }
    report = {
        "date": "2026-10-29",
        "protocol_sha256": sha256(protocol_path),
        "checks": checks,
        "cutoffs": reports,
        "scope": "Verificación MEJ-02; construye variables temporales, pero no entrena ni modifica modelos.",
    }
    target = ROOT / "docs/evidencias_mej02"
    target.mkdir(exist_ok=True)
    (target / "verificacion.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise SystemExit(json.dumps(report, ensure_ascii=False))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
