from pathlib import Path
import re
import shutil
ROOT=Path(__file__).resolve().parents[1]
for filename in ['INDICE_EVIDENCIAS_FINAL.md','GUIA_CAPTURAS.md','REVISION_COHERENCIA.md']:
    path=ROOT/'docs'/filename
    backup=ROOT/'docs/historico'/filename.replace('.md','_antes_acerca_prototipo.md')
    if not backup.exists(): shutil.copy2(path,backup)
index=ROOT/'docs/INDICE_EVIDENCIAS_FINAL.md'
s=index.read_text(encoding='utf-8').replace('30/10/2026','04/11/2026').replace('**44 páginas**','**46 páginas**')
def shift(m):
    return '| '+re.sub(r'\d+',lambda n:str(int(n[0])+2),m[1])+' |'
s=re.sub(r'\| ((?:2[1-9]|3\d|44)(?:–\d+)?) \|',shift,s)
s=s.replace('página 23. La decisión se explica en la página 24','página 25. La decisión se explica en la página 26')
s=s.replace('| Comparación de algoritmos', '| Acerca del prototipo | 21–22 | [Listado](evidencias_crm042/prediccion_guardada.png), [detalle](evidencias_crm051/sugerencia_detalle.png) y [seguimiento](evidencias_crm061/revision_integral.png) |\n| Comparación de algoritmos')
index.write_text(s,encoding='utf-8')
guide=ROOT/'docs/GUIA_CAPTURAS.md'
s=guide.read_text(encoding='utf-8').replace('30/10/2026. La tesis tiene 44','04/11/2026. La tesis tiene 46')
for a,b in [('21–29','21–31'),('Discusión: 30; conclusiones: 31; recomendaciones: 32; referencias: 33; anexo B: 34–44','Discusión: 32; conclusiones: 33; recomendaciones: 34; referencias: 35; anexo B: 36–46'),('Páginas 21–26:','Páginas 23–28:'),('Páginas 27–29:','Páginas 29–31:')]: s=s.replace(a,b)
s+='\nSección 4.1 Acerca del prototipo, páginas 21–22: listado, detalle con sugerencia, seguimiento manual, modelo utilizado y tecnologías. Figuras 4.1–4.3. Los resultados continúan desde 4.2; el seguimiento técnico es ahora 4.10.\n'
guide.write_text(s,encoding='utf-8')
(ROOT/'docs/REVISION_COHERENCIA.md').write_text('''# Revisión documental

04/11/2026. Tesis de 46 páginas. Se incorporó 4.1 Acerca del prototipo en las páginas 21–22, con tres capturas reales del módulo, explicación del modelo utilizado y tabla de herramientas y librerías. Se renumeraron las secciones posteriores hasta 4.10 y las figuras hasta 4.10. El texto mantiene la distinción entre mayor AP inicial, mejor precisión por cupo y modelo efectivamente integrado.

Las tecnologías se contrastaron con los requirements de Python, composer.json de Krayin y las versiones registradas en la aceptación local. Las capturas documentan pruebas históricas, no campañas. Se conservaron las métricas, el modelo y todas las imágenes anteriores.

Se revisaron visualmente las páginas 19 y 21–31. Las demás conservan el cuerpo de la exportación anterior píxel a píxel, descontando los números de página. La sección nueva ocupa dos páginas completas, sin un pie de tabla aislado. Evidencia Word/Poppler: `.local/docqa/acerca_prototipo/`. La auditoría documental se registra en [REVISION_COHERENCIA.json](REVISION_COHERENCIA.json).

Respaldo previo: `docs/historico/InvestigacionTesis2026_antes_acerca_prototipo.docx`. Capturas y páginas actualizadas: [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md).
''',encoding='utf-8')
p=ROOT/'scripts/audit_documentation.py';s=p.read_text(encoding='utf-8')
for a,b in [('4.1. Comparación de algoritmos','4.2. Comparación de algoritmos'),('4.2. Comparación de configuraciones','4.3. Comparación de configuraciones'),('4.3. Evaluación del modelo','4.4. Evaluación del modelo'),('4.4. Calibración','4.5. Calibración')]:s=s.replace(a,b)
s=s.replace('"date": "2026-10-30"','"date": "2026-11-04"').replace('"pages": 44','"pages": 46').replace('"review_date": "2026-10-30"','"review_date": "2026-11-04"')
s=s.replace('.local/docqa/proyecto_final/page-01.png through page-44.png','.local/docqa/acerca_prototipo/page-01.png through page-46.png')
s=s.replace('Changed pages 7-18 and 20-27 inspected visually; pages 1-6, 19, 28-44 are pixel-identical to the previously inspected export.','Pages 19 and 21-31 inspected visually; remaining page bodies are pixel-identical to the previously inspected export, excluding page numbers.')
s=s.replace('    checks["final_document_links"]', '''    checks["prototype_overview"] = core_text.index('4.1. Acerca del prototipo') < core_text.index('4.2. Comparación de algoritmos') and all(v in core_text for v in ['Herramientas y librerías', 'Modelo utilizado', '4.10. Seguimiento manual'])
    checks["final_document_links"]''')
p.write_text(s,encoding='utf-8')
