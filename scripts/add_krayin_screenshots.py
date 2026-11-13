"""Inserta evidencia real del módulo y ampliaciones sin alterar los PNG fuente."""
from pathlib import Path
from copy import deepcopy
import shutil
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'InvestigacionTesis2026.docx'
backup=ROOT/'docs/historico/InvestigacionTesis2026_antes_capturas_krayin.docx'
if not backup.exists(): shutil.copy2(target,backup)
doc=Document(backup)
body=doc._element.body
anchor=next(p._p for p in doc.paragraphs if p.text=='Despliegue y errores del modelo vigente')
before=list(body)
def p(text,style='Normal'):
    para=doc.add_paragraph(text,style)
    for run in para.runs:
        if style.startswith('Heading'): run.font.color.rgb=RGBColor(0,0,0)
    return para
def page(title):
    p(title,'Heading 1').paragraph_format.page_break_before=True
def screenshot(path, caption, crop=None):
    path=ROOT/path
    width,height=Image.open(path).size
    x0,y0,x1,y1=crop if crop else (0,0,width,height)
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    shape=para.add_run().add_picture(str(path),width=Inches(6.3),height=Inches(6.3*(y1-y0)/(x1-x0)))
    if crop:
        rect=OxmlElement('a:srcRect')
        for key,value in [('l',x0/width),('t',y0/height),('r',(width-x1)/width),('b',(height-y1)/height)]:
            rect.set(key,str(round(value*100000)))
        fill=shape._inline.find('.//'+qn('pic:blipFill'))
        fill.insert(1,rect)
    para=p(caption)
    for run in para.runs: run.font.size=Pt(9)

page('Módulo de predicciones en Krayin')
p('Las capturas documentan el módulo construido y sus datos durante las pruebas locales de octubre de 2026. El caso mostrado es AA-10315, con corte histórico 30/06/2018 y modelo churn180-v1. La fecha de cálculo y la fecha de observación son campos distintos; no se trata de una predicción de la situación actual del cliente.')
screenshot('docs/evidencias_crm042/prediccion_guardada.png','Figura 3.9. Listado real del módulo: navegación, filtros por corte/riesgo/estado, indicadores y una predicción guardada. Fuente: docs/evidencias_crm042/prediccion_guardada.png; evidencia de CRM-04.2.')
p('La fila presenta probabilidad de 34,01 %, riesgo Medio y aviso de historial limitado. El estado «Update failed; previous result retained» pertenece a la prueba de recuperación: la actualización falló y el sistema conservó el resultado anterior. No representa un valor inventado ni una predicción nueva generada para la captura.')
p('El listado permite localizar al cliente y consultar el resultado dentro de los permisos asignados. En las etapas posteriores se añadió la orientación explicada en el detalle y el seguimiento manual. Las capturas reflejan esas etapas verificadas; no se presentan como una sesión en vivo.')

page('Datos del cliente y sugerencias de revisión')
screenshot('docs/evidencias_crm051/sugerencia_detalle.png','Figura 3.10. Ampliación del resultado y la sugerencia en el detalle del cliente. Fuente: docs/evidencias_crm051/sugerencia_detalle.png, evidencia de CRM-05.1. Se recorta únicamente el área de visualización en Word; la imagen fuente se conserva íntegra.',(215,270,1424,648))
p('La orientación mostrada indica interpretar con cautela y comprobar la cobertura limitada del historial antes de considerar seguimiento. Esta regla de calidad tiene prioridad sobre la categoría Medio. Es una sugerencia explícita para revisión humana: no es una acción aprendida por el modelo y no envía contactos, ofertas ni campañas.')
screenshot('docs/evidencias_crm043/detalle_escritorio.png','Figura 3.11. Ampliación de las siete variables históricas mostradas en el módulo. Fuente: docs/evidencias_crm043/detalle_escritorio.png, evidencia de CRM-04.3. La ventana visible es 30/06/2017 < fecha de pedido ≤ 30/06/2018.',(215,600,1424,927))
p('El detalle muestra recencia de 1 día, un pedido, ventas acumuladas de 374,4800, media por línea de 187,2400, desviación muestral de 248,4773, una categoría y dos subcategorías. La huella del historial coincide con la entrada guardada. Estos datos permiten revisar el contexto del resultado; no constituyen una explicación causal del riesgo.')
p('El registro de responsable, estado y nota se presenta en la sección 4.9 de resultados. Las capturas conservan el idioma de la instalación utilizada durante QA; los textos del módulo también cuentan con traducciones al español.')

new=[e for e in list(body) if e not in before and e.tag!=qn('w:sectPr')]
for e in new: body.remove(e)
position=list(body).index(anchor)
for i,e in enumerate(new): body.insert(position+i,e)
for para in doc.paragraphs:
    for run in para.runs:
        if 'Figura 3.9. Matriz actual' in run.text:
            run.text=run.text.replace('Figura 3.9. Matriz actual','Figura 3.12. Matriz actual')
doc.save(target)
print('Tres capturas insertadas en dos páginas dentro de la fase de integración CRM.')
