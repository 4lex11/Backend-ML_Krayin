# CRM-05.1 — sugerencias orientativas

Completada el 29/10/2026. El listado incorpora una columna de sugerencias y el detalle muestra la orientación, la regla que la justifica y su carácter experimental. Se usan textos en español e inglés según el idioma de Krayin.

## Reglas y prioridad

Se evalúan en el siguiente orden; se muestra la primera aplicable. Las advertencias de datos tienen prioridad sobre las sugerencias según riesgo.

| Condición | Orientación |
|---|---|
| Sin ventas en la ventana histórica | Comprobar cobertura; no asignar probabilidad ni decidir acciones comerciales. |
| No elegible: sin compra en los últimos 180 días del corte | Revisar historial sin asignar una nueva probabilidad. |
| Elegible sin predicción del corte/versión exactos | Revisar datos y servicio; solicitar predicción antes de evaluar acciones. |
| Categoría no admitida, modelo no experimental o indicador de acción automática incompatible | Revisar integridad/configuración del resultado. |
| Huella de entrada no verificada | Resolver la discrepancia con los datos disponibles; no derivar una sugerencia por riesgo. |
| Historial limitado informado por la API | Comprobar cobertura antes de valorar seguimiento. |
| Categoría Alto | Revisar historial reciente y valorar seguimiento personalizado, previa evaluación del responsable. |
| Categoría Medio | Revisar posibles cambios en frecuencia y valorar seguimiento solo si el contexto lo justifica. No se afirma haber detectado una tendencia. |
| Categoría Bajo | Revisión habitual y reevaluación en el próximo corte disponible; no garantiza recompra. |

Las tres últimas reglas exigen elegibilidad, huella coincidente y ausencia de cobertura limitada. Usan exclusivamente la categoría guardada que devolvió la API: no comparan probabilidades ni duplican los umbrales del modelo en PHP/Blade. `automatic_action_allowed=false` se respeta; un registro incompatible no genera una sugerencia por riesgo.

Son reglas explícitas de demostración, no tratamientos aprendidos por ML ni recomendaciones comerciales validadas. No proponen descuentos, costos o beneficios que el dataset no permite fundamentar. No crean tareas de contacto, envían mensajes ni ejecutan campañas. El registro de revisión humana se completó posteriormente en [CRM-05.2](CRM052_SEGUIMIENTO.md).

## Implementación

`packages/Webkul/Churn/src/Services/RetentionAdvice.php` centraliza las reglas y devuelve una clave traducible. `PanelRepository` entrega la misma orientación al listado y al detalle. Para cada página se consulta el historial en un único lote, más la cobertura global; no se realiza una consulta por cliente ni se llama a Python para renderizar la pantalla. Las consultas respetan los permisos existentes y excluyen compras posteriores al corte.

Las vistas `index.blade.php` y `show.blade.php` presentan textos escapados y las traducciones de `Resources/lang/{es,en}/app.php`. No se modificaron modelos ML, predicciones persistidas, tablas ni rutas. La sugerencia se deriva al consultar, no constituye una acción ni un resultado histórico almacenado.

## Verificación

- `evidencias_crm051/pruebas.txt`: **44 casos, 152 aserciones, sin fallos**. Incluye 15 casos nuevos y regresión de detalle/listado. Persisten avisos de deprecación PDO preexistentes; no se midió cobertura.
- Se probaron prioridades, las tres categorías, huellas discrepantes, versión ausente, alcance vacío y traducciones. Los cambios de datos de prueba fueron transaccionales y se revirtieron.
- `evidencias_crm051/navegador.json`: Edge con cuenta temporal de solo lectura. La sugerencia de AA-10315 coincide en listado y detalle, explica `limited_history`, no muestra controles de actualización y no produce errores JavaScript ni desbordamiento móvil.
- En el registro real AA-10315 se muestra **revisar cobertura limitada**, aunque su categoría es Medio. Es el comportamiento previsto de prioridad de calidad.
- No se enviaron solicitudes a la API ni se procesaron nuevas predicciones para esta tarea. La cuenta temporal se eliminó y el servidor web de prueba se cerró.

## Capturas

1. `docs/evidencias_crm051/sugerencia_listado.png`: columna de orientación junto a la predicción.
2. `docs/evidencias_crm051/sugerencia_detalle.png`: sugerencia, regla que la justifica y advertencia de revisión humana.
3. `docs/evidencias_crm051/sugerencia_movil.png`: detalle en pantalla pequeña.

El pie fijo de Krayin aparece en la captura completa a la altura del viewport. La interfaz fotografiada está en inglés por la configuración actual del CRM; las traducciones españolas están incluidas y verificadas.

Los archivos anteriores se conservan en `.local/crm051-backup`. CRM-05.2 se completó posteriormente; quedan CRM-06.1 y CRM-06.2.
