# Plan de validación de ML e integración con Krayin CRM

Versión 1.1 — actualizada el 29 de octubre de 2026. **Validación técnica local del dataset fijo completada en [CRM-06.1](CRM061_VALIDACION_INTEGRAL.md)**. Las fases prospectivas/comerciales y las extensiones a producción siguen siendo trabajo futuro. El acta enlazada delimita los casos ejecutados y sus evidencias.

## 1. Objetivo y alcance

Comprobar por separado: (1) que los datos y la integración producen resultados correctos; (2) que el modelo anticipa ausencia de recompra; y (3) que una política de intervención apoyada en ML mejora la recompra frente a una alternativa comparable. Aprobar la integración no demuestra capacidad predictiva ni mejora de fidelización.

El plan conserva la definición acordada: abandono operacional = ninguna compra en los 180 días posteriores a la fecha de corte. Se usan compras de los 365 días anteriores al corte y clientes cuya última compra ocurrió hace 180 días o menos. No representa una baja contractual ni una medición directa de satisfacción.

El artefacto `churn180-v1` permanece experimental y devuelve `automatic_action_allowed=false`. En el test histórico obtuvo ROC-AUC 0,4571 y average precision 0,2119; la prevalencia de abandono fue 0,2343. Estos resultados no justifican campañas automáticas. El piloto comercial descrito abajo queda condicionado a una evaluación predictiva y comercial favorable; la validación técnica y observación sin intervención sí pueden realizarse.

## 2. Decisiones que deben cerrarse antes de ejecutar

| Decisión | Responsable propuesto | Registro requerido |
|---|---|---|
| Versión de Krayin y sistema que contiene las ventas | Responsable técnico | Versión, esquema, origen y mapeo de campos |
| Calendario de datos y zona horaria comercial | Responsable de datos | Fechas de cobertura, cierre diario y tratamiento de compras tardías |
| Capacidad de contacto y costo por intervención | Responsable comercial | Contactos por periodo, canal, costo y margen disponible |
| Comparador y política de intervención | Investigador y responsable comercial | Regla habitual o recencia, oferta, frecuencia y presupuesto equivalentes |
| Mejora mínima relevante y tamaño de muestra | Investigador con revisión estadística | Tasa base, diferencia absoluta buscada, cálculo y supuestos |
| Permisos de acceso y contacto | Responsable del CRM | Roles, elegibilidad de contacto, exclusiones y plazo de conservación |
| Umbrales de operación | Responsable técnico | Concurrencia, latencia p95/p99, timeout y tasa de error aceptable |

Son responsabilidades propuestas, no personas ya designadas. No se fijan costos, tasas comerciales ni tamaños de muestra sin datos del negocio. Los valores acordados deben registrarse antes de analizar los resultados finales.

## 3. Fases y criterios de aceptación

### V-01. Preparación y calidad de datos

Relacionar cada cliente con un identificador externo estable y verificar cliente, pedido, línea, fecha, importe, categoría y subcategoría. Documentar el tratamiento de devoluciones antes de generar las variables; el contrato actual rechaza importes negativos. Un importe ausente no se convierte en cero.

Verificar cobertura histórica real de 365 días, no solo la fecha declarada en la petición. Resolver diferencias de zona horaria antes de aplicar cortes por día. Excluir datos posteriores al corte del cálculo de características. Auditar compras tardías y fijar cuándo se considera cerrado el seguimiento.

**Aceptación:** todas las filas aceptadas cumplen el contrato; filas rechazadas quedan cuantificadas y con motivo; IDs no presentan colisiones; pedidos y ventas concilian con el origen en la extracción de prueba. Unir etiquetas por ID y corte, nunca por posición. Cualquier diferencia no explicada impide pasar a la siguiente fase.

**Evidencia:** diccionario de datos, tabla de mapeo, reporte de cobertura, conciliación y listado de rechazos sin información personal innecesaria. Registrar cuántos clientes fueron excluidos y por qué, para no ocultar sesgo de selección.

### V-02. Integración técnica y operación

Ejecutar los siguientes casos en una instalación de prueba de Krayin:

| Caso | Resultado esperado |
|---|---|
| Cliente válido, corte e historial completo | Predicción asociada al cliente y versión correctos |
| Variables precalculadas frente al endpoint de transacciones | Misma probabilidad, diferencia absoluta máxima de 1e-10 con el mismo artefacto |
| Predicción individual frente a lote | Misma probabilidad y correspondencia por cliente/corte |
| Sin compras, fuera de población, fechas futuras o datos inválidos | Rechazo explícito; no persistir una probabilidad inventada |
| NaN, infinito, campos adicionales, IDs de línea repetidos | Error de validación según el contrato vigente |
| Credencial ausente, IP/Host no permitido, certificado no confiable | Rechazo; el consumidor no omite validación TLS |
| Lote de 500 clientes; lote de 501 | El primero se admite si cumple el límite de bytes; el segundo se rechaza |
| Timeout, desconexión o respuesta 5xx | Reintento limitado y trazado; no repetir indefinidamente |
| Solicitud repetida | Una sola entrada lógica por cliente/corte/versión; no duplicar intervenciones |
| Resultado recibido fuera de orden | Conservar historial; no sustituir el resultado vigente por uno más antiguo |
| Caída y actualización del servicio | Recuperación y rollback verificables; errores visibles para el operador |
| Interfaz de usuario | Mostrar versión, corte, antigüedad y carácter experimental; no afirmar “cliente fidelizado” |

Una nueva compra debe reflejarse en la siguiente ejecución acordada. Verificar también permisos de lectura/escritura de la interfaz y la ejecución programada. El responsable técnico documentará la política de reintento del consumidor PHP; los 4xx no deben reintentarse sin corregir la causa.

**Aceptación:** todos los casos funcionales y de seguridad pasan; no hay duplicados lógicos ni asociaciones incorrectas; se conserva trazabilidad desde extracción hasta pantalla. API-06 debe completar la prueba concurrente sobre HTTPS y cumplir los límites acordados antes de admitir tráfico habitual. No usar el benchmark secuencial en memoria como prueba de capacidad del servidor.

**Evidencia:** resultados de casos con fecha y versión, IDs de solicitudes, muestras anonimizadas de persistencia, capturas de pantalla, métricas de carga y registro de recuperación. La verificación local de API-04/API-07 es evidencia previa, no sustituye esta prueba con Krayin.

### V-03. Validación predictiva prospectiva sin intervención

Congelar versión del modelo, variables, población, umbrales y fecha de corte. Guardar las predicciones antes de observar compras futuras. No mostrarlas a quienes deciden campañas durante esta fase, para evitar que modifiquen el resultado que se quiere observar. Registrar las campañas habituales que ocurran de todas formas.

Observar cada cliente durante 180 días completos. Clientes sin seguimiento completo no se etiquetan automáticamente como abandono: se marcan como pendientes o con seguimiento incompleto y se reporta su número. Una ausencia de datos del origen tampoco se interpreta como ausencia de compra.

Comparar sobre exactamente los mismos clientes con una regla simple de recencia y una referencia de prevalencia. Para seleccionar clientes a contactar, comparar también al mismo cupo K, fijado por capacidad comercial. No seleccionar el umbral con este periodo de evaluación.

| Indicador | Interpretación |
|---|---|
| Average precision y prevalencia | Calidad de ordenación del riesgo y referencia de un clasificador sin información |
| ROC-AUC | Separación de ambas clases; no basta por sí sola para aprobar uso |
| Precision@K y recall@K | Rendimiento con el cupo de contacto disponible |
| Matriz de confusión al umbral fijado | Falsos positivos, falsos negativos y carga de contacto |
| Brier y curva de calibración | Concordancia entre probabilidades y frecuencias observadas |
| Fracción marcada como riesgo | Viabilidad del volumen de intervención |

Reportar intervalos de confianza del 95 %. Si se evalúan varios cortes con clientes repetidos, tener en cuenta esa dependencia, por ejemplo mediante remuestreo por cliente, y presentar resultados por periodo. No presentar cada fila cliente-corte como una persona independiente.

**Puerta de decisión:** antes de abrir el periodo final, registrar una mejora mínima relevante de precision@K respecto del comparador y un criterio de incertidumbre. Se propone exigir que el intervalo del 95 % de la diferencia excluya cero, además de alcanzar la mejora mínima y no exceder la capacidad comercial. Si los datos no permiten decidir, el resultado es inconcluso; si no supera el comparador, se mantiene experimental. La discriminación no prueba que contactar a un cliente vaya a cambiar su conducta.

Si se usan los resultados para cambiar características, modelo o umbrales, ese periodo deja de ser prueba final: el candidato necesita una evaluación futura independiente. No volver a ajustar contra el test histórico ya observado.

### V-04. Piloto de impacto de la política comercial

Solo iniciar cuando V-01 a V-03 y la validación comercial de ML-06 permitan hacerlo. Aprobar explícitamente una política de contacto; no retirar de forma implícita la restricción `automatic_action_allowed=false` del modelo actual.

**Diseño principal propuesto:** asignar aleatoriamente clientes elegibles a dos grupos antes de decidir quién recibirá contacto. Grupo A: priorización con el modelo validado. Grupo B: priorización con la regla habitual o recencia. Aplicar igual proporción de contacto, presupuesto, canal, oferta y calendario en ambos grupos. Contactar dentro de cada grupo a sus K clientes priorizados. Fijar K por grupo antes del piloto.

La unidad de asignación y análisis es el cliente. Un mismo cliente conserva su grupo y se incorpora una sola vez al piloto principal. Si existen cuentas relacionadas que puedan compartir una oferta, considerar asignación por cuenta o grupo relacionado y ajustar el análisis y tamaño de muestra. Evitar contactos cruzados; registrar toda desviación.

**Resultado principal:** proporción de clientes que recompran en los 180 días posteriores a la asignación, calculada sobre todos los clientes asignados a cada grupo, incluidos quienes no fueron contactados. Este análisis por asignación original compara las políticas completas. Analizar únicamente quienes respondieron o fueron contactados introduce selección y no sustituye el análisis principal.

La diferencia A−B estima el efecto de priorizar con ML frente al comparador bajo ese presupuesto y esas condiciones. No estima automáticamente el efecto de cualquier campaña frente a no contactar. Para esa pregunta se necesitaría otro comparador y otro protocolo. Una comparación histórica antes/después puede describirse como exploratoria, pero no permite atribuir por sí sola el cambio al ML.

## 4. Indicadores de impacto y fórmulas

| Indicador | Cálculo o definición |
|---|---|
| Recompra a 180 días — principal | Clientes con al menos una compra en seguimiento / clientes asignados al grupo con seguimiento evaluable; informar por separado pérdidas y hacer análisis de sensibilidad |
| Diferencia absoluta | Tasa A − tasa B, expresada en puntos porcentuales, con intervalo del 95 % |
| Mejora relativa — secundaria | (Tasa A − tasa B) / tasa B; no definida cuando B es cero |
| Abandono operacional | 1 − recompra, solamente con seguimiento completo |
| Margen por cliente asignado | Margen observado menos costos de intervención, dividido por clientes asignados; solo si hay datos fiables de margen |
| Costo por recompra incremental | Diferencia de costos / diferencia estimada de recompradores para grupos comparables; no interpretar como favorable si el incremento es cero o negativo |
| Contactabilidad y ejecución | Contactos intentados, entregados, respondidos y desviaciones del cupo previsto |
| Molestias asociadas al contacto | Quejas, solicitudes de no contacto y bajas, con denominador explícito |
| Satisfacción — opcional | Encuesta definida antes del piloto, aplicada de forma comparable; informar tasa de respuesta y sesgo de no respuesta |

Las pérdidas de seguimiento impiden un análisis completo por asignación original. No deben eliminarse sin explicación: informar balance por grupo y escenarios conservadores/favorables, o un método de tratamiento preespecificado. Si son importantes o diferentes entre grupos, limitar la conclusión causal.

Ventas no equivalen a margen. El dataset histórico no permite demostrar satisfacción ni conocer el beneficio de una intervención real.

## 5. Tamaño de muestra y calendario

Antes de asignar clientes, estimar la recompra base con un periodo anterior independiente, fijar la diferencia absoluta mínima de interés, nivel de significación bilateral de 0,05 y potencia propuesta de 80 %. Calcular tamaño para comparación de dos proporciones y ajustar por pérdidas previstas, agrupación si existe y presupuesto de contacto. Documentar herramienta, parámetros y resultado del cálculo. Si la cartera disponible es insuficiente, presentar un piloto de factibilidad sin afirmar eficacia concluyente.

Los 793 clientes históricos de Kaggle no son automáticamente la muestra del piloto de Krayin. Tampoco las 9.800 líneas de venta representan 9.800 clientes.

| Etapa | Inicio/fin lógico |
|---|---|
| Preparación e integración | Hasta aprobar V-01/V-02 y resolver API-06 |
| Observación predictiva | Predicción congelada en T0; seguimiento hasta T0 + 180 días y conciliación de datos tardíos |
| Decisión sobre modelo | Tras cerrar el seguimiento y evaluar con criterios registrados |
| Piloto comercial, si procede | Asignación en T1; seguimiento individual hasta T1 + 180 días |
| Análisis y conclusiones | Después del cierre de datos y auditoría de ejecución |

Si la incorporación es escalonada, el análisis final espera 180 días después del último cliente incorporado, más el cierre de datos acordado. No prometer que todo el estudio termina en 180 días: una validación predictiva seguida de un piloto comercial requiere dos ventanas independientes.

## 6. Registro mínimo y trazabilidad

Conservar una tabla de predicciones con `prediction_id`, ID externo seudonimizado, corte, fecha de generación, versión/hash del modelo, versión de variables, probabilidad y umbral aplicado. Conservar aparte asignación de grupo, fecha de asignación, estrato si existe, elegibilidad y motivo de exclusión.

Para cada intervención: ID, cliente, campaña, responsable, canal, fecha prevista/real, oferta, costo, estado y motivo de no ejecución. Para resultados: cobertura de seguimiento, pedidos y ventas posteriores, recompra a 180 días, incidencias y datos de margen o encuesta únicamente cuando existan.

Usar claves estables para unir tablas. Conservar un registro de cambios y la extracción utilizada para el análisis. Restringir accesos según función; las capturas y exportaciones de tesis deben usar datos sintéticos o seudonimizados y excluir secretos de API. Definir conservación y eliminación conforme a las reglas aplicables al proyecto antes de usar datos reales.

## 7. Monitoreo y reglas de suspensión

- Revisar disponibilidad, errores y latencia según los límites de API-06; registrar fallos de tareas y antigüedad de predicciones.
- Revisar cobertura, rechazos, proporción de clientes elegibles y distribución de variables por periodo. Un cambio de distribución genera investigación, no reentrenamiento automático.
- Medir desempeño predictivo solo sobre cohortes cuyo seguimiento de 180 días ya terminó.
- Suspender contactos del piloto si hay asociaciones incorrectas, exposición de datos, duplicación de campañas o incumplimiento de las reglas comerciales acordadas. Ante caída de la API, no convertir un fallo en riesgo bajo.
- Conservar el modelo y las asignaciones del piloto congelados. Una modificación relevante requiere otra versión del protocolo y, si afecta la comparación, un nuevo piloto.
- Definir límites de quejas y costos antes de comenzar. No detener por una mejora aparente observada repetidamente sin una regla estadística preespecificada.

## 8. Entregables y capturas para la investigación

| Evidencia | Archivo propuesto al ejecutar | Captura sugerida |
|---|---|---|
| Mapeo y calidad | `docs/validacion_crm/01_calidad_datos.md` | Cobertura, población y motivos de exclusión |
| Pruebas de integración | `docs/validacion_crm/02_integracion.csv` | Casos, resultado esperado/obtenido y versión |
| Carga concurrente | `docs/validacion_crm/03_carga.json` | Concurrencia, percentiles, errores y recursos |
| Validación predictiva | `docs/validacion_crm/04_predictiva.json` | Comparador, precision@K, calibración e intervalos |
| Protocolo comercial congelado | `docs/validacion_crm/05_piloto.md` | Asignación, tamaño de muestra, cupo y criterio de éxito |
| Resultado de impacto | `docs/validacion_crm/06_impacto.md` | Tasas por grupo, diferencia, intervalo, costos y limitaciones |

**Estos archivos son entregables futuros, no resultados existentes.** Para mostrar el plan ahora, capturar las secciones 3, 4 y 5 de este archivo. Para evidencia técnica ya disponible, usar `docs/evidencias_api/08_despliegue_reversion.json` y `docs/evidencias_api/API07_pruebas_entorno_limpio.txt`. Para el desempeño histórico, usar `ML/artifacts/churn180-v1/metadata.json` y `ML/ML_Resultados_Finales.ipynb`.

## 9. Criterio de cierre y redacción de conclusiones

El plan queda preparado con este documento. Su ejecución se cierra por fases: integración aceptada, validación predictiva evaluada y, si corresponde, piloto comercial analizado. Cada acta debe indicar responsable, fecha, versión, evidencias, desviaciones y decisión de continuar o detenerse.

Si solo se completa V-02, concluir que existe una integración técnica validada. Si se completa V-03, concluir sobre predicción prospectiva en esa población y periodo. Solo un piloto comparable ejecutado y analizado permite sostener una mejora atribuible a la política probada, con su incertidumbre y límites. Un resultado negativo o inconcluso también es un resultado válido de investigación y debe conservarse.
