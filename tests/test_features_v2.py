"""Contrato de las variables temporales de MEJ-02."""

import pandas as pd
import pandas.testing as pdt
import pytest

from ML.features import clean_transactions
from ML.features_v2 import TEMPORAL_FEATURE_NAMES, build_temporal_features


def transactions() -> pd.DataFrame:
    rows = [
        [1, "A", "A0", "30/06/2017", 5.0, "C", "S"],  # borde excluido 365d
        [2, "A", "A1", "01/01/2018", 10.0, "C", "S"],
        [3, "A", "A1", "01/01/2018", 20.0, "C", "T"],
        [4, "A", "A2", "01/04/2018", 30.0, "C", "S"],  # borde excluido 90d
        [5, "A", "A3", "01/06/2018", 40.0, "C", "S"],
        [6, "A", "A4", "30/06/2018", 50.0, "C", "S"],
        [7, "B", "B1", "30/06/2018", 60.0, "C", "S"],
        [8, "A", "FUTURE", "01/07/2018", 9999.0, "C", "S"],
    ]
    return pd.DataFrame(
        rows,
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


def test_temporal_features_use_only_history_and_order_granularity() -> None:
    data, _ = clean_transactions(transactions())
    result = build_temporal_features(data, "2018-06-30")
    assert tuple(result.columns) == TEMPORAL_FEATURE_NAMES
    assert set(result.index) == {"A", "B"}
    assert result.loc["A", "Orders_30d"] == 2  # A3 and A4, not three lines
    assert result.loc["A", "Orders_90d"] == 2  # 01/04 is excluded at the boundary
    assert result.loc["A", "Orders_180d"] == 3
    assert result.loc["A", "Sales_30d"] == 90  # Lines retain their monetary values
    assert result.loc["A", "Recent90_To_Prior90_Order_Ratio"] == 1.5
    assert result.loc["A", "ActiveMonths_365d"] == 3
    assert result.loc["A", "MeanOrderGapDays"] == 60
    assert result.loc["A", "StdOrderGapDays"] == pytest.approx(30.5123, abs=0.0001)
    assert result.loc["A", "HasMultipleOrders"] == 1
    assert result.loc["B", "HasMultipleOrders"] == 0
    assert result.loc["B", "MeanOrderGapDays"] == 0
    assert result.loc["B", "StdOrderGapDays"] == 0
    assert result.loc["B", "Recent90_To_Prior90_Order_Ratio"] == 2


def test_ratio_without_recent_orders_and_exact_eligibility_boundary() -> None:
    raw = transactions()
    raw.loc[raw["Customer ID"].eq("B"), "Order Date"] = "01/01/2018"
    data, _ = clean_transactions(raw)
    result = build_temporal_features(data, "2018-06-30")
    assert "B" in result.index  # Exactly 180 days: eligible, outside Orders_180d.
    assert result.loc["B", "Orders_180d"] == 0
    assert result.loc["B", "Recent90_To_Prior90_Order_Ratio"] == 1
    raw.loc[raw["Customer ID"].eq("B"), "Order Date"] = "02/01/2018"
    data, _ = clean_transactions(raw)
    assert (
        build_temporal_features(data, "2018-06-30").loc[
            "B", "Recent90_To_Prior90_Order_Ratio"
        ]
        == 0.5
    )
    raw.loc[raw["Customer ID"].eq("B"), "Order Date"] = "31/12/2017"
    data, _ = clean_transactions(raw)
    assert "B" not in build_temporal_features(data, "2018-06-30").index


def test_removing_future_and_reordering_lines_preserves_features() -> None:
    data, _ = clean_transactions(transactions())
    history = data.loc[data["Order Date"].le("2018-06-30")]
    pdt.assert_frame_equal(
        build_temporal_features(data, "2018-06-30"),
        build_temporal_features(history.iloc[::-1], "2018-06-30"),
    )


def test_future_changes_do_not_change_temporal_features() -> None:
    data, _ = clean_transactions(transactions())
    changed = data.copy()
    changed.loc[changed["Order Date"].gt("2018-06-30"), "Sales"] = 1.0
    changed.loc[changed["Order Date"].gt("2018-06-30"), "Order ID"] = "NEW-FUTURE"
    pdt.assert_frame_equal(
        build_temporal_features(data, "2018-06-30"),
        build_temporal_features(changed, "2018-06-30"),
    )


def test_inactive_and_empty_history_are_not_returned() -> None:
    data, _ = clean_transactions(transactions())
    assert build_temporal_features(data, "2020-01-01").empty
