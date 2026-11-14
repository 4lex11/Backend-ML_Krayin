"""Render terminates public TLS; nginx forwards locally without trusting headers."""
import os
from pathlib import Path


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    if not 1024 <= port <= 65535 or port == 8443:
        raise ValueError("Invalid public port")
    # Explicitly scoped HTTP exception: Python remains on the loopback interface.
    os.environ.update({
        "CHURN_BIND_HOST": "127.0.0.1", "CHURN_PORT": "8443",
        "CHURN_ALLOWED_CIDRS": "127.0.0.1/32",
        "CHURN_ALLOWED_HOSTS": "127.0.0.1", "CHURN_ALLOW_LOCAL_HTTP": "1",
    })
    for key in ("CHURN_TLS_CERT_FILE", "CHURN_TLS_KEY_FILE"):
        os.environ.pop(key, None)
    for folder in ("/tmp/nginx/body", "/tmp/nginx/proxy"):
        Path(folder).mkdir(parents=True, exist_ok=True)
    template = Path("/app/deploy/render/nginx.conf.template").read_text()
    Path("/tmp/nginx.conf").write_text(template.replace("PUBLIC_PORT", str(port)))
    os.execvp("supervisord", ["supervisord", "-c", "/app/deploy/render/supervisord.conf"])


if __name__ == "__main__":
    main()
