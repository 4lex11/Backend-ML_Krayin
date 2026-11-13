"""Aceptación sobre HTTPS real: estado, contrato, lote, errores e inferencia."""

import argparse
import http.client
import json
import ssl
import time
from pathlib import Path
from typing import Any

from backend.schemas import PredictionResponse
from backend.security import read_api_key
from deploy.release import MODEL, verify
from deploy.runtime import ROOT, load_environment
from ML.inference import ChurnPredictor


def check(profile: Path, host: str, ca: Path, wait: int = 45) -> dict[str, Any]:
    """Verifica TLS con CA explícita y compara HTTP con el artefacto empaquetado."""
    manifest = verify(ROOT)
    values = load_environment(profile)
    credential = read_api_key(values)
    context = ssl.create_default_context(cafile=str(ca))

    def call(
        path: str, body: Any = None, authenticated: bool = True
    ) -> tuple[int, Any]:
        connection = http.client.HTTPSConnection(
            host, int(values["CHURN_PORT"]), context=context, timeout=5
        )
        headers = {"X-API-Key": credential} if authenticated else {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        try:
            connection.request(
                "POST" if body is not None else "GET",
                path,
                json.dumps(body) if body is not None else None,
                headers,
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    deadline = time.monotonic() + wait
    while True:
        try:
            status, ready = call("/health/ready")
            break
        except OSError, http.client.HTTPException:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.25)
    if status != 200 or ready["model_version"] != manifest["model_version"]:
        raise ValueError("El servicio no está listo con la versión esperada.")
    sample = json.loads((ROOT / "deploy/acceptance_request.json").read_text())
    status, prediction = call("/v1/predict", sample)
    if status != 200:
        raise ValueError("La predicción de aceptación no devolvió HTTP 200.")
    response = PredictionResponse.model_validate(prediction)
    predictor = ChurnPredictor.load(ROOT / MODEL / "model.joblib")
    expected = predictor.predict_probability(sample["features"])
    if (
        response.customer_id != sample["customer_id"]
        or response.model_version != predictor.version
        or abs(response.probabilidad_churn - expected) > 1e-12
        or response.automatic_action_allowed
    ):
        raise ValueError("Predicción distinta del artefacto o contrato esperado.")
    status, batch = call("/v1/predict/batch", {"customers": [sample]})
    if status != 200 or batch[0]["probabilidad_churn"] != response.probabilidad_churn:
        raise ValueError("Contrato de lote distinto del individual.")
    if call("/v1/predict", sample, authenticated=False)[0] != 401:
        raise ValueError("No se rechazó la solicitud sin credencial.")
    if call("/v1/predict", {**sample, "unexpected": True})[0] != 422:
        raise ValueError("No se rechazó un campo no permitido.")
    status, schema = call("/openapi.json")
    if status != 200 or "/v1/predict/transactions" not in schema["paths"]:
        raise ValueError("Contrato OpenAPI incompleto.")
    return {
        "release_version": manifest["release_version"],
        "model_version": predictor.version,
        "model_sha256": manifest["model_sha256"],
        "https_verified": True,
        "readiness": 200,
        "single_and_batch": 200,
        "no_key": 401,
        "invalid_contract": 422,
        "prediction_matches_artifact": True,
        "experimental": True,
    }


def main() -> None:
    """Imprime exclusivamente evidencia sin claves ni cuerpos de clientes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--ca", type=Path, required=True)
    parser.add_argument("--wait", type=int, default=45)
    args = parser.parse_args()
    print(json.dumps(check(args.profile, args.host, args.ca, args.wait), indent=2))


if __name__ == "__main__":
    main()
