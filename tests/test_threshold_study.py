"""ML-06: cupos, desempates, costos y conservación del artefacto."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ML.threshold_study import ROOT, decision, ranking, run, select_fraction


def test_counts_and_ties() -> None:
    frame = pd.DataFrame(
        {
            "Customer ID": ["B", "A", "C", "D"],
            "probability": [0.5, 0.5, 0.3, 0.2],
            "Churn": [0, 1, 1, 0],
        }
    )
    assert ranking(frame, "probability").tolist() == [1, 0, 2, 3]
    assert select_fraction(frame, 0.5, 1) == 0.25
    result = decision(np.array([0, 1, 1, 0]), np.array([True, True, False, False]), 5)
    assert result["relative_loss"] == 6
    assert result["tp"] == result["fp"] == result["fn"] == result["tn"] == 1
    with pytest.raises(ValueError):
        select_fraction(frame, 0, 1)


def test_report_preserves_model_and_capacity(tmp_path: Path) -> None:
    folder = ROOT / "ML/artifacts/churn180-v1"
    before = hashlib.sha256((folder / "model.joblib").read_bytes()).hexdigest()
    report = run(folder, tmp_path / "study")
    assert report["model_sha256"] == before
    assert hashlib.sha256((folder / "model.joblib").read_bytes()).hexdigest() == before
    assert report["commercially_validated"] is False
    scenarios = pd.read_csv(tmp_path / "study/capacity_scenarios.csv")
    assert len(scenarios) == 90
    assert (scenarios.selected_fraction <= scenarios.capacity_fraction).all()
    thresholds = pd.read_csv(tmp_path / "study/thresholds.csv")
    assert (
        thresholds[
            (thresholds.period == "test") & (thresholds.policy == "medium_current")
        ].selected.iloc[0]
        == 429
    )
    with pytest.raises(FileExistsError):
        run(folder, tmp_path / "study")
