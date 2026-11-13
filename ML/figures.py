"""Figuras de resultados exportables para la tesis; cada gráfico identifica su periodo."""

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve, roc_curve


def make_figures(
    report: dict[str, Any], test: pd.DataFrame, estimator: Any, output: Path
) -> None:
    """Genera imágenes separadas con datos medidos, no ilustraciones simuladas."""
    folder = output / "figures"
    folder.mkdir(exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    def save(name: str) -> None:
        plt.tight_layout()
        plt.savefig(folder / name, dpi=180, bbox_inches="tight", facecolor="white")
        plt.close()

    splits = report["splits"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    roles = {
        "train": "Entrenamiento",
        "calibration": "Calibración",
        "validation": "Selección",
        "test": "Prueba final",
    }
    labels = [f"{roles[s['role']]}\n{s['cutoff']}\nn = {s['n']}" for s in splits]
    ax.bar(
        labels,
        [s["n"] - s["churn"] for s in splits],
        label="Vuelve a comprar",
        color="#246b8e",
    )
    ax.bar(
        labels,
        [s["churn"] for s in splits],
        bottom=[s["n"] - s["churn"] for s in splits],
        label="No compra en 180 días",
        color="#c65f3b",
    )
    ax.set_ylabel("Observaciones cliente–fecha de corte")
    ax.set_title("01 · Distribución de clases por periodo temporal")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    save("01_periodos_y_clases.png")

    frame = pd.DataFrame(report["validation"]).sort_values("average_precision")
    plt.figure(figsize=(9, 5))
    plt.barh(frame["model"], frame["average_precision"], color="#246b8e")
    for i, value in enumerate(frame["average_precision"]):
        plt.text(value + 0.005, i, f"{value:.3f}", va="center")
    plt.axvline(
        frame["positive_rate"].iloc[0],
        color="#c65f3b",
        linestyle="--",
        label="Prevalencia de abandono",
    )
    plt.xlim(0, 1)
    plt.xlabel("Average Precision (AP), mayor es mejor")
    plt.title("02 · Selección de modelo — validación al 31/12/2017")
    plt.legend(loc="lower right")
    save("02_comparacion_validacion.png")

    cm = np.asarray(report["test"]["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.imshow(cm, cmap="Blues")
    for (i, j), value in np.ndenumerate(cm):
        ax.text(
            j,
            i,
            str(value),
            ha="center",
            va="center",
            fontsize=22,
            color="white" if value > cm.max() / 2 else "black",
        )
    ax.set_xticks([0, 1], ["Compra", "Abandono"])
    ax.set_yticks([0, 1], ["Compra", "Abandono"])
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Resultado observado en los 180 días siguientes")
    ax.set_title(
        f"03 · Prueba final al 30/06/2018\n{report['selected_model']} · umbral {report['thresholds']['medium']:.4f}"
    )
    save("03_matriz_confusion_test.png")

    y = test["Churn"]
    prob = test["probabilidad_churn"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fpr, tpr, _ = roc_curve(y, prob)
    precision, recall, _ = precision_recall_curve(y, prob)
    axes[0].plot(fpr, tpr, label=f"ROC-AUC = {report['test']['roc_auc']:.3f}")
    axes[0].plot([0, 1], [0, 1], "--", color="gray")
    axes[0].set(xlabel="Tasa de falsos positivos", ylabel="Recall", title="Curva ROC")
    axes[1].plot(
        recall, precision, label=f"AP = {report['test']['average_precision']:.3f}"
    )
    axes[1].axhline(
        y.mean(), linestyle="--", color="gray", label=f"Prevalencia = {y.mean():.3f}"
    )
    axes[1].set(xlabel="Recall", ylabel="Precision", title="Curva precision–recall")
    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.legend(loc="lower left")
    fig.suptitle("04 · Discriminación en prueba temporal final")
    save("04_curvas_test.png")

    actual, predicted = calibration_curve(y, prob, n_bins=5, strategy="quantile")
    plt.figure(figsize=(7, 5))
    plt.plot(predicted, actual, "o-", label=f"Brier = {report['test']['brier']:.3f}")
    plt.plot([0, 1], [0, 1], "--", color="gray", label="Calibración ideal")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel("Probabilidad media predicha")
    plt.ylabel("Proporción de abandono observada")
    plt.title("05 · Calibración en prueba final — 5 grupos por cuantiles")
    plt.legend()
    save("05_calibracion_test.png")

    core = (
        estimator.named_steps["classifier"]
        if hasattr(estimator, "named_steps")
        else estimator
    )
    importance = pd.Series(
        core.feature_importances_, index=report["features"]
    ).sort_values()
    plt.figure(figsize=(9, 5))
    plt.barh(importance.index, importance.values, color="#246b8e")
    plt.xlabel("Importancia interna del estimador (no causal)")
    plt.title(f"06 · Variables del modelo seleccionado — {report['selected_model']}")
    save("06_importancia_variables.png")
