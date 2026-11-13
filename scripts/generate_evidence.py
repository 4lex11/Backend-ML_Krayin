"""Guarda evidencia HTTP en memoria y latencia local, sin levantar un servidor permanente."""

import json
import os
import secrets
import statistics
import time
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from ML.features import FEATURE_NAMES

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Crea archivos para revisar y capturar; la credencial temporal no se guarda."""
    folder = ROOT / "docs/evidencias_api"
    folder.mkdir(exist_ok=True)
    token = secrets.token_urlsafe(48)
    os.environ["CHURN_API_KEY"] = token
    frame = pd.read_csv(ROOT / "ML/artifacts/churn180-v1/test_predictions.csv")
    row = frame.iloc[0]
    features = {name: float(row[name]) for name in FEATURE_NAMES}
    for name in ("Recency", "Frequency", "Cat_Count", "SubCat_Count"):
        features[name] = int(features[name])
    sample = {"customer_id": "DEMO-001", "as_of": "2018-06-30", "features": features}
    batch = {"customers": [{**sample, "customer_id": f"BENCH-{i}"} for i in range(500)]}
    with TestClient(
        app,
        raise_server_exceptions=False,
        base_url="https://localhost",
        client=("127.0.0.1", 50000),
    ) as client:
        client.headers["X-API-Key"] = token
        one = client.post("/v1/predict", json=sample)
        assert one.status_code == 200, one.text
        invalid = client.post("/v1/predict", json={})
        unauthorized = client.post(
            "/v1/predict", json=sample, headers={"X-API-Key": "invalid"}
        )
        ready = client.get("/health/ready")
        evidence = {
            "request": sample,
            "response": one.json(),
            "response_status": one.status_code,
            "invalid_request_status": invalid.status_code,
            "unauthorized_status": unauthorized.status_code,
            "readiness": ready.json(),
            "scope": "TestClient ASGI en memoria, sin red real ni persistencia en Krayin.",
        }
        client.post("/v1/predict/batch", json=batch).raise_for_status()
        benchmark = {}
        for name, endpoint, payload in [
            ("single", "/v1/predict", sample),
            ("batch_500", "/v1/predict/batch", batch),
        ]:
            elapsed = []
            for _ in range(20):
                start = time.perf_counter()
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                elapsed.append((time.perf_counter() - start) * 1000)
            benchmark[name] = {
                "runs": 20,
                "median_ms": statistics.median(elapsed),
                "max_ms": max(elapsed),
                "scope": "secuencial, local, en memoria; no prueba de concurrencia ni red",
            }
        for name, value in [
            ("01_solicitud.json", sample),
            ("02_respuesta.json", one.json()),
            ("03_verificacion.json", evidence),
            ("04_benchmark.json", benchmark),
            ("05_openapi.json", app.openapi()),
        ]:
            (folder / name).write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    print(json.dumps({"status": "ok", "benchmark": benchmark}, indent=2))


if __name__ == "__main__":
    main()
