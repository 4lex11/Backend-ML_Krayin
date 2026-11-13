"""Inferencia temporal versionada, independiente de HTTP y de Krayin."""

import hashlib
import importlib.metadata
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ML.features import FEATURE_NAMES

DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parent / "artifacts/churn180-v1/model.joblib"
)


def validate_features(features: Mapping[str, int | float]) -> None:
    """Valida el dominio de clientes activos y sus agregados monetarios."""
    if set(features) != set(FEATURE_NAMES):
        raise ValueError("Se requieren exactamente las siete variables de churn180-v1.")
    for name, value in features.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"{name} debe ser un número finito no negativo.")
    for name in ("Recency", "Frequency", "Cat_Count", "SubCat_Count"):
        if int(features[name]) != features[name]:
            raise ValueError(f"{name} debe ser entero.")
    if (
        features["Recency"] > 180
        or min(features[n] for n in ("Frequency", "Cat_Count", "SubCat_Count")) < 1
    ):
        raise ValueError(
            "Fuera de población: compra reciente y conteos positivos requeridos."
        )
    if features["Cat_Count"] > features["SubCat_Count"]:
        raise ValueError("Cat_Count no puede superar SubCat_Count.")
    total, mean, std = (
        features[n] for n in ("Monetary_Sum", "Monetary_Mean", "Monetary_Std")
    )
    if mean > total + 0.01 or std > total + 0.01 or (mean == 0 and total != 0):
        raise ValueError("Los agregados monetarios son inconsistentes.")


@dataclass(frozen=True)
class ChurnPredictor:
    """Modelo calibrado y metadatos del mismo artefacto evaluado."""

    model: Any
    metadata: dict[str, Any]
    version: str
    thresholds: dict[str, float]

    @classmethod
    def load(cls, model_path: Path = DEFAULT_MODEL_PATH) -> "ChurnPredictor":
        """Comprueba hash y versiones antes de deserializar un artefacto local."""
        manifest = json.loads(
            model_path.with_name("metadata.json").read_text(encoding="utf-8")
        )
        digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
        if digest != manifest["model_sha256"]:
            raise ValueError("El hash del modelo no coincide con su manifiesto.")
        for package, expected in manifest["versions"].items():
            if importlib.metadata.version(package) != expected:
                raise ValueError(
                    f"Versión incompatible de {package}; se requiere {expected}."
                )
        bundle = joblib.load(model_path)
        if (
            tuple(bundle["features"]) != FEATURE_NAMES
            or tuple(bundle["model"].feature_names_in_) != FEATURE_NAMES
        ):
            raise ValueError("Contrato de variables incompatible.")
        if list(bundle["model"].classes_) != [0, 1]:
            raise ValueError("Clases del modelo incompatibles.")
        if (
            bundle["version"] != manifest["model_version"]
            or bundle["thresholds"] != manifest["thresholds"]
        ):
            raise ValueError("Versión o umbrales del manifiesto incompatibles.")
        return cls(bundle["model"], manifest, bundle["version"], bundle["thresholds"])

    def predict_many(self, rows: Sequence[Mapping[str, int | float]]) -> list[float]:
        """Valida e infiere un lote conservando su orden."""
        if not rows:
            raise ValueError("El lote no puede estar vacío.")
        for row in rows:
            validate_features(row)
        frame = pd.DataFrame(
            [[row[name] for name in FEATURE_NAMES] for row in rows],
            columns=list(FEATURE_NAMES),
        )
        probability = self.model.predict_proba(frame)[:, 1]
        if (
            not np.isfinite(probability).all()
            or ((probability < 0) | (probability > 1)).any()
        ):
            raise ValueError("El modelo produjo probabilidades inválidas.")
        return [float(value) for value in probability]

    def predict_probability(self, features: Mapping[str, int | float]) -> float:
        """Un cliente recorre la misma ruta que los lotes."""
        return self.predict_many([features])[0]

    def risk(self, probability: float) -> str:
        """Categoriza sin redondear antes de comparar los límites."""
        if probability >= self.thresholds["high"]:
            return "Alto"
        if probability >= self.thresholds["medium"]:
            return "Medio"
        return "Bajo"
