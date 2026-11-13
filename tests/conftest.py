"""Aísla la configuración de pruebas del despliegue y de otras pruebas."""

import os

import pytest


@pytest.fixture(autouse=True)
def isolated_churn_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Los perfiles de servicio no deben filtrarse a los casos de regresión."""
    monkeypatch.setattr(
        os,
        "environ",
        {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("CHURN_")
        },
    )
