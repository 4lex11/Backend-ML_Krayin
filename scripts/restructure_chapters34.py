"""Reestructura capítulos 3 y 4 conservando el resto y las imágenes originales."""
import ast
import json
import shutil
from copy import deepcopy
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'InvestigacionTesis2026.docx'
backup=ROOT/'docs/historico/InvestigacionTesis2026_antes_reestructura_cap34.docx'
if not backup.exists(): shutil.copy2(target,backup)
doc=Document(backup)
old_tables=[deepcopy(t._tbl) for t in doc.tables]
old_paras=list(doc.paragraphs)
body=doc._element.body
def find(text): return next(p._p for p in old_paras if p.text==text)
start=find('Capítulo 3 Metodología de implementación')
end=find('Capítulo 5 Discusión')
technical=find('Resultados de funcionamiento del servicio')
elements=list(body)
technical_blocks=[deepcopy(e) for e in elements[elements.index(technical):elements.index(end)]]
for element in elements[elements.index(start):elements.index(end)]: body.remove(element)
existing={id(e) for e in body}
# Recuerda los elementos originales por identidad XML para insertar la nueva sección.
anchor=body[-1]
tree=ast.parse((ROOT/'scripts/add_improvement_tables.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'p','table'}],type_ignores=[]),'<table_helpers>','exec'))
created=[]
def page(title,subtitle=None):
    heading=p(title,'Heading 1'); heading.paragraph_format.page_break_before=True
    if subtitle: p(subtitle,'Heading 2')
def h(text): return p(text,'Heading 2')
def caption(text):
    para=p(text)
    para.paragraph_format.space_after=Pt(8)
    for run in para.runs: run.font.size=Pt(9)
def picture(path,text,width=6.25):
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.add_run().add_picture(str(ROOT/path),width=Inches(width))
    caption(text)
def copied(index):
    element=deepcopy(old_tables[index]); body.insert(len(body)-1,element); p('')
def fmt(x): return f'{x:.6f}'.replace('.',',')
def highlight(t,row=1):
    for cell in t.rows[row].cells:
        shd=cell._tc.get_or_add_tcPr().find(qn('w:shd'))
        if shd is not None: shd.set(qn('w:fill'),'DDEBF7')
        for para in cell.paragraphs:
            for run in para.runs: run.bold=True
def read(path): return json.loads((ROOT/path).read_text())
sel=read('docs/evidencias_mej04/comparacion/selection.json')
metrics=read('docs/evidencias_mej06/aceptacion/metrics.json')
v1=read('ML/artifacts/churn180-v1/metadata.json')
before=list(body)

page('Capítulo 3. Metodología De La Implementación','3.1. Métodos propuestos')
p('Las seis fases de CRISP-DM conectan la evaluación retrospectiva con Krayin CRM. Se predice ausencia de compra en los próximos 180 días con 365 días de historial. El estudio no mide efectos comerciales de fidelización.')
p('v1 comparó Random Forest, XGBoost y LightGBM, con y sin SMOTE; ganó LightGBM sin SMOTE por AP de validación. MEJ evaluó 18 configuraciones de logística, Random Forest y LightGBM, priorizando precisión al 20 %, AP y Brier. Se usaron cortes temporales; se sustituyó la partición aleatoria 80/20 del borrador. K-Means no forma parte de la implementación.')
h('Tabla 3.1 Hiperparámetros y motivo de uso')
table(['Parámetro', 'Valores MEJ', 'Definición y propósito'],[
 ['n_estimators','100 LGBM; 150 RF','Cantidad de árboles; limita el tamaño del ensamble.'],
 ['max_depth','2 o 3 LGBM; 3 o 5 RF','Profundidad máxima; restringe complejidad y sobreajuste.'],
 ['num_leaves','4 o 7 LGBM','Máximo de hojas; controla la flexibilidad de cada árbol.'],
 ['learning_rate','0,03 LGBM','Aporte de cada árbol del boosting; pasos de ajuste moderados.'],
 ['min_child_samples','20 LGBM','Mínimo de observaciones por hoja; evita particiones poco sustentadas.'],
 ['min_samples_leaf','10 o 20 RF','Mínimo por hoja del bosque; regulariza estimaciones.'],
 ['reg_lambda','1,0 LGBM','Penalización L2; limita la magnitud de los pesos de las hojas.'],
 ['C','0,1 o 1,0 logística','Inverso de la fuerza de regularización; menor C penaliza más.'],
 ['solver / max_iter','lbfgs / 3000','Optimizador y límite de iteraciones de la regresión logística.'],
 ['random_state','42','Semilla para reproducibilidad; no es una métrica de calidad.'],
], [1.45,1.6,3.35])
caption('LGBM: LightGBM; RF: Random Forest. n_jobs=1 en árboles y verbosity=−1 en LightGBM son controles de ejecución. Fuente: ML/experiments/churn180-v2/candidates_mej04.json. Los valores no especificados mantienen los predeterminados del entorno registrado.')

page('Métodos propuestos y medición','Tabla 3.2 Métricas y razones para utilizarlas')
p('La clase positiva corresponde a abandono futuro. TP, FP, FN y TN son aciertos positivos, falsos positivos, falsos negativos y aciertos negativos. El cupo k es el entero superior de q × N; se ordena la puntuación de mayor a menor y se desempata por Customer ID. Esta política permite medir priorización con capacidad limitada, sin suponer una capacidad comercial real.')
copied(19)
p('Accuracy cuantifica aciertos totales, pero puede ser elevada por la clase mayoritaria. Precision indica qué proporción de los marcados realmente abandona; Recall, qué proporción de abandonos se detecta. F1 equilibra ambas y F2 da mayor peso a Recall. Se utilizan para describir las consecuencias de un umbral, no para reemplazar el criterio principal de priorización. La matriz de confusión permite contabilizar explícitamente falsas alarmas y omisiones.')
p('Los intervalos de confianza se estiman mediante 1000 remuestreos pareados por cliente en MEJ. Son descriptivos: no corrigen la selección previa de modelos ni convierten los periodos ya observados en validación independiente. Fuente: ML/compare_v2.py, ML/evaluation.py y docs/evidencias_mej06/aceptacion/bootstrap.json.')

page('3.2. Diseño del sistema')
picture('docs/evidencias_cap34/originales/pagina_20_imagen_1.jpg','Figura 3.1. Diseño conceptual conservado sin modificaciones de InvestigacionTesis2026Original.pdf, página 20.')
p('El diseño separa tres responsabilidades: ML prepara y evalúa datos; la API Python publica inferencia por HTTPS; Krayin, mediante el paquete Webkul/Churn, consulta, persiste y presenta resultados. El modelo vigente se carga desde ML/artifacts/churn180-v1/model.joblib y se valida con metadata.json. La aplicación Laravel utiliza el contrato del servicio y una cola propia; los notebooks antiguos no son el mecanismo operativo de integración.')
p('La figura original incluye segmentación K-Means, notificaciones y acciones automáticas de fidelización. Se conserva como diseño conceptual solicitado, pero esas funciones no se presentan como implementadas. El prototipo actual muestra predicciones, reglas orientativas y revisión humana; no realiza campañas ni ofrece evidencia de retención o rentabilidad.')
table(['Componente', 'Función implementada'],[
 ['ML/','Ventanas temporales, variables, entrenamiento, calibración y artefactos versionados.'],
 ['backend/','Validación del contrato, autenticación, HTTPS y predicción individual o por lote.'],
 ['Webkul/Churn','Mapeo de clientes, preparación compatible, solicitudes, persistencia e historial.'],
 ['Panel Krayin','Listado, detalle, filtros, sugerencias y registro manual con permisos.'],
], [1.6,4.8])
p('La respuesta conserva probabilidad, riesgo, corte, fecha de inferencia, horizonte y versión. Los resultados se identifican por cliente, corte y modelo. La ausencia de predicción o la falta de elegibilidad no se interpreta como riesgo cero.')

page('3.3. Fases de implementación del proyecto')
picture('docs/evidencias_cap34/originales/pagina_21_imagen_1.jpg','Figura 3.2. Fases conservadas sin cambios de la versión original, página 21.')
p('Las fases conectan la necesidad de negocio con la disponibilidad de datos y la validación técnica. El proceso documenta resultados favorables y desfavorables. La aceptación del modelo es una condición separada de que la API y el CRM funcionen correctamente.')
h('Fase 1: Comprensión del Negocio')
p('El objetivo operativo es mostrar información de riesgo para apoyar una revisión manual y priorizar clientes en escenarios académicos de contacto. Los únicos datos de negocio disponibles son las ventas de Superstore Sales. No se conocen costos por contacto, márgenes, presupuesto, campañas ni respuestas a ofertas; por ello no se calculan beneficios reales de fidelización.')
p('Abandono se define como no comprar en los 180 días posteriores al corte. Se evalúan clientes con recencia histórica menor o igual a 180 días. Esta definición permite anticipar un evento futuro; sustituye la etiqueta del borrador que clasificaba directamente la inactividad ya observada. Recency se conserva como predictor histórico y no revela la etiqueta futura.')
p('La priorización debe equilibrar aciertos dentro del cupo, cobertura de abandonos y calidad de las probabilidades. La política principal de MEJ selecciona el 20 %; los cupos del 10 % y 30 % permiten analizar sensibilidad. Estos porcentajes no representan acuerdos de contacto de una empresa.')

page('Fase 1 y definición de las variables','Tabla 3.3 Variables derivadas usadas por v1 y el candidato')
# Las descripciones se conservan desde la tabla editable ya contrastada con el código.
source=Document(backup)
orig=[[r.cells[0].text,r.cells[1].text+' Unidad: '+r.cells[2].text+'.'] for r in source.tables[13].rows[1:]]
table(['Variable derivada','Descripción'],orig,[1.65,4.75])
p('Monetary_Mean y Monetary_Std se calculan por línea de venta, no por pedido. Frequency cuenta pedidos distintos. Todas las variables usan el historial (corte − 365 días, corte]. Fuente: ML/features.py.')
h('Tabla 3.4 Objetivo e identificadores')
copied(14)
p('Los identificadores permiten alinear resultados con Krayin, pero no entran en el entrenamiento. La variable Churn se construye solo cuando existe observación completa de los 180 días futuros.')

page('Variables adicionales de la ronda experimental','Tabla 3.5 Variables derivadas temporales')
rows=[[r.cells[0].text,r.cells[1].text] for r in source.tables[15].rows[1:]]
table(['Variable derivada','Descripción'],rows,[2.35,4.05])
p('Las tres variables Orders y las tres Sales representan ventanas diferentes: junto con las cinco restantes suman once predictores nuevos. Los meses activos pueden abarcar partes de 13 meses calendario en una ventana de 365 días. Los intervalos se calculan entre pedidos distintos; su desviación se fija en cero cuando no hay dos intervalos.')
h('Tabla 3.6 Conjuntos comparados')
copied(16)
for cell in doc.tables[-1]._tbl.iter(qn('w:t')):
    cell.text=(cell.text or '').replace('Tabla B5','Tabla 3.3').replace('Tabla B7','Tabla 3.5')
p('Las once variables temporales fueron evaluadas, pero el candidato ganador empleó las siete originales. No se añadieron al contrato actual de la API. Fuente: ML/features_v2.py y ML/temporal_validation.py.')

page('Fase 2: Comprensión de Datos')
p('El CSV disponible contiene 9.800 líneas de venta, 4.922 pedidos y 793 clientes entre el 03/01/2015 y el 30/12/2018. Las 18 columnas describen pedidos, fechas, clientes, ubicación, productos y Sales. Una línea no equivale a un pedido ni a un cliente. Se exploran estructura, fechas, duplicados y disponibilidad de campos antes de agregar por cliente.')
picture('docs/evidencias_cap34/originales/pagina_23_imagen_1.jpg','Figura 3.3. Vista original del archivo plano conservada sin modificaciones. Fuente: InvestigacionTesis2026Original.pdf, página 23.')
picture('docs/evidencias_cap34/originales/pagina_23_imagen_2.png','Figura 3.4. Vista original de columnas y registros conservada sin modificaciones. Es evidencia de estructura; no representa el conjunto final de predictores.')
p('No se eliminaron duplicados exactos y se mantuvieron las 9.800 líneas. Los once códigos postales ausentes no afectan al modelo porque ese campo no es predictor. La prevalencia cambia por corte: E1 incluye 431 clientes elegibles y 101 abandonos futuros, equivalentes al 23,43 %. Los 362 restantes del catálogo no son elegibles en ese corte.')
p('Las imágenes muestran los datos de entrada. No prueban que se utilicen todas las columnas en el entrenamiento. Se excluyen nombres, identificadores, datos geográficos y fecha de envío como predictores del contrato vigente. La procedencia declarada y la huella del CSV se conservan en la documentación del dataset.')

page('Fase 3: Preparación de los Datos')
p('Se validan fechas con formato día/mes/año, identificadores y valores numéricos de venta. Se restringe el historial antes de agregar y se controla la cobertura temporal para construir etiquetas. No se normalizan indiscriminadamente todas las columnas: StandardScaler se usa solo en la regresión logística, ajustado con entrenamiento.')
picture('docs/evidencias_cap34/preparacion_actual.png','Figura 3.5. Preparación actual reconstruida desde ML/features.py y ML/features_v2.py. Las variables y la etiqueta se calculan en ventanas separadas.')
picture('docs/evidencias_cap34/cortes_temporales.png','Figura 3.6. Cortes de la ronda MEJ. Las etiquetas de cada bloque deben estar completas antes de utilizar el bloque siguiente. Fuente: protocol.json y manifiesto MEJ-03.')
p('D1 evalúa junio de 2017; D2, diciembre de 2017; E1, junio de 2018. Los nueve CSV de entrenamiento, calibración y evaluación tienen controles de población e integridad. E1 es exploratorio porque ese periodo ya se estudió en v1. No se aplica SMOTE en la ronda MEJ ni se mezclan ejemplos sintéticos con evaluación.')

page('Fase 4: Modelado')
p('La búsqueda MEJ cruza tres familias, dos configuraciones por familia y tres conjuntos de variables, produciendo 18 candidatos. Se entrena cada configuración con los mismos clientes de cada corte y se ajusta la sigmoide en un bloque posterior reservado. Se registra también la salida sin calibrar. Se selecciona únicamente con D1/D2 y se congela la política antes de E1.')
h('Tabla 3.7 Configuraciones explícitas de los modelos')
copied(17)
p('Se usa random_state=42, n_jobs=1 en árboles y verbosity=−1 en LightGBM. La logística incluye StandardScaler. No se ejecuta una búsqueda nueva sobre E1. La configuración seleccionada es lightgbm_original_a; la receta v1 reentrenada sirve como comparador y no se confunde con el archivo instalado.')
h('Tabla 3.8 Separación de datos para modelar')
table(['Corte','Entrenamiento','Calibración','Evaluación'],[
 ['D1','Junio 2016','Diciembre 2016','Junio 2017'],
 ['D2','Junio y diciembre 2016','Junio 2017','Diciembre 2017'],
 ['E1','Junio y diciembre 2016; junio 2017','Diciembre 2017','Junio 2018'],
],[.6,2.5,1.65,1.65])
p('El ajuste E1 del candidato utiliza 1081 observaciones cliente-corte de 678 clientes; la calibración tiene 510 y la evaluación 431. La repetición de clientes entre cortes debe considerarse al interpretar incertidumbre. Artefactos, parámetros y huellas están en docs/evidencias_mej04/ y docs/evidencias_mej06/.')

page('Fase 5: Evaluación')
p('Se comparan primero las medias no ponderadas de D1/D2. La tabla presenta la mejor configuración de cada familia según precisión al 20 %, seguida de AP y Brier para desempates. Los 18 resultados completos se muestran en el capítulo 4. La fila resaltada es el mejor candidato experimental; no implica autorización para sustituir el modelo en uso.')
best=[next(r for r in sel['ranking'] if r['id'].startswith(f)) for f in ['lightgbm_','forest_','logistic_']]
recipe=next(r for r in sel['comparators'] if r['id']=='baseline_v1_recipe')
t=table(['Configuración','Precisión 20 % ↑','AP ↑','Brier ↓'],[[r['id'].replace('_',' '),fmt(r['precision_at_20']),fmt(r['average_precision']),fmt(r['brier'])] for r in best+[recipe]],[2.5,1.3,1.3,1.3]); highlight(t)
picture('docs/evidencias_cap34/comparacion_desarrollo.png','Figura 3.7. Comparación por métrica de las mejores configuraciones de cada familia y la receta v1 reentrenada. Fuente: selection.json; D1/D2, no E1.',width=5.0)
p('Modelo que se utiliza: v1 instalado. El candidato gana en priorización, pero falla dos criterios de Brier en la aceptación: exceso medio de 0,011289 frente al constante y exceso E1 de 0,024680 frente al instalado, ambos superiores a 0,01. Se conserva v1 sin afirmar que su utilidad predictiva sea suficiente.')

page('Fase 6: Despliegue e Integración CRM')
p('La integración actual utiliza churn180-v1, LightGBM sin SMOTE calibrado con sigmoide. La API ofrece predicción individual, lotes de hasta 500 clientes y cálculo de variables sobre hasta 5.000 líneas de un cliente. El consumidor PHP verifica TLS, identidad y contrato; guarda solicitudes y las procesa con churn:work fuera de la petición web.')
p('El panel presenta probabilidades, categorías, variables, cortes e historial. Las sugerencias son reglas explícitas que priorizan calidad y elegibilidad, no acciones aprendidas ni campañas automáticas. La revisión manual guarda estado, responsable, nota, autor y fecha, con permisos separados. Los errores conservan la última predicción válida.')
h('Matriz de confusión y regla de clasificación')
p('Las matrices deben indicar la política que convierte una puntuación en selección. Para comparar el ranking se seleccionan exactamente 87 de los 431 clientes en ambas alternativas. Filas: clase observada; columnas: clase predicha; orden: no abandono y abandono. No se reutilizan las matrices antiguas del ensayo aleatorio de 159 clientes.')
picture('docs/evidencias_cap34/matrices_cupo20.png','Figura 3.8. Matrices E1 con cupo común del 20 %. v1: TP=15, FP=72, FN=86, TN=258. Candidato: TP=29, FP=58, FN=72, TN=272. Fuente: E1_predictions.csv, orden descendente y desempate por Customer ID.')
p('El candidato identifica 14 abandonos adicionales en el mismo cupo. Esa comparación no cambia los umbrales del panel. La política top-20 % es una evaluación relativa; la categoría de riesgo actual se calcula con umbrales fijos guardados en el artefacto.')

page('Despliegue y errores del modelo vigente','Matriz de confusión del umbral operativo')
p('El umbral medio vigente es 0,31121803153472; el alto es 0,37729508760356534. La matriz siguiente clasifica como positivo un resultado mayor o igual al umbral medio. Es distinta de seleccionar el 20 %: marca 429 de 431 clientes, por lo que obtiene recall del 100 % a costa de 328 falsos positivos.')
picture('docs/evidencias_cap34/matriz_vigente.png','Figura 3.9. Matriz actual de v1 en E1 al umbral medio. Recalculada desde E1_predictions.csv y contrastada con metadata.json. La clase positiva significa ausencia futura de compra, no una cancelación declarada.',width=4.9)
table(['Medida','Resultado','Lectura'],[
 ['Precision','0,235431','101 abandonos entre 429 marcados.'],
 ['Recall','1,000000','Se detectan los 101 abandonos del corte.'],
 ['F1 / F2','0,381132 / 0,606242','El resultado depende del umbral; no acredita priorización útil.'],
 ['Accuracy','0,238979','Pocos aciertos negativos; 328 falsas alarmas.'],
],[1.3,1.8,3.3])
p('A 0,50, v1 no marca abandonos: su accuracy de 76,57 % refleja la clase mayoritaria. Ninguno de estos resultados justifica ejecutar acciones automáticas. La seguridad técnica utiliza HTTPS, autenticación, límites de entrada y control de concurrencia; la aceptación local y sus límites se presentan en el capítulo siguiente.')

page('Capítulo 4. Resultados','4.1. Resultados predictivos del corte E1')
p('El corte del 30/06/2018 contiene 431 clientes elegibles y 101 abandonos futuros. Se compara el candidato congelado con el artefacto v1 instalado, la receta v1 reentrenada, recencia y una probabilidad constante del entrenamiento. E1 es una aceptación exploratoria sobre datos ya observados; no es evidencia prospectiva independiente.')
copied(8)
for row_idx in [1,5]:
    highlight(doc.tables[-1], row_idx)
caption('Filas resaltadas: candidato experimental con mejor priorización E1 y v1 instalado, que se mantiene en uso. La promoción exige cumplir todos los criterios, no solo ganar en precisión.')
picture('docs/evidencias_mej08/graficas/comparacion_e1.png','Figura 4.1. Métricas E1 de las cinco alternativas. Fuente: docs/evidencias_mej06/aceptacion/metrics.json. Precisión y AP: mayor es mejor; Brier: menor es mejor.')
p('El candidato obtiene precisión al 20 % de 33,33 %, frente a 17,24 % de v1 instalado y 25,29 % de recencia. Su ROC-AUC es 0,556466 y su log-loss 0,635648. El artefacto instalado conserva ROC-AUC 0,4571, AP 0,2119 y Brier 0,1967. La probabilidad constante no ordena riesgo: su precisión en el cupo depende del desempate por ID.')
p('Decisión de uso: conservar v1. Los dos incumplimientos de Brier impiden promover al candidato, aunque la precisión de la selección mejore. MEJ-07 no aplica en esta ronda. Los intervalos y el resultado negativo se conservan sin modificar retrospectivamente los criterios.')

page('4.2. Comparación de modelos de la versión v1')
p('La evaluación inicial comparó seis alternativas en diciembre de 2017, con 510 clientes. Se eligió LightGBM sin SMOTE por la mayor AP de validación. Estos valores describen la elección histórica de v1; no son resultados de E1 ni se mezclan con las medias de D1/D2 de la ronda MEJ.')
hist=sorted(v1['validation'],key=lambda r:r['average_precision'],reverse=True)
t=table(['Modelo','AP ↑','ROC-AUC ↑','Brier ↓'],[[r['model'].replace('_SMOTE',' + SMOTE'),fmt(r['average_precision']),fmt(r['roc_auc']),fmt(r['brier'])] for r in hist],[2.5,1.3,1.3,1.3]); highlight(t)
picture('docs/evidencias_cap34/comparacion_v1.png','Figura 4.2. Comparación original de v1 por métrica, reconstruida desde metadata.json. Se resalta LightGBM sin SMOTE, modelo conservado en la integración actual.')
p('La AP de 0,474601 superó ligeramente a Random Forest, 0,471911; no se afirma significación estadística de esa diferencia. SMOTE no produjo una mejora uniforme. En E1, el artefacto seleccionado perdió capacidad de ordenación: ROC-AUC 0,457126 y AP 0,211924. El despliegue técnico no modifica esas limitaciones.')

page('4.3. Comparación completa de candidatos','Tabla 4.3 Resultados medios D1 y D2')
p('La selección de desarrollo compara 18 configuraciones. Se resalta la primera de la clasificación por precisión al 20 %, AP y Brier. Las diferencias pequeñas entre filas no constituyen por sí solas evidencia estadística de superioridad.')
t=table(['Configuración','N.º','Precisión 20 %','AP','Brier'],[[r['id'].replace('_',' '),str(r['feature_count']),f'{r["precision_at_20"]:.4f}'.replace('.',','),f'{r["average_precision"]:.4f}'.replace('.',','),f'{r["brier"]:.4f}'.replace('.',',')] for r in sel['ranking']],[2.65,.7,1.15,.95,.95]); highlight(t)
p('El ganador lightgbm_original_a utiliza siete predictores originales. La mejor configuración de bosque es forest_original_a y la mejor logística es logistic_temporal_b. Agregar once variables temporales no garantizó mejora. Fuente: docs/evidencias_mej04/comparacion/selection.json; parámetros completos en la fase 4 y anexo B.')

page('4.4. Calibración y calidad de las probabilidades')
picture('docs/evidencias_mej08/graficas/calibracion_desarrollo.png','Figura 4.3. Calibración en D1/D2; intervalos de ancho 0,10, sin intervalos de confianza y omitiendo vacíos. Fuente: calibration_bins.json. La diagonal representa coincidencia entre probabilidad y frecuencia observada.')
copied(22)
p('La sigmoide fue seleccionada por la prioridad fijada, pero incrementó el Brier medio de desarrollo. En D1 invirtió el ranking; en D2 lo conservó. No debe afirmarse que calibrar siempre mejora la fiabilidad fuera del corte donde se ajustó. Los tamaños de cada intervalo se conservan en el archivo de evidencia.')
h('Tabla 4.4 Criterios de Brier incumplidos')
copied(11)
p('La media no ponderada del Brier del candidato es 0,252908 y la del constante 0,241619. En E1, el candidato alcanza 0,221384 y el instalado 0,196703. Se aprobaron 16 comprobaciones y fallaron dos. La mayor capacidad de ordenar clientes no compensa automáticamente estos errores probabilísticos.')

page('4.5. Variación temporal e incertidumbre')
picture('docs/evidencias_mej08/graficas/precision_temporal.png','Figura 4.4. Precisión al 20 % por corte. Fuente: metrics.json. Las poblaciones cambian entre cortes; las líneas no representan una tendencia causal ni un pronóstico.')
picture('docs/evidencias_mej08/graficas/intervalos_bootstrap.png','Figura 4.5. Diferencias medias de D1/D2/E1 con 1000 remuestreos pareados por cliente. Punto: diferencia observada; segmento: intervalo descriptivo del 95 %. Fuente: bootstrap.json.')
p('Los intervalos de mejora de precisión fueron [0,002337; 0,157118] frente a recencia y [0,014615; 0,185326] frente a la receta v1. Los de AP incluyeron cero. Las 1000 réplicas fueron válidas. El remuestreo mantiene la dependencia entre observaciones de un mismo cliente, pero no corrige la selección previa ni aporta datos nuevos.')

page('4.6. Cupos y consecuencias de la selección')
copied(20)
copied(21)
p('Los cupos del 10 %, 20 % y 30 % seleccionan 44, 87 y 130 clientes. En el 20 %, el candidato identifica 29 de los 101 abandonos: recall de 28,71 % y lift de 1,422442. Aumentar el cupo al 30 % eleva el recall al 32,67 %, pero reduce la precisión al 25,38 %. No existe un presupuesto comercial observado que permita elegir por rentabilidad.')
picture('docs/evidencias_cap34/matrices_cupo20.png','Figura 4.6. Distribución de aciertos y errores con capacidad idéntica. Fuente: docs/evidencias_cap34/matrices.json. La comparación se realiza con el mismo corte, etiquetas y número de seleccionados.')
p('En MEJ-05, diez de doce combinaciones de umbral pudieron producir el tamaño exacto en calibración; dos fueron incompatibles por empates. Un umbral obtenido en calibración no garantiza seleccionar la misma proporción en evaluación. Los cupos relativos no sustituyen silenciosamente los umbrales Alto/Medio/Bajo del CRM.')
p('El análisis histórico ML-06 usó también costos abstractos de errores. Esos escenarios no son pérdidas monetarias ni efectos de una campaña y no se suman a las métricas de MEJ como si fueran un experimento independiente.')

# Conserva íntegra la evidencia técnica y de interfaz, con numeración actualizada.
for block in technical_blocks:
    for node in block.iter(qn('w:t')):
        node.text=(node.text or '').replace('4.5 Verificación técnica','4.7. Verificación técnica').replace('4.6 Aceptación técnica integral','4.8. Aceptación técnica integral').replace('4.7 Seguimiento manual de demostración','4.9. Seguimiento manual de demostración').replace('Figura 4. Registro manual','Figura 4.7. Registro manual')
    body.insert(len(body)-1,block)

# Reubica todos los bloques nuevos antes del capítulo 5; conserva relaciones de imágenes.
new=[e for e in list(body) if e not in before and e.tag!=qn('w:sectPr')]
for e in new: body.remove(e)
pos=list(body).index(end)
for i,e in enumerate(new): body.insert(pos+i,e)
doc.save(target)
print('Capítulos 3 y 4 reestructurados; imágenes originales recuperadas y conservadas.')
