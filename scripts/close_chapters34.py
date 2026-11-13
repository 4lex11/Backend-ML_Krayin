"""Actualiza guías y acta tras reorganizar los capítulos 3 y 4."""
from pathlib import Path
import shutil
import re
import json
import hashlib

root=Path(__file__).resolve().parents[1]
names=['INDICE_EVIDENCIAS_FINAL.md','GUIA_CAPTURAS.md','REVISION_COHERENCIA.md','REVISION_COHERENCIA.json']
for name in names:
    path=root/'docs'/name
    backup=root/'docs/historico'/(path.stem+'_antes_cap34'+path.suffix)
    if not backup.exists(): shutil.copy2(path,backup)

index='''# Índice final de evidencias y capturas

Actualizado el 30/10/2026. Tesis: `InvestigacionTesis2026.docx`, **42 páginas**. La numeración corresponde a la exportación de Word revisada. Los capítulos 3 y 4 siguen la estructura solicitada a partir de `InvestigacionTesis2026Original.pdf`. La versión previa y sus guías se conservan en `docs/historico/`.

| Contenido | Páginas | Archivo fuente o figura para captura |
|---|---:|---|
| Métodos e hiperparámetros con definición | 7 | [Configuraciones MEJ](../ML/experiments/churn180-v2/candidates_mej04.json) |
| Métricas e interpretación | 8 | [Evaluación](../ML/evaluation.py) y [comparación](../ML/compare_v2.py) |
| Diseño del sistema | 9 | [Imagen original](evidencias_cap34/originales/pagina_20_imagen_1.jpg) |
| Fases y comprensión del negocio | 10 | [Imagen original de fases](evidencias_cap34/originales/pagina_21_imagen_1.jpg) |
| Variables derivadas y objetivo | 11–12 | [Originales](../ML/features.py) y [temporales](../ML/features_v2.py) |
| Comprensión de datos | 13 | [Archivo plano original](evidencias_cap34/originales/pagina_23_imagen_1.jpg) y [tabla original](evidencias_cap34/originales/pagina_23_imagen_2.png) |
| Preparación actual | 14 | [Flujo](evidencias_cap34/preparacion_actual.png) y [cortes temporales](evidencias_cap34/cortes_temporales.png) |
| Modelado y configuraciones | 15 | [Manifiesto temporal](evidencias_mej03/preparacion/manifest.json) |
| Evaluación y mejor candidato | 16 | [Comparación por métrica](evidencias_cap34/comparacion_desarrollo.png) y [selección](evidencias_mej04/comparacion/selection.json) |
| Integración y matrices con cupo común | 17 | [Matrices al 20 %](evidencias_cap34/matrices_cupo20.png) |
| Matriz del umbral vigente | 18 | [Matriz v1](evidencias_cap34/matriz_vigente.png) y [metadatos](../ML/artifacts/churn180-v1/metadata.json) |
| Comparación E1 y decisión de uso | 19 | [Gráfica E1](evidencias_mej08/graficas/comparacion_e1.png), [métricas](evidencias_mej06/aceptacion/metrics.json) y [decisión](evidencias_mej06/aceptacion/decision.json) |
| Comparación histórica v1 | 20 | [Gráfica v1](evidencias_cap34/comparacion_v1.png) |
| Dieciocho candidatos MEJ | 21 | [Clasificación completa](evidencias_mej04/comparacion/selection.json) |
| Calibración y criterios incumplidos | 22 | [Gráfica](evidencias_mej08/graficas/calibracion_desarrollo.png) y [conteos](evidencias_mej05/calibracion/calibration_bins.json) |
| Variación temporal e incertidumbre | 23 | [Precisión temporal](evidencias_mej08/graficas/precision_temporal.png), [intervalos](evidencias_mej08/graficas/intervalos_bootstrap.png), [bootstrap](evidencias_mej06/aceptacion/bootstrap.json) |
| Cupos y errores | 24 | [Matrices recalculadas](evidencias_cap34/matrices.json) |
| Seguridad, carga y recuperación | 25 | [HTTPS](evidencias_api/07_seguridad_https.json), [carga](evidencias_api/09_carga_https.json), [recuperación](evidencias_api/08_despliegue_reversion.json) |
| Aceptación de la integración | 26 | [Lote HTTPS](evidencias_crm061/aceptacion_https.json), [conciliación](evidencias_crm061/conciliacion_dataset.json), [PHP](evidencias_crm061/regresion_php.txt), [Python](evidencias_crm061/regresion_python.txt) |
| Panel, sugerencias y revisión manual | 27 | [Detalle](evidencias_crm061/detalle_escritorio.png), [revisión](evidencias_crm061/revision_integral.png), [navegador](evidencias_crm061/navegador.json) |
| Discusión y conclusiones | 28–29 | [Conclusiones detalladas](CONCLUSIONES_DETALLADAS.md) |
| Recomendaciones y referencias | 30–31 | Tesis y [auditoría](REVISION_COHERENCIA.json) |
| Anexo B y detalle de mejoras | 32–42 | [Cierre MEJ-08](MEJ08_CIERRE_DOCUMENTAL.md) |

El mejor candidato experimental y el modelo instalado están resaltados en la página 19. Se conserva v1 porque el candidato incumplió dos criterios de Brier. Las gráficas originales de diseño incluyen funciones conceptuales no implementadas; el texto lo aclara sin modificar la imagen.

Las capturas de Krayin son evidencia de QA local, no de campañas. El lote de 793 clientes produjo 431 predicciones y 362 no elegibles durante una prueba revertida. Los resultados del lote no permanecieron cargados; se conservó una predicción original y 792 clientes sin resultado. Las cuentas y notas temporales de QA se eliminaron.

Para capturas nuevas, seguir [la guía de operación](GUIA_FINAL_CRM.md), seleccionar el corte 2018-06-30 y el cliente AA-10315. Una revisión manual guarda un registro real, pero no contacta al cliente. No mostrar credenciales ni presentar los datos históricos como actuales. Véase [la guía de capturas](GUIA_CAPTURAS.md).
'''
(root/'docs/INDICE_EVIDENCIAS_FINAL.md').write_text(index,encoding='utf-8')
guide='''# Guía de capturas para la investigación

30/10/2026. La tesis tiene 42 páginas. El [índice final](INDICE_EVIDENCIAS_FINAL.md) indica la ubicación exacta de cada figura y archivo. Los capítulos 3 y 4 ocupan las páginas 7–18 y 19–27, respectivamente. Discusión: 28; conclusiones: 29; recomendaciones: 30; referencias: 31; anexo B: 32–42.

## Capturas de metodología y resultados

Usar directamente los PNG de `docs/evidencias_cap34/` y `docs/evidencias_mej08/graficas/` para evitar pérdida de resolución. Las cuatro imágenes de `docs/evidencias_cap34/originales/` se extrajeron del PDF indicado por el usuario y se conservaron sin cambios de contenido.

- Páginas 7–8: hiperparámetros y métricas, con definiciones y motivos de uso.
- Páginas 9–10: imágenes originales de diseño y fases.
- Páginas 11–12: variables derivadas; distinguir las siete usadas de las once adicionales evaluadas.
- Página 13: las dos vistas originales del dataset.
- Página 14: preparación y cortes temporales actualizados.
- Páginas 15–16: configuraciones y comparación por métrica.
- Páginas 17–18: matrices con cupo del 20 % y con umbral medio; no intercambiar sus políticas.
- Páginas 19–24: resultados E1, comparación histórica v1, 18 candidatos, calibración, incertidumbre y cupos.
- Páginas 25–27: aceptación técnica y evidencia de la interfaz.

Pies sugeridos: «Comparación exploratoria en el mismo corte y población; mayor precisión no garantiza menores errores probabilísticos», «Matriz de confusión con cupo de 87 clientes; filas observadas y columnas predichas», «Diseño conceptual original; el alcance implementado se especifica en el texto».

## Capturas de Krayin

Abrir el módulo según [GUIA_FINAL_CRM.md](GUIA_FINAL_CRM.md), usar 2018-06-30 y AA-10315. El detalle permite mostrar variables, sugerencia, corte y versión. La captura de [revisión integral](evidencias_crm061/revision_integral.png) muestra responsable, nota, estado, autor y fecha. [Solicitud pendiente](evidencias_crm061/solicitud_pendiente.png) y [completada](evidencias_crm061/solicitud_completada.png) documentan procesamiento y progreso.

Las capturas previas de QA no acreditan contacto ni retención. El lote integral fue revertido y no dejó 431 resultados cargados. Evitar mostrar claves, `.env` o datos personales innecesarios. Las reglas de sugerencia requieren revisión humana y no ejecutan campañas.

Las guías anteriores están preservadas en `docs/historico/GUIA_CAPTURAS_antes_cap34.md` e `INDICE_EVIDENCIAS_FINAL_antes_cap34.md`; su paginación ya no corresponde a la entrega actual.
'''
(root/'docs/GUIA_CAPTURAS.md').write_text(guide,encoding='utf-8')

# Las descripciones generales remiten a un único índice vigente.
for name in ['README.md','docs/GUIA_FINAL_CRM.md','docs/TAREAS_PENDIENTES.md','docs/PLAN_MEJORAS_ML.md']:
    path=root/name; text=path.read_text(encoding='utf-8').replace('28 páginas','42 páginas')
    text=re.sub(r'\n\nTablas de síntesis añadidas:.*?(?=\n\n|\Z)','',text,flags=re.S)
    text=re.sub(r'\n\nAmpliación de variables y mediciones:.*?(?=\n\n|\Z)','',text,flags=re.S)
    text=text.replace('La tesis recoge la conclusión en la página 15, el diseño y la calibración en la 18 y la comparación E1 y decisión en la 19. Las recomendaciones y referencias conservan las páginas 16 y 17.', 'La tesis reorganizada presenta implementación en páginas 7–18, resultados en 19–27, conclusiones en 29 y recomendaciones en 30. El índice de evidencias contiene la paginación vigente.')
    if 'Reestructura de capítulos 3 y 4' not in text:
        link='docs/INDICE_EVIDENCIAS_FINAL.md' if name=='README.md' else 'INDICE_EVIDENCIAS_FINAL.md'
        text+='\n\nReestructura de capítulos 3 y 4 (30/10/2026): metodología en páginas 7–18 y resultados en 19–27, con las cuatro imágenes originales indicadas. Ubicaciones y archivos para capturas: [índice vigente]('+link+').\n'
    path.write_text(text,encoding='utf-8')

path=root/'docs/CONCLUSIONES_DETALLADAS.md'
text=path.read_text(encoding='utf-8').replace('páginas 18–19','páginas 32–33').replace('tesis, página 19','tesis, página 33')
path.write_text(text,encoding='utf-8')
path=root/'docs/MEJ08_CIERRE_DOCUMENTAL.md'
text=path.read_text(encoding='utf-8')
note='> Actualización 30/10/2026: la tesis tiene 42 páginas tras reorganizar los capítulos 3 y 4. El registro de cierre siguiente conserva la paginación de su entrega original; para las capturas actuales usar [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md).\n\n'
if not text.startswith('> Actualización 30/10/2026'): text=note+text
path.write_text(text,encoding='utf-8')

review='''# Revisión de capítulos 3 y 4

30/10/2026. La tesis actualizada tiene **42 páginas**. Se preservó el documento anterior en `docs/historico/InvestigacionTesis2026_antes_reestructura_cap34.docx`.

El capítulo 3 mantiene 3.1 Métodos propuestos, 3.2 Diseño del sistema y 3.3 Fases de implementación, con las seis fases solicitadas. Incluye definiciones de hiperparámetros y métricas, variables, preparación temporal, modelado, comparación y matrices. El capítulo 4 presenta resultados E1, comparación histórica v1, 18 candidatos MEJ, calibración, incertidumbre, cupos y aceptación técnica.

Se conservaron las cuatro imágenes extraídas del PDF `docs/historico/InvestigacionTesis2026Original.pdf`: diseño, fases y dos vistas del dataset. El texto aclara el carácter conceptual de K-Means y acciones automáticas que aparecen en la imagen pero no están implementadas. Las figuras de preparación, comparación y matrices se regeneraron desde evidencia local. No se entrenó ni sustituyó el modelo.

Se inspeccionaron visualmente las páginas nuevas y modificadas. Las páginas 1–6 permanecen iguales a la entrega anterior; el contenido posterior al capítulo 4 se contrasta con la exportación anterior, excluyendo únicamente la numeración del pie. Se corrigieron una nota que quedaba aislada y un encabezado que dividía una palabra. Exportación final Word y Poppler: `.local/docqa/cap34_entrega/`.

La auditoría contrasta las métricas, hiperparámetros, variables y figuras con la evidencia. Comprueba también las imágenes originales, las seis fases, las 18 filas de comparación, las matrices recalculadas y el respaldo previo. Resultado y huella del documento: [REVISION_COHERENCIA.json](REVISION_COHERENCIA.json). La inspección visual es manual; el script no la sustituye.

El candidato mejora la priorización, pero incumple dos criterios de Brier. Se conserva v1 y no se presentan campañas ni eficacia comercial. Las pruebas técnicas citadas pertenecen a sus ejecuciones históricas; no fueron repetidas para esta edición. Capturas y páginas: [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md).
'''
(root/'docs/REVISION_COHERENCIA.md').write_text(review,encoding='utf-8')

path=root/'scripts/audit_documentation.py'; text=path.read_text(encoding='utf-8')
text=text.replace('"date": "2026-10-29"','"date": "2026-10-30"').replace('"review_date": "2026-10-29"','"review_date": "2026-10-30"').replace('"pages": 28','"pages": 42').replace('.local/docqa/mediciones_final/page-01.png through page-28.png','.local/docqa/cap34_entrega/page-01.png through page-42.png')
text=text.replace('Pages 1-21 are pixel-identical to the previously inspected tables export; seven new pages inspected, with final body identity checked after removing a blank page and reinspection of the wrapped variable name.','New and modified chapter pages inspected manually; unchanged pages and post-chapter content compared to previous exports, excluding shifted page numbers.')
addition='''    from pypdf import PdfReader
    from docx.oxml.ns import qn
    structure = ["3.1. Métodos propuestos", "3.2. Diseño del sistema", "3.3. Fases de implementación del proyecto", "Fase 1: Comprensión del Negocio", "Fase 2: Comprensión de Datos", "Fase 3: Preparación de los Datos", "Fase 4: Modelado", "Fase 5: Evaluación", "Fase 6: Despliegue e Integración CRM"]
    chapter_text = text.split("Capítulo 3. Metodología De La Implementación", 1)[1].split("Capítulo 4. Resultados", 1)[0]
    checks["cap34_structure"] = all(s in chapter_text for s in structure)
    pdf = PdfReader(ROOT / "docs/historico/InvestigacionTesis2026Original.pdf")
    original_images = [im.data for i in [19, 20, 22] for im in pdf.pages[i].images]
    checks["cap34_original_images"] = len(original_images) == 4 and all(hashlib.sha256(blob).hexdigest() in embedded for blob in original_images)
    new_figures = list((ROOT / "docs/evidencias_cap34").glob("*.png"))
    checks["cap34_new_figures"] = len(new_figures) == 6 and all(hashlib.sha256(path.read_bytes()).hexdigest() in embedded for path in new_figures)
    ranking = json.loads((ROOT / "docs/evidencias_mej04/comparacion/selection.json").read_text())["ranking"]
    comparison = next(t for t in doc.tables if t.rows[0].cells[0].text == "Configuración" and len(t.columns) == 5)
    checks["cap34_all_candidates"] = len(comparison.rows) == 19 and all([cell.text for cell in row.cells] == [r["id"].replace("_", " "), str(r["feature_count"])] + [f'{r[key]:.4f}'.replace(".", ",") for key in ["precision_at_20", "average_precision", "brier"]] for row, r in zip(comparison.rows[1:], ranking))
    import csv
    with (ROOT / "docs/evidencias_mej06/aceptacion/E1_predictions.csv").open() as handle:
        predictions = list(csv.DictReader(handle))
    matrices = json.loads((ROOT / "docs/evidencias_cap34/matrices.json").read_text())
    calculated = {}
    for model in ["installed", "candidate"]:
        ids = {r["Customer ID"] for r in sorted(predictions, key=lambda r: (-float(r[model]), r["Customer ID"]))[:87]}
        cm = [[0, 0], [0, 0]]
        for r in predictions:
            cm[int(r["Churn"])][int(r["Customer ID"] in ids)] += 1
        calculated[model + "_top20"] = cm
    cm = [[0, 0], [0, 0]]
    for r in predictions:
        cm[int(r["Churn"])][int(float(r["installed"]) >= metadata["thresholds"]["medium"])] += 1
    calculated["installed_medium"] = cm
    checks["cap34_confusion_matrices"] = calculated == matrices and cm == metadata["test"]["confusion_matrix"]
    checks["cap34_backup"] = (ROOT / "docs/historico/InvestigacionTesis2026_antes_reestructura_cap34.docx").is_file()
'''
if 'checks["cap34_structure"]' not in text:
    text=text.replace('    checks["final_document_links"] = not missing',addition+'    checks["final_document_links"] = not missing')
path.write_text(text,encoding='utf-8')
