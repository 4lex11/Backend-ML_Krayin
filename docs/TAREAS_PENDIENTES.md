# Estado final de tareas — dataset y prototipo local

Actualizado el 29/10/2026. La etapa ML/API/documentación y CRM-01 a CRM-06 están completadas en el alcance acordado. No quedan tareas pendientes de esta lista para la demostración local con Superstore Sales.

Plan y criterios: [PLAN_INTEGRACION_KRAYIN.md](PLAN_INTEGRACION_KRAYIN.md). Operación: [GUIA_FINAL_CRM.md](GUIA_FINAL_CRM.md). Evidencias: [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md). El catálogo académico siguiente conserva los criterios y resultados de la etapa anterior; la integración local fue completada posteriormente. Producción externa y validación comercial permanecen fuera de alcance.

> **Nueva etapa MEJ (29/10/2026):** se inició la mejora experimental del modelo con el mismo dataset. MEJ-01 a MEJ-06 están completadas; MEJ-07 no aplica en esta ronda porque el candidato no superó los criterios. MEJ-08 está completada; no quedan tareas pendientes de esta ronda dentro del alcance acordado. El protocolo, límites y criterios de promoción están en [PLAN_MEJORAS_ML.md](PLAN_MEJORAS_ML.md), [MEJ01_PROTOCOLO.md](MEJ01_PROTOCOLO.md) y [MEJ02_VARIABLES_TEMPORALES.md](MEJ02_VARIABLES_TEMPORALES.md). El resultado final conserva v1 y la integración actual. Véase [MEJ08_CIERRE_DOCUMENTAL.md](MEJ08_CIERRE_DOCUMENTAL.md).

## Alcance acordado

- Evaluación retrospectiva de abandono a 180 días, con 365 días de historial y siete variables.
- Modelos, calibración, umbrales y escenarios hipotéticos de capacidad/costos basados en el dataset disponible.
- API y despliegue local verificados; documentación y evidencia para la investigación.
- No se exige demostrar mejora real de fidelización para cerrar esta etapa: se debe explicar que no fue medida. Los resultados negativos o limitados del modelo se conservan y discuten.
- No se requieren nuevos entrenamientos para presentar el resultado actual. No se debe ajustar reiteradamente contra el test ya observado para obtener métricas más favorables.

## Estado actual

| Grupo | Estado dentro del alcance actual |
|---|---|
| ML-01 a ML-09 | Completadas técnicamente en alcance académico. ML-06 incluye calibración y escenarios; sus costos y cupos son supuestos, no datos comerciales. |
| API-01 a API-08 | Completadas para el perfil local documentado. |
| Plan de validación | Elaborado en `docs/PLAN_VALIDACION_CRM.md`; su ejecución prospectiva/comercial es trabajo futuro. |
| Documentación general | DOC-01 a DOC-04 completadas. DOCX actualizado y revisado, ahora de 44 páginas tras MEJ-08; evidencia en `docs/REVISION_COHERENCIA.json`. |

## Documentación completada para el cierre actual

| ID documental | Tarea | Criterio de cierre |
|---|---|---|
| DOC-01 — completada | Crear `docs/CONCLUSIONES_DETALLADAS.md` | Unificar metodología, resultados ML, calibración, backend, limitaciones y conclusiones. Separar capacidad predictiva, funcionamiento técnico y efecto comercial no evaluado. |
| DOC-02 — completada | Crear `docs/GUIA_CAPTURAS.md` | Indicar archivos, figuras, tablas y secciones concretas para capturar; explicar qué demuestra cada evidencia y excluir secretos/datos personales innecesarios. |
| DOC-03 — completada | Actualizar el DOCX de investigación | Incorporar fuente/licencia del dataset, población y muestras temporales, metodología, resultados, discusión y conclusiones; ajustar objetivos y afirmaciones al alcance retrospectivo. |
| DOC-04 — completada | Revisar coherencia de la entrega documental | Comprobar correspondencia entre DOCX, notebooks, métricas, versiones, tablas, figuras y referencias; identificar claramente experimentos históricos y resultados vigentes. |

Las conclusiones y la guía de capturas están creadas; el DOCX incluye los seis capítulos, tablas, figuras y referencias. DOC-04 contrastó cifras y referencias; CRM-06.2 amplió la tesis y revisó visualmente sus 17 páginas. Se conserva el original en `docs/historico/InvestigacionTesis2026_original.docx`. No se reentrenó ni modificó el modelo.

**Estado de cierre:** no quedan tareas obligatorias pendientes en el alcance académico acordado. La revisión del asesor y eventuales cambios institucionales pueden generar ajustes posteriores.

## Trabajo futuro, fuera del cierre actual

- CRM-01 a CRM-06: integración PHP/Laravel, persistencia, interfaz, programación, intervenciones y prueba completa con Krayin.
- Configuración del servidor definitivo: certificado, red, cuenta de servicio, operación sin sesión y pruebas de capacidad en ese destino.
- Validación comercial: datos reales de capacidad, costos, márgenes e intervenciones, además de evaluación prospectiva del modelo y del impacto en recompra/retención.
- Ejecución del plan de validación y eventual mejora del modelo con información o periodos independientes.

Estas actividades se conservan en el catálogo para retomarlas después; no son pendientes obligatorios de la etapa limitada al dataset actual. No se consideran realizadas por haberlas pospuesto.

## Límites que deben quedar en las conclusiones

El modelo actual no demostró utilidad predictiva suficiente en el test temporal. La calibración mejora respecto al estimador sin calibrar, pero no acredita rentabilidad ni efecto sobre clientes. El dataset no contiene campañas ni satisfacción; no permite afirmar mejora causal de fidelización. El modelo sigue siendo experimental y la API mantiene `automatic_action_allowed=false`.

Evidencias principales: `ML/artifacts/churn180-v1/metadata.json`, `docs/ML06_CALIBRACION_UMBRALES.md`, `docs/API04_SEGURIDAD.md`, `docs/API06_CARGA.md`, `docs/API07_DESPLIEGUE.md` y sus archivos de resultados. La fuente y licencia declarada se registran en `docs/dataset_kaggle_metadata.json`.

## Catálogo original de alcance

Prioridades originales: P0 corresponde a validez del modelo; P1 a entrega del servicio; P2 a integración y evaluación de impacto. El estado vigente es el resumen anterior.

## Separación realizada

- [x] Trasladar la API de `ML/main.py` a `backend/main.py`.
- [x] Extraer carga y predicción a `ML/inference.py`, sin dependencias de HTTP ni MySQL.
- [x] Trasladar los dos importadores y su CSV enriquecido a `integraciones/krayin/`, actualizando sus rutas.
- [x] Preservar inicialmente el modelo y contrato históricos durante la separación; luego sustituirlos por el artefacto temporal y el contrato vigente de siete variables.
- [x] Resolver el modelo con una ruta estable y permitir selección mediante `CHURN_MODEL_PATH`.
- [x] Hacer que un modelo ausente o incompatible impida el arranque, en vez de dejar la API sin estimador.
- [x] Registrar dependencias, instrucciones de uso e inventario SHA-256 original.
- [x] Cargar los cuatro artefactos y reproducir sus métricas sobre las particiones descritas en los notebooks, sin reentrenarlos.

## Alcance de las tareas ML

| ID | Prioridad | Tarea | Criterio para darla por terminada |
|---|---|---|---|
| ML-01 | P0 | Unificar fechas y fecha de observación. Usar `%d/%m/%Y` para este CSV y una política explícita para la fecha de corte. | Un mismo cliente tiene la misma recencia y etiqueta en todos los experimentos. Pruebas con fechas ambiguas como 08/11/2017 y con recencia exactamente 180 días. |
| ML-02 | P0 | Definir el objetivo: detectar inactividad actual o anticipar abandono futuro. Para retención preventiva, separar historial anterior al corte y una ventana futura de observación completa. | Documento con población elegible, ventana histórica, horizonte futuro y regla de etiqueta; ninguna variable usa compras posteriores al corte. Revisar el enfoque ya iniciado en `PruebaFallida.ipynb`. |
| ML-03 | P0 | Unificar preparación y calidad de datos en funciones reutilizables. | Mismos cálculos en entrenamiento e inferencia; fechas inválidas, duplicados, nulos, un solo registro, clientes nuevos y devoluciones tienen políticas explícitas. Unir etiquetas por Customer ID, no por posición. |
| ML-04 | P0 | Volver a evaluar RF, XGBoost y LightGBM con el mismo dataset corregido, particiones y protocolo. | Entrenamiento, validación y prueba final separados; ajuste de hiperparámetros y SMOTE solo en entrenamiento de cada partición/fold; evaluación temporal cuando el objetivo sea futuro. El test final no decide hiperparámetros ni umbrales. |
| ML-05 | P0 | Elegir el modelo con una comparación reproducible y una referencia simple. | CSV/JSON generado automáticamente con precision, recall, F1, ROC-AUC, PR-AUC y matrices de confusión; comparar con clase mayoritaria y una regla comercial adecuada. Justificar errores aceptables y selección; reemplazar métricas manuales de `ML_Comparacion.ipynb`. |
| ML-06 | P0 | Calibrar probabilidades y umbrales de riesgo. | Evaluar calibración y fijar límites usando validación y capacidad/costo de las campañas. Reportar desempeño de los umbrales 0,35/0,70 si se mantienen; no deducirlo de métricas calculadas a 0,50. |
| ML-07 | P1 | Empaquetar el artefacto final con metadatos. | Archivo del modelo más versión, hash, librerías, fecha de entrenamiento, variables ordenadas, definición de churn, ventanas, métricas y umbrales; API y exportaciones usan ese mismo artefacto. |
| ML-08 | P1 | Convertir el flujo principal de entrenamiento/evaluación/exportación en comandos repetibles. | Ejecución desde un entorno limpio sin depender del estado de celdas; semillas controladas; conjunto de datos identificado por hash; dependencias de entrenamiento fijadas. |
| ML-09 | P1 | Regenerar predicciones y evidencia de tesis con el modelo elegido. | CSV/JSON y gráficos trazables a versión y fecha de corte; distinguir predicciones para demostración de métricas sobre datos de prueba no usados para entrenar. |

**Orden sugerido:** ML-01 → ML-02/ML-03 → ML-04 → ML-05/ML-06 → ML-07/ML-08/ML-09. No basta con cambiar el archivo `.pkl` que carga la API.

## Alcance de las tareas backend Python

| ID | Prioridad | Tarea | Criterio para darla por terminada |
|---|---|---|---|
| API-01 | P1 | Formalizar contrato versionado de entrada y respuesta. | Identificador externo del cliente, fecha de corte, versión del modelo y fecha de predicción; esquema de errores; ejemplos compartidos con el futuro consumidor PHP. |
| API-02 | P1 | Completar validaciones de las siete variables vigentes. | Rechazo documentado de NaN/infinito, valores fuera del dominio, conteos imposibles y campos extra; tratamiento definido de cero compras, nulos y devoluciones. Errores de cliente generan 4xx, no fallos internos genéricos. |
| API-03 | P1 | Acordar dónde se calculan las características. | Una rutina compartida en Python o una implementación PHP verificada con casos idénticos; no confundir media por línea de venta con ticket medio por pedido. |
| API-04 | P1 | **Completada en implementación y verificación local HTTPS.** | 64 pruebas aprobadas; TLS 1.2/1.3, clave por archivo/entorno, lista de IPs y Host, y rechazo sin credencial. Evidencia y alcance en `docs/API04_SEGURIDAD.md`. Activación en el servidor definitivo pendiente de su dirección, certificado e IP del consumidor. |
| API-05 | P1 | Añadir estado del servicio y registros operativos. | Endpoint de salud/disponibilidad, versión del modelo, identificador de solicitud, tiempos y errores; respuestas sin detalles internos ni datos personales innecesarios. |
| API-06 | P1 | **Completada en el perfil local HTTPS.** | Lotes hasta 500, cuatro cupos de predicción, rechazo 503 y recepción limitada a cinco segundos. 480 solicitudes medidas con concurrencia 1/4/16, saturación y recuperación comprobadas; 96 pruebas y 95,38 % de cobertura. Guía `docs/API06_CARGA.md`; repetir carga con el volumen y hardware del destino. |
| API-07 | P1 | **Completada para el perfil local Windows con sesión de usuario.** | Dos entregas con entornos aislados y manifiestos SHA-256; 94 pruebas y 95,21 % de cobertura Python; aceptación HTTPS; arranque, parada, reinicio, recuperación tras caída, actualización y rollback comprobados. Guía: `docs/API07_DESPLIEGUE.md`; evidencia: `docs/evidencias_api/08_despliegue_reversion.json`. La configuración de un servidor sin sesión y su despliegue externo dependen del destino. |
| API-08 | P1 | Revisar las acciones comerciales sugeridas. | Separar riesgo estimado de fidelización observada; sustituir o justificar “Cliente fidelizado” y definir quién aprueba/ejecuta las campañas. La API actual solo devuelve texto, no ejecuta acciones. |

## Conexión posterior con Krayin

| ID | Prioridad | Tarea | Criterio para darla por terminada |
|---|---|---|---|
| CRM-01 | P2 | Identificar versión de Krayin y fuente real del historial de compras. | Mapeo de cliente, pedido, fecha, ventas, categoría y subcategoría; confirmar si estos datos están en Krayin o vienen de otro sistema. |
| CRM-02 | P2 | Crear el cliente HTTP en PHP/Laravel. | URL y credenciales por entorno, timeout, manejo de 4xx/5xx y reintentos controlados; prueba contra el servicio Python. |
| CRM-03 | P2 | Guardar resultados mediante la capa de aplicación del CRM. | Migraciones/configuración acordes a la instalación, mapeo estable por ID externo, actualizaciones idempotentes, historial de riesgo, fecha y versión del modelo; eliminar dependencia de IDs 61–65. |
| CRM-04 | P2 | Programar actualización de predicciones y mostrar resultados. | Tarea programada o cola, ficha/listado de riesgo y filtros; nueva compra o ejecución programada actualiza la predicción sin duplicar contactos. |
| CRM-05 | P2 | Registrar intervenciones y resultados de retención. | Campaña, contacto, oferta, aceptación, recompra y fechas vinculadas al cliente; medir resultado observado después de la intervención. |
| CRM-06 | P2 | Probar el flujo completo y monitorear su evolución. | Cliente de prueba → características → API → persistencia → interfaz → acción registrada; seguimiento de fallos, cambios en datos y desempeño, con criterio de reentrenamiento. |

## Evidencia pendiente para la investigación

- [x] Completar N y tamaño de muestra con la unidad correcta: 9.800 líneas de venta, 4.922 pedidos y 793 clientes; la muestra final puede variar al usar ventanas temporales.
- [x] Ajustar la descripción del dataset en el documento: el CSV no incluye tickets de soporte, satisfacción ni una etiqueta contractual de abandono; la etiqueta vigente se deriva de ausencia de compras en los 180 días posteriores al corte.
- [x] Registrar la fuente indicada por el usuario y verificar metadatos de Kaggle: Rohit Sahoo, Superstore Sales Dataset, versión 2, licencia declarada GPL 2. Evidencia: `docs/dataset_kaggle_metadata.json`. Referencia incorporada en el documento; no se ha probado identidad binaria con una descarga remota del CSV.
- [x] Completar análisis de datos, metodología de implementación, resultados, discusión y conclusiones con el protocolo final.
- [x] Elaborar el plan de validación en `docs/PLAN_VALIDACION_CRM.md`. Su ejecución con intervenciones y seguimiento real queda fuera del alcance actual.
- [x] Si solo se dispone de datos históricos y una demostración, delimitar los resultados a capacidad predictiva e integración técnica; no afirmar mejora real de fidelización sin observarla.

## Condición de cierre de esta etapa

La etapa actual queda cerrada con DOC-01 a DOC-04 completadas y los resultados del dataset disponible presentados con trazabilidad y limitaciones. La validación comercial, el despliegue externo y CRM-01 a CRM-06 quedan como trabajo futuro y no bloquean este cierre académico.












Reestructura de capítulos 3 y 4 (30/10/2026): metodología en páginas 7–20 y resultados en 19–27, con las cuatro imágenes originales indicadas. Ubicaciones y archivos para capturas: [índice vigente](INDICE_EVIDENCIAS_FINAL.md).


Capturas de Krayin añadidas el 30/10/2026: páginas 18–19, listado del módulo, datos del cliente y sugerencia de revisión por historial limitado. Capítulo 3: 7–20; capítulo 4: 21–29.
