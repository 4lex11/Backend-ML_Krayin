import pytest

from ML.calibration_v2 import calibration_bins, classification, exact_capacity_threshold


def test_threshold_ties_and_ceiling():
    assert exact_capacity_threshold([0.1, 0.2, 0.3, 0.4, 0.5, 0.6], 0.2) == 0.5
    assert exact_capacity_threshold([0.1, 0.8, 0.8], 0.2) is None
    assert exact_capacity_threshold([0.1, 0.2], 1) == 0.1


@pytest.mark.parametrize(
    "values,fraction", [([], 0.2), ([0.1], 0), ([float("nan")], 0.2)]
)
def test_invalid_input(values, fraction):
    with pytest.raises(ValueError):
        exact_capacity_threshold(values, fraction)


def test_zero_alerts_is_undefined_precision():
    result = classification([0, 1], [0.1, 0.2], 0.8)
    assert result["precision"] is None
    assert result["fn"] == 1
    assert result["recall"] == 0


def test_bin_endpoints_and_empty_bins():
    bins = calibration_bins([0, 1, 1], [0, 0.1, 1])
    assert sum(row["n"] for row in bins) == 3
    assert bins[0]["n"] == bins[1]["n"] == bins[9]["n"] == 1
    assert bins[2]["observed_rate"] is None
