"""Cierre documental de la ronda MEJ; preserva la tesis previa."""
from pathlib import Path
import shutil
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / 'InvestigacionTesis2026.docx'
backup = ROOT / 'docs/historico/InvestigacionTesis2026_antes_MEJ08.docx'
if not backup.exists():
    shutil.copy2(target, backup)
doc = Document(backup)
for p in doc.paragraphs:
    if p.text.startswith('La contribución es una evaluación retrospectiva reproducible'):
        p.text = ('La contribución es una evaluación retrospectiva reproducible y un prototipo CRM con trazabilidad y revisión humana. La ronda posterior MEJ-01 a MEJ-06 mejoró la precisión del grupo priorizado, pero incumplió dos criterios de error probabilístico; se conservó v1. El anexo B documenta esta decisión. La validación prospectiva, el piloto comercial y el despliegue externo permanecen como trabajo futuro.')

def paragraph(text, style='Normal'):
    return doc.add_paragraph(text, style)

doc.add_page_break()
paragraph('Anexo B Mejora experimental del modelo', 'Heading 1')
paragraph('B1 Diseño y comparación de candidatos', 'Heading 2')
paragraph('Después del cierre del prototipo se ejecutó una ronda exploratoria con el mismo dataset, 365 días de historial y abandono a 180 días. Se fijó como métrica principal la precisión entre el 20 % de clientes con mayor puntuación; el cupo es un escenario académico, no una capacidad comercial acreditada. La preparación mantiene clientes y etiquetas comunes para todas las variantes.')
paragraph('Se añadieron 11 variables de actividad reciente, ventas, intervalos entre pedidos e historial limitado. Se compararon 18 configuraciones de regresión logística, Random Forest y LightGBM con variables originales, temporales y combinadas. Los hiperparámetros se registraron antes del entrenamiento. D1 evaluó junio de 2017 y D2 diciembre de 2017; las etiquetas de entrenamiento y calibración debían completarse antes del siguiente corte.')
paragraph('Ganó lightgbm_original_a: LightGBM con siete variables originales, 100 árboles, profundidad 2, cuatro hojas y tasa de aprendizaje 0,03. Las nuevas variables no integraron la combinación ganadora. La precisión media al 20 % en D1/D2 fue 51,82 %, frente a 43,68 % de recencia y 42,12 % de la receta v1 reentrenada. Estos resultados de desarrollo no bastaban para autorizar el reemplazo.')
paragraph('Se compararon las probabilidades crudas y la calibración sigmoide del único candidato. La sigmoide ganó según la prioridad fijada, pero aumentó el Brier medio de 0,252945 a 0,268670. En D1 invirtió el orden de las puntuaciones; en D2 lo conservó. Por ello, aplicar un calibrador no equivale a obtener probabilidades más fiables.')
paragraph('Los umbrales se calcularon exclusivamente en calibración para cupos del 10 %, 20 % y 30 %. Diez de doce combinaciones fueron compatibles; dos no permitieron el tamaño exacto por empates. Un umbral obtenido en calibración no garantiza el mismo porcentaje seleccionado en un periodo posterior. El top-20 % usa ceil(0,20 × N) y desempata por ID, sin convertir esa selección en categorías de riesgo del panel.')
paragraph('La configuración y política se congelaron antes de E1. No se ensayaron otros candidatos después de observarlo. La ronda es exploratoria: los periodos del dataset ya habían sido analizados en etapas anteriores y no representan evidencia prospectiva independiente.')
paragraph('Fuentes para capturas: docs/MEJ04_COMPARACION_MODELOS.md; docs/MEJ05_CALIBRACION_UMBRALES.md; docs/evidencias_mej04/comparacion/selection.json y docs/evidencias_mej05/calibracion/frozen_policy.json.')

doc.add_page_break()
paragraph('Aceptación y cierre de la mejora', 'Heading 1')
paragraph('B2 Resultado del corte E1 y decisión', 'Heading 2')
paragraph('E1 evaluó 431 clientes al 30/06/2018. El candidato se ajustó con 1081 observaciones cliente-corte de 678 clientes y se calibró en diciembre de 2017. La selección del 20 % comprende 87 clientes; el candidato identifica 29 abandonos en ese grupo. La comparación con el artefacto instalado utiliza exactamente los mismos clientes.')
t = doc.add_table(rows=1, cols=4)
t.style = doc.tables[0].style
for c, text in zip(t.rows[0].cells, ['Alternativa', 'Precisión al 20 %', 'AP', 'Brier']):
    c.text = text
for row in [
    ['Candidato', '33,33 %', '0,275907', '0,221384'],
    ['Receta v1', '20,69 %', '0,233332', '0,221572'],
    ['Recencia', '25,29 %', '0,255011', '0,279348'],
    ['Constante', '26,44 %', '0,234339', '0,236687'],
    ['v1 instalado', '17,24 %', '0,211924', '0,196703'],
]:
    for c, text in zip(t.add_row().cells, row):
        c.text = text
paragraph('La probabilidad constante no ordena riesgo; su precisión en el cupo depende del desempate por ID. La receta v1 se reentrena por división y no debe confundirse con el artefacto v1 instalado, cuyo entrenamiento permanece intacto.')
paragraph('Los 1000 remuestreos pareados de clientes fueron válidos. Los intervalos descriptivos del 95 % para la mejora media de precisión al 20 % fueron [0,002337; 0,157118] frente a recencia y [0,014615; 0,185326] frente a la receta v1. Los intervalos de diferencia de AP incluyeron cero: [−0,008903; 0,081794] y [−0,009032; 0,101318]. No corrigen la selección previa de modelos ni acreditan independencia entre años.')
paragraph('Se rechazó la promoción por dos criterios fijados previamente. El Brier medio del candidato, 0,252908, supera al constante, 0,241619, en 0,011289. En E1, el Brier 0,221384 supera al de v1 instalado, 0,196703, en 0,024681. Ambos excesos rebasan la tolerancia de 0,01. La mejora en priorización no compensa automáticamente una peor estimación de probabilidades.')
paragraph('Decisión: conservar v1, mantener el carácter experimental y no ejecutar MEJ-07 en esta ronda. MEJ-08 cierra la documentación del resultado. Se recomienda conservar los resultados desfavorables y exigir evidencia temporal independiente antes de ampliar las afirmaciones. No se modificaron API, umbrales ni Krayin; tampoco se realizaron campañas.')
paragraph('Evidencia para capturas: docs/evidencias_mej06/aceptacion/metrics.json, bootstrap.json y decision.json. Acta: docs/MEJ06_ACEPTACION.md. Las 15 pruebas de MEJ-04/05/06 verifican código, no fidelización ni exactitud comercial.')
doc.save(target)
print('Tesis actualizada con anexo B y conclusiones de MEJ.')
