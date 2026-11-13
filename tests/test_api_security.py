"""API-04: transporte, origen real, hosts, credenciales y arranque cerrado."""

import ssl
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from backend.main import app
from backend.security import (
    SecurityPolicy,
    configured_path,
    read_api_key,
    valid_api_key,
)
from backend.serve import build_config, tls_context

KEY = "test-only-credential-for-security-1234567890"


def request(
    ip: str = "127.0.0.1", scheme: str = "https", host: str = "localhost"
) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": scheme,
            "path": "/health/live",
            "query_string": b"",
            "headers": [(b"host", host.encode())],
            "client": (ip, 12345),
            "server": ("127.0.0.1", 8443),
        }
    )


@pytest.mark.parametrize("ip", ["127.0.0.1", "::1", "::ffff:127.0.0.1"])
def test_loopback_policy(ip: str) -> None:
    assert SecurityPolicy.from_env({}).reject(request(ip)) is None


def test_network_tls_host_policy() -> None:
    policy = SecurityPolicy.from_env({})
    assert policy.reject(request("10.0.0.9"))[0] == 403
    assert policy.reject(request("invalid"))[0] == 403
    assert policy.reject(request(host="attacker.example"))[0] == 400
    assert policy.reject(request(scheme="http"))[0] == 426
    dev = SecurityPolicy.from_env(
        {
            "CHURN_ALLOW_LOCAL_HTTP": "1",
            "CHURN_ALLOWED_CIDRS": "127.0.0.1/32,10.0.0.9/32",
        }
    )
    assert dev.reject(request(scheme="http")) is None
    assert dev.reject(request("10.0.0.9", scheme="http"))[0] == 426
    assert dev.reject(request("10.0.0.9")) is None


@pytest.mark.parametrize(
    "env",
    [
        {"CHURN_ALLOWED_CIDRS": "0.0.0.0/0"},
        {"CHURN_ALLOWED_CIDRS": "::/0"},
        {"CHURN_ALLOWED_CIDRS": ""},
        {"CHURN_ALLOWED_CIDRS": "nonsense"},
        {"CHURN_ALLOWED_HOSTS": "*"},
        {"CHURN_ALLOWED_HOSTS": ""},
        {"CHURN_ALLOWED_HOSTS": "https://example.com"},
        {"CHURN_ALLOW_LOCAL_HTTP": "yes"},
    ],
)
def test_invalid_policy(env: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        SecurityPolicy.from_env(env)


def test_secret_sources(tmp_path: Path) -> None:
    path = tmp_path / "secret.txt"
    path.write_text(KEY + "\n", encoding="utf-8")
    assert read_api_key({"CHURN_API_KEY_FILE": str(path)}) == KEY
    assert read_api_key({"CHURN_API_KEY": KEY}) == KEY
    assert configured_path(str(path)) == path
    assert configured_path(".local/secret.txt").is_absolute()
    with pytest.raises(ValueError):
        read_api_key({"CHURN_API_KEY": KEY, "CHURN_API_KEY_FILE": str(path)})
    for value in ["", "short", "a" * 513, "a" * 40 + " ", "ñ" * 40]:
        with pytest.raises(ValueError):
            read_api_key({"CHURN_API_KEY": value})
    path.write_text("x" * 1025)
    with pytest.raises(ValueError):
        read_api_key({"CHURN_API_KEY_FILE": str(path)})
    assert valid_api_key(KEY, KEY)
    for value in [None, "wrong", "ñ", "x" * 513]:
        assert not valid_api_key(value, KEY)


def test_serve_fail_closed() -> None:
    base = {"CHURN_API_KEY": KEY}
    for extra in [
        {},
        {"CHURN_TLS_CERT_FILE": "missing"},
        {"CHURN_PORT": "0"},
        {"CHURN_ALLOW_LOCAL_HTTP": "1", "CHURN_BIND_HOST": "0.0.0.0"},
        {
            "CHURN_TLS_CERT_FILE": "missing",
            "CHURN_TLS_KEY_FILE": "missing",
            "CHURN_BIND_HOST": "0.0.0.0",
        },
    ]:
        with pytest.raises(ValueError):
            build_config({**base, **extra})
    config = build_config({**base, "CHURN_ALLOW_LOCAL_HTTP": "1"})
    assert config.host == "127.0.0.1"
    assert config.proxy_headers is False
    assert config.forwarded_allow_ips == ""
    assert config.server_header is False
    context = tls_context(config, lambda: ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER))
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [
        "CHURN_API_KEY_FILE",
        "CHURN_MODEL_PATH",
        "CHURN_ALLOWED_HOSTS",
        "CHURN_ALLOWED_CIDRS",
        "CHURN_ALLOW_LOCAL_HTTP",
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CHURN_API_KEY", KEY)


def test_spoofed_headers_do_not_grant_access(configured: None) -> None:
    with TestClient(
        app, base_url="http://localhost", client=("127.0.0.1", 9)
    ) as client:
        result = client.get("/health/live", headers={"X-Forwarded-Proto": "https"})
        assert result.status_code == 426
    with TestClient(
        app, base_url="https://localhost", client=("10.0.0.9", 9)
    ) as client:
        result = client.get(
            "/health/live", headers={"X-Forwarded-For": "127.0.0.1", "X-API-Key": KEY}
        )
        assert result.status_code == 403


def test_auth_before_body_and_protected_docs(configured: None) -> None:
    with TestClient(
        app, base_url="https://localhost", client=("127.0.0.1", 9)
    ) as client:
        assert client.post("/v1/predict", content=b"{" * 2_000_001).status_code == 401
        for url in ["/openapi.json", "/docs", "/redoc", "/health/ready"]:
            assert client.get(url).status_code == 401
            assert client.get(url, headers={"X-API-Key": KEY}).status_code == 200
        assert (
            client.get("/health/live", headers={"Host": "attacker.example"}).status_code
            == 400
        )
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
