# Tareas para terminar ML y backend

Revisión del 27 de octubre de 2026. Prioridades: P0 bloquea la validez del modelo; P1 permite entregar el servicio; P2 corresponde a la conexión posterior con Krayin y la evaluación de impacto. El objetivo inmediato es dejar un modelo defendible y un servicio Python preparado para integrarse.

## Separación realizada

- [x] Trasladar la API de `ML/main.py` a `backend/main.py`.
- [x] Extraer carga y predicción a `ML/inference.py`, sin dependencias de HTTP ni MySQL.
- [x] Trasladar los dos importadores y su CSV enriquecido a `integraciones/krayin/`, actualizando sus rutas.
- [x] Mantener el modelo predeterminado, las seis entradas y el formato de respuesta existentes.
- [x] Resolver el modelo con una ruta estable y permitir selección mediante `CHURN_MODEL_PATH`.
- [x] Hacer que un modelo ausente o incompatible impida el arranque, en vez de dejar la API sin estimador.
- [x] Registrar dependencias, instrucciones de uso e inventario SHA-256 original.
- [x] Cargar los cuatro artefactos y reproducir sus métricas sobre las particiones descritas en los notebooks, sin reentrenarlos.

## ML pendiente

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

## Backend Python pendiente

| ID | Prioridad | Tarea | Criterio para darla por terminada |
|---|---|---|---|
| API-01 | P1 | Formalizar contrato versionado de entrada y respuesta. | Identificador externo del cliente, fecha de corte, versión del modelo y fecha de predicción; esquema de errores; ejemplos compartidos con el futuro consumidor PHP. |
| API-02 | P1 | Completar validaciones de las seis variables. | Rechazo documentado de NaN/infinito, valores fuera del dominio, conteos imposibles y campos extra; tratamiento definido de cero compras, nulos y devoluciones. Errores de cliente generan 4xx, no fallos internos genéricos. |
| API-03 | P1 | Acordar dónde se calculan las características. | Una rutina compartida en Python o una implementación PHP verificada con casos idénticos; no confundir media por línea de venta con ticket medio por pedido. |
| API-04 | P1 | Proteger la comunicación entre Krayin y Python. | Autenticación de servicio configurada por entorno, acceso de red restringido, gestión de secretos y HTTPS en el despliegue que lo requiera; prueba de rechazo sin credencial. |
| API-05 | P1 | Añadir estado del servicio y registros operativos. | Endpoint de salud/disponibilidad, versión del modelo, identificador de solicitud, tiempos y errores; respuestas sin detalles internos ni datos personales innecesarios. |
| API-06 | P1 | Definir predicción masiva y manejo de carga. | Elegir endpoint por lote o procesamiento desde cola; límites de lote, timeout, reintentos e identificación de resultados por cliente; medir latencia con el volumen esperado. |
| API-07 | P1 | Preparar despliegue reproducible y pruebas de aceptación. | Instalación limpia, servicio con inicio/reinicio controlado, configuración por entorno, contrato y regresión probados, artefacto versionado y procedimiento de reversión. |
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

- [ ] Completar N y tamaño de muestra con la unidad correcta: 9.800 líneas de venta, 4.922 pedidos y 793 clientes; la muestra final puede variar al usar ventanas temporales.
- [ ] Ajustar la descripción del dataset: el CSV revisado no incluye tickets de soporte, satisfacción ni una etiqueta de abandono observada; la etiqueta actual se deriva de recencia.
- [ ] Registrar URL exacta, autor, versión, licencia y condiciones de uso del dataset. No se verificó su origen externo en esta revisión.
- [ ] Completar análisis de datos, metodología de implementación, resultados, discusión y conclusiones con el protocolo final.
- [ ] Definir medición pre/posintervención, periodos comparables, indicadores de retención/recompra y satisfacción si se va a afirmar una mejora en ella; tratar factores de confusión y límites de atribución causal.
- [ ] Si solo se dispone de datos históricos y una demostración, delimitar los resultados a capacidad predictiva e integración técnica; no afirmar mejora real de fidelización sin observarla.

## Condición de cierre de esta etapa

La etapa ML/backend puede cerrarse cuando las tareas P0 estén resueltas, exista un artefacto final reproducible, la API cumpla el contrato y sus pruebas, y el cálculo de las seis variables esté documentado y comprobado. Las tareas P2 son la fase de integración posterior solicitada por el usuario.
