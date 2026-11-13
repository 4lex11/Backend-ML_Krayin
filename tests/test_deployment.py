"""API-07: integridad de entregas, configuración y parada administrada."""

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
import uvicorn

from deploy import acceptance, release, runtime

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def package(tmp_path: Path) -> Path:
    return release.build(ROOT, tmp_path / "deliveries", "test-v1")


def test_release_isolated(package: Path) -> None:
    manifest = release.verify(package)
    assert manifest["model_version"] == "churn180-v1"
    assert not (package / "ML/Datasets").exists()
    assert not (package / ".local").exists()
    assert not (package / "integraciones").exists()
    assert not (package / ".venv").exists()
    assert manifest["files"]["requirements-lock.txt"] == release.digest(
        ROOT / "requirements-lock.txt"
    )
    with pytest.raises(FileExistsError):
        release.build(ROOT, package.parent, "test-v1")


@pytest.mark.parametrize("version", ["../escape", "", "/absolute", "x" * 65])
def test_release_bad_version(tmp_path: Path, version: str) -> None:
    with pytest.raises(ValueError):
        release.build(ROOT, tmp_path, version)


@pytest.mark.parametrize(
    "change", ["hash", "escape", "python", "missing", "extra", "metadata"]
)
def test_release_refuses_changes(package: Path, change: str) -> None:
    path = package / "release.json"
    manifest = json.loads(path.read_text())
    if change == "hash":
        (package / "backend/main.py").write_text("changed")
    elif change == "escape":
        manifest["files"]["../escape.py"] = "0"
    elif change == "python":
        manifest["python"] = "0.0.0"
    elif change == "missing":
        del manifest["files"]["backend/main.py"]
    elif change == "metadata":
        manifest["model_version"] = "other"
    else:
        (package / "backend/injected.py").write_text("injected")
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        release.verify(package)


@pytest.fixture
def profile(tmp_path: Path) -> Path:
    reference = tmp_path / "private.txt"
    reference.write_text("a" * 48)
    values = {key: str(reference) for key in runtime.ENV_KEYS}
    values.update(
        CHURN_BIND_HOST="127.0.0.1",
        CHURN_PORT="8443",
        CHURN_ALLOWED_HOSTS="localhost",
        CHURN_ALLOWED_CIDRS="127.0.0.1/32",
    )
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(values))
    return path


def test_environment(profile: Path) -> None:
    env = runtime.load_environment(profile)
    assert env["CHURN_ALLOW_LOCAL_HTTP"] == "0"
    assert env["CHURN_MODEL_PATH"].endswith("model.joblib")


@pytest.mark.parametrize("change", ["secret", "number", "relative", "absent", "list"])
def test_environment_rejected(profile: Path, change: str) -> None:
    value = json.loads(profile.read_text())
    if change == "secret":
        value["CHURN_API_KEY"] = "secret"
    elif change == "number":
        value["CHURN_PORT"] = 8443
    elif change == "relative":
        value["CHURN_API_KEY_FILE"] = "relative.txt"
    elif change == "absent":
        value["CHURN_API_KEY_FILE"] = str(profile.parent / "absent")
    else:
        value = []
    profile.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        runtime.load_environment(profile)


def test_graceful_stop(tmp_path: Path) -> None:
    stop = tmp_path / "stop.request"
    server = runtime.ManagedServer(uvicorn.Config("backend.main:app"), stop)
    assert not asyncio.run(server.on_tick(0))
    stop.touch()
    assert asyncio.run(server.on_tick(1))


@pytest.mark.parametrize("started", [True, False])
def test_runtime_lifecycle(
    package: Path, profile: Path, monkeypatch: pytest.MonkeyPatch, started: bool
) -> None:
    monkeypatch.setattr(runtime, "ROOT", package)
    monkeypatch.setenv("CHURN_API_KEY", "must-be-cleared")
    monkeypatch.setattr(
        runtime, "build_config", lambda: uvicorn.Config("backend.main:app")
    )
    monkeypatch.setattr(uvicorn.Config, "configure_logging", lambda self: None)

    def fake_run(self: runtime.ManagedServer) -> None:
        import os

        assert "CHURN_API_KEY" not in os.environ
        assert (profile.parent / "state/process.json").exists()
        self.started = started

    monkeypatch.setattr(runtime.ManagedServer, "run", fake_run)
    if started:
        runtime.run(profile, profile.parent / "state")
    else:
        with pytest.raises(SystemExit):
            runtime.run(profile, profile.parent / "state")
    assert not (profile.parent / "state/process.json").exists()


def test_release_cli(
    package: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    monkeypatch.setattr("sys.argv", ["release", "verify", str(package)])
    release.main()
    assert json.loads(capsys.readouterr().out)["release_version"] == "test-v1"


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "ready",
        "predict",
        "mismatch",
        "batch",
        "auth",
        "validation",
        "schema",
        "offline",
    ],
)
def test_acceptance_gate(
    package: Path, profile: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    """La aceptación debe fallar si el servidor responde pero incumple el contrato."""
    monkeypatch.setattr(acceptance, "ROOT", package)
    monkeypatch.setattr(acceptance.ssl, "create_default_context", lambda **kw: object())
    prediction = json.loads(
        (ROOT / "docs/evidencias_api/02_respuesta.json").read_text()
    )
    prediction["customer_id"] = "ACCEPTANCE-001"

    class Response:
        def __init__(self, status: int, body: Any) -> None:
            self.status = status
            self.body = body

        def read(self) -> bytes:
            return json.dumps(self.body).encode()

    class Connection:
        def __init__(self, *args: Any, **kw: Any) -> None:
            self.result = Response(200, {})

        def request(
            self, method: str, path: str, body: str | None, headers: dict[str, str]
        ) -> None:
            if failure == "offline":
                raise OSError("offline")
            if path == "/health/ready":
                self.result = Response(
                    503 if failure == "ready" else 200, {"model_version": "churn180-v1"}
                )
            elif path == "/v1/predict/batch":
                self.result = Response(500 if failure == "batch" else 200, [prediction])
            elif path == "/openapi.json":
                self.result = Response(
                    500 if failure == "schema" else 200,
                    {"paths": {"/v1/predict/transactions": {}}},
                )
            elif "X-API-Key" not in headers:
                self.result = Response(200 if failure == "auth" else 401, {})
            elif body and "unexpected" in json.loads(body):
                self.result = Response(200 if failure == "validation" else 422, {})
            else:
                result = (
                    {**prediction, "customer_id": "WRONG"}
                    if failure == "mismatch"
                    else prediction
                )
                self.result = Response(500 if failure == "predict" else 200, result)

        def getresponse(self) -> Response:
            return self.result

        def close(self) -> None:
            pass

    monkeypatch.setattr(acceptance.http.client, "HTTPSConnection", Connection)
    if failure:
        with pytest.raises((ValueError, OSError)):
            acceptance.check(profile, "127.0.0.1", profile, wait=0)
    else:
        assert acceptance.check(profile, "127.0.0.1", profile)[
            "prediction_matches_artifact"
        ]
