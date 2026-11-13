# ML para gestión y fidelización de clientes

La etapa académica con el dataset disponible está documentada en `InvestigacionTesis2026.docx` (42 páginas revisadas; incluye integración con Krayin). Véanse las [conclusiones detalladas](docs/CONCLUSIONES_DETALLADAS.md), la [guía de capturas](docs/GUIA_CAPTURAS.md) y la [revisión de coherencia](docs/REVISION_COHERENCIA.md). El borrador original se conserva en `docs/historico/InvestigacionTesis2026_original.docx`.

El proyecto separa modelos e inferencia (`ML/`), API Python (`backend/`) y prototipos de integración (`integraciones/krayin/`). El flujo vigente estima ausencia de recompra a 180 días mediante un protocolo temporal. El modelo `churn180-v1` es experimental: la evaluación no demuestra utilidad predictiva suficiente para automatizar campañas.

## Ejecutar la API con HTTPS

La configuración de seguridad API-04 está implementada y comprobada localmente: TLS 1.2 o superior, autenticación, lista de IPs y nombres de servidor permitidos y secretos en archivos privados. No requiere conectar Krayin.

En este equipo existen `.venv-clean` y `.local/security/`. Desde la raíz, en PowerShell 7.4 o superior:

```powershell
Remove-Item Env:CHURN_API_KEY -ErrorAction SilentlyContinue
$env:CHURN_API_KEY_FILE = '.local/security/api-key.txt'
$env:CHURN_TLS_CERT_FILE = '.local/security/cert.pem'
$env:CHURN_TLS_KEY_FILE = '.local/security/key.pem'
$env:CHURN_ALLOWED_CIDRS = '127.0.0.1/32,::1/128'
$env:CHURN_ALLOWED_HOSTS = 'localhost,127.0.0.1,::1'
$env:CHURN_ALLOW_LOCAL_HTTP = '0'
.\backend\start.ps1
```

Dirección: `https://127.0.0.1:8443`. El certificado local dura 30 días; el cliente debe confiar explícitamente en `.local/security/cert.pem`, sin omitir la validación TLS. La clave privada y la credencial de API no deben compartirse en capturas ni subirse al repositorio. La guía completa, instalación en otro equipo y renovación están en [docs/API04_SEGURIDAD.md](docs/API04_SEGURIDAD.md).

Use el lanzador `backend.serve` o `backend/start.ps1`: validan configuración y desactivan las cabeceras de proxy. El antiguo comando directo de Uvicorn con HTTP no es el procedimiento de despliegue vigente.

## Contrato y evidencia

- `POST /v1/predict`: cliente, fecha de corte y siete variables, incluida recencia.
- `POST /v1/predict/batch`: hasta 500 clientes.
- `POST /v1/predict/transactions`: calcula variables a partir de líneas de compra.
- `GET /health/ready`: estado técnico autenticado.
- `GET /health/live`: no requiere clave; sí cumple la política de red y HTTPS.

Predicción, documentación y estado detallado requieren `X-API-Key`. El endpoint histórico `/predict` y las solicitudes de seis variables ya no corresponden al contrato vigente.

Ejemplo: [solicitud](docs/evidencias_api/01_solicitud.json). Contrato completo: [CONTRATO_KRAYIN.md](docs/CONTRATO_KRAYIN.md). Prueba de seguridad real: [07_seguridad_https.json](docs/evidencias_api/07_seguridad_https.json). Algunas evidencias anteriores describen el transporte HTTP previo a API-04 y se conservan como históricas.

## Despliegue administrado (API-07)

API-06 añade cuatro cupos de predicción por proceso, rechazo 503 al saturarse y cinco segundos para recibir el cuerpo. La carga HTTPS y la política de reintentos están en [API06_CARGA.md](docs/API06_CARGA.md). La entrega que incorpora estos cambios es `api-2.1.0-api06`; las entregas anteriores permanecen intactas.

La [guía de despliegue](docs/API07_DESPLIEGUE.md) describe entregas con manifiesto SHA-256, un entorno virtual por versión, perfiles de configuración y aceptación HTTPS. `deploy/New-Release.ps1` construye la entrega; `deploy/Service.ps1` permite instalar, iniciar, detener, reiniciar, actualizar y revertir la tarea de Windows.

El perfil de Windows usa el usuario actual, admite reinicio tras una caída y puede arrancar al iniciar sesión. Para funcionamiento sin sesión en un servidor definitivo se requiere adaptar la cuenta y supervisión al destino. Las tareas temporales de verificación se eliminan al terminar; las entregas y evidencias permanecen disponibles. El ensayo no conecta Krayin.

## ML y reproducibilidad

El análisis de ML-06 está en [ML06_CALIBRACION_UMBRALES.md](docs/ML06_CALIBRACION_UMBRALES.md), con calibración, auditoría de umbrales y escenarios hipotéticos de capacidad/costos. Es un cierre académico con el dataset disponible; no acredita utilidad comercial ni modifica los umbrales de la API.

El artefacto vigente está en `ML/artifacts/churn180-v1/model.joblib`, con su manifiesto `metadata.json`. No intercambiarlo directamente por los `.pkl` históricos: tienen otro contrato. La API comprueba integridad, variables y versiones de bibliotecas al arrancar.

```powershell
.\.venv-clean\Scripts\python.exe -m ML.train --output ML/artifacts/nueva-ejecucion
```

El destino debe ser nuevo. El protocolo está en `ML/protocol.json`; resultados y gráficos actuales en [ML_Resultados_Finales.ipynb](ML/ML_Resultados_Finales.ipynb). Las celdas de este notebook leen archivos generados. Los demás notebooks identificados como históricos conservan sus resultados anteriores.

## Pruebas

```powershell
.\.venv-clean\Scripts\python.exe -m pytest -q
.\.venv-clean\Scripts\python.exe -m scripts.verify_api04
```

La segunda prueba inicia servidores HTTPS temporales en loopback y los cierra al terminar. Requiere que existan los certificados de desarrollo y que el entorno permita conexiones locales.

La integración local con Krayin PHP está completada. La guía vigente de instalación y operación es [GUIA_FINAL_CRM.md](docs/GUIA_FINAL_CRM.md), con [índice de evidencias](docs/INDICE_EVIDENCIAS_FINAL.md). DNS, certificados y firewall de un servidor externo quedan fuera del alcance actual. La infraestructura HTTPS local está comprobada; no se ha publicado un servicio externo ni ejecutado acciones de fidelización.

## Cierre de la mejora experimental (MEJ-08)

La ronda está cerrada: MEJ-01 a MEJ-06 y MEJ-08 completadas; MEJ-07 no aplica porque el candidato incumplió dos criterios de Brier. Se conserva v1 y la integración existente. La tesis reorganizada presenta implementación en páginas 7–18, resultados en 19–27, conclusiones en 29 y recomendaciones en 30. El índice de evidencias contiene la paginación vigente. Archivos concretos para capturas y límites: [acta de cierre](docs/MEJ08_CIERRE_DOCUMENTAL.md).



Reestructura de capítulos 3 y 4 (30/10/2026): metodología en páginas 7–18 y resultados en 19–27, con las cuatro imágenes originales indicadas. Ubicaciones y archivos para capturas: [índice vigente](docs/INDICE_EVIDENCIAS_FINAL.md).
