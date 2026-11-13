# MEJ-04 Comparación de candidatos

Completada el 29/10/2026. Se fijó `ML/experiments/churn180-v2/candidates_mej04.json` antes de ejecutar el primer entrenamiento. Incluye 18 combinaciones: tres familias (regresión logística, Random Forest y LightGBM), dos configuraciones por familia y tres conjuntos de variables (original, temporal, combinado). Se respetó el presupuesto máximo de 24 y no se utilizó SMOTE.

## Resultado de desarrollo

| Configuración | Precisión al 20 % media | AP media | Brier medio |
|---|---:|---:|---:|
| Seleccionado `lightgbm_original_a` | 0,518227 | 0,458369 | 0,268670 |
| Recencia | 0,436758 | 0,414947 | 0,306142 |
| Receta v1 reentrenada | 0,421154 | 0,410606 | 0,268989 |
| Prevalencia del entrenamiento | 0,405827 | 0,401944 | 0,244086 |

Son medias no ponderadas de D1 y D2. El cupo usa `ceil(0,20 × N)`: 71 clientes en D1 y 102 en D2. Los empates se resuelven por ID ascendente. La precisión de la referencia constante depende de ese desempate; no representa capacidad de ordenar el riesgo. La expectativa de una selección aleatoria es la prevalencia de cada corte.

El candidato utiliza las siete variables originales, 100 árboles LightGBM, profundidad máxima 2, cuatro hojas, tasa de aprendizaje 0,03, mínimo de 20 observaciones por hoja y regularización L2 de 1. Se calibró con sigmoide sobre el periodo reservado. No se entrenó con calibración ni evaluación. La regresión logística aplicó escalado ajustado exclusivamente en entrenamiento.

En D1 obtuvo precisión 0,507042, AP 0,419245 y Brier 0,285522; en D2, precisión 0,529412, AP 0,497492 y Brier 0,251819. La selección siguió precisión media al 20 %, AP, Brier, número de variables e ID. Las variables temporales fueron comparadas, pero ninguna combinación con ellas quedó primera. Esto no demuestra que sean inútiles en otros periodos.

## Decisión y límites

Se congela `lightgbm_original_a` como único candidato para el análisis siguiente. La precisión media supera descriptivamente a recencia en 8,15 puntos porcentuales y a la receta v1 en 9,71 puntos. El Brier medio excede al de la probabilidad constante en aproximadamente 0,0246, por encima de la tolerancia 0,01 si se consideraran solo estos dos cortes. La aceptación definitiva requiere las reglas completas de MEJ-06; no se declara superada.

E1 no se leyó ni se utilizó para entrenar, seleccionar o calcular resultados de esta tarea. MEJ-05 analizará la calibración y política del candidato congelado. MEJ-06 realizará la comprobación exploratoria y la incertidumbre prevista. No se sustituyó el artefacto instalado ni se modificaron API, umbrales o Krayin. El modelo actual continúa vigente.

## Reproducción y trazabilidad

```powershell
& .\.venv-clean\Scripts\python.exe -m ML.compare_v2 --manifest ML/experiments/churn180-v2/candidates_mej04.json --output docs/evidencias_mej04/nueva-comparacion
```

El destino debe ser nuevo. La entrega está en `docs/evidencias_mej04/comparacion/`:

- `design.json`: copia del manifiesto fijado antes de entrenar.
- `metrics.json`: 42 filas (18 candidatos y tres referencias por corte), con resultados calibrados y métricas sin calibrar de los modelos.
- `selection.json`: clasificación completa de candidatos, referencias y configuración seleccionada; `E1_used=false`, `promoted=false`.
- `D1_*.csv` y `D2_*.csv`: probabilidades crudas/calibradas y etiquetas por cliente de los 38 ajustes de modelos, incluida la receta v1.
- `D1_*.joblib` y `D2_*.joblib`: estimadores, calibradores, parámetros y columnas de cada ajuste.
- `status.json`: estado final, hash del manifiesto, código ejecutado, versiones de dependencias y hashes de los archivos producidos.

Los archivos de MEJ-03 se validan por hash antes de su uso. Si falla un ajuste, la ejecución conserva el estado `failed` y sus resultados parciales; no se elige silenciosamente entre los ajustes restantes. El seguimiento utiliza archivos locales y las dependencias existentes, sin servicios externos.

Validación: 18 pruebas aprobadas de MEJ-02/03/04. Las siete nuevas cubren presupuesto, prohibición de E1 en el diseño, redondeo del cupo, desempate por ID, invariancia al orden de filas, probabilidades inválidas y desempates de selección. Black y Ruff aprobaron los archivos nuevos. Todavía no se midió eficacia comercial ni mejora en un periodo independiente.
