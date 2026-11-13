"""Sincroniza las guías con las tablas añadidas a la tesis."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
for name in ['REVISION_COHERENCIA.json', 'REVISION_COHERENCIA.md']:
    backup = root / 'docs/historico' / (Path(name).stem + '_antes_tablas_MEJ' + Path(name).suffix)
    if not backup.exists():
        shutil.copy2(root / 'docs' / name, backup)
names = ['README.md', 'docs/GUIA_FINAL_CRM.md', 'docs/INDICE_EVIDENCIAS_FINAL.md', 'docs/GUIA_CAPTURAS.md', 'docs/TAREAS_PENDIENTES.md', 'docs/PLAN_MEJORAS_ML.md', 'docs/MEJ08_CIERRE_DOCUMENTAL.md', 'docs/REVISION_COHERENCIA.md']
for name in names:
    path = root / name
    text = path.read_text(encoding='utf-8').replace('19 páginas', '21 páginas')
    if 'Tablas de síntesis añadidas' not in text:
        text += '\n\nTablas de síntesis añadidas: página 20, tabla B1 (incorporaciones MEJ-01 a MEJ-08); página 21, tablas B2 (v1 frente al candidato), B3 (criterios incumplidos) y B4 (balance de aceptación). Las páginas 18–19 conservan el detalle experimental. Respaldo anterior: `docs/historico/InvestigacionTesis2026_antes_tablas_MEJ.docx`.\n'
    if name == 'docs/REVISION_COHERENCIA.md':
        text = text.replace('**29 comprobaciones**', '**30 comprobaciones**')
        text += '\nRevisión de tablas: se inspeccionaron las páginas 19–21 de la exportación final; las páginas 1–18 son idénticas a las previamente revisadas. Evidencia vigente: `.local/docqa/tablas_mej/`. El exceso Brier E1 se presenta como 0,024680, calculado antes de redondear las métricas; la resta de los valores ya redondeados daba 0,024681. Esta corrección no altera la decisión.\n'
    path.write_text(text, encoding='utf-8')
for name in ['docs/CONCLUSIONES_DETALLADAS.md', 'docs/MEJ08_CIERRE_DOCUMENTAL.md', 'docs/MEJ06_ACEPTACION.md']:
    path = root / name
    text = path.read_text(encoding='utf-8').replace('0,024681', '0,024680')
    path.write_text(text, encoding='utf-8')
path = root / 'scripts/audit_documentation.py'
text = path.read_text(encoding='utf-8').replace('"pages": 19', '"pages": 21').replace('.local/docqa/mej08/page-01.png through page-19.png', '.local/docqa/tablas_mej/page-01.png through page-21.png').replace('Pages 1-14 and 16-17 are pixel-identical to the previously inspected recommendations export; pages 15, 18 and 19 manually inspected for MEJ08.', 'Pages 1-18 are pixel-identical to the previously inspected MEJ08 export; pages 19-21 manually inspected after adding tables.')
text = text.replace('    checks["final_document_links"] = not missing', '    checks["improvement_tables"] = all(v in text for v in ["Tabla B1", "Tabla B2", "Tabla B3", "Tabla B4", "+16,09 pp", "+0,024680"])\n    checks["final_document_links"] = not missing')
path.write_text(text, encoding='utf-8')
