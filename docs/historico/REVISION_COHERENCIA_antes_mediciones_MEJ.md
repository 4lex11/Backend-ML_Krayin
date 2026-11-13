# Revisión de cierre documental — MEJ-08

Actualización MEJ-08: tesis de **21 páginas**, conclusión revisada en la 15 y anexo B en las 18–19. La auditoría actual aprobó **30 comprobaciones**, con cero referencias faltantes; incluye AP y Brier de las cinco alternativas E1, decisión de conservar v1 y carácter exploratorio. Resultado vigente: [REVISION_COHERENCIA.json](REVISION_COHERENCIA.json).

Las páginas 1–14 y 16–17 son idénticas píxel a píxel a la exportación anterior. Se inspeccionaron las páginas 15, 18 y 19, sin cortes ni desbordamientos. Exportación de Word y rasterización de Poppler en `.local/docqa/mej08/`. El script registra la inspección visual, pero no la realiza. Respaldo: `docs/historico/InvestigacionTesis2026_antes_MEJ08.docx`.

MEJ-01 a MEJ-06 y MEJ-08 completadas; MEJ-07 no aplica. El candidato mejora la priorización, pero incumple dos criterios de Brier; se conserva v1. En esta tarea documental no se reentrenó ni se repitieron pruebas de modelos o CRM. Detalle y capturas: [MEJ08_CIERRE_DOCUMENTAL.md](MEJ08_CIERRE_DOCUMENTAL.md).

## Registro histórico de CRM-06.2 y recomendaciones

El texto siguiente describe la revisión anterior de 17 páginas y sus 21 comprobaciones, conservada también en `docs/historico/REVISION_COHERENCIA_antes_MEJ08.json`; sus conteos no corresponden a la entrega actual.

29 de octubre de 2026. CRM-06.2 completada para el dataset Superstore Sales y la integración local con Krayin.

Se actualizó `InvestigacionTesis2026.docx` conservando portada, estructura académica y resultados del modelo. Se incorporaron aceptación integral, panel y seguimiento manual, y se corrigieron las referencias que presentaban la integración como futura. La copia previa está en `docs/historico/InvestigacionTesis2026_antes_CRM062.docx`; el borrador original también se conserva.

La exportación de Microsoft Word generó **17 páginas**, rasterizadas con Poppler y revisadas visualmente una por una: no se observaron textos cortados, tablas fuera de margen ni figuras superpuestas. LibreOffice no está instalado, por lo que se utilizó Word en segundo plano. Los archivos internos de revisión están en `.local/docqa/recomendaciones/`.

La auditoría `scripts/audit_documentation.py` aprobó **21 comprobaciones**, con cero referencias faltantes en las guías finales y notebooks verificados. Cotejó métricas con el artefacto, población, conservación del modelo y respaldos, cifras de aceptación y presencia de documentos. Resultado reproducible y huellas: [REVISION_COHERENCIA.json](REVISION_COHERENCIA.json). La inspección visual fue manual; el script registra su resultado y no sustituye esa inspección.

Entregables: [guía final de instalación y operación](GUIA_FINAL_CRM.md), [índice de evidencias y capturas](INDICE_EVIDENCIAS_FINAL.md), [conclusiones](CONCLUSIONES_DETALLADAS.md) y [lista actualizada](PLAN_INTEGRACION_KRAYIN.md).

Se reutilizó la evidencia de CRM-06.1: 161 casos PHP, 477 aserciones y 98 casos Python; no se volvió a entrenar ni a medir cobertura en esta tarea documental. La cobertura histórica de 95,14 % corresponde a ML-06. El lote de 793 clientes produjo 431 resultados coincidentes y 362 no elegibles dentro de una prueba revertida; no quedaron 431 predicciones cargadas. El estado final de aceptación conserva una predicción original, sin cuentas ni revisiones temporales de QA.

No quedan tareas pendientes de CRM-01 a CRM-06 dentro del alcance local acordado. El modelo sigue siendo experimental: la integración técnica no demuestra fidelización, rentabilidad ni eficacia de las sugerencias. La producción externa y la validación comercial no forman parte de este cierre.

Actualización solicitada: se añadió una página de recomendaciones derivadas de los resultados. Las páginas 1–15 son idénticas píxel a píxel a la versión ya revisada; se inspeccionaron visualmente las páginas 15–17 de la nueva exportación. La copia previa se conserva en `docs/historico/InvestigacionTesis2026_antes_recomendaciones.docx`. No cambiaron métricas ni conclusiones.


Tablas de síntesis añadidas: página 20, tabla B1 (incorporaciones MEJ-01 a MEJ-08); página 21, tablas B2 (v1 frente al candidato), B3 (criterios incumplidos) y B4 (balance de aceptación). Las páginas 18–19 conservan el detalle experimental. Respaldo anterior: `docs/historico/InvestigacionTesis2026_antes_tablas_MEJ.docx`.

Revisión de tablas: se inspeccionaron las páginas 19–21 de la exportación final; las páginas 1–18 son idénticas a las previamente revisadas. Evidencia vigente: `.local/docqa/tablas_mej/`. El exceso Brier E1 se presenta como 0,024680, calculado antes de redondear las métricas; la resta de los valores ya redondeados daba 0,024681. Esta corrección no altera la decisión.
