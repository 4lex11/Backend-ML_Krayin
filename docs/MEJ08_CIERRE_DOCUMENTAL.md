> Actualización 30/10/2026: la tesis tiene 42 páginas tras reorganizar los capítulos 3 y 4. El registro de cierre siguiente conserva la paginación de su entrega original; para las capturas actuales usar [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md).

# MEJ-08 — Cierre documental

29/10/2026. Completada dentro del alcance del dataset Superstore Sales y el prototipo local.

Se actualizó [la tesis](../InvestigacionTesis2026.docx), conservando la [copia anterior](historico/InvestigacionTesis2026_antes_MEJ08.docx). La conclusión del capítulo 6 distingue el modelo instalado de la ronda experimental. El anexo B describe las 18 configuraciones, las 11 variables nuevas, la calibración, los umbrales y la aceptación del único candidato congelado. Las variables temporales no integraron la configuración ganadora.

En E1, el candidato identifica 29 abandonos entre 87 clientes prioritarios: precisión de 33,33 %, frente a 25,29 % de recencia y 17,24 % del artefacto instalado. Esta mejora de priorización no acredita probabilidades fiables: el Brier medio supera al constante en 0,011289 y el Brier E1 supera a v1 instalado en 0,024680, ambos por encima de la tolerancia de 0,01. Se conserva v1; MEJ-07 no aplica en esta ronda. Los intervalos de AP incluyen cero y E1 no es una prueba independiente, pues esos periodos ya se habían estudiado.

## Archivos y páginas para capturas

| Contenido | Archivo | Página de la tesis |
|---|---|---|
| Conclusión actualizada | InvestigacionTesis2026.docx, capítulo 6 | 15 |
| Diseño, comparación y calibración | [MEJ04](MEJ04_COMPARACION_MODELOS.md), [MEJ05](MEJ05_CALIBRACION_UMBRALES.md) | 18 |
| Métricas finales | [metrics.json](evidencias_mej06/aceptacion/metrics.json), bloque E1 | 19 |
| Incertidumbre y decisión | [bootstrap.json](evidencias_mej06/aceptacion/bootstrap.json), [decision.json](evidencias_mej06/aceptacion/decision.json), [acta](MEJ06_ACEPTACION.md) | 19 |

La exportación de Word tiene 28 páginas. Se inspeccionaron visualmente las páginas 15, 18 y 19, sin cortes ni desbordamientos; las otras 16 son idénticas píxel a píxel a la exportación previamente revisada. Evidencia interna: `.local/docqa/mej08/page-01.png` a `page-19.png`. La [auditoría](REVISION_COHERENCIA.json) contrasta cifras y referencias; no sustituye la inspección visual.

MEJ-08 solo modifica documentación. No reentrena modelos ni cambia API, umbrales o Krayin. Las pruebas de etapas anteriores se mantienen como evidencia histórica, sin atribuirles una nueva ejecución. El plan queda cerrado: MEJ-01 a MEJ-06 y MEJ-08 completadas; MEJ-07 no aplicable. La validación comercial y los datos independientes permanecen fuera del alcance acordado.


Tablas de síntesis añadidas: página 20, tabla B1 (incorporaciones MEJ-01 a MEJ-08); página 21, tablas B2 (v1 frente al candidato), B3 (criterios incumplidos) y B4 (balance de aceptación). Las páginas 18–19 conservan el detalle experimental. Respaldo anterior: `docs/historico/InvestigacionTesis2026_antes_tablas_MEJ.docx`.


Ampliación de variables y mediciones: páginas 22–23, diccionario de las siete variables originales y once temporales; página 24, hiperparámetros; página 25, definición de métricas; página 26, comparación E1 y cupos; página 27, precisión temporal e intervalos bootstrap; página 28, calibración. Gráficas: `docs/evidencias_mej08/graficas/`. Se conserva `docs/historico/InvestigacionTesis2026_antes_mediciones_MEJ.docx`.
