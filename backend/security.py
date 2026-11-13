"""Política de transporte, origen y secretos para API-04."""

import ipaddress
import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from starlette.requests import Request

Network = ipaddress.IPv4Network | ipaddress.IPv6Network
ROOT = Path(__file__).resolve().parents[1]


def configured_path(value: str) -> Path:
    """Resuelve rutas de configuración relativas a la raíz del proyecto."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_api_key(env: Mapping[str, str]) -> str:
    """Acepta un secreto por entorno o archivo, nunca ambas fuentes a la vez."""
    value = env.get("CHURN_API_KEY", "")
    filename = env.get("CHURN_API_KEY_FILE", "")
    if value and filename:
        raise ValueError("Configure solo CHURN_API_KEY o CHURN_API_KEY_FILE.")
    if filename:
        path = configured_path(filename)
        if path.stat().st_size > 1024:
            raise ValueError("Archivo de clave demasiado grande.")
        value = path.read_text(encoding="utf-8-sig").rstrip("\r\n")
    if (
        not 32 <= len(value) <= 512
        or not value.isascii()
        or any(c.isspace() for c in value)
    ):
        raise ValueError("CHURN_API_KEY requiere 32–512 caracteres ASCII sin espacios.")
    return value


def valid_api_key(candidate: str | None, expected: str) -> bool:
    """No acepta valores enormes o no ASCII; compara sin exponer el secreto."""
    if candidate is None or len(candidate) > 512 or not candidate.isascii():
        return False
    return secrets.compare_digest(candidate, expected)


@dataclass(frozen=True)
class SecurityPolicy:
    """La IP es la del socket; el lanzador no confía en X-Forwarded-* recibidos."""

    allowed_networks: tuple[Network, ...]
    allowed_hosts: frozenset[str]
    allow_local_http: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "SecurityPolicy":
        """Carga una política cerrada por defecto y rechaza comodines globales."""
        values = os.environ if env is None else env
        local_http = values.get("CHURN_ALLOW_LOCAL_HTTP", "0")
        if local_http not in {"0", "1"}:
            raise ValueError("CHURN_ALLOW_LOCAL_HTTP debe ser 0 o 1.")
        raw_networks = values.get("CHURN_ALLOWED_CIDRS", "127.0.0.1/32,::1/128")
        networks = tuple(
            ipaddress.ip_network(item.strip())
            for item in raw_networks.split(",")
            if item.strip()
        )
        if not networks or any(network.prefixlen == 0 for network in networks):
            raise ValueError(
                "Defina IPs o redes permitidas; no se acepta acceso global /0."
            )
        hosts = frozenset(
            item.strip().lower()
            for item in values.get(
                "CHURN_ALLOWED_HOSTS", "localhost,127.0.0.1,::1"
            ).split(",")
            if item.strip()
        )
        if not hosts or any(
            "*" in host or "/" in host or any(c.isspace() for c in host)
            for host in hosts
        ):
            raise ValueError(
                "CHURN_ALLOWED_HOSTS requiere nombres exactos, sin comodines."
            )
        return cls(networks, hosts, local_http == "1")

    def reject(self, request: Request) -> tuple[int, str, str] | None:
        """Rechaza orígenes, hosts y transporte inválidos antes de leer el cuerpo."""
        try:
            address = ipaddress.ip_address(
                request.client.host if request.client else ""
            )
        except ValueError:
            return 403, "source_denied", "Origen no permitido."
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        if not any(address in network for network in self.allowed_networks):
            return 403, "source_denied", "Origen no permitido."
        try:
            host = request.url.hostname
        except ValueError:
            host = None
        if len(request.headers.getlist("host")) != 1 or host not in self.allowed_hosts:
            return 400, "host_denied", "Nombre de servidor no permitido."
        if request.url.scheme != "https" and not (
            self.allow_local_http and address.is_loopback
        ):
            return 426, "https_required", "Se requiere HTTPS."
        return None
