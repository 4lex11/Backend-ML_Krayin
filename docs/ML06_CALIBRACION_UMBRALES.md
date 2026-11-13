# ML-06 — Calibración, umbrales y capacidad

28 de octubre de 2026. **Análisis académico completado con el dataset disponible. Validación comercial no acreditada.**

## Alcance y datos disponibles

El usuario confirmó que solo dispone del [Superstore Sales Dataset de Rohit Sahoo en Kaggle](https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting). La cabecera del CSV local incluye ventas, fechas, clientes, pedidos, productos y categorías, pero no costos de contacto, márgenes, campañas, efecto de ofertas ni capacidad de los agentes. No se puede deducir rentabilidad de una campaña a partir del importe de ventas.

Por ello, ML-06 se completa como estudio retrospectivo reproducible de calibración y sensibilidad. No se inventan datos del negocio ni se certifica que un umbral sea comercialmente óptimo. El modelo y los umbrales de la API permanecen intactos; `automatic_action_allowed=false` sigue vigente.

## Método

Se utiliza el artefacto `churn180-v1` existente, sin volver a entrenarlo. La calibración sigmoide fue ajustada en el corte de junio de 2017; la elección del modelo y umbrales se realizó sobre diciembre de 2017. El estudio reconstruye sus predicciones de validación y test a partir de los snapshots y registra sus hashes.

El test de junio de 2018 ya había sido observado. Este análisis adicional **no constituye una nueva prueba independiente**: sus comparaciones son descriptivas y no se usan para promover otra política a producción. Un cambio posterior de modelo o política requiere otro periodo de evaluación no utilizado para decidirlo.

Se compara el estimador antes y después de calibrar mediante Brier, log-loss y curvas por intervalos fijos de probabilidad de amplitud 0,10. Los CSV incluyen el número de observaciones de cada intervalo; algunos tienen pocos clientes. Las líneas del gráfico no son intervalos de confianza ni prueban una calibración perfecta.

## Resultados de calibración

| Periodo | N | Brier sin calibrar | Brier calibrado | Probabilidad media calibrada | Abandono observado |
|---|---|---|---|---|---|
| Validación | 510 | 0,2701 | 0,2524 | 36,09 % | 43,92 % |
| Test | 431 | 0,2805 | 0,1967 | 35,91 % | 23,43 % |

Un Brier menor indica menor error cuadrático de las probabilidades. La calibración mejora respecto al estimador sin calibrar, pero en test la probabilidad media todavía sobreestima el abandono observado en aproximadamente 12,48 puntos porcentuales. La diferencia entre periodos limita la interpretación estable de esos valores como riesgos individuales.

La mejora de Brier no demuestra buena discriminación, mejor priorización comercial ni efecto de una intervención. El ROC-AUC histórico de 0,4571 y la average precision de 0,2119 siguen siendo limitaciones del modelo.

## Umbrales auditados

Las reglas usan `probabilidad >= umbral`. La tabla muestra resultados del test; el CSV contiene también validación.

| Regla | Umbral | Clientes marcados / 431 | Precisión | Recall |
|---|---|---|---|---|
| Medio vigente, elegido por F2 | 0,311218 | 429 | 23,54 % | 100,00 % |
| Alto vigente | 0,377295 | 92 | 19,57 % | 17,82 % |
| Referencia histórica | 0,35 | 274 | 22,63 % | 61,39 % |
| Referencia convencional | 0,50 | 0 | No definida | 0,00 % |
| Referencia histórica | 0,70 | 0 | No definida | 0,00 % |

En los CSV se guarda precisión cero cuando no hay seleccionados como convención de cálculo; no significa que se hayan evaluado contactos con precisión cero. La regla de riesgo medio marca el 99,54 % de la muestra: su recall alto no proporciona una priorización práctica con capacidad limitada. El límite alto tampoco garantiza mejor precisión observada. Las etiquetas de riesgo son categorías de puntuación, no evidencia de fidelización.

## Escenarios de capacidad y costos relativos

Se exploran cupos máximos del 10 %, 20 % y 30 % de clientes. Son supuestos académicos. El costo de falso positivo se fija en una unidad abstracta y el de falso negativo se varía entre 1, 2 y 5. La pérdida es:

`pérdida relativa = FP + costo_FN × FN`

Esta pérdida penaliza errores de clasificación. No mide costo por contacto, beneficio de retener a un cliente ni probabilidad de que una oferta cambie su conducta. La identificación de alguien que abandonará no implica que sea recuperable.

Para cada combinación se evalúan todos los prefijos del ranking de probabilidad permitidos por el cupo en validación, incluyendo no seleccionar a nadie. Se elige el de menor pérdida y, en empates, el menor número de seleccionados. Se traslada esa **fracción** al test sin optimizarla con sus etiquetas. El número se redondea hacia abajo. Empates de puntuación se resuelven por ID ascendente; el ID no es una variable predictiva.

Se compara con seleccionar hasta el cupo completo por probabilidad, con recencia al mismo número de seleccionados y al cupo completo, y con no seleccionar a nadie. Hay nueve escenarios, cinco políticas y dos periodos: 90 filas de resultados. Una política top-k adapta su umbral implícito a la población; no equivale a mantener un umbral de probabilidad fijo ni sustituye las categorías que devuelve la API.

Ejemplo descriptivo: cupo máximo 20 %, costo FN = 2 y FP = 1, sobre el test:

| Política | Seleccionados | Precisión | Recall | Pérdida relativa |
|---|---|---|---|---|
| Modelo, fracción elegida en validación | 85 | 17,65 % | 14,85 % | 242 |
| Recencia, mismo cupo de 85 | 85 | 24,71 % | 20,79 % | 224 |
| Modelo, cupo completo | 86 | 17,44 % | 14,85 % | 243 |
| Recencia, cupo completo | 86 | 25,58 % | 21,78 % | 222 |
| Ningún seleccionado | 0 | No definida | 0,00 % | 202 |

En este escenario la pérdida del modelo es mayor que la del comparador y que la de no seleccionar. Esto no recomienda abandonar clientes: muestra que, bajo esa función hipotética, el modelo no justifica la política. Las diferencias son descriptivas, sin afirmar significación estadística. Tampoco debe elegirse retrospectivamente otro escenario porque resulte más favorable en este test.

## Decisión de ML-06

1. Conservar la calibración y los umbrales como parte del artefacto experimental auditado, no como umbrales comerciales aprobados.
2. No habilitar campañas automáticas ni presentar el nivel alto como una garantía de mayor precisión.
3. Usar este estudio para justificar las limitaciones y mostrar cómo cambian los errores al restringir capacidad y ponderar errores.
4. Si se obtienen datos reales del negocio, fijar capacidad, costos, comparador y criterio de éxito antes de evaluar un nuevo periodo, conforme a `PLAN_VALIDACION_CRM.md`.

Con los datos disponibles se cierra el **análisis técnico/académico** de ML-06. La validación comercial permanece pendiente de información y de un estudio prospectivo; conectarse a Krayin por sí solo no la resuelve.

## Reproducción, archivos y capturas

```powershell
.\.venv-clean\Scripts\python.exe -m ML.threshold_study --output docs/evidencias_ml06_nueva_ejecucion
```

El destino debe ser nuevo para evitar sobrescribir evidencia. Archivos generados:

| Archivo | Uso y captura sugerida |
|---|---|
| `docs/evidencias_ml06/report.json` | Estado experimental, hashes y limitaciones |
| `docs/evidencias_ml06/calibration.csv` | Comparación numérica antes/después de calibrar |
| `docs/evidencias_ml06/calibration_bins.csv` | Tamaño de los grupos del gráfico |
| `docs/evidencias_ml06/calibration.png` | Figura exportable de calibración por periodo |
| `docs/evidencias_ml06/thresholds.csv` | Umbrales vigentes e históricos y matrices de errores |
| `docs/evidencias_ml06/capacity_scenarios.csv` | Escenarios completos de cupos y costos relativos |
| `docs/evidencias_ml06/pruebas.txt` | Regresión, pruebas del cálculo y cobertura |

Código: `ML/threshold_study.py`. Pruebas: `tests/test_threshold_study.py`. Los casos comprueban conteos, desempates, respeto de cupos, conservación del modelo y rechazo de sobrescritura. Para la tesis, capturar las tablas de este documento y la figura, acompañadas de su explicación de límites.
