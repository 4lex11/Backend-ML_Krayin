from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
import shutil
root=Path(__file__).resolve().parents[1]
source=root/'InvestigacionTesis2026.docx'
backup=root/'docs/historico/InvestigacionTesis2026_antes_CRM062.docx'
if not backup.exists():shutil.copy2(source,backup)
doc=Document(backup);p=list(doc.paragraphs)
changes={
18:'Esta investigación evalúa la aplicación de Machine Learning a la estimación de ausencia de recompra e integra un servicio de inferencia con una instalación local de Krayin CRM. Se utiliza exclusivamente Superstore Sales, con 9.800 líneas de venta, 4.922 pedidos y 793 clientes. El resultado de interés es ninguna compra durante los 180 días posteriores al corte; los predictores usan los 365 días anteriores.',
20:'La integración implementa HTTPS, persistencia, panel de predicciones, sugerencias orientativas y revisión manual. La aceptación final aprobó 161 pruebas PHP y 98 pruebas Python. El lote de 793 clientes produjo 431 predicciones coincidentes con el test y 362 casos no elegibles; sus escrituras se revirtieron. El funcionamiento técnico no demuestra mejora de fidelización: no se ejecutaron campañas ni se midió su efecto. El modelo conserva estado experimental.',
27:'Una herramienta de gestión de clientes necesita distinguir entre almacenar información y convertirla en una prioridad de atención útil. Este proyecto estudia si el historial permite estimar ausencia de recompra y comunica esas estimaciones a un CRM local. La respuesta correcta de una API no basta para demostrar que el modelo distingue resultados futuros de forma útil.',
28:'El problema de investigación es determinar qué capacidad predictiva y viabilidad técnica ofrece ML basado en Superstore Sales para apoyar la gestión de clientes en un CRM. El título expresa la finalidad de mejorar la gestión y fidelización; el alcance ejecutado es retrospectivo y técnico, por lo que no presupone que esa mejora haya ocurrido.',
30:'Evaluar un modelo de predicción de ausencia de recompra a 180 días e integrarlo en un prototipo local reproducible con Krayin CRM, identificando su desempeño, funcionamiento técnico y limitaciones con el dataset disponible.',
36:'Integrar y validar el panel de Krayin con predicciones, sugerencias orientativas y seguimiento manual; documentar resultados y límites de uso.',
70:'ML contiene preparación, entrenamiento, evaluación e inferencia. El backend Python expone el modelo por HTTPS; Krayin consume el servicio mediante el paquete Webkul/Churn. Los notebooks de integraciones/krayin se conservan como antecedentes, no como importadores operativos. model.joblib y metadata.json registran variables, ventanas, métricas, versión e integridad; la carga rechaza incompatibilidades.',
75:'El consumidor PHP verifica TLS, contrato e identidad, con un máximo de tres intentos y un presupuesto de 50 segundos. Conserva resultados por cliente, corte y versión sin sobrescritura silenciosa. Las solicitudes del panel se guardan en una cola del módulo y se procesan con churn:work fuera de la petición web. La operación local requiere iniciar base, API y procesador; no se instaló un servicio permanente de Krayin.',
76:'3.4 Integración local con Krayin',
77:'El módulo mapea los 793 clientes y 9.800 líneas, conserva predicciones e intentos, y ofrece listado, detalle, variables e historial. Las reglas orientativas priorizan calidad y elegibilidad; no son acciones aprendidas por ML. La revisión manual registra responsable, nota, estado, autor y fecha. Lectura, actualización y revisión tienen permisos separados y ámbito por propietario. Ninguna función envía campañas ni acredita retención.',
118:'La integración local con PHP quedó verificada desde el dataset hasta el panel y el registro manual. Las pruebas de permisos, duplicados, fallos y recuperación respaldan ese alcance técnico, pero no certifican operación permanente o producción externa. Para atribuir una mejora comercial a ML sería necesario un piloto comparable con presupuesto y seguimiento definidos antes de analizar los resultados.',
119:'La validación prospectiva, las intervenciones comerciales y el despliegue externo permanecen fuera del alcance. No se requieren datos inventados ni cambiar de dataset para presentar la investigación; sí se deben conservar los resultados negativos y distinguirlos de la integración funcional.',
125:'El prototipo separó ML y backend e integró Krayin con contrato trazable, HTTPS, persistencia, panel, sugerencias y revisión manual. La aceptación final aprobó 161 pruebas PHP con 477 aserciones y 98 pruebas Python. La cobertura de 95,14 % corresponde al ensayo Python previo de ML-06; no se volvió a medir en el cierre ni representa exactitud predictiva.',
126:'No se demostró mejora de fidelización, recompra o satisfacción causada por el sistema. Se verificó una integración local real con Krayin, pero no hubo intervención comercial ni medición de sus efectos. El modelo conserva estado experimental y no autoriza campañas automáticas.',
127:'La contribución es una evaluación retrospectiva reproducible que expone las limitaciones del modelo y un prototipo CRM con trazabilidad técnica y revisión humana. La validación prospectiva, el piloto comercial y el despliegue externo son trabajo futuro; la implementación local y su documentación quedan completadas dentro del alcance acordado.'}
for i,text in changes.items():
 if p[i].runs:
  p[i].runs[0].text=text
  for r in p[i].runs[1:]:r.text=''
 else:p[i].add_run(text)
anchor=p[109]._p

def para(text,style='Normal',page=False):
 x=doc.add_paragraph(text,style);anchor.addprevious(x._p)
 if page:x.paragraph_format.page_break_before=True
 return x

def table(rows):
 t=doc.add_table(rows=1,cols=2);t.style=doc.tables[0].style
 for c,txt in zip(t.rows[0].cells,rows[0]):c.text=txt
 for row in rows[1:]:
  for c,txt in zip(t.add_row().cells,row):c.text=txt
 for row in t.rows:
  for cell in row.cells:
   for par in cell.paragraphs:
    for run in par.runs:run.font.size=Pt(10.5)
  row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 anchor.addprevious(t._tbl)
 return t
para('Resultados de la integración con Krayin','Heading 1',True)
para('4.6 Aceptación técnica integral','Heading 2')
para('El 29 de octubre de 2026 se verificó el flujo dataset → PHP → HTTPS → persistencia → panel → sugerencia → revisión manual. La conciliación encontró cero diferencias frente al CSV. La instalación utilizó PHP 8.5.11, MariaDB 10.4.32 y Python 3.14.6; las versiones y huellas de código se registran en docs/evidencias_crm061/versiones.json.')
table([['Comprobación','Resultado observado'],['Regresión de Krayin','161 casos y 477 aserciones sin fallos'],['Regresión Python','98 casos aprobados'],['Lote de clientes','793 solicitudes; 431 completadas; 362 no elegibles'],['Concordancia con el test','431 probabilidades; diferencia máxima 4,9960 × 10⁻¹⁵'],['Distribución durante el ensayo','92 Alto, 337 Medio y 2 Bajo; 95 con historial limitado'],['Errores y recuperación','401/422: un intento; 503 y caída: tres; recuperación correcta']])
para('El lote utilizó los servicios reales dentro de una transacción exterior de prueba, revertida al terminar. Duró 42,2 segundos en el equipo local; no constituye un benchmark de producción. Las 431 predicciones no quedaron cargadas en la demostración: el estado final mantiene una predicción original y 792 clientes sin resultado para el corte inicial.')
para('Los errores conservaron la predicción válida y su fecha. Se comprobó el rechazo de solicitudes duplicadas, ámbitos de acceso y formularios desactualizados. La suite conserva avisos de deprecación PDO y TestClient; no se midió cobertura en este cierre. El primer intento falló por MariaDB detenido; tras iniciarlo se repitió satisfactoriamente. Acta: docs/CRM061_VALIDACION_INTEGRAL.md.')
para('Interfaz y trazabilidad de la revisión','Heading 1',True)
para('4.7 Seguimiento manual de demostración','Heading 2')
para('El detalle distingue fecha de corte y cálculo, versión y horizonte. Compara la huella del historial reconstruido con la entrada guardada. Las sugerencias explican sus reglas y exigen revisión humana. El registro manual añade notas con responsable, estado, autor y fecha; no sustituye las entradas anteriores ni modifica la probabilidad.')
x=para('');x.add_run().add_picture(str(root/'docs/evidencias_crm061/revision_integral.png'),width=Inches(6.1))
para('Figura 4. Registro manual en Krayin con cuenta y nota de QA. La captura demuestra trazabilidad del prototipo, no contacto con clientes ni retención. Los datos temporales de QA se eliminaron tras la prueba. Fuente: docs/evidencias_crm061/revision_integral.png.','Caption')
para('La revisión del navegador confirmó actualización HTTPS, progreso, sugerencia por historial limitado y registro manual, sin errores JavaScript ni desbordamiento móvil. Una solicitud sin token CSRF fue rechazada con 419. El sistema conserva automatic_action_allowed=false y no ejecuta campañas.')
para('La guía consolidada de instalación y operación está en docs/GUIA_FINAL_CRM.md. El índice de capturas y evidencias está en docs/INDICE_EVIDENCIAS_FINAL.md; permite localizar la pantalla y el archivo que respaldan cada resultado.')
t=doc.tables[-1] # newly inserted table; update original evidence table explicitly
for original in doc.tables:
 if original.cell(0,0).text=='Evidencia':
  for a,b in [('Integración y operación','docs/GUIA_FINAL_CRM.md'),('Aceptación integral','docs/CRM061_VALIDACION_INTEGRAL.md'),('Capturas de Krayin','docs/INDICE_EVIDENCIAS_FINAL.md')]:
   cells=original.add_row().cells;cells[0].text=a;cells[1].text=b
  break
doc.core_properties.comments='Actualización CRM-06.2 del 29/10/2026. Versión anterior conservada en docs/historico/InvestigacionTesis2026_antes_CRM062.docx.'
doc.save(source)
print('Updated DOCX; backup retained')
