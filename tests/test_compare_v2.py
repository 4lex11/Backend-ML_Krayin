"""Métricas de cupo y selección determinista del experimento."""

import numpy as np
import pandas as pd
import pytest

from ML.compare_v2 import plan, rank_candidates, scores


def test_budget_and_no_test_selection():
    design = plan()
    assert len(design["candidates"]) == 18
    assert len({c["id"] for c in design["candidates"]}) == 18
    assert design["evaluation_folds"] == ["D1", "D2"]
    assert design["E1_used"] is False


def test_top_k_uses_ceiling_and_stable_customer_tie_break():
    frame = pd.DataFrame(
        {"Customer ID": ["B", "A", "C", "D", "E", "F"], "Churn": [0, 1, 1, 0, 0, 0]}
    )
    result = scores(frame, np.array([0.8, 0.8, 0.2, 0.1, 0.1, 0.1]))
    assert result["selected_20"] == 2
    assert result["precision_at_20"] == 0.5
    assert result["precision_at_10"] == 1
    assert result["recall_at_20"] == 0.5
    shuffled = frame.iloc[::-1]
    assert scores(shuffled, np.array([0.1, 0.1, 0.1, 0.2, 0.8, 0.8])) == result


@pytest.mark.parametrize(
    "probability", [[float("nan"), 0.2], [-0.1, 0.5], [1.1, 0.4], [0.2]]
)
def test_invalid_predictions_rejected(probability):
    frame = pd.DataFrame({"Customer ID": ["A", "B"], "Churn": [0, 1]})
    with pytest.raises(ValueError):
        scores(frame, probability)


def test_tie_breakers_do_not_depend_on_input_order():
    base = dict(precision_at_20=0.5, average_precision=0.4, brier=0.2, feature_count=7)
    rows = [
        dict(base, id="z"),
        dict(base, id="a"),
        dict(base, id="fewer", feature_count=5),
    ]
    assert [r["id"] for r in rank_candidates(rows)] == ["fewer", "a", "z"]
