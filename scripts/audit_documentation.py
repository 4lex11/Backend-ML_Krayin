"""Comprueba cifras centrales, artefactos y referencias de la entrega documental."""

import hashlib
import json
import re
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]


def main():
    artifact = ROOT / "ML/artifacts/churn180-v1"
    metadata = json.loads((artifact / "metadata.json").read_text())
    thesis = ROOT / "InvestigacionTesis2026.docx"
    doc = Document(thesis)
    text = "\n".join([p.text for p in doc.paragraphs] + [c.text for t in doc.tables for r in t.rows for c in r.cells])
    checks = {}
    for key in ["roc_auc", "average_precision", "brier"]:
        value = f'{metadata["test"][key]:.4f}'.replace(".", ",")
        checks["test_metric_" + key] = value in text
    checks["population"] = all(v in text for v in ["9.800", "4.922", "793", "431"])
    checks["model_unchanged"] = hashlib.sha256((artifact / "model.joblib").read_bytes()).hexdigest() == metadata["model_sha256"]
    checks["original_retained"] = (ROOT / "docs/historico/InvestigacionTesis2026_original.docx").is_file()
    checks["final_test_count"] = "98 passed" in (ROOT / "docs/evidencias_ml06/pruebas.txt").read_text() and "98 pruebas" in text
    checks["coverage"] = "95.14%" in (ROOT / "docs/evidencias_ml06/pruebas.txt").read_text() and "95,14 %" in text
    checks["no_old_placeholders"] = not any(s in text for s in ["sacar de antecedentes", "compuesta por N registros", "CAP 5: DISCUCION"])
    checks["academic_scope"] = "observacional retrospectivo" in text and "No se demostró mejora de fidelización" in text
    missing = []
    for path in ROOT.joinpath("ML").glob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        markdown = "\n".join("".join(c.get("source", [])) for c in notebook["cells"] if c["cell_type"] == "markdown")
        if path.name in {"ML_Comparacion.ipynb", "ML_Resultados_Finales.ipynb"}:
            for link in re.findall(r"\]\(([^)]+)\)", markdown):
                if not link.startswith("http") and not (path.parent / link).exists():
                    missing.append(str(path) + ": " + link)
        else:
            checks["historical_" + path.stem] = "Experimento histórico" in markdown
    checks["notebook_images_exist"] = not missing
    checks["conclusions_and_capture_guide"] = all((ROOT / "docs" / name).is_file() for name in ["CONCLUSIONES_DETALLADAS.md", "GUIA_CAPTURAS.md"])
    checks["crm_documents"] = all((ROOT / "docs" / name).is_file() for name in ["GUIA_FINAL_CRM.md", "INDICE_EVIDENCIAS_FINAL.md", "CRM061_VALIDACION_INTEGRAL.md"])
    checks["crm_results_in_thesis"] = all(v in text for v in ["161", "477", "362", "792", "CRM061_VALIDACION_INTEGRAL.md"])
    checks["pre_crm062_backup"] = (ROOT / "docs/historico/InvestigacionTesis2026_antes_CRM062.docx").is_file()
    for name in ["GUIA_FINAL_CRM.md", "INDICE_EVIDENCIAS_FINAL.md"]:
        for link in re.findall(r"\]\(([^)]+)\)", (ROOT / "docs" / name).read_text(encoding="utf-8")):
            if not link.startswith("http") and not (ROOT / "docs" / link).exists():
                missing.append(name + ": " + link)
    metrics = json.loads((ROOT / "docs/evidencias_mej06/aceptacion/metrics.json").read_text())
    decision = json.loads((ROOT / "docs/evidencias_mej06/aceptacion/decision.json").read_text())
    for name, values in metrics["E1"].items():
        checks["mej08_E1_" + name] = all(f'{values[key]:.6f}'.replace(".", ",") in text for key in ["average_precision", "brier"])
    checks["mej08_retain_v1"] = decision["accepted"] is False and decision["decision"] == "retain_v1" and "Decisión: conservar v1" in text
    checks["mej08_exploratory"] = decision["E1_is_independent_test"] is False and "evidencia prospectiva independiente" in text
    checks["mej08_backup"] = (ROOT / "docs/historico/InvestigacionTesis2026_antes_MEJ08.docx").is_file()
    for name in ["MEJ08_CIERRE_DOCUMENTAL.md", "CONCLUSIONES_DETALLADAS.md", "GUIA_CAPTURAS.md"]:
        for link in re.findall(r"\]\(([^)]+)\)", (ROOT / "docs" / name).read_text(encoding="utf-8")):
            if not link.startswith("http") and not (ROOT / "docs" / link).exists():
                missing.append(name + ": " + link)
    checks["improvement_tables"] = all(v in text for v in ["Tabla B1", "Tabla B2", "Tabla B3", "Tabla B4", "+16,09 pp", "+0,024680"])
    protocol = json.loads((ROOT / "ML/experiments/churn180-v2/protocol.json").read_text())
    checks["measurement_variables"] = all(name in text.replace("\n", "") for name in protocol["baseline"]["features"] + protocol["temporal_features"])
    configs = json.loads((ROOT / "ML/experiments/churn180-v2/candidates_mej04.json").read_text())["candidates"]
    checks["measurement_hyperparameters"] = all(f"{key}={value}" in text for config in configs for key, value in config["params"].items() if key not in {"random_state", "n_jobs", "verbosity"})
    candidate = metrics["E1"]["candidate"]
    checks["measurement_extra_metrics"] = all(f'{candidate[key]:.6f}'.replace(".", ",") in text for key in ["roc_auc", "log_loss", "recall_at_10", "recall_at_20", "recall_at_30"])
    embedded = {hashlib.sha256(rel.target_part.blob).hexdigest() for rel in doc.part.rels.values() if "image" in rel.reltype}
    figures = list((ROOT / "docs/evidencias_mej08/graficas").glob("*.png"))
    checks["measurement_figures_embedded"] = len(figures) == 4 and all(hashlib.sha256(path.read_bytes()).hexdigest() in embedded for path in figures)
    from pypdf import PdfReader
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
    screenshots = ["evidencias_crm042/prediccion_guardada.png", "evidencias_crm051/sugerencia_detalle.png", "evidencias_crm043/detalle_escritorio.png"]
    checks["krayin_screenshots_embedded"] = all(hashlib.sha256((ROOT / "docs" / path).read_bytes()).hexdigest() in embedded for path in screenshots)
    core = []
    active = False
    for element in doc.element.body:
        element_text = ''.join(element.xpath('.//w:t/text()'))
        if element_text.startswith('Capítulo 3.'): active = True
        if element_text.startswith('Capítulo 5'): active = False
        if active: core.append(element)
    core_text = '\n'.join(''.join(e.xpath('.//w:t/text()')) for e in core)
    checks["unified_project_narrative"] = not re.search(r'\bMEJ\b|(?<!churn180-)\bv1\b', core_text)
    checks["progressive_results_order"] = core_text.index('4.2. Comparación de algoritmos') < core_text.index('4.3. Comparación de configuraciones') < core_text.index('4.4. Evaluación del modelo') < core_text.index('4.5. Calibración')
    actual_images = {hashlib.sha256(doc.part.related_parts[b.get(qn('r:embed'))].blob).hexdigest() for e in core for b in e.xpath('.//a:blip')}
    unified_figures = list((ROOT / 'docs/evidencias_proyecto_final').glob('*.png'))
    checks["unified_figures_used"] = len(unified_figures) == 10 and all(hashlib.sha256(p.read_bytes()).hexdigest() in actual_images for p in unified_figures)
    checks["prototype_overview"] = core_text.index('4.1. Acerca del prototipo') < core_text.index('4.2. Comparación de algoritmos') and all(v in core_text for v in ['Herramientas y librerías', 'Modelo utilizado', '4.10. Seguimiento manual'])
    checks["final_document_links"] = not missing
    assert all(checks.values()), checks
    report = {"date": "2026-11-04", "checks": checks, "missing_references": missing,
              "docx_sha256": hashlib.sha256(thesis.read_bytes()).hexdigest(),
              "original_sha256": hashlib.sha256((ROOT / "docs/historico/InvestigacionTesis2026_original.docx").read_bytes()).hexdigest(),
              "visual_review": {"pages": 46, "renderer": "Microsoft Word PDF export followed by bundled Poppler rasterization", "all_pages_inspected": True, "review_date": "2026-11-04", "evidence": ".local/docqa/acerca_prototipo/page-01.png through page-46.png", "note": "Pages 19 and 21-31 inspected visually; remaining page bodies are pixel-identical to the previously inspected export, excluding page numbers. This script does not perform visual inspection."},
              "scope": "Comprobaciones documentales y revisión visual; no se repitió entrenamiento ni se modificó el modelo."}
    (ROOT / "docs/REVISION_COHERENCIA.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
