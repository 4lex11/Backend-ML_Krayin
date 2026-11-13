"""Sincroniza índice y auditoría con las mediciones añadidas a la tesis."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
for name in ['REVISION_COHERENCIA.json', 'REVISION_COHERENCIA.md']:
    backup = root / 'docs/historico' / (Path(name).stem + '_antes_mediciones_MEJ' + Path(name).suffix)
    if not backup.exists():
        shutil.copy2(root / 'docs' / name, backup)
for name in ['README.md', 'docs/GUIA_FINAL_CRM.md', 'docs/INDICE_EVIDENCIAS_FINAL.md', 'docs/GUIA_CAPTURAS.md', 'docs/TAREAS_PENDIENTES.md', 'docs/PLAN_MEJORAS_ML.md', 'docs/MEJ08_CIERRE_DOCUMENTAL.md', 'docs/REVISION_COHERENCIA.md']:
    path = root / name
    text = path.read_text(encoding='utf-8').replace('21 páginas', '28 páginas')
    if 'Ampliación de variables y mediciones' not in text:
        text += '\n\nAmpliación de variables y mediciones: páginas 22–23, diccionario de las siete variables originales y once temporales; página 24, hiperparámetros; página 25, definición de métricas; página 26, comparación E1 y cupos; página 27, precisión temporal e intervalos bootstrap; página 28, calibración. Gráficas: `docs/evidencias_mej08/graficas/`. Se conserva `docs/historico/InvestigacionTesis2026_antes_mediciones_MEJ.docx`.\n'
    if name == 'docs/REVISION_COHERENCIA.md':
        text = text.replace('**30 comprobaciones**', '**34 comprobaciones**')
        text += '\nRevisión vigente de mediciones: exportación Word de 28 páginas en `.local/docqa/mediciones_final/`. Las páginas 1–21 son idénticas a la versión previamente revisada. Se inspeccionaron las siete páginas nuevas y se corrigió un salto que generaba una página vacía. La auditoría verifica variables, parámetros explícitos, métricas adicionales e imágenes incrustadas contra los PNG generados. No se reentrenaron modelos.\n'
    path.write_text(text, encoding='utf-8')
path = root / 'scripts/audit_documentation.py'
text = path.read_text(encoding='utf-8').replace('"pages": 21', '"pages": 28').replace('.local/docqa/tablas_mej/page-01.png through page-21.png', '.local/docqa/mediciones_final/page-01.png through page-28.png').replace('Pages 1-18 are pixel-identical to the previously inspected MEJ08 export; pages 19-21 manually inspected after adding tables.', 'Pages 1-21 are pixel-identical to the previously inspected tables export; seven new pages inspected, with final body identity checked after removing a blank page and reinspection of the wrapped variable name.')
addition = '''    protocol = json.loads((ROOT / "ML/experiments/churn180-v2/protocol.json").read_text())
    checks["measurement_variables"] = all(name in text.replace("\\n", "") for name in protocol["baseline"]["features"] + protocol["temporal_features"])
    configs = json.loads((ROOT / "ML/experiments/churn180-v2/candidates_mej04.json").read_text())["candidates"]
    checks["measurement_hyperparameters"] = all(f"{key}={value}" in text for config in configs for key, value in config["params"].items() if key not in {"random_state", "n_jobs", "verbosity"})
    candidate = metrics["E1"]["candidate"]
    checks["measurement_extra_metrics"] = all(f'{candidate[key]:.6f}'.replace(".", ",") in text for key in ["roc_auc", "log_loss", "recall_at_10", "recall_at_20", "recall_at_30"])
    embedded = {hashlib.sha256(rel.target_part.blob).hexdigest() for rel in doc.part.rels.values() if "image" in rel.reltype}
    figures = list((ROOT / "docs/evidencias_mej08/graficas").glob("*.png"))
    checks["measurement_figures_embedded"] = len(figures) == 4 and all(hashlib.sha256(path.read_bytes()).hexdigest() in embedded for path in figures)
'''
if 'checks["measurement_variables"]' not in text:
    text = text.replace('    checks["final_document_links"] = not missing', addition + '    checks["final_document_links"] = not missing')
path.write_text(text, encoding='utf-8')
