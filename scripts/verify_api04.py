"""Prueba HTTPS real en loopback y registra resultados sin secretos."""

import http.client
import json
import os
import secrets
import socket
import ssl
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / ".local/security"


@contextmanager
def server(
    overrides: dict[str, str], process_info: dict[str, int] | None = None
) -> Iterator[int]:
    """Inicia el lanzador real desde otro directorio y cierra siempre el proceso."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("CHURN_"):
            env.pop(key)
    env.update(
        {
            "PYTHONPATH": str(ROOT),
            "CHURN_PORT": str(port),
            "CHURN_API_KEY_FILE": str(FOLDER / "api-key.txt"),
            "CHURN_TLS_CERT_FILE": str(FOLDER / "cert.pem"),
            "CHURN_TLS_KEY_FILE": str(FOLDER / "key.pem"),
        }
    )
    env.update(overrides)
    process = subprocess.Popen(
        [sys.executable, "-m", "backend.serve"],
        cwd=ROOT / "docs",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        if process_info is not None:
            process_info["pid"] = process.pid
        deadline = time.monotonic() + 30
        while True:
            if process.poll() is not None:
                raise RuntimeError(
                    "El servidor no arrancó: "
                    + process.stderr.read().decode(errors="replace")
                )
            try:
                call(port, "/health/live")
                break
            except OSError, http.client.HTTPException:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.1)
        yield port
    finally:
        process.terminate()
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def call(
    port: int,
    path: str,
    key: str | None = None,
    host: str | None = None,
    tls12: bool = False,
) -> tuple[int, dict[str, Any], str]:
    """Verifica nombre y certificado del servidor; no usa verify=False."""
    context = ssl.create_default_context(cafile=str(FOLDER / "cert.pem"))
    if tls12:
        context.maximum_version = ssl.TLSVersion.TLSv1_2
    connection = http.client.HTTPSConnection(
        "127.0.0.1", port, context=context, timeout=5
    )
    headers = {"X-API-Key": key} if key is not None else {}
    if host:
        headers["Host"] = host
    try:
        connection.connect()
        version = connection.sock.version()
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = json.loads(response.read())
        return response.status, body, version
    finally:
        connection.close()


def main() -> None:
    """Comprueba HTTPS, rechazo por IP/host, credenciales y renovación de clave."""
    key = (FOLDER / "api-key.txt").read_text().strip()
    results: dict[str, Any] = {}
    with server({}) as port:
        status, data, protocol = call(port, "/health/ready", key)
        assert status == 200 and data["model_version"] == "churn180-v1"
        results["trusted_certificate_and_hostname"] = True
        results["https_authenticated_status"] = status
        results["negotiated_protocol"] = protocol
        assert call(port, "/health/ready", key, tls12=True)[2] == "TLSv1.2"
        results["tls12_supported"] = True
        assert call(port, "/health/ready")[0] == 401
        assert call(port, "/health/ready", "incorrect")[0] == 401
        results["absent_and_invalid_key_status"] = 401
        assert call(port, "/health/live", host="untrusted.example")[0] == 400
        results["untrusted_host_status"] = 400
        client = http.client.HTTPSConnection(
            "127.0.0.1", port, context=ssl.create_default_context(), timeout=5
        )
        try:
            try:
                client.request("GET", "/health/live")
            except ssl.SSLCertVerificationError:
                results["untrusted_certificate_rejected"] = True
            else:
                raise AssertionError(
                    "El cliente aceptó un certificado local no confiable."
                )
        finally:
            client.close()
        client_http = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            try:
                client_http.request(
                    "GET", "/health/live", headers={"X-Forwarded-Proto": "https"}
                )
                response = client_http.getresponse()
                assert response.status != 200
            except OSError, http.client.HTTPException:
                pass
            results["plaintext_http_not_accepted"] = True
        finally:
            client_http.close()
    with server({"CHURN_ALLOWED_CIDRS": "192.0.2.10/32"}) as port:
        assert call(port, "/health/ready", key)[0] == 403
        results["disallowed_peer_even_with_valid_key"] = 403
    new_key = secrets.token_urlsafe(48)
    with server({"CHURN_API_KEY_FILE": "", "CHURN_API_KEY": new_key}) as port:
        assert call(port, "/health/ready", key)[0] == 401
        assert call(port, "/health/ready", new_key)[0] == 200
        results["rotation_old_rejected_new_accepted"] = True
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": results,
        "scope": "Prueba local con Uvicorn, TLS real y certificado autofirmado confiado explícitamente por el cliente. Sin Krayin, DNS público ni cambios en firewall o confianza de Windows.",
    }
    output = ROOT / "docs/evidencias_api/07_seguridad_https.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
