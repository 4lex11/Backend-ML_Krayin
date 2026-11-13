"""API autenticada: iniciar con python -m backend.serve para aplicar TLS y política de red."""

import asyncio
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, cast

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.schemas import (
    BatchRequest,
    CustomerFeatures,
    PredictionRequest,
    PredictionResponse,
    TransactionRequest,
)
from backend.security import SecurityPolicy, read_api_key, valid_api_key
from ML.features import build_features, clean_transactions
from ML.inference import DEFAULT_MODEL_PATH, ChurnPredictor

logger = logging.getLogger("crm_churn")
MAX_BODY_BYTES = 2_000_000
MAX_INFLIGHT = 4
BODY_TIMEOUT_SECONDS = 5.0


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Carga el artefacto y exige un secreto del entorno al iniciar."""
    key = read_api_key(os.environ)
    application.state.security = SecurityPolicy.from_env()
    path = Path(os.environ.get("CHURN_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    application.state.predictor = ChurnPredictor.load(path)
    application.state.api_key = key
    application.state.inflight = 0
    yield
    del application.state.predictor
    del application.state.api_key
    del application.state.security


app = FastAPI(
    title="CRM - Predicción prospectiva de abandono",
    version="2.1.0",
    lifespan=lifespan,
    description="Horizonte de 180 días. Prototipo experimental: no ejecutar campañas automáticamente.",
)
key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def authorize(
    request: Request, key: Annotated[str | None, Depends(key_header)]
) -> None:
    """Autenticación de servicio con comparación constante."""
    if not valid_api_key(key, request.app.state.api_key):
        raise HTTPException(status_code=401, detail="Credencial ausente o inválida.")


def get_predictor(request: Request) -> ChurnPredictor:
    """Obtiene el recurso de inferencia cargado."""
    return cast(ChurnPredictor, request.app.state.predictor)


PredictorDependency = Annotated[ChurnPredictor, Depends(get_predictor)]


@app.middleware("http")
async def trace_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Limita el cuerpo incluso sin Content-Length y registra metadatos operativos."""
    request.state.request_id = uuid.uuid4().hex
    started = time.perf_counter()
    rejected = request.app.state.security.reject(request)
    if rejected is not None:
        status, code, message = rejected
        return JSONResponse(
            status_code=status,
            content={
                "error": {"code": code, "message": message},
                "request_id": request.state.request_id,
            },
            headers={"X-Request-ID": request.state.request_id},
        )
    if request.url.path.startswith("/v1/") or request.url.path in {
        "/health/ready",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }:
        if not valid_api_key(
            request.headers.get("X-API-Key"), request.app.state.api_key
        ):
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "http_401",
                        "message": "Credencial ausente o inválida.",
                    },
                    "request_id": request.state.request_id,
                },
                headers={"X-Request-ID": request.state.request_id},
            )
    limited = request.url.path.startswith("/v1/")
    if limited and request.app.state.inflight >= MAX_INFLIGHT:
        return capacity_error(request, 503, "capacity_exceeded", "Servicio ocupado.")
    if limited:
        request.app.state.inflight += 1
    try:
        return await process_request(request, call_next, started)
    finally:
        if limited:
            request.app.state.inflight -= 1


def capacity_error(
    request: Request, status: int, code: str, message: str
) -> JSONResponse:
    """Rechazo trazable sin encolar trabajo ni reflejar los datos recibidos."""
    logger.warning(
        "request_id=%s status=%s code=%s", request.state.request_id, status, code
    )
    headers = {"X-Request-ID": request.state.request_id, "Cache-Control": "no-store"}
    if status == 503:
        headers["Retry-After"] = "1"
    return JSONResponse(
        status_code=status,
        content={
            "error": {"code": code, "message": message},
            "request_id": request.state.request_id,
        },
        headers=headers,
    )


async def read_body(request: Request) -> bool:
    """Limita bytes incluso en envíos fragmentados; False indica exceso."""
    body_size = 0
    chunks = []
    async for chunk in request.stream():
        body_size += len(chunk)
        if body_size > MAX_BODY_BYTES:
            return False
        chunks.append(chunk)
    request._body = b"".join(chunks)
    return True


async def process_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    started: float,
) -> Response:
    """Acota recepción; mantiene el cupo hasta completar el trabajo síncrono."""
    try:
        async with asyncio.timeout(BODY_TIMEOUT_SECONDS):
            accepted = await read_body(request)
        if not accepted:
            return capacity_error(
                request, 413, "payload_too_large", "Cuerpo demasiado grande."
            )
    except TimeoutError:
        return capacity_error(
            request, 408, "body_timeout", "Tiempo de recepción agotado."
        )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("prediction_error request_id=%s", request.state.request_id)
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "No se pudo procesar la solicitud.",
                },
                "request_id": request.state.request_id,
            },
        )
    elapsed = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.2f}"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    logger.info(
        "request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
        request.state.request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """No refleja valores de entrada, NaN ni credenciales en los errores."""
    details = [
        {"field": ".".join(str(v) for v in item["loc"]), "message": item["msg"]}
        for item in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Solicitud inválida.",
                "details": details,
            },
            "request_id": request.state.request_id,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Forma uniforme para errores de autenticación, dominio y ruta."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": f"http_{exc.status_code}", "message": str(exc.detail)},
            "request_id": request.state.request_id,
        },
    )


def response_for(
    data: PredictionRequest, probability: float, predictor: ChurnPredictor
) -> PredictionResponse:
    """Añade trazabilidad sin cambiar el resultado numérico del modelo."""
    return PredictionResponse(
        customer_id=data.customer_id,
        as_of=data.as_of,
        predicted_at=datetime.now(timezone.utc),
        model_version=predictor.version,
        probabilidad_churn=probability,
        categoria_riesgo=cast(Any, predictor.risk(probability)),
        limited_history=data.features.Frequency == 1,
    )


@app.get("/health/live")
def live() -> dict[str, str]:
    """Vida del proceso; no equivale a utilidad del modelo."""
    return {"status": "alive"}


@app.get("/health/ready", dependencies=[Depends(authorize)])
def ready(predictor: PredictorDependency) -> dict[str, Any]:
    """Separa disponibilidad técnica del estado científico."""
    return {
        "status": "ready",
        "model_version": predictor.version,
        "model_status": "experimental",
        "automatic_action_allowed": False,
    }


@app.post("/v1/predict", dependencies=[Depends(authorize)])
def predict(
    data: PredictionRequest, predictor: PredictorDependency
) -> PredictionResponse:
    """Predicción con variables ya calculadas conforme al contrato."""
    probability = predictor.predict_probability(data.features.model_dump())
    return response_for(data, probability, predictor)


@app.post("/v1/predict/batch", dependencies=[Depends(authorize)])
def predict_batch(
    data: BatchRequest, predictor: PredictorDependency
) -> list[PredictionResponse]:
    """Hasta 500 clientes; valida el lote completo antes de inferir."""
    probabilities = predictor.predict_many(
        [item.features.model_dump() for item in data.customers]
    )
    return [
        response_for(item, probability, predictor)
        for item, probability in zip(data.customers, probabilities)
    ]


@app.post("/v1/predict/transactions", dependencies=[Depends(authorize)])
def predict_transactions(
    data: TransactionRequest, predictor: PredictorDependency
) -> PredictionResponse:
    """Calcula variables mediante la misma función usada para entrenar."""
    if (data.as_of - data.history_start).days < 365:
        raise HTTPException(
            422, "El origen debe declarar cobertura de al menos 365 días."
        )
    rows = []
    for item in data.transactions:
        if item.order_date > data.as_of or item.order_date < data.history_start:
            raise HTTPException(422, "Compra fuera de cobertura o posterior al corte.")
        rows.append(
            {
                "Row ID": item.line_id,
                "Customer ID": data.customer_id,
                "Order ID": item.order_id,
                "Order Date": item.order_date.strftime("%d/%m/%Y"),
                "Sales": item.sales,
                "Category": item.category,
                "Sub-Category": item.subcategory,
            }
        )
    try:
        transactions, _ = clean_transactions(pd.DataFrame(rows))
        features = build_features(transactions, data.as_of.isoformat())
        if features.empty:
            raise ValueError(
                "Cliente fuera de población: sin compra en los últimos 180 días."
            )
        values = features.iloc[0].to_dict()
        for name in ("Recency", "Frequency", "Cat_Count", "SubCat_Count"):
            values[name] = int(values[name])
        prepared = PredictionRequest(
            customer_id=data.customer_id,
            as_of=data.as_of,
            features=CustomerFeatures.model_validate(values),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return predict(prepared, predictor)
