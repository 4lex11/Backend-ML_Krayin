# MEJ-01 Protocolo de mejora experimental

Estado: completado el 29/10/2026. Estas decisiones se fijan antes de entrenar candidatos de esta nueva etapa, después de haber observado los resultados de v1. No constituyen un registro previo al conocimiento del dataset. Su configuración verificable se conserva en `ML/experiments/churn180-v2/protocol.json`.

## Objetivo y alcance

El objetivo principal es aumentar la proporción de abandonos observados entre el 20 % de clientes con mayor puntuación, sin degradar de forma material la ordenación general ni el error de las probabilidades. El 20 % es un escenario académico fijo, no una capacidad de contacto acreditada. El 10 % y 30 % son análisis secundarios: no se elegirá después el cupo con mejores resultados.

Se mantienen la fuente, limpieza, definición de abandono, elegibilidad y población de v1. Abandono significa ninguna compra en `(corte, corte + 180 días]`; las variables usan `(corte − 365 días, corte]`, y la última compra debe estar dentro de los 180 días previos. No se cambiará la etiqueta ni se eliminarán clientes difíciles para mejorar las métricas. No se incorporan costos, campañas ni datos externos inventados.

## Cortes fijados

| Evaluación | Cortes de entrenamiento | Calibración | Corte evaluado | Fin de seguimiento |
|---|---|---|---|---|
| D1 desarrollo | 2016-06-30 | 2016-12-31 | 2017-06-30 | 2017-12-27 |
| D2 desarrollo | 2016-06-30, 2016-12-31 | 2017-06-30 | 2017-12-31 | 2018-06-29 |
| E1 comprobación exploratoria | 2016-06-30, 2016-12-31, 2017-06-30 | 2017-12-31 | 2018-06-30 | 2018-12-27 |

Solo se usan etiquetas de entrenamiento completamente observables antes del corte de calibración; las de calibración deben estar completas antes del corte evaluado. Se validan 365 días de cobertura previa y 180 posteriores. Los clientes pueden repetirse: se evalúa una cartera conocida en el tiempo, no generalización a clientes nuevos. No se mezclan aleatoriamente filas entre periodos. Concatenar cortes no aumenta el número de clientes independientes.

D1 y D2 permiten seleccionar una única configuración y política. Después se fijan sus hashes y se ejecuta E1; su resultado puede impedir la promoción, pero no escoger otro candidato ni iniciar ajustes adicionales dentro de esta ejecución. Junio de 2018 ya fue test de v1: E1 no es una prueba independiente. También D1/D2 tienen resultados históricos conocidos. Una revisión del protocolo requiere nueva versión, motivo y registro de lo ya observado.

## Comparadores y experimentos

Comparadores obligatorios sobre exactamente los mismos clientes: puntuación de recencia `Recency / 180` (mayor recencia, mayor riesgo), probabilidad constante igual a la prevalencia del entrenamiento, y receta LightGBM de v1 con sus siete variables, reentrenada y calibrada en cada división. El artefacto v1 congelado solo se compara adicionalmente en E1: usarlo en D1/D2 introduciría información posterior. Se informan ambas comparaciones sin confundir receta reentrenada con artefacto instalado.

Familias candidatas: regresión logística, Random Forest y LightGBM regularizados. El presupuesto máximo es 24 combinaciones de familia, hiperparámetros y conjunto de variables, excluidos los comparadores. Se deben declarar en un manifiesto antes del primer entrenamiento de MEJ-04. No hay búsqueda ilimitada, redes neuronales ni SMOTE en esta primera ronda. El manifiesto debe incluir conjuntos de variables originales, temporales y combinados para evaluar el aporte de las nuevas variables. Los valores concretos de hiperparámetros se fijarán tras implementar las variables, antes de ver resultados de los candidatos.

Escalado, imputación y cualquier selección aprendida se ajustan únicamente con entrenamiento; calibración sigmoide solo con el corte reservado. Las categorías/IDs no se utilizan para memorizar clientes. Se mantiene el conjunto de clientes con historial limitado, con indicadores y reglas explícitas para variables no definidas. MEJ-02 debe comprobar por ejemplo que añadir compras posteriores al corte no altera predictores.

## Métricas y selección

La métrica principal es `precision_at_20`: ordenar por puntuación descendente y seleccionar `k = ceil(0,20 × N)`. Los empates se resuelven por Customer ID ascendente, solo para reproducibilidad, nunca como predictor. Precisión = verdaderos abandonos seleccionados / k. Informar también recall del grupo seleccionado, k, falsos positivos, falsos negativos, prevalencia y lift frente a la selección aleatoria esperada. La política de cupo no equivale a una categoría individual de riesgo ni debe ocultarse detrás de los umbrales actuales de Krayin.

Métricas secundarias: average precision (AP), ROC-AUC, Brier, log-loss, curvas de calibración, precisión/recall al 10 % y 30 %, y matriz de confusión de cualquier umbral analizado. Si no hay positivos predichos, la precisión se informa como no definida con su conteo; no se interpreta como buena precisión. Accuracy no es criterio de selección.

Elegir por media no ponderada de precision_at_20 en D1 y D2; desempatar por mayor AP media, menor Brier medio, menor cantidad de variables y finalmente ID de configuración en orden alfabético. No elegir por E1. Mostrar resultados individuales además de medias; no combinar todos los cliente-corte como observaciones independientes.

MEJ-05 comparará puntuación sin calibrar y sigmoide. La variante se elige con D1/D2 y se congela antes de E1. Cualquier umbral candidato se obtiene del corte de calibración, nunca del evaluado; el uso de ese mismo corte para calibrar y proponer umbral se declara como limitación y se evalúa en el siguiente corte. Si no existe un umbral compatible con el cupo objetivo, se informa: no se inventa un umbral. Los umbrales de v1 siguen intactos durante la experimentación.

## Condiciones para considerar una mejora

Las siguientes tolerancias son decisiones técnicas del estudio, no valores derivados del negocio. Se fijan ahora y se aplicarán conjuntamente al único candidato seleccionado:

1. Aumentar la media de precision_at_20 de D1, D2 y E1 al menos **0,05 absolutos (5 puntos porcentuales)** frente a cada comparador de recencia y receta v1. Superar estrictamente a cada uno en al menos dos de los tres cortes.
2. Aumentar AP media al menos **0,02 absolutos** frente a cada uno de esos dos comparadores y no perder más de 0,02 de AP frente a ninguno en ningún corte.
3. En E1, superar estrictamente tanto precision_at_20 como AP de recencia, de la receta v1 y del artefacto v1 instalado. Esto es un filtro de aceptación exploratorio, no selección de otro candidato.
4. El Brier medio no debe exceder en más de **0,01** al de la probabilidad constante ni al de la receta v1. En E1 tampoco debe exceder en más de 0,01 al del artefacto v1 instalado. Una mejor clasificación con probabilidades deficientes no basta para mostrar nuevos riesgos individuales en el CRM.
5. No debe haber fuga temporal, diferencias en la población evaluada, variables no finitas sin tratamiento declarado ni modificaciones del artefacto vigente. Cada corte evaluado debe tener al menos 100 clientes y ambas clases. Si no se cumple, el resultado es inconcluso; no se cambian las fechas para favorecer al candidato.

Se informarán intervalos percentiles del 95 % para diferencias pareadas de precisión al 20 % y AP, mediante 1.000 remuestreos de clientes con semilla 42. Cada cliente remuestreado conserva todos sus cortes; recalcular el ranking y k en cada réplica y aplicar las mismas muestras a candidato/comparadores. Reportar réplicas válidas; con menos del 90 % no emitir intervalo. Estos intervalos son descriptivos, no corrigen selección de modelos ni prueban independencia entre años. Si el intervalo de la mejora media de la métrica principal incluye cero frente a cualquiera de los dos comparadores, la promoción queda inconclusa aunque las medias cumplan las tolerancias.

Si falla un criterio de mejora, mantener v1 y documentar el resultado. Si supera todos, autoriza únicamente preparar la integración **experimental local** de MEJ-07; no demuestra beneficio comercial ni permite campañas automáticas. La prueba de contrato, paridad PHP/Python, persistencia por versión y reversión sigue siendo obligatoria antes de activarla.

## Conservación y evidencia

Los hashes del CSV, modelo, metadatos y protocolo vigentes se fijan en la configuración nueva. No se modifica `ML/protocol.json`, `ML/artifacts/churn180-v1`, backend ni Krayin. Los ensayos deberán escribir en directorios nuevos, conservar resultados de todos los candidatos, configuración, semilla, dependencias, variables y predicciones por cliente/corte. No sobrescribir ensayos desfavorables.

La verificación de MEJ-01 comprueba hashes, población de snapshots y cronología; no entrena ni evalúa nuevos modelos. Evidencia en [evidencias_mej01/verificacion.json](evidencias_mej01/verificacion.json). El entrenador de esta configuración aún está pendiente de MEJ-03/04; no pasar este JSON a `ML.train` de v1.
