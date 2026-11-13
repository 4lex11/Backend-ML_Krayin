"""Añade tablas de síntesis basadas en las evidencias MEJ existentes."""
import json
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / 'InvestigacionTesis2026.docx'
backup = ROOT / 'docs/historico/InvestigacionTesis2026_antes_tablas_MEJ.docx'
if not backup.exists():
    shutil.copy2(target, backup)
doc = Document(backup)
for paragraph in doc.paragraphs:
    if '0,024681' in paragraph.text:
        for run in paragraph.runs:
            run.text = run.text.replace('0,024681', '0,024680')
metrics = json.loads((ROOT / 'docs/evidencias_mej06/aceptacion/metrics.json').read_text())

def p(text, style='Normal'):
    paragraph = doc.add_paragraph(text, style)
    if style.startswith('Heading'):
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
    return paragraph

def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for col, width in zip(t.columns, widths):
        col.width = Inches(width)
    for i, values in enumerate([headers] + rows):
        row = t.rows[0] if i == 0 else t.add_row()
        trpr = row._tr.get_or_add_trPr()
        no_split = OxmlElement('w:cantSplit')
        trpr.append(no_split)
        if i == 0:
            trpr.append(OxmlElement('w:tblHeader'))
        for j, (cell, value) in enumerate(zip(row.cells, values)):
            cell.width = Inches(widths[j])
            cell.text = str(value)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr = cell._tc.get_or_add_tcPr()
            shading = OxmlElement('w:shd')
            shading.set(qn('w:fill'), 'E7E6E6' if i == 0 else 'FFFFFF')
            pr.append(shading)
            margins = OxmlElement('w:tcMar')
            for edge in ['top', 'left', 'bottom', 'right']:
                el = OxmlElement('w:' + edge)
                el.set(qn('w:w'), '85')
                el.set(qn('w:type'), 'dxa')
                margins.append(el)
            pr.append(margins)
            borders = OxmlElement('w:tcBorders')
            for edge in ['top', 'left', 'bottom', 'right']:
                el = OxmlElement('w:' + edge)
                for key, val in [('val', 'single'), ('sz', '6'), ('color', 'D9D9D9')]:
                    el.set(qn('w:' + key), val)
                borders.append(el)
            pr.append(borders)
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                para.paragraph_format.space_after = Pt(2)
                para.paragraph_format.space_before = Pt(2)
                para.paragraph_format.line_spacing = 1.05
                for run in para.runs:
                    run.font.size = Pt(11)
                    run.bold = i == 0
    p('')
    return t

doc.add_page_break()
p('Síntesis de incorporaciones al proyecto', 'Heading 1')
p('B3 Componentes y alcance de la mejora', 'Heading 2')
p('Las tablas siguientes reúnen los cambios de la ronda MEJ y sus resultados. Se distingue lo implementado para experimentar de lo incorporado al sistema en uso. La decisión final conserva v1.')
p('Tabla B1 Incorporaciones y estado final', 'Heading 3')
table(['Etapa', 'Elemento añadido', 'Resultado o estado'], [
    ['MEJ-01', 'Protocolo con cortes, métricas y criterios de aceptación.', 'Completado; criterios fijados antes de comparar.'],
    ['MEJ-02', '11 variables temporales; ventanas de compras, ventas e intervalos.', 'Implementadas y verificadas; no integran el candidato ganador.'],
    ['MEJ-03', 'Preparación temporal D1, D2 y E1 con población común y huellas.', 'Nueve CSV; controles de integridad y ausencia de datos futuros.'],
    ['MEJ-04', '18 configuraciones de tres familias y tres conjuntos de variables.', 'Seleccionado lightgbm_original_a, con las siete variables originales.'],
    ['MEJ-05', 'Comparación crudo/sigmoide y cupos del 10 %, 20 % y 30 %.', 'Política congelada; 10 de 12 casos de umbral compatibles.'],
    ['MEJ-06', 'Evaluación E1 y 1000 remuestreos pareados por cliente.', '16 criterios favorables y dos desfavorables; no promover.'],
    ['MEJ-07', 'Integración condicionada a la aceptación.', 'No aplica; API y Krayin conservan v1.'],
    ['MEJ-08', 'Conclusiones, anexo B, evidencias y guía de capturas.', 'Documentación completada; resultados y límites registrados.'],
], [0.8, 2.8, 2.8])
p('El prototipo previo ya dispone de separación ML/API, integración con Krayin, panel de predicciones, sugerencias y seguimiento manual. La ronda MEJ no reemplaza esos componentes ni acredita efectos sobre fidelización o rentabilidad.')
p('Para capturas: docs/PLAN_MEJORAS_ML.md y docs/MEJ08_CIERRE_DOCUMENTAL.md. Las métricas y la decisión se consultan en docs/evidencias_mej06/aceptacion/.')

doc.add_page_break()
p('Comparación cuantitativa y aceptación', 'Heading 1')
p('B4 Cambios respecto al modelo instalado', 'Heading 2')
p('E1 comprende los mismos 431 clientes. Se seleccionan 87 por alternativa; las diferencias son candidato menos v1 instalado. Los puntos porcentuales (pp) expresan diferencias absolutas de precisión.')
e1 = metrics['E1']
def number(value, n=6):
    return f'{value:.{n}f}'.replace('.', ',')
rows = []
for key, label in [('precision_at_20', 'Precisión al 20 % ↑'), ('average_precision', 'AP ↑'), ('brier', 'Brier ↓')]:
    a, b = e1['installed'][key], e1['candidate'][key]
    vals = [f'{number(a*100, 2)} %', f'{number(b*100, 2)} %', f'+{number((b-a)*100, 2)} pp'] if key == 'precision_at_20' else [number(a), number(b), '+' + number(b-a)]
    rows.append([label] + vals)
rows.append(['Abandonos en el cupo', str(round(e1['installed']['precision_at_20']*87)), '29', '+14'])
p('Tabla B2 Comparación E1 con el artefacto instalado', 'Heading 3')
table(['Indicador', 'v1 instalado', 'Candidato', 'Diferencia'], rows, [2.05, 1.45, 1.45, 1.45])
p('↑ Mayor es mejor. ↓ Menor es mejor. El aumento de Brier representa un deterioro de las probabilidades, aunque la precisión del grupo prioritario mejore.')
p('Tabla B3 Criterios que impiden promover el candidato', 'Heading 3')
table(['Criterio de Brier', 'Exceso observado', 'Máximo permitido', 'Resultado'], [
    ['Media D1/D2/E1 frente al constante', '0,011289', '0,010000', 'No cumple'],
    ['E1 frente a v1 instalado', number(e1['candidate']['brier'] - e1['installed']['brier']), '0,010000', 'No cumple'],
], [2.4, 1.35, 1.35, 1.3])
p('Tabla B4 Balance de la decisión automatizada', 'Heading 3')
table(['Comprobaciones favorables', 'Desfavorables', 'Decisión'], [['16 de 18', '2 de 18', 'Conservar v1']], [2.5, 1.5, 2.4])
p('La mejora es exploratoria: E1 ya se había observado y los intervalos de AP incluyen cero. Conservar v1 es una decisión de control de versiones; no demuestra utilidad predictiva suficiente del modelo anterior.')
p('Para capturas y verificación: docs/evidencias_mej06/aceptacion/metrics.json (bloque E1), decision.json y docs/MEJ06_ACEPTACION.md. La tabla B3 usa medias no ponderadas de los tres cortes para su primera fila.')
doc.save(target)
print('Tablas B1 a B4 añadidas; respaldo preservado.')
