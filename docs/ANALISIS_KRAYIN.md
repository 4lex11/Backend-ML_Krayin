# Diagnóstico de Krayin para integrar ML

> Actualización posterior: CRM-01 ya se completó. MySQL fue iniciado, el esquema verificado y el dataset importado sin duplicados. Véase [CRM01_DATOS.md](CRM01_DATOS.md). Las limitaciones de conexión descritas abajo corresponden al diagnóstico inicial, no al estado actual.

Fecha: 28 de octubre de 2026. Revisión del código local y comprobaciones de consola; no se modificaron el código del CRM ni sus datos. No se ejecutaron importadores, migraciones ni campañas.

## Instalación identificada

- Raíz real: `C:\xampp\htdocs\KrayinCRM\laravel-crm-2.2` (contiene `artisan` y `composer.json`).
- Krayin declara **2.2.6** en `packages/Webkul/Core/src/Core.php:21`; el nombre de la carpeta no identifica la versión exacta.
- Laravel **v12.66.0** en `composer.lock`; PHP CLI de XAMPP **8.5.11**. Composer requiere PHP `^8.3` y simula plataforma `8.3.30`: la versión CLI observada no acredita la de Apache ni compatibilidad completa de todas las dependencias.
- Dependencias `vendor` presentes, incluido Guzzle. Configuración observada: entorno local, depuración activa y cola `sync`.
- Existe un módulo propio `packages/Webkul/Churn/src`, registrado en el autoload de Composer y en `bootstrap/providers.php`. Contiene cinco archivos: menú, controlador, proveedor, rutas y vista.
- `git status` indica que esta carpeta no es un repositorio Git. No hay una base local de Git con la que atribuir cambios o comparar con una distribución original.

## Hallazgos prioritarios

| Prioridad | Hallazgo comprobado en código | Consecuencia / corrección necesaria |
|---|---|---|
| Alta | `Churn/src/Routes/admin-routes.php:6` usa `user_session`; el proveedor de Admin registra `user` y no se encontró registro de `user_session` en el código de aplicación revisado. | Adaptar la ruta a la autenticación de esta instalación. Una ruta declarada no demuestra que pueda abrirse correctamente. |
| Alta | `Churn/src/Resources/views/index.blade.php:1` extiende `admin::layouts.master`, ausente en las vistas de Admin. Los contactos actuales usan `<x-admin::layouts>`. | Migrar la vista al componente existente; la plantilla antigua es incompatible con esta instalación. |
| Alta | El controlador une atributos mediante IDs fijos **64 y 65**, sin restringir `entity_type`. | Resolver atributos por código y tipo o usar tablas propias con relaciones y migraciones. Evitar depender de IDs de otra instalación. |
| Alta | La vista aplica umbrales **0,40 / 0,70**, recomienda un descuento del 20 % y convierte `null` a `float` al mostrar probabilidad. | Consumir la categoría de la API vigente, mostrar «Sin predicción» para ausencias y retirar ofertas sin validación comercial. El modelo es experimental; mantener revisión humana. |
| Alta | El módulo solo consulta atributos existentes. No contiene cliente HTTP, jobs, persistencia versionada ni pruebas específicas. | La presencia de un dashboard no equivale a una conexión con la API Python actual. Implementar y comprobar el flujo completo. |
| Media | El módulo no incluye configuración ACL; la ruta fija `admin/churn` en vez de usar el prefijo configurable. | Añadir permiso de lectura/actualización y respetar `config('app.admin_path')`. El middleware `user` por sí solo no sustituye el registro de permisos del módulo. |
| Media | La consulta usa `get()` para todos los contactos y ordena una probabilidad guardada como texto. | Usar paginación y tipo numérico validado para la probabilidad. No se comprobó el formato de los valores existentes. |
| Media | Cola configurada como `sync`. | Para procesamiento asíncrono se necesitarán una conexión de cola y un worker, o un comando programado con límites explícitos. No existe aún esa operación en Churn. |

Los umbrales vigentes del modelo son aproximadamente **0,311218 / 0,377295**; no deben duplicarse manualmente en Blade. La respuesta de `backend/schemas.py` incluye `categoria_riesgo`, `model_version`, `as_of`, `predicted_at`, `limited_history`, `model_status=experimental` y `automatic_action_allowed=false`.

## Historial de compras y alcance con el dataset

Los modelos revisados de Krayin representan personas, oportunidades, cotizaciones y productos. `Person` tiene relación con oportunidades; `Quote` tiene persona e ítems. Esto no prueba que una cotización o una oportunidad ganada sea una compra efectivamente realizada. Los campos estándar de `Product` revisados no proporcionan por sí solos las categorías y subcategorías del dataset.

Como el alcance acordado usa únicamente Superstore Sales, el origen para la demostración debe seguir siendo ese dataset. Propuesta de mapeo, pendiente de implementar:

| Dataset | Contrato / persistencia propuesta |
|---|---|
| Customer ID | `customer_id` externo estable y relación explícita con `persons.id` |
| Row ID | `line_id` de la línea de venta |
| Order ID | `order_id` |
| Order Date | `order_date`, convertido de día/mes/año a ISO |
| Sales | `sales`, importe de la línea |
| Category / Sub-Category | `category` / `subcategory` |

Para evitar diferencias entre PHP y entrenamiento, enviar líneas históricas a `/v1/predict/transactions`, donde Python calcula las siete variables, o consumir una exportación vigente para una demostración de visualización claramente identificada. Esta última alternativa no prueba integración HTTP.

Mantener una fecha de corte histórica explícita. No usar automáticamente la fecha actual sobre compras de 2015–2018: los clientes dejarían de cumplir la elegibilidad de compra en los últimos 180 días. Enviar solo el historial que corresponda al corte; las compras posteriores quedan fuera de las variables. Respetar el límite de 5.000 líneas por solicitud y comprobar cobertura del historial.

Los notebooks de `integraciones/krayin` son históricos: insertan contactos sin deduplicación, dependen de IDs 61–65 y emplean datos de contacto de demostración. No deben ejecutarse como mecanismo definitivo ni tratar esos contactos como evidencia comercial real.

## Comprobaciones y límites

- Se revisaron instrucciones `AGENTS.md`, Composer, proveedores, módulo Churn, modelos Contact/Lead/Quote/Product, middleware de Admin, migraciones de atributos y contrato Python.
- Se ejecutó `php -v` correctamente.
- Se intentaron `php artisan route:list --path=churn -vv` y `php artisan migrate:status --no-ansi`. El primer intento encontró restricciones del entorno; el segundo, con acceso autorizado al equipo, confirmó **conexión rechazada a MySQL en 127.0.0.1:3306**. No se debe atribuir este resultado a credenciales incorrectas: ni siquiera se estableció la conexión.
- No se confirmó el contenido actual de la base, conteos de contactos, existencia de los atributos 64/65, migraciones aplicadas ni funcionamiento de la página en navegador.
- `AGENTS.md` referencia `.github/skills/crm-package-development/SKILL.md`, pero ese archivo no está presente y la búsqueda de `SKILL.md` fuera de dependencias no encontró una copia. Para esta revisión se siguieron las convenciones explícitas del propio `AGENTS.md` y los módulos existentes. Antes de implementar conviene restaurar esa documentación del proyecto.
- No se ejecutó una batería funcional: esta entrega es un diagnóstico, no una certificación de funcionamiento.

## Orden recomendado para la siguiente etapa

1. **CRM-01:** habilitar/verificar MySQL y confirmar esquema, contactos y atributos mediante consultas de lectura. Completar el mapeo con Customer ID y la fecha de corte del dataset. Estado: análisis de código realizado; base sin verificar.
2. **CRM-02:** cliente HTTP Laravel para HTTPS, credencial externa, certificado verificado, tiempos de espera y reintentos limitados según API-06. Nunca desactivar la verificación TLS.
3. **CRM-03:** migraciones y repositorios para identificación externa y predicciones trazables; unicidad por cliente, corte y versión, historial y actualización idempotente. No reutilizar ciegamente los atributos históricos.
4. **CRM-04:** corregir rutas, permisos y plantilla del módulo; mostrar riesgo recibido, corte, versión y condición experimental. Añadir paginación, filtros, estado sin predicción y ejecución por comando/cola.
5. **CRM-06:** probar dataset → PHP → API → almacenamiento → interfaz, incluyendo indisponibilidad, 401/422/503, reintentos y repetición sin duplicados; conservar evidencia para capturas.
6. **CRM-05:** el registro y evaluación de intervenciones reales sigue fuera del alcance del dataset. Si se desarrolla una demostración de registro, etiquetarla como simulación; no enviar campañas ni afirmar mejora de retención.

La etapa académica anterior permanece cerrada. Este diagnóstico identifica trabajo de integración separado; no altera el modelo ni justifica reentrenarlo con el test ya observado.
