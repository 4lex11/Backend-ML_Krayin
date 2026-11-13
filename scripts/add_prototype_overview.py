"""Añade una presentación visual concisa del prototipo al inicio de resultados."""
import ast
import re
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'InvestigacionTesis2026.docx'
backup=ROOT/'docs/historico/InvestigacionTesis2026_antes_acerca_prototipo.docx'
if not backup.exists(): shutil.copy2(target,backup)
doc=Document(backup)
body=doc.element.body
chapter=next(p for p in doc.paragraphs if p.text=='Capítulo 4. Resultados')
anchor=next(p for p in doc.paragraphs if p.text.startswith('4.1. Comparación'))
active=False
for para in doc.paragraphs:
    if para.text.startswith('Capítulo 4.'): active=True
    if para.text.startswith('Capítulo 5'): active=False
    for run in para.runs:
        if not run.text: continue
        if active:
            run.text=re.sub(r'^4\.(\d+)\.',lambda m:f'4.{int(m[1])+1}.',run.text)
            run.text=re.sub(r'Figura 4\.(\d+)\.',lambda m:f'Figura 4.{int(m[1])+3}.',run.text)
            run.text=re.sub(r'Tabla 4\.(\d+)\b',lambda m:f'Tabla 4.{int(m[1])+1}',run.text)
        if 'sección 4.9 de resultados' in run.text:
            run.text=run.text.replace('sección 4.9 de resultados','sección 4.10 de resultados')

tree=ast.parse((ROOT/'scripts/add_improvement_tables.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'p','table'}],type_ignores=[]),'<helpers>','exec'))
def caption(text):
    para=p(text)
    para.paragraph_format.space_after=Pt(6)
    for run in para.runs: run.font.size=Pt(9)
def picture(path, text, width=6.0, crop=None):
    path=ROOT/path
    w,h=Image.open(path).size
    x0,y0,x1,y1=crop or (0,0,w,h)
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after=Pt(3)
    shape=para.add_run().add_picture(str(path),width=Inches(width),height=Inches(width*(y1-y0)/(x1-x0)))
    if crop:
        rect=OxmlElement('a:srcRect')
        for key,value in [('l',x0/w),('t',y0/h),('r',(w-x1)/w),('b',(h-y1)/h)]: rect.set(key,str(round(value*100000)))
        shape._inline.find('.//'+qn('pic:blipFill')).insert(1,rect)
    caption(text)

before=list(body)
p('4.1. Acerca del prototipo','Heading 2')
p('El prototipo es una solución web integrada en Krayin CRM para consultar el riesgo de ausencia de compra a 180 días y apoyar la revisión de clientes. El usuario accede al módulo de predicciones desde el panel; la aplicación consulta el servicio de ML y conserva los resultados junto con su fecha de corte.')
p('Interfaz del módulo','Heading 2')
p('El listado permite buscar clientes, filtrar por riesgo, corte y estado, y abrir su detalle. Presenta indicadores y probabilidades guardadas. La captura muestra 34,01 % de riesgo Medio; el aviso de actualización fallida corresponde a una prueba que conservó la predicción anterior.')
picture('docs/evidencias_crm042/prediccion_guardada.png','Figura 4.1. Pantalla de listado de predicciones. Fuente: docs/evidencias_crm042/prediccion_guardada.png.',5.3)
p('El detalle reúne la probabilidad, el horizonte, las variables históricas y una sugerencia de revisión. En este caso, el historial limitado aconseja comprobar la cobertura de datos antes de considerar seguimiento. Las sugerencias se generan mediante reglas explícitas.')
picture('docs/evidencias_crm051/sugerencia_detalle.png','Figura 4.2. Resultado y sugerencia en el detalle del cliente. Fuente: docs/evidencias_crm051/sugerencia_detalle.png; ampliación del área relevante.',6.3,(215,270,1424,648))

p('Acerca del prototipo: seguimiento y tecnología','Heading 1').paragraph_format.page_break_before=True
p('La sección de seguimiento, dentro del detalle, permite registrar estado, responsable y nota. Cada revisión conserva autor y fecha en el historial. La captura pertenece a una prueba local; guardar una revisión no envía mensajes ni ejecuta campañas.')
picture('docs/evidencias_crm061/revision_integral.png','Figura 4.3. Formulario e historial de seguimiento manual. Fuente: docs/evidencias_crm061/revision_integral.png; cuenta y nota de prueba.',4.5)
p('Modelo utilizado','Heading 2')
p('Se utiliza LightGBM sin SMOTE, calibrado con sigmoide y siete variables del historial anual. Obtuvo la mayor AP en la comparación inicial (0,474601). Emplea 150 árboles, profundidad 3, siete hojas y tasa de aprendizaje 0,05. El candidato con mejor precisión por cupo incumplió los criterios de Brier; se conserva el modelo integrado. Las secciones siguientes explican esta decisión.')
p('Herramientas y librerías','Heading 2')
table(['Componente','Tecnologías y función'],[
 ['Solución web','Krayin CRM, PHP y Laravel; vistas Blade y módulo Webkul/Churn para consulta y seguimiento.'],
 ['Persistencia y entorno','MariaDB almacena clientes, predicciones y revisiones; instalación local en Windows y XAMPP.'],
 ['Servicio de predicción','Python, FastAPI, Pydantic y Uvicorn: validación de entradas e inferencia mediante HTTPS.'],
 ['Datos y modelos','pandas y NumPy para preparar datos; scikit-learn, LightGBM, XGBoost e imbalanced-learn para evaluación, modelos y balanceo.'],
 ['Artefactos y gráficas','joblib conserva el modelo; Matplotlib y Seaborn apoyan las visualizaciones del estudio.'],
],[1.55,4.85])
caption('Tabla 4.1. Tecnologías del prototipo. Fuentes: backend/requirements.txt, ML/requirements-training.txt, ML/requirements.txt y docs/evidencias_crm061/versiones.json. Las pantallas usan datos históricos del dataset y evidencias locales de octubre de 2026.')
new=[e for e in list(body) if e not in before and e.tag!=qn('w:sectPr')]
for e in new: body.remove(e)
pos=list(body).index(anchor._p)
for i,e in enumerate(new): body.insert(pos+i,e)
anchor.paragraph_format.page_break_before=True
doc.save(target)
print('Sección 4.1 incorporada; secciones posteriores y figuras renumeradas.')
