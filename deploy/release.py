"""Construye y verifica una entrega sin datasets ni secretos."""

import argparse
import hashlib
import json
import platform
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = Path("ML/artifacts/churn180-v1")


def digest(path: Path) -> str:
    """Calcula la huella de un archivo distribuido."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(source: Path, destination: Path, version: str) -> Path:
    """Copia una lista explícita de archivos a un destino nuevo."""
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", version):
        raise ValueError("Identificador de entrega inválido.")
    target = destination.resolve() / version
    target.mkdir(parents=True, exist_ok=False)
    paths = [Path("requirements-lock.txt")]
    for folder in ("backend", "ML", "deploy"):
        paths.extend(p.relative_to(source) for p in (source / folder).glob("*.py"))
    paths += [
        Path("backend/logging.json"),
        MODEL / "model.joblib",
        MODEL / "metadata.json",
    ]
    paths += [Path("deploy/acceptance_request.json")]
    for relative in sorted(set(paths)):
        original = source / relative
        if original.is_symlink():
            raise ValueError("No se distribuyen enlaces simbólicos.")
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, output)
    metadata = json.loads((target / MODEL / "metadata.json").read_text())
    if digest(target / MODEL / "model.joblib") != metadata["model_sha256"]:
        raise ValueError("Modelo distinto del manifiesto de entrenamiento.")
    manifest = {
        "release_version": version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "model_version": metadata["model_version"],
        "model_sha256": metadata["model_sha256"],
        "files": {p.as_posix(): digest(target / p) for p in sorted(set(paths))},
    }
    (target / "release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return target


def verify(folder: Path) -> dict[str, Any]:
    """Rechaza rutas escapadas, archivos alterados y Python incompatible."""
    folder = folder.resolve()
    manifest: dict[str, Any] = json.loads((folder / "release.json").read_text())
    if manifest["python"] != platform.python_version():
        raise ValueError("Versión de Python distinta de la entrega.")
    files = manifest["files"]
    required = {
        "backend/main.py",
        "deploy/runtime.py",
        "requirements-lock.txt",
        (MODEL / "model.joblib").as_posix(),
        (MODEL / "metadata.json").as_posix(),
    }
    if not required <= files.keys():
        raise ValueError("Manifiesto de entrega incompleto.")
    for relative, expected in files.items():
        path = (folder / relative).resolve()
        if not path.is_relative_to(folder) or path == folder:
            raise ValueError("Ruta fuera de la entrega.")
        if digest(path) != expected:
            raise ValueError(f"Integridad inválida: {relative}")
    # Un módulo extra también podría cambiar los imports, aunque no aparezca en el manifiesto.
    for name in ("backend", "ML", "deploy"):
        for path in (folder / name).rglob("*.py"):
            if path.relative_to(folder).as_posix() not in files:
                raise ValueError("Código no registrado en la entrega.")
    metadata = json.loads((folder / MODEL / "metadata.json").read_text())
    if (
        metadata["model_version"] != manifest["model_version"]
        or metadata["model_sha256"] != manifest["model_sha256"]
    ):
        raise ValueError("Metadatos del modelo distintos de la entrega.")
    return manifest


def main() -> None:
    """Expone construcción y verificación para PowerShell."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build")
    create.add_argument("--destination", type=Path, required=True)
    create.add_argument("--version", required=True)
    check = sub.add_parser("verify")
    check.add_argument("folder", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        print(build(ROOT, args.destination, args.version))
    else:
        print(json.dumps(verify(args.folder), indent=2))


if __name__ == "__main__":
    main()
