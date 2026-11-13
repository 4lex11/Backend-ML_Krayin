# CRM-03 — predicciones e historial persistentes

Estado: **completado**, 28 de octubre de 2026. Se amplió el módulo Churn de Krayin con almacenamiento versionado, historial de resultados y ejecuciones. No se implementaron todavía el panel ni campañas.

## Datos guardados

La migración `2026_10_28_000002_create_churn_prediction_tables.php` crea:

- `churn_predictions`: relación con el cliente externo y su contacto mediante `churn_dataset_customers`, corte, versión del modelo/esquema, horizonte, probabilidad numérica, categoría, historial limitado, estado experimental, permiso de acción automática, fecha de cálculo en UTC, respuesta y hash de la entrada.
- `churn_prediction_runs`: una fila por ejecución iniciada para un cliente conocido, con corte, hash, inicio, fin, estado, predicción vinculada o código de error, HTTP e intentos si están disponibles en el fallo.

No se copian nombres, correos, teléfonos ni credenciales a las nuevas tablas. Se conserva la respuesta validada del servicio; el hash de entrada permite detectar cambios sin duplicar allí el historial de ventas.

La clave única es **cliente + fecha de corte + versión del modelo**. Las predicciones son inmutables en el repositorio:

1. Una primera respuesta válida se guarda y la ejecución termina como `succeeded`.
2. La repetición con la misma entrada y contenido de respuesta reutiliza el registro y termina como `reused`. Se ignora para esa comparación la nueva fecha de cálculo; se conserva la fecha del resultado original.
3. Cambiar entrada o resultado bajo la misma clave produce `prediction_conflict`; no sobrescribe el registro anterior.
4. Otro corte o versión genera una predicción independiente. El historial se consulta por corte descendente, no solo por fecha de inserción, y se pagina en grupos de 50.
5. Un fallo del servicio se registra como `failed`; no elimina ni convierte en cero la última predicción válida.

El repositorio inicia el registro de ejecución antes de llamar a la API. La solicitud HTTPS se realiza fuera de la transacción de escritura. Al guardar, bloquea la fila del cliente y confirma en una transacción tanto la predicción como el estado final de la ejecución. La clave única refuerza la protección frente a duplicados. No se realizó una prueba de carga concurrente en esta tarea.

## Archivos de Krayin

Dentro de `C:\xampp\htdocs\KrayinCRM\laravel-crm-2.2`:

- `packages/Webkul/Churn/src/Contracts/PredictionRepository.php`.
- `packages/Webkul/Churn/src/Repositories/PredictionRepository.php`.
- `packages/Webkul/Churn/src/Models/Prediction.php` y `PredictionRun.php`.
- Migración y registro en `ChurnServiceProvider.php`.
- `PredictDatasetCustomer.php`: incorpora `--save`, conservando la consulta sin escritura por defecto.
- `tests/Feature/ChurnPredictionTest.php` y adaptación de los fixtures transaccionales de CRM-01 a las nuevas claves foráneas.
- `CHANGELOG.md` actualizado.

## Uso

Con MySQL y la API HTTPS activos, desde la raíz de Krayin:

```powershell
# Consulta sin guardar, comportamiento de CRM-02 conservado:
C:\xampp\php\php.exe artisan churn:predict-customer AA-10315 --as-of=2018-06-30

# Consulta y registra resultado / ejecución:
C:\xampp\php\php.exe artisan churn:predict-customer AA-10315 --as-of=2018-06-30 --save
```

Con `--save`, el resultado incluye `run_id`, `prediction_id`, `created` y `prediction`. Si se reutiliza, devuelve la predicción almacenada con su fecha original. Los errores de corte o cliente desconocido se rechazan antes de crear una ejecución porque todavía no existe una identidad válida a la cual asociarla.

El código `persistence_or_execution_error` evita guardar mensajes inesperados con información sensible. Si la propia base está inaccesible, no puede garantizarse el registro del fallo en esa misma base. Una interrupción abrupta del proceso puede dejar una ejecución `running`; su recuperación y supervisión corresponden a CRM-04.4. No se ejecuta ninguna acción comercial.

## Comprobaciones reales y capturas

Archivo principal: **`docs/evidencias_crm03/persistencia_https.json`**.

- Se consultó AA-10315 para 30/06/2018 mediante Laravel → API HTTPS real.
- Se guardó probabilidad **0,3400690869680104**, categoría **Medio**, versión **churn180-v1**, estado experimental y `automatic_action_allowed=false`.
- Una segunda consulta reutilizó el mismo `prediction_id`; quedó una sola fila de predicción.
- Una tercera consulta con clave inválida registró HTTP 401, un intento y estado `failed`; conservó la predicción previa.
- Los tres estados observados fueron `succeeded`, `reused` y `failed`. El fallo es una prueba deliberada, no una campaña fallida.
- `estado_final.json` confirma que esos registros persistieron después de las pruebas de regresión.
- `contactos_despues.json` conserva las mismas huellas de los contactos y atributos de CRM-01.

`docs/evidencias_crm03/pruebas.txt`: **67 casos, 183 aserciones, ningún fallo**. Pest muestra 51 aprobados y 16 con aviso de deprecación por la configuración existente `PDO::MYSQL_ATTR_SSL_CA` bajo PHP 8.5. Incluye pruebas de CRM-01/02 y nueve casos nuevos de persistencia: trazabilidad/UTC, reutilización, preservación ante fallo, conflictos, versiones/cortes, errores sanitizados y respuestas incompatibles. No se ejecutó toda la batería original de Krayin ni se calculó cobertura.

Para repetir la aceptación desde el proyecto de investigación:

```powershell
.\.venv-clean\Scripts\python.exe -m scripts.verify_crm03
```

Requiere MySQL activo y la configuración de seguridad local. Cada ejecución añade registros de prueba de ejecución, pero reutiliza la predicción existente. El script levanta una API temporal, la cierra al finalizar y elimina la clave inválida temporal. `scripts/audit_crm03.php` realiza las consultas de comprobación.

Respaldo previo local: `.local/crm03-backup/database-before.sql`, acompañado de los archivos reemplazados. No se restauró la base ni se borraron los contactos.

## Continuación

CRM-04: adaptar el módulo del panel para mostrar el listado, detalle e historial y permitir actualización controlada. La presencia de resultados guardados no implica que ya estén visibles en la pantalla antigua. CRM-05 incorporará sugerencias y revisión manual.
