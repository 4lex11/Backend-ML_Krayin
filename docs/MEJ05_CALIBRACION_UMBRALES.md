# MEJ-05 Calibración y políticas de selección

Completada el 29/10/2026 para el candidato congelado `lightgbm_original_a`. Se reutilizaron los ajustes de D1/D2 de MEJ-04, verificando los hashes antes de cargar los modelos. No se entrenó otro candidato ni se consultó E1.

## Regla aplicada

Antes del análisis se escribió `analysis_plan.json`: comparar salida cruda y sigmoide del candidato, ordenar por precisión media al 20 %, AP media, menor Brier e ID de variante. Se conserva el objetivo principal de MEJ-01. Los cupos 10 % y 30 % son secundarios. Se congela la variante ganadora para MEJ-06; no se reinterpretan estos resultados como aceptación.

| Variante | Precisión al 20 % media | AP media | Brier medio | Log-loss medio |
|---|---:|---:|---:|---:|
| Sigmoide, seleccionada | 0,518227 | 0,458369 | 0,268670 | 0,731283 |
| Sin calibrar | 0,419635 | 0,426186 | 0,252945 | 0,700012 |

La sigmoide mejora la ordenación según la métrica principal, pero empeora Brier y log-loss medios. Por tanto, aquí «calibrado» describe el procedimiento aplicado, no una calibración necesariamente mejor. La probabilidad constante de MEJ-04 obtuvo Brier medio 0,244086, menor que ambas variantes.

En D1, la sigmoide estima una media de 59,69 % frente a 36,47 % de abandono observado. En D2 estima 36,48 % frente a 43,92 %. La variación de prevalencia entre periodos limita trasladar las probabilidades sin una comprobación adicional. Se conservan diez intervalos de anchura 0,10 con tamaño, probabilidad media y fracción observada en `calibration_bins.json`; los intervalos vacíos llevan valores nulos y no constituyen intervalos de confianza.

La sigmoide invierte el orden de las puntuaciones en D1 y lo conserva en D2. Se comprobó el coeficiente del calibrador: a=0,0171914 y a=−0,0119021, respectivamente, para la forma `1 / (1 + exp(a*f + b))`. En D1 ROC-AUC pasa de 0,461060 a 0,538940. Este cambio explica que AP y precisión puedan cambiar tras calibrar; no debe afirmarse que la calibración siempre conserva el ranking ni que se haya demostrado una mejora estable.

## Umbrales

Para cada variante se buscaron umbrales que seleccionen exactamente `ceil(fracción × N)` en su corte de calibración mediante la condición `probabilidad >= umbral`. Si los empates impiden ese tamaño, se devuelve nulo. Se obtuvieron diez combinaciones compatibles de doce. Fueron incompatibles D1 sin calibrar al 20 % y D1 sigmoide al 10 %. No se inventaron umbrales ni se descartaron empates.

| Corte y variante seleccionada | Umbral para cupo 20 % en calibración | Seleccionados después en evaluación | Precisión | Recall | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| D1 sigmoide | 0,59897069 | 62 de 351 | 0,467742 | 0,226563 | 33 | 99 |
| D2 sigmoide | 0,36528975 | 106 de 510 | 0,528302 | 0,250000 | 50 | 168 |

Un umbral aprendido para seleccionar 20 % en calibración no garantiza seleccionar 20 % después. Esto es distinto de la política principal top-20 %, que ordena cada población y selecciona exactamente 71 y 102 clientes en D1/D2, con desempates por ID. No se traducen esos cupos en categorías individuales Alto/Medio/Bajo del CRM.

Los umbrales utilizan el mismo corte que ajustó el calibrador; esa reutilización es una limitación explícita. La evaluación se realiza en el corte posterior. No se usa la etiqueta de evaluación para elegir un umbral. Una selección sin alertas informa precisión no definida y conteos, no éxito artificial.

## Decisión congelada y siguiente paso

`frozen_policy.json` fija candidato, variante sigmoide, selección principal top-20 %, regla de empates y regla de obtención de umbrales desde calibración. No fija un único umbral numérico universal: MEJ-06 debe ajustar el candidato en el entrenamiento de E1 y aplicar su calibración reservada antes de evaluar. No se deben reutilizar como definitivos los umbrales numéricos de D1/D2 ni escoger otro candidato a partir de E1.

El estado sigue siendo `promoted=false`. Las condiciones de aceptación de Brier, estabilidad e incertidumbre permanecen vigentes; ganar en precisión de desarrollo no las sustituye. API, artefacto v1 y Krayin siguen con su configuración actual.

## Evidencias y reproducción

Carpeta: `docs/evidencias_mej05/calibracion/`. Contiene plan, métricas por corte/variante, probabilidades por cliente, intervalos de calibración, doce casos de umbral, resumen, política congelada y manifiesto con hashes de código y archivos.

```powershell
& .\.venv-clean\Scripts\python.exe -m ML.calibration_v2 --output docs/evidencias_mej05/nuevo-analisis
```

El destino debe ser nuevo. Validación: 13 pruebas aprobadas de MEJ-04/05, incluidas seis nuevas para umbrales, empates, redondeo, entradas inválidas, ausencia de alertas y extremos de los intervalos de calibración. Black y Ruff aprobaron los archivos nuevos. Los resultados son retrospectivos y no acreditan rentabilidad ni fidelización.
