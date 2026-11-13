# Contrato para conectar Krayin posteriormente

La API está preparada para un consumidor PHP, pero este repositorio no incluye la instalación de Krayin. No se han ejecutado campañas, insertado contactos ni verificado migraciones en un CRM real.

## HTTP y autenticación

- Base local segura: `https://127.0.0.1:8443`; el cliente debe verificar el certificado y el nombre del servidor. Preparación y arranque: [API04_SEGURIDAD.md](API04_SEGURIDAD.md).
- Autenticación: cabecera `X-API-Key`, secreto de al menos 32 caracteres obtenido del entorno; nunca enviar como parámetro de URL ni guardarlo en el repositorio.
- `GET /health/live`: vida del proceso, sin clave ni datos del modelo; sujeto a HTTPS, IP y Host permitidos.
- `GET /health/ready`: disponibilidad técnica, autenticado; el modelo conserva estado `experimental`.
- `POST /v1/predict`: predicción de un cliente con agregados.
- `POST /v1/predict/batch`: hasta 500 clientes; preserva el orden y rechaza claves cliente-fecha duplicadas. No hay escrituras ni efectos comerciales.
- `POST /v1/predict/transactions`: hasta 5.000 líneas de compra de un cliente; calcula variables en Python.
- Límite general del cuerpo: 2.000.000 bytes. Campos adicionales son errores.

El endpoint anterior `/predict` fue sustituido por `/v1/predict`: el contrato cambió de seis variables sin contexto a siete variables con cliente y fecha de corte. No enviar solicitudes del prototipo antiguo.

## Definición de variables

Se consideran compras en `(fecha_corte - 365 días, fecha_corte]`. La población elegible tiene al menos una compra en los últimos 180 días. Clientes sin compras o ya inactivos fuera de ese plazo se rechazan, no se les asigna un riesgo ficticio.

| Campo | Significado |
|---|---|
| Recency | Días desde la última compra hasta el corte, de 0 a 180 |
| Frequency | Cantidad de pedidos distintos en la ventana anual |
| Monetary_Sum | Suma de ventas de las líneas de pedido |
| Monetary_Mean | Media por línea, no ticket medio por pedido |
| Monetary_Std | Desviación muestral por línea, 0 cuando solo existe una línea |
| Cat_Count | Categorías distintas |
| SubCat_Count | Subcategorías distintas |

Conteos enteros positivos, valores monetarios finitos y no negativos. Las devoluciones deben resolverse en el origen antes de usar este contrato: no se ignoran ni se imputan silenciosamente. Clientes con un solo pedido son aceptados con `limited_history: true`.

La recencia vuelve a incluirse porque ahora se calcula antes de la ventana futura que define la etiqueta. Ya no es la misma variable que determina directamente la respuesta.

## Solicitud y respuesta

Ejemplo real ejecutado y guardado: `docs/evidencias_api/01_solicitud.json`; respuesta correspondiente: `docs/evidencias_api/02_respuesta.json`.

La respuesta conserva probabilidad sin redondear, riesgo, cliente, corte, fecha UTC de inferencia, versión, horizonte de 180 días y estado experimental. `automatic_action_allowed` es `false`: el consumidor debe respetarlo. La sugerencia es revisión humana, no una campaña automática ni la afirmación “cliente fidelizado”.

Para el endpoint de compras, el origen declara `history_start` con cobertura mínima de 365 días. Cada línea contiene `line_id`, `order_id`, `order_date` en ISO `YYYY-MM-DD`, `sales`, `category` y `subcategory`. Dos líneas legítimas, aunque tengan el mismo importe, necesitan IDs diferentes. Una línea idéntica repetida se deduplica; el mismo ID con datos diferentes se rechaza. Se rechazan fechas posteriores al corte y anteriores a la cobertura declarada. La cobertura declarada no prueba que el sistema de origen haya enviado todas sus ventas: debe validarse en la integración.

## Manejo de errores y reintentos

| Estado | Significado | Acción del consumidor |
|---|---|---|
| 401 | Clave ausente o inválida | Revisar configuración; no reintentar sin corregir |
| 400 / 403 | Host o IP no permitidos | Revisar la configuración del servicio y origen |
| 426 | Transporte HTTP no permitido | Conectar por HTTPS desde el inicio |
| 404 | Ruta incorrecta, incluida la antigua `/predict` | Usar contrato versionado |
| 413 | Cuerpo excedido | Reducir tamaño del envío |
| 408 | Recepción del cuerpo agotada | Reenviar cuerpo completo dentro del presupuesto de reintentos |
| 503 | Saturación | Respetar `Retry-After` si existe y aplicar reintentos limitados |
| 422 | Campos, dominio o cobertura inválidos | Corregir datos; no reintentar la misma solicitud |
| 500 | Error interno | Registrar `request_id`; reintento limitado |

Las respuestas de la aplicación incluyen `X-Request-ID`; `X-Process-Time-Ms` aparece en el procesamiento normal y puede faltar en rechazos tempranos. Los errores de la aplicación usan `error.code`, `error.message` y `request_id`. La respuesta de validación incluye nombres de campos, sin copiar sus valores. Un rechazo del transporte Uvicorn o de un intermediario puede tener otro formato y no incluir esas cabeceras.

Política API-06 para PHP: conexión de 3 segundos, total de 15 segundos por intento, hasta dos reintentos y presupuesto total de 50 segundos. Manejar 408 y fallos transitorios según [API06_CARGA.md](API06_CARGA.md), respetando `Retry-After` y sin reintentar errores de certificado o datos inválidos. La instancia admite cuatro predicciones simultáneas y limita a cinco segundos la recepción del cuerpo. La inferencia no tiene efectos, pero la escritura posterior en Krayin debe ser idempotente mediante `(customer_id, as_of, model_version)`.

## Persistencia futura

Krayin debe resolver su ID interno a partir de un ID externo estable, conservar histórico de probabilidad, versión y corte, y mostrar la antigüedad de cada resultado. Los IDs de atributos 61–65 del importador antiguo no forman parte de este contrato. Falta verificar la versión de Krayin, construir el cliente Laravel y probar las escrituras mediante su capa de aplicación.

## Operación

El script `backend/start.ps1` utiliza el lanzador HTTPS `backend.serve` y escucha por defecto en loopback. API-04 incorpora TLS, lista de IPs y nombres permitidos, credenciales en archivo y pruebas de comunicación segura. Los nombres, certificados y reglas del servidor definitivo deberán configurarse en ese entorno; no se modificó un servidor externo ni el firewall de Windows. Véase [API04_SEGURIDAD.md](API04_SEGURIDAD.md).

Conservar juntos `model.joblib` y `metadata.json`. Cambiar `CHURN_MODEL_PATH` y reiniciar cambia de versión; la carga verifica hash, variables, clases y versiones de librerías. Para volver atrás, apuntar a una versión temporal previamente validada y reiniciar. Los cuatro `.pkl` históricos no tienen el nuevo contrato y no son candidatos de reversión directa.

Registrar fallos, latencia y frecuencia de puntuación; comparar cambios de distribución y medir desempeño solo cuando maduren los 180 días de resultados. Cualquier nuevo entrenamiento debe usar otro directorio/versionado y un periodo futuro no usado para ajustar el modelo actual.
