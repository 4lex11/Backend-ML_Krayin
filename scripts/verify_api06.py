"""Carga HTTPS acotada sobre un servidor temporal; sin reintentos en la medición."""

import http.client
import json
import os
import platform
import ssl
import subprocess
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import numpy as np

from scripts.verify_api04 import FOLDER, ROOT, server


def resources(pid: int) -> dict[str, float]:
    """CPU y memoria del launcher y sus hijos directos en Windows."""
    command = f"$ids = @({pid}) + @(Get-CimInstance Win32_Process | Where-Object {{ $_.ParentProcessId -eq {pid} }} | Select-Object -ExpandProperty ProcessId); @(Get-Process -Id $ids -ErrorAction Stop | Select-Object CPU,WorkingSet64,PeakWorkingSet64) | ConvertTo-Json -Compress"
    value = json.loads(
        subprocess.check_output(
            ["powershell.exe", "-NoProfile", "-Command", command],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    )
    rows = value if isinstance(value, list) else [value]
    return {
        "cpu_seconds": sum(x["CPU"] for x in rows),
        "rss_mib": sum(x["WorkingSet64"] for x in rows) / 2**20,
        "sum_process_peak_rss_mib": sum(x["PeakWorkingSet64"] for x in rows) / 2**20,
    }


def main() -> None:
    """Mide escenarios normales y sobrecarga, y verifica recuperación."""
    sample = json.loads((ROOT / "deploy/acceptance_request.json").read_text())
    key = (FOLDER / "api-key.txt").read_text().strip()
    context = ssl.create_default_context(cafile=str(FOLDER / "cert.pem"))
    info: dict[str, int] = {}
    results: list[dict[str, Any]] = []
    with server({}, info) as port:

        def call(size: int) -> tuple[int, float]:
            body = (
                sample
                if size == 1
                else {
                    "customers": [
                        {**sample, "customer_id": f"LOAD-{i}"} for i in range(size)
                    ]
                }
            )
            path = "/v1/predict" if size == 1 else "/v1/predict/batch"
            connection = http.client.HTTPSConnection(
                "127.0.0.1", port, context=context, timeout=15
            )
            start = time.perf_counter()
            try:
                connection.request(
                    "POST",
                    path,
                    json.dumps(body),
                    {"X-API-Key": key, "Content-Type": "application/json"},
                )
                response = connection.getresponse()
                payload = response.read()
                if response.status == 200:
                    rows = [json.loads(payload)] if size == 1 else json.loads(payload)
                    assert len(rows) == size
                    assert all(
                        abs(row["probabilidad_churn"] - 0.3400690869680104) < 1e-12
                        for row in rows
                    )
                    assert [r["customer_id"] for r in rows] == (
                        [sample["customer_id"]]
                        if size == 1
                        else [f"LOAD-{i}" for i in range(size)]
                    )
                else:
                    assert response.status == 503
                    assert response.getheader("Retry-After") == "1"
                return response.status, (time.perf_counter() - start) * 1000
            finally:
                connection.close()

        for size in [1, 500]:
            for concurrency in [1, 4, 16]:
                for _ in range(3):
                    assert call(size)[0] == 200
                before = resources(info["pid"])
                started = time.perf_counter()
                with ThreadPoolExecutor(concurrency) as executor:
                    observations = list(executor.map(call, [size] * 80))
                elapsed = time.perf_counter() - started
                after = resources(info["pid"])
                successful = [ms for status, ms in observations if status == 200]
                counts = dict(Counter(str(status) for status, _ in observations))
                assert successful and (concurrency > 4 or counts.get("503", 0) == 0)
                assert np.percentile(successful, 95) < 5000
                assert call(1)[0] == 200
                results.append(
                    {
                        "batch_size": size,
                        "concurrency": concurrency,
                        "requests": 80,
                        "status_counts": counts,
                        "successful_latency_ms": {
                            f"p{p}": round(float(np.percentile(successful, p)), 2)
                            for p in [50, 95, 99]
                        },
                        "successful_requests_per_second": round(
                            len(successful) / elapsed, 2
                        ),
                        "successful_customers_per_second": round(
                            len(successful) * size / elapsed, 2
                        ),
                        "elapsed_seconds": round(elapsed, 3),
                        "before": before,
                        "after": after,
                        "cpu_seconds_during_load_upper_bound": round(
                            after["cpu_seconds"] - before["cpu_seconds"], 3
                        ),
                        "recovery_http_status": 200,
                    }
                )
                print(
                    f"size={size} concurrency={concurrency} statuses={counts}",
                    flush=True,
                )
        slow = []
        try:
            for _ in range(4):
                connection = http.client.HTTPSConnection(
                    "127.0.0.1", port, context=context, timeout=10
                )
                connection.putrequest("POST", "/v1/predict")
                connection.putheader("X-API-Key", key)
                connection.putheader("Content-Length", "1")
                connection.endheaders()
                slow.append(connection)
            time.sleep(0.2)
            assert call(1)[0] == 503
            for connection in slow:
                response = connection.getresponse()
                assert response.status == 408
                response.read()
        finally:
            for connection in slow:
                connection.close()
        assert call(1)[0] == 200
    report = {
        "slow_body_check": {
            "occupied_slots": 4,
            "saturation_status": 503,
            "incomplete_body_status": 408,
            "recovery_status": 200,
        },
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "logical_cpus": os.cpu_count(),
        "model_version": "churn180-v1",
        "scenarios": results,
        "scope": "Loopback HTTPS con validación de certificado; conexión TLS nueva por solicitud; cliente y servidor en el mismo equipo; 3 calentamientos y 80 solicitudes por escenario; sin reintentos. Memoria: instantáneas y suma de máximos por proceso desde el arranque, no pico simultáneo. CPU incluye consulta de recursos posterior. No prueba prolongada ni garantía de capacidad en otro servidor.",
        "acceptance": "Sin 503 con concurrencia 1/4, sin errores inesperados, p95 exitoso <5000 ms y recuperación 200 en todos los escenarios.",
    }
    (ROOT / "docs/evidencias_api/09_carga_https.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
