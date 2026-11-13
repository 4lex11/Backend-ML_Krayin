"""Lanzador HTTPS sin confianza en cabeceras de proxy: python -m backend.serve."""

import ipaddress
import os
import ssl
from collections.abc import Callable, Mapping

import uvicorn

from backend.security import ROOT, SecurityPolicy, configured_path, read_api_key


def tls_context(
    config: uvicorn.Config, factory: Callable[[], ssl.SSLContext]
) -> ssl.SSLContext:
    """Exige TLS 1.2 como mínimo; conserva validación de cadena/clave de Uvicorn."""
    context = factory()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def build_config(env: Mapping[str, str] | None = None) -> uvicorn.Config:
    """Valida secretos y certificados antes de abrir el puerto."""
    values = os.environ if env is None else env
    policy = SecurityPolicy.from_env(values)
    read_api_key(values)
    host = values.get("CHURN_BIND_HOST", "127.0.0.1")
    address = ipaddress.ip_address(host)
    port = int(values.get("CHURN_PORT", "8443"))
    if not 1 <= port <= 65535:
        raise ValueError("CHURN_PORT debe estar entre 1 y 65535.")
    cert = values.get("CHURN_TLS_CERT_FILE", "")
    key = values.get("CHURN_TLS_KEY_FILE", "")
    if bool(cert) != bool(key):
        raise ValueError("Configure certificado y clave TLS juntos.")
    if not cert and not (policy.allow_local_http and address.is_loopback):
        raise ValueError(
            "Faltan certificados TLS; HTTP solo se permite explícitamente en loopback."
        )
    if not address.is_loopback and (
        not values.get("CHURN_ALLOWED_HOSTS") or not values.get("CHURN_ALLOWED_CIDRS")
    ):
        raise ValueError(
            "Una interfaz externa requiere hosts y redes permitidos explícitos."
        )
    cert_path = str(configured_path(cert)) if cert else None
    key_path = str(configured_path(key)) if key else None
    if cert_path and key_path:
        check = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        check.minimum_version = ssl.TLSVersion.TLSv1_2
        check.load_cert_chain(cert_path, key_path)
    return uvicorn.Config(
        "backend.main:app",
        host=host,
        port=port,
        ssl_certfile=cert_path,
        ssl_keyfile=key_path,
        ssl_context_factory=tls_context if cert else None,
        proxy_headers=False,
        forwarded_allow_ips="",
        server_header=False,
        access_log=False,
        log_config=str(ROOT / "backend/logging.json"),
        timeout_keep_alive=5,
        limit_concurrency=64,
        backlog=64,
        timeout_graceful_shutdown=15,
    )


def main() -> None:
    """Inicia un proceso; no instala servicios ni abre reglas de firewall."""
    server = uvicorn.Server(build_config())
    server.run()
    if not server.started:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
