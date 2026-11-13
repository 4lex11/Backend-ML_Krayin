from copy import deepcopy

import pandas as pd

from ML.acceptance_v2 import gates, paired_bootstrap


def test_identical_predictions_have_zero_paired_difference():
    frame = pd.DataFrame(
        {
            "Customer ID": ["A", "B", "C", "D"],
            "Churn": [0, 1, 0, 1],
            "candidate": [0.1, 0.9, 0.2, 0.8],
        }
    )
    frame["recipe"] = frame["candidate"]
    frame["recency"] = frame["candidate"]
    result = paired_bootstrap([frame, frame.copy()], repeats=100, seed=42)
    for value in result.values():
        # Single-class replicas are explicitly excluded.
        assert value["valid_replicates"] <= 100
        if value["precision_at_20_ci95"] is not None:
            assert value["precision_at_20_ci95"] == [0, 0]
            assert value["ap_ci95"] == [0, 0]
    assert result == paired_bootstrap([frame, frame.copy()], repeats=100, seed=42)


def test_acceptance_requires_all_gates():
    good = dict(precision_at_20=0.7, average_precision=0.7, brier=0.1)
    base = dict(precision_at_20=0.4, average_precision=0.4, brier=0.2)
    metrics = {
        fold: {
            "candidate": dict(good),
            "recipe": dict(base),
            "recency": dict(base),
            "constant": dict(base),
            "installed": dict(base),
        }
        for fold in ["D1", "D2", "E1"]
    }
    intervals = {
        name: {"precision_at_20_ci95": [0.1, 0.4]} for name in ["recipe", "recency"]
    }
    assert all(gates(metrics, intervals).values())
    bad = deepcopy(metrics)
    bad["E1"]["candidate"]["average_precision"] = 0.39
    assert not gates(bad, intervals)["E1_beats_installed"]
    intervals["recipe"]["precision_at_20_ci95"] = [-0.01, 0.4]
    assert not gates(metrics, intervals)["positive_ci_recipe"]
