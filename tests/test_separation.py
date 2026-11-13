"""Pruebas del contrato temporal, integridad de artefactos y API autenticada."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app, get_predictor
from ML.evaluation import bootstrap_intervals, metrics, select_thresholds
from ML.features import FEATURE_NAMES, build_features, clean_transactions, make_snapshot
from ML.inference import DEFAULT_MODEL_PATH, ChurnPredictor, validate_features
from ML.train import ROOT, run_training

KEY = "test-only-credential-not-for-deployment-123456"
SAMPLE = {
    "Recency": 20,
    "Frequency": 2,
    "Monetary_Sum": 100.0,
    "Monetary_Mean": 50.0,
    "Monetary_Std": 10.0,
    "Cat_Count": 1,
    "SubCat_Count": 2,
}
PAYLOAD = {"customer_id": "TEST-01", "as_of": "2018-06-30", "features": SAMPLE}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CHURN_API_KEY", KEY)
    monkeypatch.delenv("CHURN_MODEL_PATH", raising=False)
    with TestClient(
        app,
        raise_server_exceptions=False,
        base_url="https://localhost",
        client=("127.0.0.1", 50000),
    ) as session:
        session.headers["X-API-Key"] = KEY
        yield session
    app.dependency_overrides.clear()


@pytest.fixture
def predictor() -> ChurnPredictor:
    return ChurnPredictor.load()


def raw_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [1, "A", "old", "01/01/2015", 10.0, "C", "S"],
            [2, "A", "a", "08/11/2017", 20.0, "C", "S"],
            [3, "A", "b", "30/06/2018", 30.0, "C", "T"],
            [4, "B", "c", "01/01/2018", 5.0, "C", "S"],
            [5, "B", "d", "01/07/2018", 8.0, "C", "S"],
            [6, "Z", "last", "30/12/2018", 10.0, "C", "S"],
        ],
        columns=[
            "Row ID",
            "Customer ID",
            "Order ID",
            "Order Date",
            "Sales",
            "Category",
            "Sub-Category",
        ],
    )


def test_date_and_temporal_boundaries() -> None:
    data, quality = clean_transactions(raw_data())
    assert data.loc[1, "Order Date"] == pd.Timestamp("2017-11-08")
    assert quality["clean_rows"] == 6
    snapshot = make_snapshot(data, "2018-06-30")
    assert snapshot.loc["A", "Churn"] == 1
    assert snapshot.loc["B", "Churn"] == 0
    assert snapshot.loc["A", "Monetary_Sum"] == 50
    assert snapshot.loc["B", "Recency"] == 180
    assert snapshot.loc["B", "Monetary_Std"] == 0
    changed = data.copy()
    changed.loc[changed["Order Date"].gt("2018-06-30"), "Sales"] = 99999.0
    pd.testing.assert_frame_equal(
        build_features(data, "2018-06-30"), build_features(changed, "2018-06-30")
    )
    with pytest.raises(ValueError, match="futuro"):
        make_snapshot(data, "2018-12-30")
    with pytest.raises(ValueError, match="histórica"):
        make_snapshot(data, "2015-06-30")


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "null",
        "empty",
        "negative",
        "infinite",
        "bad_date",
        "duplicate_id",
        "order_conflict",
        "null_id",
    ],
)
def test_bad_transactions(kind: str) -> None:
    data = raw_data()
    if kind == "missing":
        data = data.drop(columns="Sales")
    if kind == "null":
        data.loc[0, "Sales"] = None
    if kind == "empty":
        data.loc[0, "Category"] = "  "
    if kind == "negative":
        data.loc[0, "Sales"] = -1
    if kind == "infinite":
        data.loc[0, "Sales"] = float("inf")
    if kind == "bad_date":
        data.loc[0, "Order Date"] = "30/02/2018"
    if kind == "duplicate_id":
        data.loc[1, "Row ID"] = 1
    if kind == "order_conflict":
        data.loc[1, "Order ID"] = "old"
    if kind == "null_id":
        data.loc[0, "Row ID"] = None
    with pytest.raises(ValueError):
        clean_transactions(data)


def test_exact_duplicate_and_window() -> None:
    raw = raw_data()
    data, quality = clean_transactions(pd.concat([raw, raw.iloc[[0]]]))
    assert quality["exact_duplicates_removed"] == 1
    cutoff = pd.Timestamp("2018-06-30")
    data.loc[1, "Order Date"] = cutoff - pd.Timedelta(days=365)
    result = build_features(data, str(cutoff.date()))
    assert result.loc["A", "Monetary_Sum"] == 30
    assert build_features(data, "2020-01-01").empty


@pytest.mark.parametrize(
    "change",
    [
        {"Recency": 181},
        {"Frequency": 0},
        {"Cat_Count": 3},
        {"Monetary_Mean": 101},
        {"Monetary_Mean": 0},
        {"Monetary_Std": 102},
        {"Frequency": 1.5},
        {"Frequency": True},
        {"Monetary_Sum": float("nan")},
        {"Monetary_Sum": -1},
    ],
)
def test_feature_domain(change: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        validate_features({**SAMPLE, **change})


def test_inference_contract(predictor: ChurnPredictor) -> None:
    with pytest.raises(ValueError):
        predictor.predict_probability({})
    with pytest.raises(ValueError):
        predictor.predict_many([])
    expected = predictor.model.predict_proba(
        pd.DataFrame([SAMPLE], columns=list(FEATURE_NAMES))
    )[0, 1]
    assert (
        predictor.predict_probability(dict(reversed(list(SAMPLE.items())))) == expected
    )
    assert predictor.predict_many([SAMPLE, SAMPLE]) == [expected, expected]
    assert predictor.risk(0) == "Bajo"
    assert predictor.risk(predictor.thresholds["medium"]) == "Medio"
    assert predictor.risk(predictor.thresholds["high"]) == "Alto"
    with patch.object(
        predictor.model, "predict_proba", return_value=np.array([[0, float("nan")]])
    ):
        with pytest.raises(ValueError):
            predictor.predict_probability(SAMPLE)


def test_model_integrity(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ChurnPredictor.load(tmp_path / "model.joblib")
    path = tmp_path / "model.joblib"
    path.write_bytes(b"broken")
    manifest = json.loads(DEFAULT_MODEL_PATH.with_name("metadata.json").read_text())
    (tmp_path / "metadata.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="hash"):
        ChurnPredictor.load(path)
    manifest["model_sha256"] = hashlib.sha256(b"broken").hexdigest()
    manifest["versions"] = {"numpy": "0.0"}
    (tmp_path / "metadata.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Versión incompatible"):
        ChurnPredictor.load(path)


@pytest.mark.parametrize("kind", ["features", "classes", "version", "thresholds"])
def test_bundle_contract(kind: str) -> None:
    import joblib

    bundle = joblib.load(DEFAULT_MODEL_PATH)
    if kind == "features":
        bundle["features"] = ["wrong"]
    if kind == "classes":
        bundle["model"].classes_ = np.array([0, 2])
    if kind == "version":
        bundle["version"] = "wrong"
    if kind == "thresholds":
        bundle["thresholds"] = {"medium": 0, "high": 1}
    with patch("ML.inference.joblib.load", return_value=bundle):
        with pytest.raises(ValueError):
            ChurnPredictor.load()


def test_api_authorization_health(client: TestClient) -> None:
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").json()["automatic_action_allowed"] is False
    client.headers.pop("X-API-Key")
    assert client.get("/health/ready").status_code == 401
    assert client.post("/v1/predict", json=PAYLOAD).status_code == 401
    assert (
        client.post(
            "/v1/predict", json=PAYLOAD, headers={"X-API-Key": "wrong"}
        ).status_code
        == 401
    )
    assert client.get("/missing").status_code == 404


def test_api_predictions(client: TestClient, predictor: ChurnPredictor) -> None:
    one = client.post("/v1/predict", json=PAYLOAD)
    assert one.status_code == 200, one.text
    result = one.json()
    assert result["probabilidad_churn"] == predictor.predict_probability(SAMPLE)
    assert result["model_status"] == "experimental"
    assert result["automatic_action_allowed"] is False
    assert one.headers["X-Request-ID"]
    second = {**PAYLOAD, "customer_id": "TEST-02"}
    batch = client.post("/v1/predict/batch", json={"customers": [PAYLOAD, second]})
    assert [r["customer_id"] for r in batch.json()] == ["TEST-01", "TEST-02"]
    for customers in [
        [],
        [PAYLOAD, PAYLOAD],
        [{**PAYLOAD, "customer_id": str(i)} for i in range(501)],
    ]:
        assert (
            client.post("/v1/predict/batch", json={"customers": customers}).status_code
            == 422
        )


@pytest.mark.parametrize(
    "change",
    [
        {"unknown": 1},
        {"Frequency": -1},
        {"Frequency": 1.5},
        {"Monetary_Mean": 200},
        {"Recency": 181},
    ],
)
def test_api_invalid_fields(client: TestClient, change: dict[str, Any]) -> None:
    payload = deepcopy(PAYLOAD)
    payload["features"].update(change)
    result = client.post("/v1/predict", json=payload)
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "validation_error"


def test_api_nan_body_limit_errors(
    client: TestClient, predictor: ChurnPredictor
) -> None:
    assert client.post("/v1/predict", json={}).status_code == 422
    invalid = json.dumps(PAYLOAD).replace(
        '"Monetary_Sum": 100.0', '"Monetary_Sum": NaN'
    )
    assert (
        client.post(
            "/v1/predict", content=invalid, headers={"Content-Type": "application/json"}
        ).status_code
        == 422
    )
    assert client.post("/v1/predict", content=b"x" * 2_000_001).status_code == 413
    app.dependency_overrides[get_predictor] = lambda: predictor
    with patch.object(
        predictor.model,
        "predict_proba",
        side_effect=RuntimeError("internal-path-should-not-leak"),
    ):
        result = client.post("/v1/predict", json=PAYLOAD)
        assert result.status_code == 500
        assert "internal-path-should-not-leak" not in result.text


def tx_payload() -> dict[str, Any]:
    return {
        "customer_id": "A",
        "as_of": "2018-06-30",
        "history_start": "2017-06-30",
        "transactions": [
            {
                "line_id": "1",
                "order_id": "O1",
                "order_date": "2018-06-20",
                "sales": 10,
                "category": "C",
                "subcategory": "S",
            },
            {
                "line_id": "2",
                "order_id": "O2",
                "order_date": "2018-06-25",
                "sales": 20,
                "category": "C",
                "subcategory": "S",
            },
        ],
    }


def test_transactions_parity(client: TestClient) -> None:
    request = tx_payload()
    result = client.post("/v1/predict/transactions", json=request)
    assert result.status_code == 200, result.text
    expected = {
        "customer_id": "A",
        "as_of": "2018-06-30",
        "features": {
            "Recency": 5,
            "Frequency": 2,
            "Monetary_Sum": 30,
            "Monetary_Mean": 15,
            "Monetary_Std": float(np.std([10, 20], ddof=1)),
            "Cat_Count": 1,
            "SubCat_Count": 1,
        },
    }
    assert (
        result.json()["probabilidad_churn"]
        == client.post("/v1/predict", json=expected).json()["probabilidad_churn"]
    )


@pytest.mark.parametrize(
    "kind",
    ["coverage", "future", "before_start", "inactive", "duplicate", "empty_category"],
)
def test_transactions_errors(client: TestClient, kind: str) -> None:
    p = tx_payload()
    if kind == "coverage":
        p["history_start"] = "2018-01-01"
    if kind == "future":
        p["transactions"][0]["order_date"] = "2018-07-01"
    if kind == "before_start":
        p["transactions"][0]["order_date"] = "2017-01-01"
    if kind == "inactive":
        for item in p["transactions"]:
            item["order_date"] = "2017-07-01"
    if kind == "duplicate":
        p["transactions"][1]["line_id"] = "1"
    if kind == "empty_category":
        p["transactions"][0]["category"] = " "
    assert client.post("/v1/predict/transactions", json=p).status_code == 422


def test_startup_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHURN_API_KEY", raising=False)
    with pytest.raises(ValueError, match="CHURN_API_KEY"):
        with TestClient(app):
            pass
    monkeypatch.setenv("CHURN_API_KEY", KEY)
    monkeypatch.setenv("CHURN_MODEL_PATH", "missing/model.joblib")
    with pytest.raises(FileNotFoundError):
        with TestClient(app):
            pass


def test_evaluation() -> None:
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert metrics(y, p)["roc_auc"] == 1
    limits = select_thresholds(y, p)
    assert limits["medium"] < limits["high"]
    assert bootstrap_intervals(y, p, 0.5, 20)["roc_auc"] == [1.0, 1.0]


def test_training_pipeline(tmp_path: Path) -> None:
    protocol = json.loads((ROOT / "ML/protocol.json").read_text())
    protocol["bootstrap_repetitions"] = 10
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(protocol))
    report = run_training(
        ROOT / "ML/Datasets/train.csv", path, tmp_path / "verification"
    )
    assert report["selected_model"] == "LightGBM"
    original = json.loads(DEFAULT_MODEL_PATH.with_name("metadata.json").read_text())
    assert report["test"] == original["test"]
    assert (
        ChurnPredictor.load(tmp_path / "verification/model.joblib").version
        == "verification"
    )
    assert len(list((tmp_path / "verification/figures").glob("*.png"))) == 6
    protocol["train_cutoffs"] = ["2016-06-30", "2016-07-01"]
    path.write_text(json.dumps(protocol))
    with pytest.raises(ValueError, match="ventanas"):
        run_training(ROOT / "ML/Datasets/train.csv", path, tmp_path / "bad")


@pytest.mark.parametrize(
    "change", [{"seed": 1}, {"horizon_days": 90}, {"bootstrap_repetitions": 0}]
)
def test_reject_unsupported_protocol(tmp_path: Path, change: dict[str, Any]) -> None:
    protocol = json.loads((ROOT / "ML/protocol.json").read_text())
    protocol.update(change)
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(protocol))
    with pytest.raises(ValueError):
        run_training(ROOT / "ML/Datasets/train.csv", path, tmp_path / "unused")
    assert not (tmp_path / "unused").exists()
