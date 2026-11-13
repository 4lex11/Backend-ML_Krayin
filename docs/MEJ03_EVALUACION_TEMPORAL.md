# MEJ-03 Preparación de evaluación temporal

Completada el 29/10/2026. `ML/temporal_validation.py` implementa las divisiones de MEJ-01 y prepara los datos que utilizarán los candidatos de MEJ-04. En esta etapa no se entrenan modelos ni se calculan métricas predictivas nuevas.

## Resultado

| División | Filas de entrenamiento | Clientes únicos de entrenamiento | Calibración | Evaluación | Abandonos en evaluación |
|---|---:|---:|---:|---:|---:|
| D1 | 286 | 286 | 444 | 351 | 128 |
| D2 | 730 | 566 | 351 | 510 | 224 |
| E1 | 1081 | 678 | 510 | 431 | 101 |

Se exportan nueve CSV, uno por división y función. Contienen el ID para unir resultados, fecha de corte, etiqueta y las 18 variables disponibles. El manifiesto declara tres conjuntos de predictores: original (7), temporal (11) y combinado (18). Customer ID, cutoff y Churn nunca deben entrar como predictores. Los conjuntos se seleccionan por columnas de las mismas filas; no se descartan clientes según las variables elegidas.

La etiqueta se calcula con `make_snapshot`, compartida con v1. Cada etiqueta de entrenamiento debe completar sus 180 días antes del siguiente corte; la calibración debe completar su horizonte antes de la evaluación. Se rechazan cortes repetidos/desordenados, horizontes incompatibles, cobertura incompleta, menos de 100 clientes, una sola clase, variables no finitas y población diferente entre las variables originales y temporales.

D1 y D2 están habilitados para selección. E1 se marca `usable_for_selection=false` y queda reservado para comprobar el único candidato congelado en MEJ-04/05. Los archivos E1 están disponibles para reproducibilidad; esta marca es un contrato para el futuro evaluador, no un control de acceso. No es un test independiente porque ese periodo ya se analizó en v1.

La repetición de clientes entre fechas es intencional: la población objetivo es una cartera conocida. Las 1081 filas de entrenamiento de E1 corresponden a 678 clientes diferentes, no a 1081 personas independientes.

## Ejecución y evidencias

Desde la raíz del proyecto:

```powershell
& .\.venv-clean\Scripts\python.exe -m ML.temporal_validation --output docs/evidencias_mej03/nueva-preparacion
```

El destino debe ser nuevo. La ejecución entregada está en [preparacion/manifest.json](evidencias_mej03/preparacion/manifest.json). El manifiesto conserva hashes de dataset, protocolo, código y cada CSV; una copia exacta del protocolo acompaña los resultados. Se verifica también que modelo, metadatos y protocolo de v1 coincidan con las referencias de MEJ-01 antes de escribir resultados.

Validación: **11 pruebas aprobadas**, incluyendo MEJ-02 y seis casos de MEJ-03. Cubren solapamiento de etiquetas, duplicados de corte, incompatibilidad de variables/ventanas, paridad con etiquetas y población v1, cobertura futura incompleta, cambios de ventas futuras, exportación y rechazo de sobrescritura o CSV incompatible. Black y Ruff aprobaron los archivos nuevos.

El JSON de protocolo conserva su estado histórico `design_only_mej01`: es configuración de experimento, no un modelo desplegado; su estado operativo se registra en este documento y el plan. No se cambió el protocolo congelado durante MEJ-03. La implementación de ajuste, métricas, comparación de candidatos y decisiones de promoción corresponde a MEJ-04, MEJ-05 y MEJ-06.
