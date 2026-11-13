# CRM-02 — cliente HTTPS de Krayin

Estado: **completado**, 28 de octubre de 2026. Implementación en `C:\xampp\htdocs\KrayinCRM\laravel-crm-2.2\packages\Webkul\Churn\src`. Conecta Laravel con `/v1/predict/transactions`; Python calcula las variables y aplica el modelo. No guarda predicciones ni envía comunicaciones: esas funciones corresponden a las siguientes tareas.

## Implementación y configuración

- `Services/ChurnApiClient.php`: cliente Guzzle inyectable, autenticación `X-API-Key`, HTTPS obligatorio, certificado y nombre verificados. No sigue redirecciones ni usa proxies heredados del entorno.
- `Config/api.php`: configuración Laravel mediante `CHURN_API_URL`, `CHURN_CLIENT_KEY_FILE`, `CHURN_CLIENT_CA_FILE` y `CHURN_EXPECTED_MODEL`.
- `Exceptions/ChurnApiException.php`: errores con motivo, estado HTTP e intentos; sin encadenar mensajes de transporte que pudieran incluir credenciales o datos del cliente.
- `Console/PredictDatasetCustomer.php`: comando `churn:predict-customer`. Lee el historial importado y consulta la API; no modifica contactos, atributos ni predicciones.
- Registro en `ChurnServiceProvider.php`, entrada en `CHANGELOG.md` y parámetros sin secretos en `.env.example`.

La instalación local tiene URL `https://127.0.0.1:8443`. La clave y la CA se leen desde los archivos ya existentes en `.local/security` del proyecto de investigación, fuera de la carpeta pública de Krayin. No se copiaron sus contenidos al código ni al `.env`. La cuenta que ejecute PHP debe tener permiso de lectura sobre esos archivos; se comprobó el acceso desde PHP CLI bajo la cuenta actual, no desde otra cuenta de servicio de Apache.

## Límites, fallos y contrato

- Conexión: hasta 3 segundos. Cada intento: hasta 15 segundos. Máximo 3 intentos y presupuesto de 50 segundos incluyendo esperas.
- Reintentos para 408, 500, 502, 503 y 504, y errores transitorios de cURL reconocidos. Esperas de 1 y 2 segundos más variación de 0–250 ms. Se respeta `Retry-After` numérico o como fecha HTTP; si no cabe en el presupuesto, se cancela.
- Certificados/configuración de transporte inválidos no se reintentan. Tampoco redirecciones ni errores HTTP permanentes como 401, 403 y 422.
- Máximo 5.000 líneas y 2.000.000 bytes por petición. Valores no representables en JSON son rechazados antes del envío.
- Respuestas válidas deben corresponder al cliente y corte solicitados, versión esperada, esquema `churn180-v1`, horizonte 180, probabilidad numérica entre 0 y 1, categoría admitida, fecha de cálculo y estados experimentales coherentes. Se exige `automatic_action_allowed=false` y `limited_history` booleano.
- Errores HTML, JSON incompatible o respuesta de otra versión no se presentan como predicciones. Un fallo nunca se convierte en riesgo bajo.

El consumidor es síncrono y procesa una consulta cada vez. La ejecución por lotes, coordinación de concurrencia y worker de cola quedan en CRM-04.4. El endpoint batch no es necesario para este consumidor de transacciones por cliente y no se ha implementado en esta tarea.

## Consulta de un cliente

Con MySQL y la API HTTPS activos, ejecutar desde la raíz de Krayin:

```powershell
C:\xampp\php\php.exe artisan churn:predict-customer AA-10315 --as-of=2018-06-30
```

El comando selecciona `(corte - 365 días, corte]` y envía identificadores de línea/pedido, fecha, ventas, categoría y subcategoría. No envía nombres, correos ni teléfonos. La cobertura se informa mediante `history_start`; el indicador `limited_history` recibido se conserva, sin reinterpretarlo.

Para iniciar manualmente la API local en una terminal del proyecto de investigación:

```powershell
$env:CHURN_API_KEY_FILE = (Resolve-Path '.local/security/api-key.txt').Path
$env:CHURN_TLS_CERT_FILE = (Resolve-Path '.local/security/cert.pem').Path
$env:CHURN_TLS_KEY_FILE = (Resolve-Path '.local/security/key.pem').Path
& .\backend\start.ps1 -Port 8443
```

No configurar simultáneamente `CHURN_API_KEY` y `CHURN_API_KEY_FILE`. El certificado local debe seguir vigente. Estos comandos mantienen la API activa mientras se conserve el proceso; no instalan un servicio permanente. El ensayo de CRM-02 utilizó un puerto temporal y cerró el servidor al terminar.

## Evidencia obtenida

Archivo principal para capturas: `docs/evidencias_crm02/https_real.json`.

| Caso | Resultado |
|---|---|
| PHP → ventas de MySQL → API HTTPS → modelo | Respuesta válida para AA-10315, corte 30/06/2018 |
| Probabilidad | 0,3400690869680104, exactamente coincidente con el artefacto de prueba temporal |
| Categoría | Medio, devuelta por Python |
| Estado | Experimental, `automatic_action_allowed=false`, `limited_history=true` |
| Clave inválida | HTTP 401, un intento |
| Venta negativa | HTTP 422, un intento |
| Archivo CA inválido | Error de transporte/TLS, un intento; no se desactivó la validación |
| API detenida | Tres intentos y error explícito por agotamiento |

`docs/evidencias_crm02/pruebas.txt`: **51 pruebas aprobadas y 131 aserciones**. Incluye 40 casos del cliente HTTP y los 11 del lector CSV anterior. Se verificaron éxito, errores permanentes, redirecciones, estados transitorios, espera, presupuesto, errores de conexión/TLS y respuestas incompatibles. Las pruebas unitarias usan transporte simulado; el JSON anterior registra el ensayo HTTPS real. Pint pasó en los archivos PHP modificados. No se calculó cobertura ni se ejecutó toda la batería original de Krayin.

`docs/evidencias_crm02/contactos_despues.json` conserva las huellas de CRM-01: personas y atributos permanecen iguales. No se volvió a importar el dataset.

Reproducir el ensayo desde el proyecto de investigación:

```powershell
.\.venv-clean\Scripts\python.exe -m scripts.verify_crm02
```

Requiere MySQL activo y los archivos locales de certificado y clave. El script usa `scripts/probe_crm02.php` y crea únicamente credenciales inválidas temporales para pruebas; las elimina al terminar. La probabilidad reproducida demuestra integración técnica, no utilidad comercial ni mejora de fidelización.

## Siguiente paso

CRM-03: guardar resultados e historial mediante migraciones y repositorios. CRM-04 construirá el panel sobre esos resultados; CRM-05 añadirá sugerencias y revisión manual.
