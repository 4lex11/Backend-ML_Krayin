# CRM-04.4 — actualización operativa de predicciones

Completada el 29 de octubre de 2026 para la demostración local con Superstore Sales. Python calcula las predicciones; Krayin gestiona solicitudes, persistencia y visualización. El modelo permanece experimental y no inicia acciones comerciales.

## Uso desde el panel

1. Abrir **Churn predictions / Predicciones de abandono**, escoger un corte histórico y aplicar el filtro. El corte inicial es 2018-06-30.
2. Abrir un cliente y pulsar **Request update / Solicitar actualización**. Para un lote, usar **Queue all my authorized customers / Solicitar lote de todos mis clientes autorizados** en el listado.
3. La solicitud queda pendiente hasta ejecutar el procesador de abajo. El botón no inicia por sí solo un servicio en segundo plano. Mientras la API esté detenida, no procesar la cola hasta iniciarla.
4. Usar **Check progress / Consultar progreso** para recargar el estado. No existe polling automático ni notificación externa.

Ambos botones requieren `churn` y `churn.update`. El lote incluye todos los clientes que permite el ámbito del usuario, incluso los que no están en la página actual. **No aplica la búsqueda ni los filtros de riesgo/estado**, y así lo indica la pantalla. Las consultas de progreso siempre respetan permisos, corte y versión configurada. Un grupo vacío no obtiene acceso global.

La actualización individual sobre una versión histórica distinta de la configurada no está habilitada. Las predicciones son inmutables por cliente/corte/versión: un resultado idéntico se reutiliza conservando su fecha original. Una respuesta o entrada distinta genera conflicto; no se reemplaza silenciosamente. No hay un botón para forzar sobrescrituras.

## Iniciar API y procesador

Se requiere MariaDB de XAMPP accesible, la migración `2026_10_29_000003_create_churn_work_items_table.php` aplicada y la configuración HTTPS de [CRM02_CONEXION_API.md](CRM02_CONEXION_API.md). La migración ya está aplicada en esta instalación. No hay que cambiar `QUEUE_CONNECTION` ni ejecutar `php artisan queue:work`: esta cola pertenece al módulo Churn.

En una terminal de PowerShell, desde el proyecto de investigación, iniciar la API:

```powershell
Set-Location 'C:\Users\Alex11\Documents\Trabajo de Investigacion'
$env:CHURN_API_KEY_FILE = (Resolve-Path '.local/security/api-key.txt').Path
$env:CHURN_TLS_CERT_FILE = (Resolve-Path '.local/security/cert.pem').Path
$env:CHURN_TLS_KEY_FILE = (Resolve-Path '.local/security/key.pem').Path
& .\backend\start.ps1 -Port 8443
```

En otra terminal, desde Krayin, procesar hasta cien solicitudes pendientes:

```powershell
Set-Location 'C:\xampp\htdocs\KrayinCRM\laravel-crm-2.2'
& C:\xampp\php\php.exe artisan churn:work --limit=100
```

El comando termina al alcanzar el límite o agotar pendientes. Ejecutarlo de nuevo para continuar. `--limit` admite 1–1000. Un lote completo puede tardar: el cliente HTTPS conserva su presupuesto máximo de 50 segundos por cliente y sus reintentos acotados. Se procesa secuencialmente para esta demostración; el comando no tiene que permanecer instalado como servicio.

Para enviar desde consola, alternativa al panel:

```powershell
& C:\xampp\php\php.exe artisan churn:queue --customer=AA-10315 --as-of=2018-06-30
& C:\xampp\php\php.exe artisan churn:work --limit=1
```

Para solicitar explícitamente todos los clientes del dataset:

```powershell
& C:\xampp\php\php.exe artisan churn:queue --all --as-of=2018-06-30
& C:\xampp\php\php.exe artisan churn:work --limit=1000
```

La consola es una operación del administrador local con acceso a la instalación; `--all` no representa el ámbito de un usuario del panel. Hay 793 clientes en el dataset; 431 son elegibles en el corte inicial. Los restantes se marcan no elegibles sin llamar a la API. En la verificación real de esta tarea **solo se procesó AA-10315**; las pruebas de lotes restantes fueron transaccionales.

El comando antiguo `churn:predict-customer --save` sigue disponible para diagnóstico, pero no participa en el progreso ni en la exclusión de esta cola. Para operar lotes y evitar cálculos paralelos, utilizar exclusivamente `churn:queue` y `churn:work`; no ejecutar a la vez comandos de diagnóstico sobre los mismos clientes.

## Estados, progreso y recuperación

| Estado | Significado |
|---|---|
| Pendiente | Solicitud persistida, todavía no procesada. |
| En proceso | El procesador tomó el cliente y está comprobando datos o consultando HTTPS. |
| Completado | Resultado guardado o resultado idéntico reutilizado. |
| Error | Fallo de servicio, configuración, persistencia, conflicto o interrupción. Puede existir una predicción válida anterior. |
| No elegible | No hay una compra dentro de los 180 días previos al corte. No equivale a riesgo bajo ni 0 %. |

El resumen considera la **última solicitud por cliente** para el corte y versión configurados, dentro del ámbito de lectura. Porcentaje terminado = (completados + errores + no elegibles) / solicitudes representadas. Alcanzar 100 % significa que terminaron, no que todas tuvieron éxito; los contadores separan cada resultado. No es el porcentaje de los 793 clientes con predicción.

`churn_work_items` guarda cliente, corte, versión solicitada, autor (ID de usuario o nulo para consola), estado, resultado y tiempos UTC. Las solicitudes anteriores permanecen para auditoría aunque el resumen solo muestre la última por cliente. Las ejecuciones HTTPS están enlazadas por `churn_prediction_runs.work_item_id`.

Al enviar, una transacción bloquea los clientes en orden y reutiliza cualquier tarea pendiente/en proceso de la misma identidad. El procesador obtiene un bloqueo consultivo de MariaDB por base de datos: un segundo procesador termina con `worker_busy`. No se mantienen transacciones ni bloqueos de filas durante HTTPS. Esta implementación depende de MariaDB/MySQL; no se presenta como portable a SQLite/PostgreSQL.

Si el proceso se interrumpe, la conexión libera el bloqueo. Al iniciar de nuevo `churn:work`, las tareas que quedaron en proceso se cierran como error `worker_interrupted`, junto con sus intentos incompletos. No se repiten automáticamente; después de revisar el servicio, solicitar otra actualización. Los pendientes restantes continúan. Si un resultado llegó a guardarse antes de la interrupción, se conserva y el reenvío podrá reutilizarlo.

El comando devuelve JSON con cantidades `completed`, `error` y `skipped`; código de salida 1 si hubo errores, incluyendo interrupciones recuperadas, o si otro procesador está activo. Un fallo 401 requiere revisar la clave configurada; no se soluciona repitiendo continuamente. Los detalles de respuesta y secretos no se muestran en el panel. Los códigos técnicos seguros se conservan en la base para diagnóstico.

Las solicitudes autorizadas se ejecutan con el ámbito capturado al enviarlas; la consulta posterior aplica el ámbito de lectura vigente. No se añadieron cron, campañas, descuentos ni contactos automáticos.

## Evidencia y reproducción

- `evidencias_crm044/navegador.json`: navegador real, duplicados, CSRF 419, procesamiento HTTPS, escritorio/móvil y cero errores JavaScript.
- `evidencias_crm044/https_concurrencia.json`: tres envíos simultáneos, una sola tarea, fallo 401, recuperación y predicción original conservada.
- `evidencias_crm044/regresion_modulo.txt`: 114 casos, 316 aserciones sin fallos; `pruebas_acceso.txt`: 11 casos, 32 aserciones sin fallos. Avisos preexistentes de PDO bajo PHP 8.5.
- `evidencias_crm044/contactos_despues.json`: contactos y atributos intactos.
- `evidencias_crm043/paridad_variables.json`: siete variables consistentes para 431 clientes.

Los scripts locales `.local/verify_crm044_browser.py`, `.local/verify_crm044_browser.cjs` y `.local/verify_crm044_https.py` preparan servidores temporales y cierran sus procesos. La prueba del navegador crea y elimina una cuenta de QA. No publicar los archivos temporales de credenciales. La evidencia real deja intentos de prueba auditables sobre AA-10315; no elimina esa trazabilidad.

Estado final comprobado: una predicción válida original, ninguna solicitud pendiente/en proceso y última solicitud completada. API y servidor web temporales detenidos. Para usar la actualización más adelante, iniciar los servicios y ejecutar el procesador como se indica arriba.
