# Lista de tareas: integración de ML en Krayin

Actualizada: 29 de octubre de 2026. CRM-01 a CRM-06 completados para el alcance local acordado. Plan basado en `ANALISIS_KRAYIN.md` y en la solicitud de un módulo del panel con predicciones y sugerencias. Se conservan los IDs CRM-01 a CRM-06; las subdivisiones permiten implementar y verificar por partes. Evidencias en [CRM01_DATOS.md](CRM01_DATOS.md), [CRM02_CONEXION_API.md](CRM02_CONEXION_API.md), [CRM03_PERSISTENCIA.md](CRM03_PERSISTENCIA.md) y [CRM04_PANEL.md](CRM04_PANEL.md).

## Alcance

Extender el módulo `Webkul/Churn` existente para una demostración local con el dataset Superstore Sales. Mantener Python como servicio independiente y Krayin como interfaz y capa de gestión. La etapa ML/API/documentación previa permanece cerrada; esta lista corresponde a una nueva etapa de integración.

El modelo es experimental y no demostró utilidad predictiva suficiente. Las sugerencias serán reglas orientativas visibles para revisión humana, no acciones aprendidas por el modelo ni recomendaciones comerciales validadas. No se enviarán correos, ofertas ni campañas. La evaluación de impacto comercial sigue siendo trabajo futuro.

## Tareas y criterios de cierre

| ID | Tarea | Criterio de cierre | Estado |
|---|---|---|---|
| CRM-01.1 | Verificar instalación y base de datos | MySQL accesible; versión, esquema, migraciones, contactos y atributos existentes comprobados con consultas de lectura. Revisar configuración de Apache/PHP. | Completada: MariaDB accesible, migraciones verificadas y configuración revisada. Panel comprobado en navegador durante CRM-04. |
| CRM-01.2 | Preparar datos de demostración | Importación por la aplicación con mapeo estable Customer ID → contacto, líneas identificadas por Row ID y sin duplicados al repetir. Conservar fechas, pedidos, ventas y categorías del dataset. Separar explícitamente cualquier contacto ficticio. | Completada: 793 contactos reutilizados, 9.800 líneas y 4.922 pedidos; repetición sin duplicados y cotejo sin diferencias. |
| CRM-02 | Conectar PHP con la API Python | Cliente HTTP configurable, clave fuera del código, TLS verificado, tiempos de espera y reintentos acotados; validar contrato de respuesta y manejar errores. Usar cálculo compartido de variables en Python. | Completada: consumidor transaccional, comando histórico, 51 pruebas y aceptación HTTPS real con predicción coincidente. |
| CRM-03 | Guardar predicciones e historial | Migraciones, modelos y repositorios propios. Guardar cliente externo, probabilidad numérica, categoría, corte, horizonte, versión, fecha de predicción y cobertura limitada. Repetir cliente/corte/versión no duplica resultados. Mantener registro separado de ejecuciones y fallos. | Completada: tablas y repositorio, --save, historial, reutilización sin duplicados y conservación ante fallos comprobadas con HTTPS real; 67 casos de regresión sin fallos. |
| CRM-04.1 | Adaptar módulo, menú y permisos | Entrada «Predicciones de abandono» en el panel; corregir middleware, prefijo y layout. Permisos para consultar y actualizar; acceso directo por URL también protegido y visibilidad de clientes acorde al rol. | Completada: layout y rutas nativas, ACL de lectura y actualización separadas, 11 pruebas de acceso. Actualizaciones implementadas en 04.4. |
| CRM-04.2 | Crear resumen y listado | Indicadores por categoría y sin predicción, tabla paginada, búsqueda por cliente/ID, filtros por riesgo, corte y estado; orden numérico de probabilidad. Contadores y tabla usan la misma población y filtros. | Completada: 18 pruebas del listado y revisión real de escritorio/móvil; capturas en evidencias_crm042. |
| CRM-04.3 | Crear detalle del cliente | Mostrar predicción, datos históricos usados, corte, versión, horizonte de 180 días, historial de resultados y sugerencia. Diferenciar fecha del cálculo y fecha de corte; no presentar datos históricos como situación actual. | Completada: detalle autorizado, siete variables cotejadas con 431 clientes del test, huella de entrada, historial paginado y mensaje guardado de la API; capturas en evidencias_crm043. |
| CRM-04.4 | Ejecutar y actualizar predicciones | Acción manual protegida y comando/cola para lotes; estado pendiente/en proceso/completado/error, progreso y resumen. Evitar ejecuciones simultáneas duplicadas; errores o respuestas antiguas no sobrescriben silenciosamente resultados vigentes. | Completada: POST con permisos/CSRF, cola persistente, comandos de lote/procesamiento, progreso, exclusión concurrente y recuperación; evidencia HTTPS y navegador en evidencias_crm044. |
| CRM-05.1 | Mostrar sugerencias orientativas | Reglas explícitas según categoría y calidad de datos; texto que explique su propósito y necesidad de revisión. Usar categoría devuelta por la API, sin umbrales duplicados en Blade. Respetar `automatic_action_allowed=false`. | Completada: reglas compartidas en listado/detalle, prioridad de calidad y elegibilidad, explicación y traducciones; 44 pruebas de sugerencias y regresión, revisión visual. |
| CRM-05.2 | Registrar seguimiento manual de demostración | Permitir registrar revisión, responsable, nota y estado (pendiente/revisado/descartado), con autor y fecha. No implica contactar clientes ni acredita retención. | Completada: responsable, nota y estado por cliente/corte/versión; permiso independiente, historial con autor/UTC, validación y conflictos; pruebas y capturas en evidencias_crm052. |
| CRM-06.1 | Probar integración y permisos | Flujo dataset → PHP → HTTPS → persistencia → panel; comprobar roles, duplicados, predicciones ausentes, historial limitado, errores 401/422/503, caída y recuperación del servicio. No enviar comunicaciones reales durante las pruebas. | Completada: 161 casos PHP y 98 Python; lote HTTPS de 793 clientes con rollback, 431 resultados coincidentes; 401/422/503, caída/recuperación y navegador verificados. Evidencia en CRM061_VALIDACION_INTEGRAL.md. |
| CRM-06.2 | Documentar y generar evidencia | Guía de instalación y uso, comandos/worker, configuración sin secretos, resultados de pruebas y archivos/pantallas para capturas. Actualizar investigación con evidencia técnica efectivamente obtenida. | Completada: guía final de instalación/operación, índice de capturas, tesis de 17 páginas revisadas y auditoría de coherencia; véase GUIA_FINAL_CRM.md. |

Orden: CRM-01 → CRM-02/CRM-03 → CRM-04 → CRM-05 → CRM-06. La programación automática puede prepararse después de verificar la ejecución manual y la idempotencia. No se requiere reentrenar el modelo para estas tareas.

## Contenido del módulo

### Pantalla principal

- Encabezado «Predicciones de abandono» y aviso breve de uso experimental.
- Fecha de corte histórica seleccionada y fecha de última ejecución; estado de conexión con la API sin exponer detalles internos.
- Tarjetas: clientes dentro de la población mostrada, riesgo alto/medio/bajo y sin predicción. No mezclar conteos de clientes con conteos de predicciones históricas.
- Tabla: cliente e ID externo, probabilidad estimada, categoría, fecha de corte, última actualización, sugerencia breve y enlace «Ver detalle».
- Búsqueda, filtros y paginación; botón «Actualizar predicciones» solo para usuarios autorizados.
- Estados diferenciados: sin datos, no elegible, sin predicción, en proceso y error. Una ausencia o fallo nunca se representa como 0 % de riesgo. Conservar el último resultado válido con su fecha cuando falle una actualización.

### Detalle

- Resumen de cliente, probabilidad, categoría, horizonte, corte y advertencia experimental.
- Variables del periodo histórico realmente utilizado, incluyendo recencia, frecuencia e importes; explicar que la media monetaria es por línea de venta.
- Versión y fecha del cálculo, cobertura limitada cuando corresponda e historial ordenado por corte.
- Sugerencia orientativa y registro de revisión manual. Un cambio entre cortes no demuestra efecto de una intervención.

## Ejemplos de sugerencias a implementar

Estas reglas son una propuesta funcional para la demostración, no resultados del entrenamiento ni efectos comprobados. La interfaz no debe mostrarlas como garantías de abandono o fidelización.

| Situación | Sugerencia visible |
|---|---|
| Riesgo alto | «Revisar el historial reciente y valorar una tarea de seguimiento personalizada, previa evaluación del responsable.» |
| Riesgo medio | «Revisar cambios en frecuencia de compra y valorar seguimiento si el contexto lo justifica.» |
| Riesgo bajo | «Mantener seguimiento habitual y revisar en el próximo corte; un riesgo bajo no garantiza recompra.» |
| Historial limitado | «Interpretar con cautela: comprobar la cobertura del historial antes de decidir.» |
| Sin predicción o datos inválidos | «Revisar datos y disponibilidad del servicio antes de evaluar acciones.» |
| No elegible para este modelo | «El cliente no cumple las condiciones de este modelo; revisar su historial sin asignar una probabilidad de abandono.» |

Las advertencias de calidad tienen prioridad sobre la sugerencia por riesgo. No proponer descuentos concretos: el dataset no proporciona márgenes, costos ni evidencia del efecto de las ofertas. No hace falta añadir otro modelo de IA para generar estos textos.

## Condiciones del dataset y operación

Usar una fecha de corte histórica acordada, historial de 365 días y elegibilidad de compra en los últimos 180 días. No usar la fecha actual sobre el dataset antiguo. No incluir compras posteriores al corte en las variables. Las predicciones son demostraciones retrospectivas, aunque se calculen hoy.

El procesamiento debe respetar los límites de la API, conservar trazabilidad y realizarse fuera de la petición que renderiza la tabla. CRM-04.4 utiliza su propia cola persistente en MariaDB con `churn:work`; no depende de `QUEUE_CONNECTION=sync` ni del worker genérico de Laravel. El cron/Programador de tareas debe reutilizar un comando de aplicación probado; no avanzar el corte histórico automáticamente como si llegasen ventas nuevas.

La documentación `AGENTS.md` de Krayin exige paquetes, migraciones y convenciones propias. Se debe resolver la documentación local de skills ausente antes de implementar y preservar los cambios existentes. La lista no autoriza ni incluye sustitución masiva de contactos, campañas reales ni despliegue público.

## Fuera de esta etapa

- Medir mejora real de fidelización, rentabilidad o efecto de campañas: requiere datos e intervenciones que este dataset no contiene.
- Integrar una fuente nueva de ventas reales.
- Despliegue en un servidor externo y operación de producción.

CRM-05 se concreta aquí como sugerencias y seguimiento de demostración; la parte original de intervenciones comerciales y resultados reales permanece fuera del alcance y no se marcará como validada al terminar el panel.
