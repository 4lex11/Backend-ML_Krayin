# Guía de capturas para la investigación

Actualización MEJ-08: la tesis tiene 28 páginas; integración en páginas 12–13, discusión en 14, conclusiones en 15, recomendaciones en 16 y referencias en 17. El [índice final](INDICE_EVIDENCIAS_FINAL.md) reúne las evidencias vigentes. Las secciones siguientes conservan el detalle por etapa.

Fecha: 28 de octubre de 2026. Las rutas son relativas a la carpeta del proyecto. Abrir los archivos indicados y capturar la sección concreta, incluyendo título, periodo y versión cuando existan. Preferir insertar las figuras PNG originales en Word para conservar legibilidad; una captura de pantalla no mejora su resolución.

| N.º | Archivo y sección | Qué mostrar y qué demuestra | Ubicación sugerida en el DOCX |
|---|---|---|---|
| 1 | `docs/dataset_kaggle_metadata.json` | Nombre, autor, versión y licencia declarada; fuente identificada, no prueba de igualdad binaria remota | Metodología 2.2 |
| 2 | `ML/artifacts/churn180-v1/metadata.json`, `quality` y `splits` | 9.800 líneas, 4.922 pedidos, 793 clientes y tamaños por corte | Metodología 2.3 |
| 3 | `ML/protocol.json` | Ventanas 365/180, fechas de corte y criterio de selección | Metodología 2.4 |
| 4 | `ML/artifacts/churn180-v1/figures/01_periodos_y_clases.png` | Distribución por periodo; diferenciar clientes de observaciones cliente-corte | Metodología 2.4 |
| 5 | `ML/artifacts/churn180-v1/figures/02_comparacion_validacion.png` | Comparación entre candidatos en validación, no en test | Resultados 4.1 |
| 6 | `ML/artifacts/churn180-v1/selection_before_test.json` | Modelo y umbrales seleccionados antes de computar test en el pipeline | Resultados 4.1 |
| 7 | `ML/artifacts/churn180-v1/figures/03_matriz_confusion_test.png` | 101 TP, 328 FP, 0 FN y 2 TN al umbral medio | Resultados 4.2 |
| 8 | `ML/artifacts/churn180-v1/figures/04_curvas_test.png` | Discriminación y referencia; evitar afirmar utilidad solo por el recall | Resultados 4.2 |
| 9 | `docs/evidencias_ml06/calibration.png` | Antes/después de calibración, por periodo; no son intervalos de confianza | Resultados 4.3 |
| 10 | `docs/evidencias_ml06/thresholds.csv`, filtrar `period=test` | Umbrales y número de clientes marcados; precisión indefinida sin seleccionados | Resultados 4.3 |
| 11 | `docs/evidencias_ml06/capacity_scenarios.csv`, test, capacidad 0,2 y costo FN 2 | Comparación por cupo; costos abstractos, no dinero | Resultados 4.4 |
| 12 | `docs/CONTRATO_KRAYIN.md`, endpoints y variables | Contrato de siete variables y trazabilidad de resultados | Implementación 3.2 |
| 13 | `docs/evidencias_api/01_solicitud.json` y `02_respuesta.json` | Ejemplo de estructura con ID DEMO; la respuesta es evidencia histórica del contrato, no del transporte actual | Implementación 3.2 |
| 14 | `docs/evidencias_api/07_seguridad_https.json` | HTTPS real, TLS y rechazos de credenciales/origen | Resultados 4.5 |
| 15 | `docs/evidencias_api/09_carga_https.json` | Concurrencia, tamaño de lote, 200/503, p95 y comprobación de cuerpos lentos | Resultados 4.5 |
| 16 | `docs/evidencias_api/08_despliegue_reversion.json` | Recuperación, actualización, reversión y limpieza de tarea temporal | Resultados 4.5 |
| 17 | `docs/evidencias_ml06/pruebas.txt`, bloque final | 98 pruebas y cobertura 95,14 %; calidad del código, no del modelo | Resultados 4.5 |
| 18 | `docs/PLAN_VALIDACION_CRM.md`, fases V-03/V-04 | Plan futuro; no confundir con un piloto ya ejecutado | Discusión 5.3 |

## Pies de figura propuestos

Paginación comprobada del DOCX actualizado: metodología y tamaños en páginas 4–6, implementación en 7, comparación de candidatos en 8, test y matriz en 9, calibración y escenarios en 10, resultados técnicos en 11, discusión en 12 y conclusiones en 13. Referencias y trazabilidad están en la página 14. Esta paginación corresponde a la exportación revisada en Word; puede variar con cambios posteriores de formato.

- Comparación de average precision en validación temporal de diciembre de 2017. Fuente: ejecución reproducible del proyecto.
- Matriz de confusión del test temporal de junio de 2018 al umbral medio de 0,311218. N = 431 clientes. Fuente: artefacto churn180-v1.
- Calibración retrospectiva antes y después de ajuste sigmoide. Intervalos de probabilidad de amplitud 0,10; los puntos no representan intervalos de confianza. Fuente: análisis ML-06.
- Respuestas y latencia en carga HTTPS local. Indicar tamaño de lote y concurrencia; incluir rechazos 503 además de éxitos. Fuente: ensayo API-06.

## Precauciones de interpretación

No capturar credenciales, `api-key.txt`, `key.pem`, variables de entorno con secretos, nombres de clientes o extractos de compras innecesarios. Para tablas de escenarios utilizar resultados agregados. El CSV fuente contiene nombres: su disponibilidad pública no demuestra que estén anonimizados.

No usar métricas antiguas de los notebooks históricos para explicar el artefacto vigente. Los archivos `03_verificacion.json`, `04_benchmark.json` y `06_http_real.json` son evidencias anteriores; para seguridad y carga actuales utilizar 07/08/09. Los conteos 64, 94 y 96 corresponden a etapas previas de pruebas; la regresión posterior a ML-06 tiene 98.

La figura de importancia de variables `06_importancia_variables.png` puede añadirse como análisis descriptivo del estimador. No prueba causalidad ni que una variable permita retener clientes. No presentar el umbral alto como una garantía de mayor precisión observada.

La selección de capturas debe servir a la argumentación: no es necesario insertar las 18 en el cuerpo principal. El DOCX actualizado incorpora las tablas y figuras centrales; el resto puede respaldar anexos o la exposición oral. Los archivos de renderización usados para revisar el DOCX son materiales internos de control de formato.


## Integración Krayin — CRM-04.3 y CRM-04.4 (29/10/2026)

| Archivo | Qué permite mostrar |
|---|---|
| `docs/evidencias_crm043/detalle_escritorio.png` | Predicción histórica, fecha de corte/cálculo, siete variables, huella e historial. |
| `docs/evidencias_crm043/detalle_movil.png` | Detalle y tablas con desplazamiento en pantalla pequeña. |
| `docs/evidencias_crm043/paridad_variables.json` | Cotejo de siete variables para los 431 clientes del test. |
| `docs/evidencias_crm044/solicitud_pendiente.png` | Solicitud manual persistida esperando procesador. |
| `docs/evidencias_crm044/solicitud_completada.png` | Progreso tras procesar la solicitud por HTTPS. |
| `docs/evidencias_crm044/https_concurrencia.json` | Envíos simultáneos sin duplicación, 401 y recuperación conservando el resultado. |
| `docs/evidencias_crm044/regresion_modulo.txt` y `pruebas_acceso.txt` | 125 casos / 348 aserciones sin fallos; avisos PDO visibles. |

Pie sugerido: «Módulo local de consulta y procesamiento de predicciones retrospectivas de abandono a 180 días. Demostración técnica con Superstore Sales; no acredita eficacia comercial del modelo». El panel está en inglés por la configuración del CRM; existen traducciones del módulo en español. El pie fijo nativo puede cruzar una sección en una captura de página completa: para la exposición también puede capturarse cada sección visible al desplazarse.


## Sugerencias orientativas — CRM-05.1

Capturar `docs/evidencias_crm051/sugerencia_listado.png` y `sugerencia_detalle.png`. La segunda muestra el motivo de la regla y la revisión humana requerida. Pie sugerido: «Orientación mediante reglas explícitas con prioridad de calidad del historial; no representa una acción aprendida por ML ni eficacia comercial validada». Pruebas y reglas completas en `docs/CRM051_SUGERENCIAS.md`.


## Seguimiento manual — CRM-05.2

Usar `docs/evidencias_crm052/seguimiento_historial.png` para responsable, estados, nota, autor y fecha; `seguimiento_movil.png` muestra la adaptación móvil. Pie sugerido: «Registro manual de revisión de un contexto histórico de predicción. Datos de QA para demostrar trazabilidad; no implica contacto con clientes ni evidencia de retención». Las notas fotografiadas se eliminaron tras la verificación. Detalles y resultados en `docs/CRM052_SEGUIMIENTO.md`.


## Validación integral — CRM-06.1

En `docs/evidencias_crm061/`, usar `aceptacion_https.json` para el lote (793 solicitudes, 431 completadas, 362 no elegibles) y los errores 401/422/503/caída/recuperación. Capturar `solicitud_completada.png` y `revision_integral.png` para el recorrido de interfaz. El lote se revirtió y sus 431 resultados no quedaron almacenados: no confundir el ensayo con el conteo final del panel. `regresion_php.txt`, `permisos.txt` y `regresion_python.txt` contienen la regresión final; `estado_final.json` demuestra limpieza y conservación de contactos. Acta: `docs/CRM061_VALIDACION_INTEGRAL.md`.

## Cierre de la mejora experimental (MEJ-08)

La ronda está cerrada: MEJ-01 a MEJ-06 y MEJ-08 completadas; MEJ-07 no aplica porque el candidato incumplió dos criterios de Brier. Se conserva v1 y la integración existente. La tesis recoge la conclusión en la página 15, el diseño y la calibración en la 18 y la comparación E1 y decisión en la 19. Las recomendaciones y referencias conservan las páginas 16 y 17. Archivos concretos para capturas y límites: [acta de cierre](MEJ08_CIERRE_DOCUMENTAL.md).


Tablas de síntesis añadidas: página 20, tabla B1 (incorporaciones MEJ-01 a MEJ-08); página 21, tablas B2 (v1 frente al candidato), B3 (criterios incumplidos) y B4 (balance de aceptación). Las páginas 18–19 conservan el detalle experimental. Respaldo anterior: `docs/historico/InvestigacionTesis2026_antes_tablas_MEJ.docx`.


Ampliación de variables y mediciones: páginas 22–23, diccionario de las siete variables originales y once temporales; página 24, hiperparámetros; página 25, definición de métricas; página 26, comparación E1 y cupos; página 27, precisión temporal e intervalos bootstrap; página 28, calibración. Gráficas: `docs/evidencias_mej08/graficas/`. Se conserva `docs/historico/InvestigacionTesis2026_antes_mediciones_MEJ.docx`.
