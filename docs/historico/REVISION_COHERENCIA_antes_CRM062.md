# Revisión de cierre documental

28 de octubre de 2026. DOC-01 a DOC-04 completadas para el alcance acordado del dataset y prototipo local.

## Cambios en el documento

Se actualizó `InvestigacionTesis2026.docx` conservando la identidad institucional, autores, asesor y organización de seis capítulos. La copia original se conserva en `docs/historico/InvestigacionTesis2026_original.docx`. Se completaron introducción, objetivos, implementación, resultados, discusión, conclusiones y referencias.

El borrador original contenía capítulos vacíos y un planteamiento cuasiexperimental causal no ejecutado. Se sustituyó por un diseño observacional retrospectivo de evaluación temporal, coherente con los datos. Se eliminaron afirmaciones de disponibilidad de satisfacción y tickets de soporte, una población sin tamaño definido y la suposición de anonimización del CSV. Las referencias del nuevo documento corresponden a la fuente del dataset y documentación metodológica utilizada; la bibliografía anterior se conserva en el original, sin presentarla como evidencia de una intervención realizada.

## Comprobaciones

- Tamaños del corpus y de cada corte contrastados con `metadata.json`.
- Comparación de modelos y métricas de test contrastadas con el artefacto vigente; umbrales y calibración consistentes con ML-06.
- Diferenciación entre average precision, recall, calibración y utilidad comercial.
- Separación entre pruebas históricas de API-07, carga actual de API-06 y regresión posterior de 98 pruebas tras ML-06.
- Figuras de los notebooks vigentes localizables; notebooks anteriores identificados como históricos.
- Referencias a conclusiones y capturas ya disponibles; los modelos y sus hashes no se alteraron.
- DOCX renderizado en 14 páginas y todas revisadas visualmente, con tablas y figuras completas y legibles.

El renderizador habitual no encontró LibreOffice en este Windows. Se utilizó exportación PDF de Microsoft Word en segundo plano y rasterización con Poppler empaquetado, sin instalar otro renderizador ni modificar la aplicación del usuario. Los archivos de revisión visual permanecen en `.local/docqa/render/` y no son entregables adicionales.

Las comprobaciones ejecutables están en `scripts/audit_documentation.py`; el resultado y hashes se conservan en `docs/REVISION_COHERENCIA.json`. Esta revisión no implica aprobación institucional de la tesis ni validación comercial del modelo.

## Estado final

La documentación refleja un prototipo local funcional y un modelo sin utilidad predictiva suficiente demostrada en el test. No afirma mejora causal de fidelización. Krayin, operación externa y evaluación comercial siguen como trabajo futuro; no bloquean el cierre de esta etapa académica.
