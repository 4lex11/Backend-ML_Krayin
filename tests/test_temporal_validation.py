"""Guardas temporales y paridad de población para MEJ-03."""

import json
from copy import deepcopy

import pandas as pd
import pytest

from ML.features import clean_transactions, make_snapshot
from ML.temporal_validation import ROOT, build_snapshots, prepare, validate_protocol


@pytest.fixture
def protocol():
    return json.loads((ROOT / "ML/experiments/churn180-v2/protocol.json").read_text())


@pytest.mark.parametrize("kind", ["overlap", "duplicate", "window", "features"])
def test_reject_invalid_protocol(protocol, kind):
    p = deepcopy(protocol)
    if kind == "overlap":
        p["evaluations"][0]["calibration_cutoff"] = "2016-07-01"
    elif kind == "duplicate":
        p["evaluations"][0]["train_cutoffs"] *= 2
    elif kind == "window":
        p["definition"]["horizon_days"] = 90
    else:
        p["temporal_features"] = []
    with pytest.raises(ValueError):
        validate_protocol(p)


def test_real_snapshots_population_labels_and_future_invariance(protocol):
    data, _ = clean_transactions(pd.read_csv(ROOT / "ML/Datasets/train.csv"))
    snapshots = build_snapshots(data, protocol)
    assert [len(x) for x in snapshots.values()] == [286, 444, 351, 510, 431]
    for cutoff, snapshot in snapshots.items():
        reference = make_snapshot(data, cutoff)
        pd.testing.assert_frame_equal(snapshot[reference.columns], reference)
    # Future purchases change the target, never predictors.
    cutoff = "2018-06-30"
    changed = data.copy()
    changed.loc[changed["Order Date"].gt(cutoff), "Sales"] *= 10
    altered = build_snapshots(changed, protocol)[cutoff]
    pd.testing.assert_frame_equal(snapshots[cutoff], altered)
    with pytest.raises(ValueError, match="futuro"):
        build_snapshots(data.loc[data["Order Date"].le("2018-10-01")], protocol)


def test_export_integrity_and_no_overwrite(protocol, tmp_path):
    p = ROOT / "ML/experiments/churn180-v2/protocol.json"
    destination = tmp_path / "prepared"
    report = prepare(ROOT / "ML/Datasets/train.csv", p, destination)
    assert report["trained_models"] == 0
    assert [fold["roles"]["train"]["rows"] for fold in report["folds"]] == [
        286,
        730,
        1081,
    ]
    assert report["folds"][-1]["usable_for_selection"] is False
    for fold in report["folds"]:
        for role in fold["roles"].values():
            frame = pd.read_csv(destination / role["file"])
            assert not frame.duplicated(["Customer ID", "cutoff"]).any()
            assert len(frame) == role["rows"]
    with pytest.raises(FileExistsError):
        prepare(ROOT / "ML/Datasets/train.csv", p, destination)
    bad = tmp_path / "wrong.csv"
    bad.write_text("invalid")
    with pytest.raises(ValueError, match="Hash"):
        prepare(bad, p, tmp_path / "absent")
    assert not (tmp_path / "absent").exists()
