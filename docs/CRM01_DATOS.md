# CRM-01 — instalación y datos de demostración

Estado: **completado**, 28 de octubre de 2026. Alcance: preparar los datos para la futura conexión de Krayin con la API, sin ejecutar predicciones nuevas ni campañas.

## Resultado verificado

| Comprobación | Resultado |
|---|---|
| Instalación | `C:\xampp\htdocs\KrayinCRM\laravel-crm-2.2`, Krayin 2.2.6, Laravel 12.66.0 |
| Base local | MariaDB 10.4.32, MySQL de XAMPP iniciado para esta operación |
| PHP CLI | 8.5.11; Apache está configurado para cargar `C:/xampp/php/php8apache2_4.dll` y su configuración PHP desde `C:/xampp/php` |
| Contactos reutilizados | 793, vinculados por el atributo de código `customer_id` y tipo `persons` |
| Contactos nuevos | 0 |
| Líneas de ventas | 9.800, cada una con Row ID único |
| Pedidos | 4.922 |
| Ventas acumuladas | 2.261.536,782700, en la unidad monetaria del dataset |
| Fechas de ventas | 03/01/2015–30/12/2018 |
| Repetición de la importación | 0 líneas nuevas; 9.800 sin cambios; 793 mapeos existentes |
| Cotejo fila por fila | 0 diferencias y 0 filas faltantes |
| Preservación | Los 793 contactos y sus 3.965 valores de atributos conservan exactamente las mismas huellas SHA-256 antes y después |
| Fecha de corte de demostración | 30/06/2018; 431 clientes cumplen la condición de compra en los últimos 180 días |

La revisión de Apache fue de configuración. No se certificó aquí el funcionamiento de la pantalla de Churn en navegador: sus correcciones siguen en CRM-04. La carga funciona mediante Laravel CLI.

## Implementación

El módulo `packages/Webkul/Churn/src` incorpora:

- `Console/ImportSuperstore.php`: comando `churn:import-superstore`, con modo `--dry-run` y responsable explícito `--owner`.
- `Services/SuperstoreCsv.php`: validación de columnas, fechas día/mes/año, identificadores, duplicados, coherencia de pedidos/clientes y decimales.
- `Contracts/DatasetRepository.php` y `Repositories/DatasetRepository.php`: servicio registrado en el contenedor, transacción y bloqueo del registro de origen para serializar importaciones.
- `Models/DatasetCustomer.php` y `Models/SalesLine.php`: persistencia de mapeos y ventas.
- Migración `2026_10_28_000001_create_churn_dataset_tables.php`, aplicada como lote 2.

Tablas nuevas: `churn_datasets`, `churn_dataset_customers` y `churn_sales_lines`. Las claves únicas impiden repetir clientes externos o líneas dentro de la fuente. No se borran ni sobrescriben contactos existentes. Las coincidencias ambiguas y las líneas incompatibles cancelan la transacción.

El importador exige el SHA-256 del CSV usado en la investigación:

`dbb0f167b27ccf02d7ff8cb0446a9abc6dbc3522e83cf9daa6939801acfdd196`

Los atributos históricos se localizan por código y tipo, no por el número 61. Los contactos conservados pertenecen al prototipo de demostración: sus correos/teléfonos no se consideran información acreditada por Kaggle. `churn_datasets.is_demo=1` identifica el origen de demostración. Para nuevos contactos, el importador utiliza una marca DEMO y correo con dominio `.invalid`; en esta carga no hizo falta crear ninguno.

Se almacena el historial completo para posteriores consultas por corte. La siguiente etapa debe seleccionar exclusivamente `(corte - 365 días, corte]` para las variables y respetar la elegibilidad del modelo. No debe utilizar ventas posteriores al corte ni sustituir el corte histórico por la fecha de hoy.

## Ejecución reproducible

Desde la raíz de Krayin, con MySQL iniciado y el CSV extraído del ZIP original:

```powershell
C:\xampp\php\php.exe artisan churn:import-superstore "RUTA\train.csv" --owner=1 --dry-run
C:\xampp\php\php.exe artisan churn:import-superstore "RUTA\train.csv" --owner=1
```

El usuario activo 1 fue comprobado en esta instalación; en otra instalación debe elegirse un responsable válido. El CSV utilizado localmente está en `.local/crm01-stage/train.csv` dentro del proyecto de investigación y puede volver a extraerse de `train.csv.zip`.

Respaldo previo: `.local/crm01-backup/database-before.sql`, junto con la copia anterior del proveedor del módulo. El respaldo contiene datos de la base y se conserva localmente; no es material para capturas públicas. No se ejecutó una restauración destructiva como parte de esta tarea.

## Pruebas y evidencias

- `docs/evidencias_crm01/pruebas.txt`: 18 pruebas ejecutadas, 34 aserciones y ningún fallo. Pest presenta 11 como aprobadas y 7 con avisos de deprecación de `PDO::MYSQL_ATTR_SSL_CA` en la configuración existente bajo PHP 8.5. No se modificó esa configuración global para silenciar el aviso.
- Las pruebas cubren fechas ambiguas/inválidas, importes inválidos, duplicados, inconsistencias, simulación sin escritura, reutilización, repetición, rollback, responsable inválido, IDs ambiguos y rechazo de archivos no reconocidos. Las pruebas de base emplean transacciones con reversión; no se usó `RefreshDatabase` sobre la base local.
- `simulacion.json`, `importacion.json` y `repeticion.json`: resultados reales de los comandos.
- `verificacion.json`: cotejo de cada línea con el CSV, conteos, versión de base, hash, corte y migración aplicada; `passed=true`.
- `contactos_antes.json` y `contactos_despues.json`: conteos y huellas iguales para personas y atributos.
- `scripts/verify_crm01.php`: verificación de lectura reutilizable, ejecutada con la raíz de Krayin y la ruta al CSV como argumentos.

Para capturas de CRM-01, usar `importacion.json`, `repeticion.json` y `verificacion.json`. Demuestran preparación e integridad de datos, no predicción nueva ni mejora de fidelización.

La guía de paquete que referencia el `AGENTS.md` local no estaba incluida; se intentó recuperarla del repositorio público, que devolvió 404. Se aplicaron las convenciones explícitas del `AGENTS.md` y los patrones locales, junto con la guía Laravel disponible. No se inventó una copia de esa skill.

## Siguiente tarea

**CRM-02:** conectar Laravel con la API HTTPS. La persistencia de nuevas predicciones, el panel y las sugerencias siguen pendientes en CRM-03 a CRM-05; CRM-01 no sustituye esas tareas.
