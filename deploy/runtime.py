"""Proceso de servicio HTTPS con parada ordenada y logs con rotación."""

import argparse
import json
import os
from pathlib import Path

import uvicorn

from backend.serve import build_config
from deploy.release import MODEL, verify

ROOT = Path(__file__).resolve().parents[1]
ENV_KEYS = frozenset(
    {
        "CHURN_API_KEY_FILE",
        "CHURN_TLS_CERT_FILE",
        "CHURN_TLS_KEY_FILE",
        "CHURN_BIND_HOST",
        "CHURN_PORT",
        "CHURN_ALLOWED_CIDRS",
        "CHURN_ALLOWED_HOSTS",
    }
)


def load_environment(path: Path) -> dict[str, str]:
    """Carga un perfil cerrado sin secretos inline ni interpolación de comandos."""
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or set(value) != ENV_KEYS:
        raise ValueError(
            "El perfil debe contener exactamente las siete opciones documentadas."
        )
    if not all(isinstance(v, str) and v for v in value.values()):
        raise ValueError("Todas las opciones deben ser cadenas no vacías.")
    for key in ("CHURN_API_KEY_FILE", "CHURN_TLS_CERT_FILE", "CHURN_TLS_KEY_FILE"):
        if not Path(value[key]).is_absolute() or not Path(value[key]).is_file():
            raise ValueError(
                "Los secretos y certificados requieren archivos absolutos existentes."
            )
    return {
        **value,
        "CHURN_ALLOW_LOCAL_HTTP": "0",
        "CHURN_MODEL_PATH": str(ROOT / MODEL / "model.joblib"),
    }


class ManagedServer(uvicorn.Server):
    """Observa una señal local y deja a Uvicorn drenar solicitudes en curso."""

    def __init__(self, config: uvicorn.Config, stop_file: Path) -> None:
        super().__init__(config)
        self.stop_file = stop_file

    async def on_tick(self, counter: int) -> bool:
        """Comprueba la parada cada tick, sin exponer un endpoint administrativo."""
        return self.stop_file.exists() or await super().on_tick(counter)


def run(profile: Path, state: Path) -> None:
    """Verifica la entrega y ejecuta un solo proceso supervisado por Windows."""
    manifest = verify(ROOT)
    values = load_environment(profile)
    for key in list(os.environ):
        if key.startswith("CHURN_"):
            del os.environ[key]
    os.environ.update(values)
    state.mkdir(parents=True, exist_ok=True)
    config = build_config()
    config.log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(state / "service.log"),
                "maxBytes": 5_000_000,
                "backupCount": 3,
                "encoding": "utf-8",
                "formatter": "default",
            }
        },
        "loggers": {
            "crm_churn": {"level": "INFO", "handlers": ["file"], "propagate": False},
            "uvicorn": {"level": "INFO", "handlers": ["file"], "propagate": False},
        },
        "root": {"level": "INFO", "handlers": ["file"]},
    }
    config.configure_logging()
    pid = state / "process.json"
    pid.write_text(
        json.dumps({"pid": os.getpid(), "release_version": manifest["release_version"]})
    )
    try:
        server = ManagedServer(config, state / "stop.request")
        server.run()
        if not server.started:
            raise SystemExit(1)
    finally:
        pid.unlink(missing_ok=True)


def main() -> None:
    """Entrada del proceso usado por el Programador de tareas."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    run(args.profile.resolve(), args.state.resolve())


if __name__ == "__main__":
    main()
