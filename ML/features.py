"""Única definición de fechas, calidad y variables para entrenamiento e inferencia."""

from typing import Any

import numpy as np
import pandas as pd

FEATURE_NAMES = (
    "Recency",
    "Frequency",
    "Monetary_Sum",
    "Monetary_Mean",
    "Monetary_Std",
    "Cat_Count",
    "SubCat_Count",
)
REQUIRED_COLUMNS = (
    "Customer ID",
    "Order ID",
    "Order Date",
    "Sales",
    "Category",
    "Sub-Category",
)
LOOKBACK_DAYS = 365
HORIZON_DAYS = 180


def clean_transactions(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Valida líneas de venta; elimina duplicados exactos y rechaza datos ambiguos.

    Row ID, si existe, identifica una línea. Sin él solo se eliminan filas
    exactamente repetidas. Ventas negativas, nulas o no finitas se rechazan:
    el protocolo actual no contempla devoluciones ni imputaciones monetarias.
    """
    if not set(REQUIRED_COLUMNS).issubset(frame.columns):
        raise ValueError("Faltan columnas transaccionales requeridas.")
    data = frame.copy()
    original_count = len(data)
    if data[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Hay valores nulos en variables requeridas.")
    for name in ("Customer ID", "Order ID", "Category", "Sub-Category"):
        data[name] = data[name].astype(str).str.strip()
        if data[name].eq("").any():
            raise ValueError("Hay identificadores o categorías vacíos.")
    data["Order Date"] = pd.to_datetime(
        data["Order Date"], format="%d/%m/%Y", errors="raise"
    )
    data["Sales"] = pd.to_numeric(data["Sales"], errors="raise")
    if not np.isfinite(data["Sales"]).all() or data["Sales"].lt(0).any():
        raise ValueError(
            "Ventas negativas o no finitas: revisar devoluciones y origen."
        )
    data = data.drop_duplicates()
    if "Row ID" in data.columns:
        if data["Row ID"].isna().any() or data["Row ID"].duplicated().any():
            raise ValueError("Row ID nulo o repetido con contenido diferente.")
    if (
        data.groupby("Order ID")[["Customer ID", "Order Date"]]
        .nunique()
        .gt(1)
        .any()
        .any()
    ):
        raise ValueError("Un pedido no puede pertenecer a varias fechas o clientes.")
    report = {
        "input_rows": original_count,
        "clean_rows": len(data),
        "exact_duplicates_removed": original_count - len(data),
        "customers": int(data["Customer ID"].nunique()),
        "orders": int(data["Order ID"].nunique()),
        "min_date": str(data["Order Date"].min().date()),
        "max_date": str(data["Order Date"].max().date()),
        "ignored_missing_postal_codes": int(
            data.get("Postal Code", pd.Series(dtype=float)).isna().sum()
        ),
    }
    return data, report


def build_features(data: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Agrega (corte-365 días, corte]; conserva clientes activos hasta 180 días."""
    date = pd.Timestamp(cutoff)
    history = data.loc[
        data["Order Date"].gt(date - pd.Timedelta(days=LOOKBACK_DAYS))
        & data["Order Date"].le(date)
    ]
    if history.empty:
        return pd.DataFrame(
            columns=list(FEATURE_NAMES),
            index=pd.Index([], name="Customer ID"),
            dtype=float,
        )
    result = history.groupby("Customer ID", sort=True).agg(
        Recency=("Order Date", lambda values: (date - values.max()).days),
        Frequency=("Order ID", "nunique"),
        Monetary_Sum=("Sales", "sum"),
        Monetary_Mean=("Sales", "mean"),
        Monetary_Std=("Sales", "std"),
        Cat_Count=("Category", "nunique"),
        SubCat_Count=("Sub-Category", "nunique"),
    )
    result["Monetary_Std"] = result["Monetary_Std"].fillna(0)
    return result.loc[result["Recency"].le(HORIZON_DAYS), list(FEATURE_NAMES)]


def make_snapshot(data: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Añade etiqueta futura solo cuando hay cobertura completa del horizonte."""
    date = pd.Timestamp(cutoff)
    end = date + pd.Timedelta(days=HORIZON_DAYS)
    if data["Order Date"].max() < end:
        raise ValueError("El horizonte futuro no está completamente observado.")
    if data["Order Date"].min() > date - pd.Timedelta(days=LOOKBACK_DAYS):
        raise ValueError("No hay cobertura completa de la ventana histórica.")
    result = build_features(data, cutoff)
    future_ids = data.loc[
        data["Order Date"].gt(date) & data["Order Date"].le(end), "Customer ID"
    ]
    result["Churn"] = (~result.index.isin(future_ids)).astype(int)
    result["cutoff"] = cutoff
    return result
