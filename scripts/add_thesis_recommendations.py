"""Añade recomendaciones basadas en los resultados, conservando una copia previa."""
from pathlib import Path
import shutil
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / 'InvestigacionTesis2026.docx'
backup = ROOT / 'docs/historico/InvestigacionTesis2026_antes_recomendaciones.docx'
if not backup.exists():
    shutil.copy2(target, backup)
doc = Document(backup)
anchor = next(p for p in doc.paragraphs if p.text == 'Referencias y evidencia del proyecto')
# Insertar después del salto previo a las referencias y mantenerlas en página propia.
heading = anchor.insert_paragraph_before('Recomendaciones', 'Heading 1')
anchor.paragraph_format.page_break_before = True
items = [
    ('Uso del prototipo. ', 'Se recomienda emplear el módulo como demostración de integración y apoyo a la revisión humana. La ROC-AUC de 0,4571 y la average precision de 0,2119 no respaldan usar el riesgo estimado como criterio único para priorizar contactos. Debe conservarse la advertencia experimental y mantenerse deshabilitada la ejecución automática de campañas.'),
    ('Interpretación de los datos. ', 'Para presentar el estudio, se recomienda conservar el corte histórico del 30/06/2018 y explicar la ventana previa de 365 días y el horizonte posterior de 180 días. Los casos no elegibles, sin predicción o con historial limitado deben identificarse por separado. La ausencia de recompra no debe interpretarse como insatisfacción ni como abandono contractual.'),
    ('Evaluación del modelo. ', 'En futuras investigaciones se recomienda comparar cada alternativa con reglas simples de recencia y evaluar discriminación y calibración en periodos posteriores no utilizados para seleccionar modelos o umbrales. No conviene ajustar repetidamente contra el test ya observado. Si el dataset actual no permite otro periodo independiente con seguimiento completo, esa evaluación debe quedar como trabajo futuro.'),
    ('Operación y trazabilidad. ', 'Antes de cada demostración se recomienda comprobar la disponibilidad de la base de datos, la API HTTPS y el procesador de solicitudes. Deben conservarse permisos por rol, respaldos, versiones del modelo y registros de errores. Al revisar una predicción, corresponde verificar su corte, calidad del historial y sugerencia, y registrar responsable, nota y estado sin sustituir los resultados anteriores.'),
    ('Uso de las sugerencias. ', 'Se recomienda presentar las orientaciones del panel como reglas de revisión y no como tratamientos cuya eficacia haya sido aprendida o validada por ML. Registrar una revisión aporta trazabilidad, pero no acredita contacto ni retención. El estado de una solicitud y el porcentaje terminado deben explicarse separadamente de su éxito y de la existencia de una predicción válida.'),
    ('Validación comercial futura. ', 'Si se amplía el alcance, se recomienda definir previamente una intervención, un grupo de comparación, un periodo de seguimiento y medidas de recompra y costos. Solo entonces podría evaluarse si una acción aporta beneficios frente a la práctica habitual. Los costos, márgenes y resultados de campañas ausentes en Superstore Sales no deben inventarse; esta propuesta no es un requisito pendiente del prototipo local entregado.'),
]
intro = anchor.insert_paragraph_before('Las siguientes recomendaciones se derivan de los resultados y límites del estudio. Distinguen el uso del prototipo ya implementado de las investigaciones que requerirían evidencia adicional.')
for label, body in items:
    p = anchor.insert_paragraph_before()
    p.add_run(label).bold = True
    p.add_run(body)
doc.core_properties.comments = 'Recomendaciones añadidas el 29/10/2026; copia previa conservada en docs/historico/InvestigacionTesis2026_antes_recomendaciones.docx.'
doc.save(target)
print('Recomendaciones incorporadas; copia previa conservada.')
