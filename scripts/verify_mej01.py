"""Verifica los supuestos congelados de MEJ-01 sin entrenar modelos."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "ML/experiments/churn180-v2/protocol.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%d/%m/%Y").date()


def main() -> None:
    protocol: dict[str, Any] = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = protocol["source"]
    baseline = protocol["baseline"]
    csv_path = ROOT / ".local/crm01-stage/train.csv"
    checks: dict[str, bool] = {
        "protocol_schema": protocol["schema_version"] == "churn180-v2-experimental",
        "design_only": protocol["status"] == "design_only_mej01",
        "zip_hash": sha256(ROOT / source["dataset_zip"]) == source["dataset_zip_sha256"],
        "csv_hash": sha256(csv_path) == source["dataset_csv_sha256"],
        "model_hash": sha256(ROOT / "ML/artifacts/churn180-v1/model.joblib") == baseline["model_sha256"],
        "metadata_hash": sha256(ROOT / "ML/artifacts/churn180-v1/metadata.json") == baseline["metadata_sha256"],
        "v1_protocol_hash": sha256(ROOT / "ML/protocol.json") == baseline["protocol_sha256"],
        "no_smote_first_round": protocol["smote"] == "not_allowed_in_first_round",
        "e1_not_for_selection": protocol["selection"]["evaluation_cutoff_not_for_selection"] == "E1",
        "automatic_actions_disabled": protocol["immutability"]["automatic_action_allowed"] is False,
    }
    with zipfile.ZipFile(ROOT / source["dataset_zip"]) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
    checks["single_csv_in_zip"] = len(members) == 1
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    dates = [parse_date(row["Order Date"]) for row in rows]
    checks["row_count"] = len(rows) == source["expected_rows"]
    checks["customer_count"] = len({row["Customer ID"].strip() for row in rows}) == source["expected_customers"]
    checks["order_count"] = len({row["Order ID"].strip() for row in rows}) == source["expected_orders"]
    checks["coverage"] = min(dates) == date(2015, 1, 3) and max(dates) == date(2018, 12, 30)
    cutoff_report = []
    for evaluation in protocol["evaluations"]:
        train = [date.fromisoformat(value) for value in evaluation["train_cutoffs"]]
        calibration = date.fromisoformat(evaluation["calibration_cutoff"])
        tested = date.fromisoformat(evaluation["evaluation_cutoff"])
        history_start = tested - timedelta(days=protocol["definition"]["lookback_days"])
        label_end = tested + timedelta(days=protocol["definition"]["horizon_days"])
        valid = (
            train == sorted(train)
            and train[-1] < calibration < tested
            and min(dates) < history_start
            and label_end <= max(dates)
        )
        cutoff_report.append({
            "id": evaluation["id"],
            "train_cutoffs": [value.isoformat() for value in train],
            "calibration_cutoff": calibration.isoformat(),
            "evaluation_cutoff": tested.isoformat(),
            "history_start_exclusive": history_start.isoformat(),
            "label_end_inclusive": label_end.isoformat(),
            "chronology_and_coverage_valid": valid,
        })
    checks["all_cutoff_chronology_and_coverage"] = all(row["chronology_and_coverage_valid"] for row in cutoff_report)
    report = {
        "date": "2026-10-29",
        "protocol_sha256": sha256(PROTOCOL),
        "checks": checks,
        "cutoffs": cutoff_report,
        "scope": "Verificación MEJ-01; no entrena, calibra, evalúa ni modifica ningún modelo.",
    }
    evidence = ROOT / "docs/evidencias_mej01"
    evidence.mkdir(exist_ok=True)
    (evidence / "verificacion.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise SystemExit(json.dumps(report, ensure_ascii=False))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
