"""Variables temporales experimentales para churn180-v2.

Este módulo no modifica el contrato de inferencia churn180-v1. Todas las
variables se calculan exclusivamente con compras en (corte - 365 días, corte].
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ML.features import HORIZON_DAYS, LOOKBACK_DAYS

TEMPORAL_FEATURE_NAMES = (
    "Orders_30d",
    "Orders_90d",
    "Orders_180d",
    "Sales_30d",
    "Sales_90d",
    "Sales_180d",
    "Recent90_To_Prior90_Order_Ratio",
    "ActiveMonths_365d",
    "MeanOrderGapDays",
    "StdOrderGapDays",
    "HasMultipleOrders",
)


def _window_orders(
    order_level: pd.DataFrame, cutoff: pd.Timestamp, days: int
) -> pd.Series:
    return (
        order_level.loc[
            order_level["Order Date"].gt(cutoff - pd.Timedelta(days=days))
            & order_level["Order Date"].le(cutoff)
        ]
        .groupby("Customer ID")["Order ID"]
        .nunique()
    )


def _window_sales(history: pd.DataFrame, cutoff: pd.Timestamp, days: int) -> pd.Series:
    return (
        history.loc[
            history["Order Date"].gt(cutoff - pd.Timedelta(days=days))
            & history["Order Date"].le(cutoff)
        ]
        .groupby("Customer ID")["Sales"]
        .sum()
    )


def build_temporal_features(data: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Construye variables v2 para clientes activos y evita fuga temporal.

    `data` debe pasar antes por ``clean_transactions``. La agregación por pedido
    evita contar varias líneas de un mismo pedido como compras distintas. Para
    un único pedido, ambas estadísticas de intervalo son 0 y
    ``HasMultipleOrders`` vale 0; el indicador permite al modelo distinguir esa
    ausencia de un patrón de compras realmente regular.
    """
    required = {"Customer ID", "Order ID", "Order Date", "Sales"}
    if not required.issubset(data.columns):
        raise ValueError("Faltan columnas para variables temporales v2.")
    date = pd.Timestamp(cutoff)
    history = data.loc[
        data["Order Date"].gt(date - pd.Timedelta(days=LOOKBACK_DAYS))
        & data["Order Date"].le(date)
    ].copy()
    if history.empty:
        return pd.DataFrame(
            columns=list(TEMPORAL_FEATURE_NAMES),
            index=pd.Index([], name="Customer ID"),
            dtype=float,
        )
    order_level = (
        history.groupby(["Customer ID", "Order ID"], as_index=False)
        .agg(**{"Order Date": ("Order Date", "first")})
        .sort_values(["Customer ID", "Order Date", "Order ID"])
    )
    latest = order_level.groupby("Customer ID")["Order Date"].max()
    result = pd.DataFrame(index=latest.index)
    for days in (30, 90, 180):
        result[f"Orders_{days}d"] = _window_orders(order_level, date, days)
        result[f"Sales_{days}d"] = _window_sales(history, date, days)
    recent_90 = _window_orders(order_level, date, 90)
    prior_90 = (
        order_level.loc[
            order_level["Order Date"].gt(date - pd.Timedelta(days=180))
            & order_level["Order Date"].le(date - pd.Timedelta(days=90))
        ]
        .groupby("Customer ID")["Order ID"]
        .nunique()
    )
    # Align before smoothing: customers absent from one period still need +1.
    result["Recent90_To_Prior90_Order_Ratio"] = (
        recent_90.reindex(result.index, fill_value=0) + 1
    ) / (prior_90.reindex(result.index, fill_value=0) + 1)
    result["ActiveMonths_365d"] = (
        history.assign(_month=history["Order Date"].dt.to_period("M"))
        .groupby("Customer ID")["_month"]
        .nunique()
    )
    gaps = order_level.groupby("Customer ID")["Order Date"].agg(
        lambda values: values.sort_values().diff().dt.days.dropna().tolist()
    )
    result["MeanOrderGapDays"] = gaps.map(
        lambda values: float(np.mean(values)) if values else 0.0
    )
    result["StdOrderGapDays"] = gaps.map(
        lambda values: float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    )
    result["HasMultipleOrders"] = (
        order_level.groupby("Customer ID")["Order ID"].nunique().ge(2).astype(int)
    )
    result = result.fillna(0.0).astype(float)
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Variables temporales no finitas.")
    recency = (date - latest).dt.days
    return result.loc[recency.le(HORIZON_DAYS), list(TEMPORAL_FEATURE_NAMES)]
