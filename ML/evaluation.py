"""Métricas y reglas de decisión reproducibles, sin elegir con el test final."""

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def metrics(y: Any, probability: Any, threshold: float = 0.5) -> dict[str, Any]:
    """Calcula AP (resumen de curva PR), discriminación, calibración y errores."""
    prediction = np.asarray(probability) >= threshold
    return {
        "n": len(y),
        "positive_rate": float(np.mean(y)),
        "threshold": threshold,
        "accuracy": float(accuracy_score(y, prediction)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "f2": float(fbeta_score(y, prediction, beta=2, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, probability)),
        "average_precision": float(average_precision_score(y, probability)),
        "brier": float(brier_score_loss(y, probability)),
        "confusion_matrix": confusion_matrix(y, prediction, labels=[0, 1]).tolist(),
        "flagged_rate": float(np.mean(prediction)),
    }


def select_thresholds(y: Any, probability: Any) -> dict[str, float]:
    """F2 prioriza recall; riesgo alto se aproxima al quintil superior de validación."""
    candidates = np.unique(np.r_[0, np.minimum(np.asarray(probability), 0.99)])
    best = max(
        candidates,
        key=lambda t: (
            fbeta_score(y, probability >= t, beta=2, zero_division=0),
            precision_score(y, probability >= t, zero_division=0),
            float(t),
        ),
    )
    high = min(1.0, max(float(best) + 0.01, float(np.quantile(probability, 0.8))))
    return {"medium": float(best), "high": high}


def bootstrap_intervals(
    y: Any, probability: Any, threshold: float, repeats: int
) -> dict[str, list[float]]:
    """IC percentiles al 95% por cliente del único corte final; no inferencia causal."""
    rng = np.random.default_rng(42)
    target = np.asarray(y)
    probs = np.asarray(probability)
    samples: dict[str, list[float]] = {
        name: []
        for name in ["roc_auc", "average_precision", "recall", "precision", "brier"]
    }
    for _ in range(repeats):
        indices = rng.integers(0, len(target), len(target))
        if len(np.unique(target[indices])) < 2:
            continue
        result = metrics(target[indices], probs[indices], threshold)
        for name in samples:
            samples[name].append(result[name])
    return {
        name: np.quantile(values, [0.025, 0.975]).tolist()
        for name, values in samples.items()
    }
