"""Admisión, saturación y recuperación sin depender de la velocidad del modelo."""

import asyncio
import importlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

main = importlib.import_module("backend.main")
SAMPLE = json.loads(
    (Path(__file__).parents[1] / "deploy/acceptance_request.json").read_text()
)
KEY = "test-capacity-only-credential-12345678901234"


def test_saturation_and_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHURN_API_KEY", KEY)
    entered = threading.Event()
    release = threading.Event()
    original = main.ChurnPredictor.predict_many
    monkeypatch.setattr(main, "MAX_INFLIGHT", 1)

    def blocked(self, rows):
        entered.set()
        assert release.wait(10)
        return original(self, rows)

    monkeypatch.setattr(main.ChurnPredictor, "predict_many", blocked)
    with TestClient(
        main.app, base_url="https://localhost", client=("127.0.0.1", 9)
    ) as client:
        headers = {"X-API-Key": KEY}
        with ThreadPoolExecutor(1) as pool:
            pending = pool.submit(
                client.post, "/v1/predict", json=SAMPLE, headers=headers
            )
            try:
                assert entered.wait(5)
                busy = client.post("/v1/predict", json=SAMPLE, headers=headers)
                assert busy.status_code == 503
                assert busy.headers["Retry-After"] == "1"
                assert busy.json()["error"]["code"] == "capacity_exceeded"
                assert client.get("/health/live").status_code == 200
                assert client.post("/v1/predict", json=SAMPLE).status_code == 401
            finally:
                release.set()
            assert pending.result().status_code == 200
        assert main.app.state.inflight == 0
        assert (
            client.post("/v1/predict", json=SAMPLE, headers=headers).status_code == 200
        )
        assert client.post("/v1/predict", json={}, headers=headers).status_code == 422
        assert main.app.state.inflight == 0


def test_body_timeout_releases_capacity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHURN_API_KEY", KEY)
    monkeypatch.setattr(main, "BODY_TIMEOUT_SECONDS", 0.02)
    original = main.read_body

    async def slow(request):
        await asyncio.sleep(1)
        return await original(request)

    with TestClient(
        main.app, base_url="https://localhost", client=("127.0.0.1", 9)
    ) as client:
        monkeypatch.setattr(main, "read_body", slow)
        response = client.post("/v1/predict", json=SAMPLE, headers={"X-API-Key": KEY})
        assert response.status_code == 408
        assert main.app.state.inflight == 0
        monkeypatch.setattr(main, "read_body", original)
        assert (
            client.post(
                "/v1/predict", json=SAMPLE, headers={"X-API-Key": KEY}
            ).status_code
            == 200
        )
