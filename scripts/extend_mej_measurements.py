"""Añade diccionario de variables, parámetros, métricas y figuras MEJ."""
import ast
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
backup = ROOT / 'docs/historico/InvestigacionTesis2026_antes_mediciones_MEJ.docx'
if not backup.exists():
    shutil.copy2(target, backup)
doc = Document(backup)
# Reutiliza solo los dos helpers de formato, sin ejecutar el autor anterior.
tree = ast.parse((ROOT / 'scripts/add_improvement_tables.py').read_text(encoding='utf-8'))
helpers = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'p','table'}], type_ignores=[])
exec(compile(helpers, '<table_helpers>', 'exec'))
metrics = json.loads((ROOT / 'docs/evidencias_mej06/aceptacion/metrics.json').read_text())
configs = json.loads((ROOT / 'ML/experiments/churn180-v2/candidates_mej04.json').read_text())['candidates']
def page(title, subtitle):
    heading = p(title, 'Heading 1')
    heading.paragraph_format.page_break_before = True
    p(subtitle, 'Heading 2')
def fig(name, caption):
    doc.add_picture(str(ROOT / 'docs/evidencias_mej08/graficas' / name), width=Inches(6.3))
    para = p(caption)
    for r in para.runs:
        r.font.size = Pt(10)
def fmt(v):
    return f'{v:.6f}'.replace('.', ',')

page('Variables usadas en los modelos', 'B5 Variables originales y población de estudio')
p('La unidad de análisis es cliente por fecha de corte. Se usan transacciones en (corte − 365 días, corte] y clientes cuya última compra ocurrió como máximo 180 días antes del corte. Estas siete variables alimentan tanto v1 como el candidato seleccionado lightgbm_original_a.')
p('Tabla B5 Diccionario de las siete variables originales', 'Heading 3')
table(['Variable', 'Cálculo en el historial', 'Unidad'], [
    ['Recency', 'Días desde la última compra hasta el corte.', 'Días'],
    ['Frequency', 'Número de Order ID distintos; un pedido con varias líneas cuenta una vez.', 'Pedidos'],
    ['Monetary_Sum', 'Suma de Sales de las líneas del cliente.', 'Unidad monetaria del CSV'],
    ['Monetary_Mean', 'Media de Sales por línea; no es el importe medio por pedido.', 'Unidad monetaria del CSV'],
    ['Monetary_Std', 'Desviación estándar muestral de Sales por línea; 0 si no puede estimarse.', 'Unidad monetaria del CSV'],
    ['Cat_Count', 'Cantidad de categorías distintas compradas.', 'Categorías'],
    ['SubCat_Count', 'Cantidad de subcategorías distintas compradas.', 'Subcategorías'],
], [1.55, 3.35, 1.5])
p('Tabla B6 Etiqueta y campos de control', 'Heading 3')
table(['Campo', 'Uso'], [
    ['Churn', 'Objetivo: 1 si no hay compra en (corte, corte + 180 días]; 0 si la hay. No es predictor.'],
    ['Customer ID', 'Agrupación, alineación, remuestreo y desempate; no es predictor.'],
    ['cutoff', 'Fecha de observación y separación temporal; no es predictor.'],
], [1.55, 4.85])
p('La etiqueta requiere cobertura completa del horizonte futuro. Los predictores solo usan el historial anterior al corte. Fuente: ML/features.py y ML/experiments/churn180-v2/protocol.json. No se incorporaron datos comerciales adicionales al dataset acordado.')

page('Variables temporales evaluadas', 'B6 Once variables nuevas y conjuntos comparados')
p('Estas variables se implementaron y probaron en la ronda MEJ. No forman parte del candidato ganador ni del contrato actual de inferencia. Las ventanas excluyen su límite inferior e incluyen la fecha de corte.')
p('Tabla B7 Diccionario temporal', 'Heading 3')
table(['Variables', 'Definición y tratamiento'], [
    ['Orders_30d\nOrders_90d\nOrders_180d', 'Número de pedidos distintos en los últimos 30, 90 y 180 días, respectivamente. Cero si no hay pedidos.'],
    ['Sales_30d\nSales_90d\nSales_180d', 'Suma de Sales por línea en los últimos 30, 90 y 180 días. Cero si no hay ventas en la ventana.'],
    ['Recent90_To_Prior90_\nOrder_Ratio', '(Pedidos de últimos 90 días + 1) / (pedidos de los 90 días anteriores + 1). El suavizado evita división por cero.'],
    ['ActiveMonths_365d', 'Meses calendario distintos con compra dentro de 365 días; la ventana puede abarcar partes de 13 meses.'],
    ['MeanOrderGapDays', 'Media de días entre pedidos consecutivos distintos; 0 si no existen intervalos.'],
    ['StdOrderGapDays', 'Desviación estándar muestral de intervalos; 0 con menos de dos intervalos. Pedidos del mismo día generan intervalo 0.'],
    ['HasMultipleOrders', '1 con al menos dos pedidos distintos en el historial; 0 en otro caso. Ayuda a interpretar ausencia de historial de intervalos.'],
], [2.35, 4.05])
p('Tabla B8 Conjuntos de predictores comparados', 'Heading 3')
table(['Conjunto', 'Cantidad', 'Composición'], [['original', '7', 'Tabla B5; seleccionado.'], ['temporal', '11', 'Tabla B7; evaluado.'], ['combined', '18', 'Original + temporal; evaluado.']], [1.5, 1, 3.9])
p('Fuente: ML/features_v2.py y ML/temporal_validation.py. Las variables se calculan sobre clientes elegibles comunes, sin utilizar compras futuras.')

page('Hiperparámetros de la comparación', 'B7 Configuraciones reproducibles')
p('Se cruzaron seis configuraciones con los tres conjuntos de variables (7, 11 y 18): 18 candidatos. Para cada familia y variante se mantuvieron los mismos parámetros al cambiar de conjunto. La selección usó D1/D2; E1 no se usó para elegir hiperparámetros.')
p('Tabla B9 Parámetros explícitos de las seis configuraciones', 'Heading 3')
rows = []
for c in configs[:6]:
    params = dict(c['params'])
    params.pop('random_state', None)
    params.pop('n_jobs', None)
    params.pop('verbosity', None)
    rows.append([c['family'] + ' ' + c['id'][-1], '; '.join(f'{k}={v}' for k,v in params.items())])
table(['Familia y variante', 'Hiperparámetros'], rows, [1.5, 4.9])
p('En todos los candidatos: random_state=42. Random Forest y LightGBM: n_jobs=1; LightGBM: verbosity=−1. La regresión logística usa StandardScaler ajustado al entrenamiento. No se utilizó SMOTE. Los parámetros no especificados conservan los valores por defecto de las bibliotecas del entorno registrado.')
p('Tabla B10 Configuración vigente y candidato seleccionado', 'Heading 3')
table(['Aspecto', 'v1 instalado', 'Candidato MEJ'], [
    ['Estimador', 'LightGBM', 'lightgbm_original_a'],
    ['Árboles / profundidad / hojas', '150 / 3 / 7', '100 / 2 / 4'],
    ['learning_rate', '0,05', '0,03'],
    ['Predictores', 'Siete originales', 'Siete originales'],
    ['Calibración', 'Sigmoide', 'Sigmoide seleccionada en MEJ-05'],
], [2.2, 2.1, 2.1])
p('La calibración se ajusta en un corte reservado posterior al entrenamiento. El candidato fija min_child_samples=20 y reg_lambda=1,0. Fuente completa: ML/experiments/churn180-v2/candidates_mej04.json; implementación v1: ML/train.py; política: docs/evidencias_mej05/calibracion/frozen_policy.json.')

page('Métricas para medir el desempeño', 'B8 Definición e interpretación')
p('La clase positiva es abandono. TP, FP, FN y TN representan aciertos positivos, falsos positivos, falsos negativos y aciertos negativos. Para un cupo q, k es el entero superior de q × N. Se ordena por puntuación descendente y se desempata por Customer ID.')
p('Tabla B11 Métricas y sentido de mejora', 'Heading 3')
table(['Métrica', 'Cálculo o definición', 'Interpretación'], [
    ['Precisión al k', 'TP entre los k seleccionados, dividido por k.', 'Mayor: más abandonos identificados en el cupo. Principal: 20 %.'],
    ['Recall al k', 'TP entre los k seleccionados / total de abandonos.', 'Mayor: cubre más abandonos; depende del cupo.'],
    ['Lift al k', 'Precisión al k / prevalencia del abandono.', 'Mayor que 1: concentración superior a la prevalencia.'],
    ['AP', 'Suma de los incrementos de recall multiplicados por la precisión de cada umbral.', 'Mayor es mejor. No es el área trapezoidal de la curva PR.'],
    ['ROC-AUC', 'Probabilidad de ordenar un positivo por encima de un negativo; empates cuentan la mitad.', 'Mayor es mejor; 0,5 es referencia de ordenación aleatoria.'],
    ['Brier', 'Media de los cuadrados de la diferencia entre probabilidad y etiqueta 0/1.', 'Menor es mejor. Evalúa el error probabilístico global.'],
    ['Log-loss', 'Media negativa de y·ln(p) + (1−y)·ln(1−p); p se acota numéricamente.', 'Menor es mejor. Penaliza errores con alta confianza.'],
    ['Curva de calibración', 'Probabilidad media frente a frecuencia observada por intervalos.', 'Cercanía a la diagonal; depende de tamaño y población de cada intervalo.'],
], [1.2, 2.85, 2.35])
p('Accuracy = (TP + TN) / N; F1 = 2TP / (2TP + FP + FN); F2 = 5TP / (5TP + 4FN + FP). Estas medidas dependen del umbral de clasificación y no sustituyen la evaluación del ranking. La matriz de confusión separa los cuatro conteos de error/acierto.')
p('Fuentes de implementación: ML/compare_v2.py y ML/evaluation.py. Las gráficas de MEJ representan resultados exploratorios; no miden fidelización, rentabilidad ni efectos causales.')

page('Mediciones del corte final exploratorio', 'B9 Comparación E1 y selección por cupo')
p('Figura B1 Comparación de cinco alternativas en E1', 'Heading 3')
fig('comparacion_e1.png', 'Fuente: docs/evidencias_mej06/aceptacion/metrics.json. Mayor precisión y AP son favorables; menor Brier es favorable. La receta v1 se reentrena por corte y difiere del artefacto instalado. La constante no ordena riesgo.')
p('Tabla B12 Mediciones adicionales del candidato en E1', 'Heading 3')
e = metrics['E1']['candidate']
table(['Cupo', 'Seleccionados', 'Precisión', 'Recall', 'Lift'], [[str(k)+' %', str(e[f'selected_{k}']), fmt(e[f'precision_at_{k}']), fmt(e[f'recall_at_{k}']), fmt(e[f'precision_at_{k}']/(101/431))] for k in [10,20,30]], [0.7,1.25,1.45,1.5,1.5])
table(['ROC-AUC', 'Log-loss', 'Prevalencia E1'], [[fmt(e['roc_auc']), fmt(e['log_loss']), '101 / 431 = '+fmt(101/431)]], [2.1,2.1,2.2])
p('Con el cupo del 20 %, TP=29, FP=58, FN=72 y TN=272. Se identifica el 28,71 % de los abandonos. Ampliar el cupo al 30 % aumenta el recall, pero reduce la precisión; estos cupos son escenarios académicos y no capacidades comerciales medidas.')
p('La evaluación completa conserva v1 porque el candidato incumple los criterios de Brier. El resultado no autoriza campañas automáticas ni demuestra que v1 tenga utilidad predictiva suficiente.')

page('Estabilidad temporal e incertidumbre', 'B10 Resultados por corte e intervalos descriptivos')
fig('precision_temporal.png', 'Figura B2. Precisión al 20 % en D1, D2 y E1. Fuente: metrics.json. Los cortes tienen poblaciones diferentes; las líneas permiten comparar variación temporal, no representan una mejora continua ni un pronóstico.')
fig('intervalos_bootstrap.png', 'Figura B3. Diferencias medias no ponderadas de D1/D2/E1. Punto: diferencia observada; segmento: intervalo percentil descriptivo del 95 %, con 1000 remuestreos pareados por cliente. Fuentes: metrics.json y bootstrap.json.')
p('Los intervalos de precisión quedan por encima de cero frente a ambas referencias, pero los de AP incluyen cero. El remuestreo conserva los cortes de un mismo cliente y no corrige la selección previa del modelo. E1 ya se había analizado en etapas anteriores: no constituye una prueba independiente.')

page('Calibración de las probabilidades', 'B11 Comparación en los cortes de desarrollo')
fig('calibracion_desarrollo.png', 'Figura B4. Probabilidad media y abandono observado en intervalos de ancho 0,10; se omiten intervalos vacíos. Fuente: docs/evidencias_mej05/calibracion/calibration_bins.json. Las líneas conectan medias de intervalos; no son ajustes continuos ni incluyen intervalos de confianza.')
p('La sigmoide fue seleccionada por la prioridad preestablecida de precisión al 20 %, AP y Brier. En D1 invirtió el orden de las puntuaciones y en D2 lo conservó. La calibración no garantiza por sí sola una mejora de las probabilidades fuera del corte donde se ajustó.')
table(['D1/D2 media', 'Sin calibrar', 'Sigmoide', 'Interpretación'], [['Precisión al 20 %', '0,419635', '0,518227', 'Mejoró el ranking con la regla fijada.'], ['AP', '0,426186', '0,458369', 'Mejoró la media de desarrollo.'], ['Brier', '0,252945', '0,268670', 'Empeoró el error probabilístico.']], [1.6,1.3,1.3,2.2])
p('La comparación de desarrollo no reemplaza la aceptación E1. Las probabilidades concentradas en pocos intervalos hacen menos informativa la curva; conviene leerla junto con Brier, prevalencia y tamaños por intervalo. Los conteos se conservan en calibration_bins.json.')
p('Archivos para capturas: docs/evidencias_mej08/graficas/ contiene las cuatro figuras PNG. Las tablas B5–B12 y figuras B1–B4 complementan las tablas B1–B4. No se entrenaron nuevos modelos para elaborar estas páginas.')
doc.save(target)
print('Variables, hiperparámetros, métricas y cuatro figuras añadidas.')
