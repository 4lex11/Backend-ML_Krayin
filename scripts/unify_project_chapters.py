"""Redacción por etapas del proyecto; mantiene resultados y evidencia originales."""
from pathlib import Path
import shutil
import hashlib
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / 'InvestigacionTesis2026.docx'
backup = ROOT / 'docs/historico/InvestigacionTesis2026_antes_redaccion_proyecto_final.docx'
if not backup.exists():
    shutil.copy2(target, backup)
doc = Document(backup)
body = doc.element.body
elements = list(body)
def txt(e): return ''.join(e.xpath('.//w:t/text()'))
start = next(i for i,e in enumerate(elements) if txt(e).startswith('Capítulo 3.'))
end = next(i for i,e in enumerate(elements) if txt(e).startswith('Capítulo 5'))
chapter_elements = elements[start:end]

replacements = {
 'v1 comparó Random Forest': 'El procedimiento comienza con la comparación de Random Forest, XGBoost y LightGBM, con y sin SMOTE. Después se evalúan combinaciones de hiperparámetros y variables mediante regresión logística, Random Forest y LightGBM. La selección considera precisión con cupo del 20 %, AP y Brier en cortes temporales. A continuación se verifica la calibración y se contrasta la configuración candidata con referencias comunes antes de decidir su uso en el CRM.',
 'El diseño separa tres responsabilidades': 'El sistema separa tres responsabilidades: ML prepara los datos y evalúa los modelos; la API Python proporciona inferencia por HTTPS; Krayin, mediante el paquete Webkul/Churn, consulta, guarda y presenta las predicciones. El servicio carga un artefacto acompañado de sus metadatos. Laravel consume el contrato de la API y procesa las solicitudes mediante una cola. Esta separación permite verificar cada componente antes de comprobar el recorrido completo.',
 'Abandono se define como': 'Abandono se define como no comprar durante los 180 días posteriores al corte. Se consideran clientes con recencia histórica menor o igual a 180 días y se utiliza el año anterior para describir su comportamiento. La variable Recency mide la inactividad conocida al corte; la etiqueta se obtiene exclusivamente de las compras posteriores. Así se separa la información disponible para predecir del evento que se desea anticipar.',
 'Variables adicionales de la ronda experimental': 'Definición de las variables temporales',
 'Tabla 3.3 Variables derivadas usadas': 'Tabla 3.3 Variables derivadas del historial de compras',
 'Las tres variables Orders': 'Orders y Sales se calculan en tres ventanas cada una; junto con las cinco variables restantes forman once predictores temporales. Los meses activos pueden abarcar partes de 13 meses calendario en 365 días. Los intervalos se calculan entre pedidos distintos; su desviación se fija en cero cuando no hay dos intervalos.',
 'Las once variables temporales fueron evaluadas': 'Se comparan tres conjuntos: siete variables de comportamiento, once variables temporales y la combinación de las dieciocho. Esta organización permite comprobar si describir la actividad reciente aporta información adicional. La elección se realiza en la fase de evaluación. Fuente: ML/features_v2.py y ML/temporal_validation.py.',
 'No se eliminaron duplicados exactos': 'La revisión no identificó duplicados exactos que debieran eliminarse; se conservaron las 9.800 líneas. Se encontraron once códigos postales ausentes. Este campo no forma parte de los predictores, por lo que esas ausencias no requieren imputación para entrenar los modelos. La población elegible se determina después, al construir las ventanas temporales de cada corte.',
 'Figura 3.6. Cortes': 'Figura 3.6. Separación temporal para entrenamiento, calibración y evaluación. Las etiquetas deben disponer de su horizonte completo antes de utilizar el bloque siguiente. Fuente: protocolo y manifiesto de particiones.',
 'D1 evalúa junio': 'D1 evalúa junio de 2017; D2, diciembre de 2017; E1, junio de 2018. Los nueve archivos de entrenamiento, calibración y evaluación incluyen controles de población e integridad. E1 se trata como evaluación exploratoria porque ese periodo ya fue examinado durante el estudio. La comparación de 18 configuraciones no utiliza SMOTE; los datos de evaluación siempre corresponden a observaciones reales.',
 'La búsqueda MEJ': 'Para modelar se comparan primero seis alternativas de árboles con y sin SMOTE mediante AP de validación. La búsqueda de configuraciones cruza después tres familias, dos ajustes por familia y tres conjuntos de variables, obteniendo 18 candidatos. Cada ajuste usa los mismos clientes de cada corte; la sigmoide se estima en un bloque posterior reservado. La selección usa D1/D2 y se congela antes de E1.',
 'Se usa random_state=42': 'Se fija random_state=42 y n_jobs=1 en árboles; la logística incorpora StandardScaler. También se reentrena una configuración de referencia bajo las mismas particiones. Se distingue este comparador del artefacto integrado, porque compartir hiperparámetros no implica compartir ajuste ni probabilidades. E1 no se utiliza para buscar nuevos hiperparámetros.',
 'Modelo que se utiliza:': 'Después de ordenar las configuraciones se comprueba su aceptación. Se exige que el exceso de Brier no supere 0,01 frente al constante en la media de los cortes ni frente al artefacto integrado en E1. Estos controles complementan la precisión del ranking. El capítulo 4 presenta la aplicación de los criterios y la decisión de uso.',
 'La integración actual utiliza': 'El despliegue utiliza LightGBM sin SMOTE calibrado con sigmoide, con 150 árboles, profundidad 3, siete hojas y learning_rate de 0,05. La API admite predicción individual, lotes de hasta 500 clientes y cálculo de variables sobre hasta 5.000 líneas de un cliente. El consumidor PHP verifica TLS y el contrato; guarda las solicitudes y las procesa con churn:work fuera de la petición web.',
 'Las matrices deben indicar': 'Para interpretar las matrices se especifica la regla que convierte una puntuación en selección. La comparación del ranking utiliza exactamente 87 de los 431 clientes en ambas alternativas. Las filas representan la clase observada y las columnas la predicha, en el orden no abandono y abandono. A continuación se contrasta esta selección por cupo con el umbral utilizado por el panel.',
 'El corte del 30/06/2018 contiene': 'Una vez elegida la configuración en desarrollo, se evalúa el corte del 30/06/2018: 431 clientes elegibles y 101 abandonos futuros. Se contrastan el candidato, el modelo integrado, la referencia reentrenada, recencia y una probabilidad constante del entrenamiento. E1 ofrece evidencia exploratoria sobre datos ya examinados; no es evidencia prospectiva independiente.',
 'Filas resaltadas:': 'Las filas resaltadas identifican la configuración candidata y el modelo integrado para facilitar su comparación. La precisión mide aciertos en el cupo; AP resume el ranking y Brier evalúa las probabilidades. La decisión de uso requiere revisar conjuntamente estos resultados.',
 'Decisión de uso: conservar': 'El siguiente paso consiste en examinar la calibración y los criterios de aceptación. Una mayor precisión en el cupo no demuestra, por sí sola, que las probabilidades estimadas sean suficientemente fiables para sustituir el modelo integrado.',
 '4.2. Comparación de modelos de la versión': '4.1. Comparación de algoritmos y balanceo',
 'La evaluación inicial comparó': 'Primero se comparan seis alternativas de árboles, con y sin SMOTE, en la validación de diciembre de 2017, con 510 clientes. El criterio es AP. Esta comparación permite identificar una configuración de referencia antes de examinar los conjuntos de variables y los ajustes de desarrollo. Sus métricas pertenecen a este bloque de validación y se presentan por separado de las medias temporales D1/D2.',
 'Figura 4.2. Comparación original': 'Figura 4.1. Comparación de algoritmos por AP, ROC-AUC y Brier en validación. LightGBM sin SMOTE presenta la mayor AP. Fuente: metadata.json.',
 'La AP de 0,474601': 'LightGBM sin SMOTE obtiene AP de 0,474601, frente a 0,471911 de Random Forest. La diferencia es pequeña y no se interpreta como superioridad estadísticamente demostrada. SMOTE no produce una mejora uniforme entre algoritmos. Con esta referencia se examina después el efecto de variar los hiperparámetros y los conjuntos de variables.',
 '4.3. Comparación completa': '4.2. Comparación de configuraciones y variables',
 'Tabla 4.3 Resultados': 'Tabla 4.2 Resultados medios D1 y D2',
 '4.1. Resultados predictivos': '4.3. Evaluación del modelo en el corte E1',
 'Figura 4.1. Métricas': 'Figura 4.2. Métricas de las cinco alternativas en E1. Fuente: metrics.json. En precisión y AP, mayor es mejor; en Brier, menor es mejor.',
 'En MEJ-05, diez': 'En calibración, diez de doce combinaciones de umbral produjeron el tamaño de selección previsto; dos fueron incompatibles por empates. Un umbral obtenido en calibración no garantiza seleccionar la misma proporción al evaluar. Los cupos relativos permiten estudiar capacidad de contacto, mientras que las categorías Alto/Medio/Bajo del CRM utilizan umbrales fijos.',
 'El análisis histórico ML-06': 'También se analizan escenarios con costos abstractos de error para ilustrar las consecuencias de omitir un abandono o generar una falsa alarma. Estos valores no corresponden a pérdidas monetarias observadas ni permiten estimar el efecto de una campaña.',
 'API-07 verificó': 'Las pruebas operativas verificaron reinicio controlado, recuperación tras caída en 50,11 segundos y reversión de una entrega. La tarea temporal de ensayo se eliminó. La regresión completa registró 98 pruebas aprobadas y 95,14 % de cobertura Python. Estas cifras miden la comprobación del software, no la exactitud predictiva. Los scripts PowerShell se verificaron mediante ensayos operativos y no forman parte de ese porcentaje.',
 'El listado permite localizar': 'El listado permite localizar al cliente y abrir el detalle con los permisos asignados. Allí se consultan las variables, la orientación y el seguimiento manual. Las capturas muestran esas funciones durante sus pruebas locales; sus fechas y archivos fuente permiten identificar la evidencia de cada pantalla.',
 'La media no ponderada del Brier': 'El Brier medio del candidato es 0,252908, frente a 0,241619 del constante. En E1 alcanza 0,221384, frente a 0,196703 del modelo integrado. Se aprueban 16 comprobaciones y fallan las dos de la tabla. Por ello se mantiene el modelo integrado: ganar precisión en el cupo no basta para cumplir los criterios de aceptación.',
}
for e in chapter_elements:
    if e.tag != qn('w:p'): continue
    p = Paragraph(e, doc)
    for prefix, value in replacements.items():
        if p.text.startswith(prefix):
            # These paragraphs contain text only; image paragraphs are never replaced.
            assert not p._p.xpath('.//w:drawing')
            p.runs[0].text = value
            for run in p.runs[1:]: run.text = ''
            break

simple = {
 'Valores MEJ': 'Valores evaluados',
 'Tabla 3.3; seleccionado.': 'Variables de comportamiento de la tabla 3.3.',
 'Tabla 3.5; evaluado.': 'Variables temporales de la tabla 3.5.',
 'Original + temporal; evaluado.': 'Comportamiento y variables temporales.',
 'en MEJ.': 'en la evaluación.',
 'La política principal de MEJ': 'La política principal de evaluación',
 'baseline v1 recipe': 'Referencia reentrenada',
 'la receta v1 reentrenada': 'la referencia reentrenada',
 'la receta v1': 'la referencia reentrenada',
 'Receta v1': 'Referencia reentrenada',
 'v1 instalado': 'Modelo integrado',
 'frente a v1 instalado': 'frente al modelo integrado',
 'Matriz actual de v1': 'Matriz del modelo integrado',
 'A 0,50, v1': 'A 0,50, el modelo integrado',
 ' %. v1:': ' %. Modelo integrado:',
}
for e in chapter_elements:
    for node in e.iter(qn('w:t')):
        for a,b in simple.items(): node.text = (node.text or '').replace(a,b)
        node.text = (node.text or '').replace('de Modelo integrado','del modelo integrado').replace('frente a Modelo integrado','frente al modelo integrado')

# Reorder only the first three result blocks; all drawings remain in their blocks.
els = list(body)
c4 = next(e for e in els if txt(e).startswith('Capítulo 4.'))
initial = next(e for e in els if txt(e).startswith('4.1. Comparación de algoritmos'))
configs = next(e for e in els if txt(e).startswith('4.2. Comparación de configuraciones'))
calibration = next(e for e in els if txt(e).startswith('4.4. Calibración'))
ia, ib, ic, iz = map(els.index, [c4,initial,configs,calibration])
evaluation_block = els[ia+1:ib]
initial_block = els[ib:ic]
configs_block = els[ic:iz]
# The chapter heading starts the page; the initial subsection must not force another.
Paragraph(initial,doc).paragraph_format.page_break_before = False
Paragraph(evaluation_block[0],doc).paragraph_format.page_break_before = True
for e in els[ia+1:iz]: body.remove(e)
for i,e in enumerate(initial_block+configs_block+evaluation_block): body.insert(ia+1+i,e)

# Use neutral plot captions in the core chapters. Annex source images stay intact.
new_dir = ROOT/'docs/evidencias_proyecto_final'
image_map = {}
for folder in ['evidencias_cap34','evidencias_mej08/graficas']:
    for source in (ROOT/'docs'/folder).glob('*.png'):
        replacement = new_dir/source.name
        if replacement.exists(): image_map[hashlib.sha256(source.read_bytes()).hexdigest()] = replacement
for e in chapter_elements:
    for blip in e.xpath('.//a:blip'):
        rid = blip.get(qn('r:embed'))
        part = doc.part.related_parts[rid]
        path = image_map.get(hashlib.sha256(part.blob).hexdigest())
        if path:
            new_rid, _ = doc.part.get_or_add_image(str(path))
            blip.set(qn('r:embed'),new_rid)
doc.save(target)
print('Capítulos unificados; comparaciones y datos preservados.')
