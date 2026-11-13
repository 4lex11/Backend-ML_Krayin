# MEJ-06 Aceptación exploratoria

Estado: completada el 29/10/2026. Resultado: conservar v1; no promover el candidato.

Se evalúa exclusivamente el candidato `lightgbm_original_a`, variante sigmoide congelada en MEJ-05. Se ajustó en el entrenamiento de E1 (1081 filas, 678 clientes únicos) y se calibró en diciembre de 2017 (510 clientes). La evaluación E1 incluye 431 clientes al 30/06/2018. No se buscaron nuevos candidatos ni se modificaron umbrales usando los resultados E1.

## Resultados E1

| Modelo o referencia | Precisión al 20 % | AP | Brier |
|---|---:|---:|---:|
| Candidato sigmoide | 0,333333 | 0,275907 | 0,221384 |
| Receta v1 reentrenada | 0,206897 | 0,233332 | 0,221572 |
| Recencia | 0,252874 | 0,255011 | 0,279348 |
| Probabilidad constante del entrenamiento | 0,264368 | 0,234339 | 0,236687 |
| Artefacto v1 instalado | 0,172414 | 0,211924 | 0,196703 |

Se seleccionan 87 clientes mediante `ceil(0,20 × 431)`, con desempate por Customer ID. El candidato acierta 29 abandonos en ese grupo. El top-20 % es una política relativa de evaluación, no los umbrales Alto/Medio/Bajo existentes del CRM. La referencia constante no ordena riesgo: su precisión depende del desempate por ID.

## Decisión

**Conservar v1. No autorizar MEJ-07 en esta ronda.** El candidato mejora las métricas de priorización de E1 frente a las referencias, pero su Brier 0,221384 excede al del artefacto instalado 0,196703 en aproximadamente 0,024680. La tolerancia fijada antes del experimento era 0,01. Una mejora de precisión no sustituye el requisito de calidad de las probabilidades mostradas al usuario.

No se cambian las tolerancias después de observar E1. La prueba es exploratoria porque ese periodo ya fue analizado durante v1; no constituye validación independiente ni acredita impacto en fidelización. El modelo, API y panel siguen usando v1. Conservarlo es una decisión de control de versiones, no una afirmación de utilidad predictiva suficiente del modelo anterior.

En la media no ponderada de D1/D2/E1, la precisión al 20 % del candidato es 45,66 %, frente a 37,55 % de recencia y 34,97 % de la receta v1. La AP media es 0,397548 frente a 0,361635 y 0,351515. Sin embargo, el Brier medio 0,252908 supera el de la probabilidad constante 0,241619 en 0,011289; también falla este criterio, cuya tolerancia era 0,01.

## Reproducción y evidencias

```powershell
& .\.venv-clean\Scripts\python.exe -m ML.acceptance_v2 --output docs/evidencias_mej06/nueva-aceptacion
```

El destino debe ser nuevo. La entrega está en `docs/evidencias_mej06/aceptacion/`: predicciones por cliente/corte de los comparadores y candidato, ajustes E1, métricas, umbrales derivados únicamente de calibración, decisión por criterio, intervalos bootstrap y manifiesto de integridad. Se verificaron hashes de MEJ-03/04/05 antes de usar los resultados y se comprobó que el modelo vigente permaneciera intacto.

La incertidumbre utiliza 1000 remuestreos pareados con semilla 42, muestreando clientes de la unión de D1/D2/E1. Cada cliente seleccionado conserva todos sus cortes; el mismo remuestreo se aplica a candidato, recencia y receta v1. Se recalculan ranking y cupo dentro de cada réplica. Réplicas con un corte de una sola clase se descartan y se informa su cantidad; no se emite intervalo si quedan menos del 90 %. Los intervalos no corrigen la selección previa del candidato y son descriptivos.

Validación del código: 15 pruebas aprobadas de MEJ-04/05/06, incluidas invariancia de diferencias pareadas con predicciones idénticas, reproducibilidad por semilla y rechazo de promoción cuando falla un criterio. Black y Ruff aprobaron los archivos nuevos. El siguiente trabajo aplicable es MEJ-08: incorporar los resultados y límites a la investigación.

## Incertidumbre final

Las 1000 réplicas fueron válidas. El intervalo descriptivo del 95 % para la mejora media de precisión al 20 % fue [0,002337; 0,157118] frente a recencia y [0,014615; 0,185326] frente a la receta v1. Ambos superan cero, pero el primero apenas lo hace. Para AP, los intervalos fueron [−0,008903; 0,081794] y [−0,009032; 0,101318], respectivamente: incluyen cero y no respaldan una mejora concluyente de AP.

El acta automatizada `decision.json` registra 16 comprobaciones favorables y dos desfavorables: `brier_constant` y `E1_brier_installed`. La decisión es `retain_v1`, con `accepted=false`. MEJ-07 no aplica en esta ronda; queda pendiente MEJ-08. Los intervalos y el resultado negativo se conservan sin ajustar retrospectivamente los criterios.
