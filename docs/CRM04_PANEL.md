# CRM-04 — panel de predicciones

Estado: **CRM-04.1 a CRM-04.4 completadas**, 29 de octubre de 2026. Las secciones 04.1/04.2 conservan la evidencia de su cierre del 28/10; las novedades de detalle y actualización se describen al final.

## CRM-04.1: módulo integrado al panel

- Ruta GET `/{prefijo-administrativo}/churn`, con nombre `admin.churn.index`; respeta `config('app.admin_path')`. En la configuración actual corresponde a `/admin/churn` dentro de la URL base de Krayin.
- Middleware nativo `web`, `admin_locale` y `user`: sesión, usuario activo y comprobación ACL. Se reemplazó el middleware inexistente `user_session`.
- Menú condicionado por el permiso `churn`. La URL directa también está protegida: ocultar el menú no es el único control.
- Permiso separado `churn.update` registrado para asignación posterior. No habilita por sí solo lectura ni hay todavía una ruta de actualización; su ejecución corresponde a 04.4.
- Layout `<x-admin::layouts>`, compatible con esta instalación, en lugar de la plantilla antigua ausente.
- Traducciones del módulo en español e inglés. La interfaz respeta el idioma del CRM; en la instalación comprobada el menú aparece como **Churn predictions**, y en español como **Predicciones de abandono**. No se modificó el idioma global del usuario.
- Consultas limitadas por propietario conforme al ámbito global, de grupo o individual de Krayin. Un grupo vacío devuelve cero resultados; no se interpreta como acceso global. Los contactos sin propietario solo aparecen en el ámbito global.

Las pruebas aisladas de acceso cubren 11 casos y 31 aserciones sin fallos. Se ejecutan con PHPUnit directamente porque el menú del núcleo usa una caché estática por proceso y el lanzador Pest de esta instalación no inicializa correctamente sus subprocesos. No se modificó el núcleo para resolver esa particularidad de pruebas. La configuración PDO existente produce dos avisos de deprecación bajo PHP 8.5.

Evidencias: `docs/evidencias_crm041/pruebas_acceso.txt`, `rutas.txt` y la regresión final `docs/evidencias_crm042/pruebas_acceso_regresion.txt`.

## CRM-04.2: resumen y listado

El panel muestra una fila por cliente del dataset para **el corte exacto seleccionado y la versión configurada del modelo**. No mezcla cortes ni multiplica filas por versiones históricas.

Incluye:

- Indicadores de clientes encontrados, riesgo alto/medio/bajo y clientes sin predicción. Todos se calculan con los mismos filtros y permisos de la tabla, sobre el total de resultados, no únicamente sobre la página visible.
- Tabla con nombre del contacto, ID externo, probabilidad, categoría, corte, fecha del cálculo en UTC y estado. Se conservan los nombres existentes; algunos contactos históricos tienen el propio ID como nombre.
- Búsqueda por nombre o ID, con caracteres de búsqueda tratados como texto, no como comodines SQL.
- Filtros por riesgo, fecha de corte, con/sin predicción, última ejecución fallida y ejecución en proceso.
- Orden numérico de probabilidad ascendente/descendente y orden por cliente, con desempate estable por ID externo. Las probabilidades ausentes quedan al final.
- Paginación de 20 clientes; los enlaces conservan los filtros y el formulario vuelve a la primera página al aplicarlos.
- Validación de filtros y fechas dentro de la cobertura del dataset. Corte inicial: 30/06/2018; no se usa la fecha actual sobre datos históricos.
- Ausencias representadas con «Sin predicción» y «—», nunca como 0 % ni como riesgo bajo.
- Si la última ejecución falló pero existe una predicción válida, se muestra esa probabilidad y el mensaje de conservación del resultado anterior. La hora del cálculo no se sustituye por la del intento fallido.
- Advertencia de modelo experimental, historial limitado y contexto histórico; no se proponen descuentos ni se ejecutan campañas.
- Ajustes de contenido para móvil, tabla con desplazamiento horizontal y etiquetas de formulario. Se conserva el layout y el pie fijo nativos de Krayin.

La columna de última ejecución consulta el último intento para cliente y corte; `churn_prediction_runs` todavía no almacena una versión solicitada. La predicción sí se restringe a la versión configurada. Si en el futuro se operan varias versiones simultáneamente, habrá que ampliar ese registro antes de interpretar los intentos como específicos de una versión.

## Estado al cerrar CRM-04.2 (28/10/2026)

Hay **793 clientes mapeados y una predicción guardada** para el corte y versión iniciales. Los otros 792 aparecen sin predicción: no se ejecutó una predicción masiva para rellenar la pantalla. La ejecución fallida que se muestra para AA-10315 procede de la prueba de autenticación de CRM-03; su resultado válido, **34,01 % / Medio**, permanece disponible.

## Pruebas y revisión visual

- `docs/evidencias_crm042/pruebas_listado.txt`: 18 casos, 44 aserciones y ningún fallo. Incluyen filtros/conteos, orden numérico, permisos, cortes/versiones, ausencia de duplicados, paginación y entradas inválidas. Pest los marca con avisos de deprecación de PDO de la configuración existente.
- Regresión de acceso: 11 casos y 31 aserciones sin fallos. En total, **29 casos y 75 aserciones** para acceso y listado; no se ejecutó toda la batería original de Krayin.
- `docs/evidencias_crm042/navegador.json`: prueba real en Edge sin ventana visible, a 1440×1000 y 390×844. Verificó total 793, filtro con predicción 1, búsqueda con 34,01 %, 20 filas en página 2, ausencia de desbordamiento de página móvil y cero errores JavaScript de página.
- Se revisaron visualmente las capturas; se corrigió codificación de traducciones y se esperó a que terminara la transición responsive antes de capturar móvil.
- El usuario y rol temporales usados para iniciar sesión se eliminaron. El servidor PHP de prueba se detuvo. No se cambió la cuenta habitual ni su contraseña.
- `contactos_despues.json`: las huellas de personas y atributos coinciden con CRM-03. Las pruebas de datos emplearon transacciones reversibles; no se modificaron las ventas ni las predicciones vigentes para preparar la vista.
- Pint aprobó los archivos PHP revisados. No se midió cobertura.

## Archivos para capturas

1. `docs/evidencias_crm042/panel_escritorio.png`: menú, resumen y listado general.
2. `docs/evidencias_crm042/prediccion_guardada.png`: filtro con predicción, probabilidad y conservación del resultado ante fallo.
3. `docs/evidencias_crm042/panel_movil.png`: controles y tabla adaptados a pantalla pequeña. El pie fijo de Krayin aparece a la altura del borde del viewport en la captura de página completa.
4. `docs/evidencias_crm042/navegador.json`: resultados de las comprobaciones de navegador.

## Archivos y comandos

En `packages/Webkul/Churn/src`: `Config/acl.php`, `Config/menu.php`, `Routes/admin-routes.php`, `Http/Controllers/ChurnController.php`, contrato/repositorio `PanelRepository`, proveedor, vista `Resources/views/index.blade.php` y traducciones `Resources/lang/{es,en}/app.php`. Las consultas no dependen de los atributos antiguos 64 y 65.

Desde la raíz de Krayin, con MySQL activo:

```powershell
C:\xampp\php\php.exe vendor\bin\phpunit tests/Feature/ChurnPanelAccessTest.php --display-deprecations
C:\xampp\php\php.exe artisan test --compact tests/Feature/ChurnListingTest.php --display-deprecations
C:\xampp\php\php.exe artisan route:list --path=churn -vv
```

Se conservaron los archivos anteriores en `.local/crm041-backup` y `.local/crm042-backup` del proyecto de investigación. El script local de comprobación visual está en `.local/verify_crm042_browser.cjs`; utiliza un usuario temporal y un servidor de prueba en el puerto 8765, que debe estar libre.

## CRM-04.3: detalle del cliente

Completada el 29/10/2026. El nombre de cada cliente enlaza a `/{prefijo}/churn/customers/{id}`. El detalle exige permiso `churn` y comprueba el propietario antes de consultar resultados. Un ID fuera del ámbito no permite leer sus datos.

La vista muestra probabilidad, categoría, fecha de corte, versión, horizonte, fecha de cálculo UTC, cobertura limitada y mensaje `accion_sugerida` guardado por la API. Ese mensaje exige revisión humana; las reglas orientativas más específicas siguen en CRM-05.1. La pantalla distingue el contexto retrospectivo del estado actual del cliente.

Las siete variables se reconstruyen con la ventana `(corte − 365 días, corte]`: recencia, pedidos únicos, suma de ventas, media por línea, desviación muestral por línea, categorías y subcategorías. No se utilizan ventas futuras. Una única línea produce desviación 0; sin ventas se muestra ausencia de historial. Recencia mayor de 180 días indica no elegibilidad. Los importes conservan las unidades del dataset, sin asumir una moneda del CRM.

Se coteja el SHA-256 del payload reconstruido con la huella almacenada. Solo cuando coincide se indica que los datos corresponden a la predicción guardada. Una discrepancia se presenta como reconstrucción no verificada; no se afirma que exista una copia inmutable de las ventas. La inferencia continúa en Python: las variables PHP son para visualización y comprobación de elegibilidad.

El historial pagina diez resultados, ordenados por corte y cálculo, con enlaces a la versión exacta. Los diez últimos intentos del corte aparecen aparte; un fallo conserva el resultado válido. El botón de actualización solo aparece al consultar la versión actualmente configurada y con permiso de actualización.

`evidencias_crm043/paridad_variables.json` compara las siete variables con el test temporal para **431 clientes**. Diferencia absoluta máxima: **9,094947 × 10⁻¹³**, inferior a la tolerancia de 10⁻⁸. Esto confirma consistencia del cálculo, no calidad predictiva.

Capturas revisadas: [detalle de escritorio](evidencias_crm043/detalle_escritorio.png) y [detalle móvil](evidencias_crm043/detalle_movil.png). El pie fijo del layout nativo aparece a la altura del viewport en la captura completa; las tablas tienen desplazamiento horizontal propio y la página no desborda.

## CRM-04.4: actualización y procesamiento

Completada el 29/10/2026. La acción individual y el lote de clientes autorizados generan solicitudes persistentes. El comando `churn:work` las procesa fuera de la petición web. El panel muestra pendientes, en proceso, completados, errores, no elegibles, porcentaje terminado y las últimas solicitudes por cliente.

La protección incluye permisos de lectura y actualización, ámbito por propietario, CSRF, límite de solicitudes y bloqueo frente a duplicados. El POST usa el verificador CSRF nativo mediante un adaptador del módulo que conserva HTTP 419; el manejador HTML del núcleo, en modo no debug, devolvía HTTP 200 para esa excepción. No se modificó el núcleo.

Consultar [CRM044_ACTUALIZACIONES.md](CRM044_ACTUALIZACIONES.md) para comandos, límites, recuperación y criterio de progreso. Capturas: [solicitud pendiente](evidencias_crm044/solicitud_pendiente.png) y [solicitud completada](evidencias_crm044/solicitud_completada.png).

## Verificación final de CRM-04

- **125 casos, 348 aserciones, sin fallos**, sumando la regresión del módulo (114 casos / 316 aserciones) y acceso aislado (11 / 32). Hay avisos por `PDO::MYSQL_ATTR_SSL_CA` en la configuración preexistente bajo PHP 8.5. No se midió cobertura ni se ejecutaron todos los módulos de Krayin.
- Edge real: detalle 34,01 %, huella coincidente, móvil sin desbordamiento, CSRF sin token rechazado con 419, doble envío sin duplicación, procesamiento HTTPS y progreso completado; cero errores JavaScript de página. Evidencia: `evidencias_crm044/navegador.json`.
- Tres comandos de envío simultáneos añadieron **una** tarea y reutilizaron la pendiente en las otras dos solicitudes. Un intento HTTPS con clave de prueba incorrecta produjo 401; el siguiente envío con configuración correcta terminó y reutilizó la predicción original. Probabilidad y fecha originales intactas. Evidencia: `evidencias_crm044/https_concurrencia.json`.
- Pruebas reversibles de worker ocupado, interrupción, límites, no elegibilidad, cambios de versión, permisos y conflicto de resultados. Las tablas de pruebas se restauran por transacciones.
- 793 contactos y 3.965 atributos con las mismas huellas que antes. No se ejecutó un lote masivo real: continúa una predicción guardada y 792 clientes sin predicción para el corte inicial. Al terminar no quedan solicitudes pendientes/en proceso. La última solicitud de AA-10315 está completada.
- Usuarios/roles temporales eliminados; servidores web/API de comprobación cerrados. No se instaló un proceso permanente. Archivos anteriores conservados en `.local/crm043-backup` y `.local/crm044-backup`.

## Pendiente

CRM-05.1 completada posteriormente: [reglas de sugerencias](CRM051_SUGERENCIAS.md). CRM-05.2 también completada: [seguimiento manual](CRM052_SEGUIMIENTO.md). CRM-06.1 y CRM-06.2 se completaron posteriormente: [aceptación integral](CRM061_VALIDACION_INTEGRAL.md) y [guía final](GUIA_FINAL_CRM.md). Los resultados anteriores corresponden a la etapa CRM-04.

