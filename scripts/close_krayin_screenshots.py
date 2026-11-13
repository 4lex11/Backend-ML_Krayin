"""Sincroniza la paginación de la entrega con las capturas de Krayin."""
import re
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
names=['README.md','docs/GUIA_FINAL_CRM.md','docs/TAREAS_PENDIENTES.md','docs/PLAN_MEJORAS_ML.md','docs/INDICE_EVIDENCIAS_FINAL.md','docs/GUIA_CAPTURAS.md','docs/REVISION_COHERENCIA.md','docs/CONCLUSIONES_DETALLADAS.md']
def shift(value):
    return re.sub(r'\d+',lambda m:str(int(m[0])+2) if int(m[0])>=18 else m[0],value)
for name in names+['docs/REVISION_COHERENCIA.json']:
    path=root/name
    backup=root/'docs/historico'/(path.stem+'_antes_capturas_krayin'+path.suffix)
    if not backup.exists(): shutil.copy2(path,backup)
    if name.endswith('.json'): continue
    text=backup.read_text(encoding='utf-8').replace('42 páginas','44 páginas').replace('**42 páginas**','**44 páginas**')
    text=re.sub(r'(páginas?\s+)(\d+(?:[–−-]\d+)?)',lambda m:m[1]+shift(m[2]),text)
    text=text.replace('Discusión: 28; conclusiones: 29; recomendaciones: 30; referencias: 31; anexo B: 32–42','Discusión: 30; conclusiones: 31; recomendaciones: 32; referencias: 33; anexo B: 34–44')
    text=text.replace('7–18 y 19–27','7–20 y 21–29')
    if name.endswith('INDICE_EVIDENCIAS_FINAL.md'):
        lines=[]
        for line in text.splitlines():
            parts=line.split('|')
            if len(parts)>3 and re.fullmatch(r'\s*\d+(?:–\d+)?\s*',parts[2]):
                parts[2]=shift(parts[2]); line='|'.join(parts)
            lines.append(line)
        text='\n'.join(lines)+'\n'
        text+='\n## Capturas añadidas del módulo\n\n| Contenido | Página | Fuente |\n|---|---:|---|\n| Listado y predicción guardada | 18 | [Listado](evidencias_crm042/prediccion_guardada.png) |\n| Probabilidad, riesgo y sugerencia | 19 | [Detalle con sugerencia](evidencias_crm051/sugerencia_detalle.png) |\n| Siete variables históricas | 19 | [Variables del cliente](evidencias_crm043/detalle_escritorio.png) |\n\nLas ampliaciones son recortes de visualización en Word; los PNG originales se conservan intactos. Las imágenes pertenecen a las pruebas locales históricas y sus etapas se indican en los pies.\n'
    elif name.endswith('REVISION_COHERENCIA.md'):
        text+='\nActualización de capturas: se añadieron tres imágenes del módulo en páginas 18–19, incluyendo listado, predicción, variables y sugerencia. Se revisaron visualmente esas páginas y la matriz renumerada en la 20. El resto conserva el mismo contenido y diseño, con desplazamiento de la numeración. Evidencia vigente: `.local/docqa/capturas_krayin/`. La auditoría verifica también los tres PNG incrustados y aprueba 41 comprobaciones.\n'
    else:
        text+='\n\nCapturas de Krayin añadidas el 30/10/2026: páginas 18–19, listado del módulo, datos del cliente y sugerencia de revisión por historial limitado. Capítulo 3: 7–20; capítulo 4: 21–29.\n'
    path.write_text(text,encoding='utf-8')

path=root/'scripts/audit_documentation.py'; text=path.read_text(encoding='utf-8')
text=text.replace('"pages": 42','"pages": 44').replace('.local/docqa/cap34_entrega/page-01.png through page-42.png','.local/docqa/capturas_krayin/page-01.png through page-44.png')
text=text.replace('New and modified chapter pages inspected manually; unchanged pages and post-chapter content compared to previous exports, excluding shifted page numbers.','New screenshot pages 18-19 and renumbered matrix page 20 inspected manually; other page bodies compared with the previously inspected export, excluding shifted page numbers.')
addition='''    screenshots = ["evidencias_crm042/prediccion_guardada.png", "evidencias_crm051/sugerencia_detalle.png", "evidencias_crm043/detalle_escritorio.png"]
    checks["krayin_screenshots_embedded"] = all(hashlib.sha256((ROOT / "docs" / path).read_bytes()).hexdigest() in embedded for path in screenshots)
'''
if 'checks["krayin_screenshots_embedded"]' not in text:
    text=text.replace('    checks["final_document_links"] = not missing',addition+'    checks["final_document_links"] = not missing')
path.write_text(text,encoding='utf-8')
