# CRM-06.1 — validación integral de la integración

Fecha: **29 de octubre de 2026**. Resultado: **aceptada técnicamente para la demostración local con el dataset Superstore Sales**. CRM-05.2 también quedó cerrada, con formato, capturas e historial manual comprobados. CRM-06.2 quedó completada posteriormente: guía consolidada, índice de capturas y documento de investigación actualizado.

## Alcance y versiones

Se validó el recorrido dataset importado → PHP → API Python por HTTPS → persistencia → panel → sugerencia → revisión manual. No se enviaron mensajes, ofertas ni campañas. No se reentrenó el modelo ni se cambió su categoría experimental.

- Dataset: 9.800 líneas, 4.922 pedidos y 793 clientes; SHA-256 `dbb0f167b27ccf02d7ff8cb0446a9abc6dbc3522e83cf9daa6939801acfdd196`.
- Corte: 2018-06-30; historial de 365 días; elegibilidad por compra en los últimos 180 días.
- Modelo `churn180-v1`, SHA-256 `ad1eb6205eb40ec9cf53e3a429d7a2c3b16bc045e56dcf7f063eb3355243ffdd`.
- PHP 8.5.11, Python 3.14.6, MariaDB 10.4.32; versión Laravel y huellas de los 40 archivos del módulo en `evidencias_crm061/versiones.json`.

## Matriz de aceptación

| Caso | Evidencia y resultado | Estado |
|---|---|---|
| A01. Conciliar origen e importación | `conciliacion_dataset.json`: cero líneas distintas o ausentes; 793 enlaces únicos y sumatoria 2.261.536,782700. | Aprobado |
| A02. Inferencia individual desde PHP con ventas históricas | `aceptacion_https.json`, valid: AA-10315, 34,00690869680104 %, misma identidad, reutilización del resultado original. | Aprobado |
| A03. Procesar lote completo | 793 solicitudes, 431 completadas, 362 no elegibles, cero errores; cada resultado cotejado por ID con el test temporal. | Aprobado |
| A04. Consistencia de persistencia, listado y detalle | Durante el ensayo: 431 guardadas, 362 sin predicción; 92 Alto, 337 Medio, 2 Bajo. Detalle con huella verificada y sugerencia de historial limitado. | Aprobado |
| A05. Credencial inválida — 401 | HTTPS real, un intento, ejecución fallida visible para el repositorio del panel, predicción anterior intacta. | Aprobado |
| A06. Entrada inválida — 422 | Importe negativo enviado únicamente en el payload de prueba, sin alterar ventas; HTTPS real, un intento y resultado anterior intacto. | Aprobado |
| A07. Saturación — 503 | Cuatro conexiones HTTPS ocupan temporalmente los cupos reales con cuerpos incompletos; PHP recibe 503 y agota tres intentos acotados. | Aprobado |
| A08. Caída y recuperación | API temporal detenida: tres intentos y fallo sin sobrescritura. API reiniciada: respuesta correcta y resultado original reutilizado. | Aprobado |
| A09. Roles y ámbito | Regresión de permisos: sesión, rol de lectura, actualización y revisión independientes, usuario inactivo, ámbito individual/grupo/global y grupo vacío. Pruebas específicas del seguimiento y actualizaciones en la suite completa. | Aprobado |
| A10. Duplicados, conflictos e historial | Suite PHP verifica identidad cliente/corte/versión, respuesta fuera de orden, conflictos, worker ocupado, límites e interrupciones. Navegador repite un envío y comprueba una sola tarea pendiente. Evidencia complementaria de tres envíos concurrentes en CRM-04.4. | Aprobado |
| A11. Ausencias, elegibilidad y cobertura | 362 no elegibles no reciben probabilidad; 95 de las 431 predicciones informan historial limitado. Pruebas de entradas vacías, fechas futuras, versión ausente y prioridad de advertencias. | Aprobado |
| A12. Flujo de interfaz completo | `navegador.json`: sesión real, detalle, POST, worker HTTPS, progreso completado, sugerencia `limited`, registro manual `reviewed`, escritorio/móvil y cero errores JavaScript. | Aprobado |
| A13. Seguridad de formularios y notas | CSRF sin token → 419 en navegador; revisión antigua rechazada; notas escapadas y expresiones Vue literales; autoría del servidor y permisos separados. Pruebas de CRM-05.2 y regresión actual. | Aprobado |
| A14. Contrato, TLS y límites de API | 98 pruebas Python y 40 casos del cliente PHP dentro de su suite: validación estricta, NaN, duplicados, límites, TLS, errores y reintentos. HTTPS de esta aceptación verifica certificado y nombre; pruebas negativas de TLS reales previas en CRM-02. | Aprobado |
| A15. Conservación y limpieza | Rollback comprobado en cada caso del driver; cuenta y nota QA del navegador eliminadas. Auditoría final: 793 contactos, 3.965 atributos con huellas originales, una predicción y ninguna tarea pendiente/en proceso. | Aprobado |

## Resultados cuantitativos

- **PHP/Krayin: 161 casos, 477 aserciones, ningún fallo.** La ejecución principal contiene 150 casos / 445 aserciones; acceso aislado añade 11 / 32. Los avisos PDO preexistentes hacen que Pest marque algunos casos como deprecated.
- **Python: 98 casos aprobados**, con un aviso de deprecación de Starlette/TestClient. No se midió cobertura en esta ejecución.
- Lote real: **431 resultados comparados**, diferencia absoluta máxima de probabilidad **4,9960 × 10⁻¹⁵**, inferior a la tolerancia de 10⁻¹⁰. Los IDs se compararon de forma explícita, no por posición de las filas.
- Duración observada del ensayo del lote: **42,2 segundos**, incluyendo inicialización del driver. Es un ensayo funcional secuencial en un único equipo, dentro de una transacción de prueba; **no es un benchmark de producción ni una garantía de tiempo**.
- En el navegador: AA-10315 mantiene 34,01 % mostrado; doble envío genera una sola tarea, worker termina correctamente, sugerencia e historial manual visibles.

## Cómo se evitó modificar la demostración

`scripts/probe_crm061.php` abre una transacción de prueba y revierte todas las escrituras antes de devolver el resultado. Verifica cantidades y predicción original antes y después. El lote usa los servicios y repositorios reales, incluida la API HTTPS; los 430 resultados nuevos que completaban la población elegible no se dejaron guardados.

Esa transacción exterior se utiliza **solo en el ensayo** para restaurar el estado. En operación normal `churn:work` no mantiene una transacción abierta durante HTTP. Por esa diferencia, el ensayo no mide el comportamiento de bloqueo ni el rendimiento de una carga concurrente de producción. El bloqueo de workers y la exclusión concurrente se verifican por pruebas específicas.

La prueba del navegador sí realiza una solicitud normal y confirma su persistencia; añade una ejecución de reutilización auditada sobre AA-10315. La cuenta y nota de revisión QA se eliminan al finalizar, pero se conserva la trazabilidad operativa de la solicitud. La predicción original y su fecha no se sustituyen.

Estado final: **una predicción guardada**, 792 clientes sin predicción en el panel ordinario del corte inicial, cero tareas pendientes/en proceso, cero cuentas/notas CRM061 QA y cero revisiones manuales de demostración persistentes. Los conteos de 431/362 corresponden al ensayo transaccional, no a la pantalla después del rollback.

## Incidencia del entorno

El primer intento de regresión encontró MariaDB detenido y produjo 60 fallos de conexión. Se conservó su salida en `intento_mysql_detenido.txt`, se inició MariaDB y se repitió la suite: 150 casos sin fallos; acceso aislado también terminó sin fallos. No se atribuyó el problema a los modelos ni se modificaron datos para hacer pasar las pruebas. La primera ejecución Python no entregaba salida en el entorno restringido; se detuvieron únicamente sus procesos identificados y se repitió con diagnóstico, obteniendo los 98 casos aprobados.

Los servidores temporales de API y web se cerraron. MariaDB se inició para las pruebas; no se instaló un servicio permanente nuevo, cron ni tarea programada para Krayin. Para operar después se requiere que la base y la API estén disponibles según la guía de CRM-04.4.

## Archivos de evidencia y reproducción

Todos los resultados de esta aceptación están en `docs/evidencias_crm061/`:

- `conciliacion_dataset.json`, `versiones.json`, `estado_final.json` y `formato.json`.
- `regresion_php.txt`, `permisos.txt` y `regresion_python.txt`.
- `aceptacion_https.json` y `navegador.json`.
- `detalle_escritorio.png`, `detalle_movil.png`, `solicitud_pendiente.png`, `solicitud_completada.png` y `revision_integral.png`.

Desde el proyecto de investigación, con MariaDB disponible y sin tareas pendientes en la cola:

```powershell
& .\.venv-clean\Scripts\python.exe -m scripts.verify_crm061
```

El script inicia API temporal con certificado y clave existentes, realiza los casos, termina los procesos y elimina su clave de prueba inválida. No imprime secretos. `scripts/audit_crm061.php` permite una auditoría final de lectura. El recorrido de navegador se reproduce con `.local/verify_crm061_browser.py` y usa Edge, una cuenta temporal y el puerto local 8765 libre. No ejecutar estos ensayos mientras otros operadores estén enviando trabajos o modificando datos.

## Decisión y límites

CRM-06.1 se considera completada para el alcance local y retrospectivo acordado. Esta aceptación no demuestra que el modelo prediga mejor que los comparadores ni que las sugerencias mejoren la recompra. No se hicieron campañas, seguimiento prospectivo ni medición de satisfacción o rentabilidad. El modelo conserva `automatic_action_allowed=false`.

V-01/V-02 del plan general se aplican aquí con el alcance de dataset fijo y demostración local. Sus extensiones a fuentes de ventas reales y operación productiva, junto con V-03/V-04 prospectivas y comerciales, permanecen fuera del alcance actual. CRM-06.2 también está completada: [guía final](GUIA_FINAL_CRM.md), [índice de evidencias](INDICE_EVIDENCIAS_FINAL.md) y tesis actualizada de 17 páginas.
