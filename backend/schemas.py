"""Contrato HTTP v1 de predicción prospectiva a 180 días."""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ML.inference import validate_features

Identifier = Annotated[
    str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
]
PositiveCount = Annotated[int, Field(ge=1, le=1_000_000, strict=True)]
Money = Annotated[
    float, Field(ge=0, le=1_000_000_000_000, allow_inf_nan=False, strict=True)
]


class StrictModel(BaseModel):
    """No ignora silenciosamente nombres de campos equivocados."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class CustomerFeatures(StrictModel):
    """Agregados del último año de un cliente con compra en los últimos 180 días."""

    Recency: int = Field(ge=0, le=180, strict=True)
    Frequency: PositiveCount
    Monetary_Sum: Money
    Monetary_Mean: Money
    Monetary_Std: Money
    Cat_Count: PositiveCount
    SubCat_Count: PositiveCount

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        """Comparte la validación de dominio con ML."""
        validate_features(self.model_dump())
        return self


class PredictionRequest(StrictModel):
    """Cliente y fecha de corte explícitos para trazabilidad."""

    customer_id: Identifier
    as_of: date
    features: CustomerFeatures


class BatchRequest(StrictModel):
    """Lote acotado; duplicados cliente-fecha se rechazan."""

    customers: list[PredictionRequest] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def unique_keys(self) -> Self:
        """Evita ambigüedad al persistir resultados desde PHP."""
        keys = {(item.customer_id, item.as_of) for item in self.customers}
        if len(keys) != len(self.customers):
            raise ValueError("Cliente y fecha de corte duplicados en el lote.")
        return self


class Transaction(StrictModel):
    """Una línea de venta; líneas legítimas diferentes requieren IDs distintos."""

    line_id: Identifier
    order_id: Identifier
    order_date: date
    sales: Money
    category: str = Field(min_length=1, max_length=100)
    subcategory: str = Field(min_length=1, max_length=100)


class TransactionRequest(StrictModel):
    """Cobertura declarada por el origen; Python calcula las variables."""

    customer_id: Identifier
    as_of: date
    history_start: date
    transactions: list[Transaction] = Field(min_length=1, max_length=5000)


class PredictionResponse(StrictModel):
    """Riesgo experimental, sin afirmar fidelización ni ejecutar acciones."""

    status: Literal["success"] = "success"
    customer_id: str
    as_of: date
    predicted_at: datetime
    model_version: str
    schema_version: Literal["churn180-v1"] = "churn180-v1"
    horizon_days: Literal[180] = 180
    probabilidad_churn: float
    categoria_riesgo: Literal["Bajo", "Medio", "Alto"]
    accion_sugerida: str = (
        "Revisión humana; modelo experimental sin utilidad predictiva demostrada."
    )
    model_status: Literal["experimental"] = "experimental"
    automatic_action_allowed: Literal[False] = False
    limited_history: bool
