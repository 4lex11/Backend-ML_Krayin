"""Actualiza la tesis con evidencia local; usar el Python documental empaquetado."""

import csv
import io
import json
import shutil
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "InvestigacionTesis2026.docx"
BACKUP = ROOT / "docs/historico/InvestigacionTesis2026_original.docx"
M = json.loads((ROOT / "ML/artifacts/churn180-v1/metadata.json").read_text())


def build():
    if not BACKUP.exists():
        shutil.copy2(SOURCE, BACKUP)
    doc = Document(BACKUP)
    defaults = Document()
    for style in defaults.styles:
        if style.name not in doc.styles:
            doc.styles.element.append(deepcopy(style.element))
    body = doc._element.body
    for element in list(body):
        if element.tag != qn("w:sectPr"):
            body.remove(element)
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Cm(2.3)
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.header_distance = sec.footer_distance = Cm(1.1)
    for name in ["Normal", "Title", "Heading 1", "Heading 2", "Caption", "List Bullet"]:
        if name not in doc.styles:
            doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.size = Pt(11)
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.line_spacing = 1.12
        style.paragraph_format.widow_control = True
    doc.styles["Title"].font.size = Pt(20)
    doc.styles["Heading 1"].font.size = Pt(16)
    doc.styles["Heading 2"].font.size = Pt(12)
    doc.styles["Caption"].font.size = Pt(9)
    for name in ["Heading 1", "Heading 2"]:
        doc.styles[name].paragraph_format.keep_with_next = True
        doc.styles[name].paragraph_format.space_before = Pt(9)
    footer = sec.footer.paragraphs[0]
    footer.clear()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    footer._p.append(fld)

    def p(text, style=None):
        return doc.add_paragraph(text, style)

    def h(text):
        doc.add_heading(text, level=2)

    def page(title):
        doc.add_page_break()
        doc.add_heading(title, level=1)

    def table(headers, rows):
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        for c, value in zip(t.rows[0].cells, headers):
            c.text = value
            for r in c.paragraphs[0].runs:
                r.bold = True
        repeat = OxmlElement("w:tblHeader")
        t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for values in rows:
            for c, value in zip(t.add_row().cells, values):
                c.text = str(value)
        for row in t.rows:
            prevent = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(prevent)
            for c in row.cells:
                for para in c.paragraphs:
                    para.paragraph_format.space_after = Pt(4)
                    para.paragraph_format.space_before = Pt(4)
                    for r in para.runs:
                        r.font.size = Pt(9)
        p("")

    def figure(relative, caption, width=15.5):
        paragraph = p("")
        paragraph.paragraph_format.keep_with_next = True
        paragraph.add_run().add_picture(str(ROOT / relative), width=Cm(width))
        p(caption, "Caption")

    # Conserva la identidad institucional y los autores del original.
    with ZipFile(BACKUP) as z:
        images = [n for n in z.namelist() if n.startswith("word/media/")]
        if images:
            para = p("")
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.add_run().add_picture(io.BytesIO(z.read(images[0])), width=Cm(5))
    for text in ["FACULTAD DE INGENIERÍA", "Carrera de Sistemas Computacionales"]:
        p(text).alignment = WD_ALIGN_PARAGRAPH.CENTER
    p("")
    para = p("Aplicación de ML para mejorar la gestión y fidelización de clientes en un sistema CRM", "Title")
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p("Evaluación retrospectiva con Superstore Sales y prototipo local").alignment = WD_ALIGN_PARAGRAPH.CENTER
    p("")
    for text in ["Trabajo de investigación", "Autores", "Alejandra Alfaro de la cruz", "Alex Noe Álvarez Hernandez", "Asesor", "Fernando Alex Sierra Liñan", "ORCID 0000-0002-0687-3377", "Lima Perú", "2026"]:
        p(text).alignment = WD_ALIGN_PARAGRAPH.CENTER

    page("Resumen")
    p("Esta investigación evalúa la aplicación de Machine Learning a la estimación de ausencia de recompra y desarrolla un servicio de inferencia preparado para una futura integración con un CRM. Se utiliza exclusivamente el dataset Superstore Sales disponible, con 9.800 líneas de venta, 4.922 pedidos y 793 clientes. El resultado de interés se define como ninguna compra durante los 180 días posteriores al corte; los predictores se calculan con los 365 días anteriores.")
    p("Se comparan Random Forest, XGBoost y LightGBM con y sin SMOTE mediante particiones temporales de entrenamiento, calibración, validación y test. LightGBM sin SMOTE presenta la mayor average precision de validación, 0,4746. En el test de 431 clientes obtiene ROC-AUC 0,4571 y average precision 0,2119, sin evidenciar utilidad predictiva suficiente frente a referencias simples. La calibración mejora el Brier respecto al estimador sin calibrar, pero no corrige las limitaciones de priorización.")
    p("El backend implementa HTTPS, autenticación, validación de entradas, lotes y control de carga. La suite posterior al análisis ML-06 registra 98 pruebas aprobadas y 95,14 % de cobertura Python. Se concluye que el prototipo es técnicamente reproducible, pero no se ha demostrado una mejora real de fidelización: no se ejecutaron campañas ni se integró una instalación real de Krayin. El estudio conserva el carácter experimental del modelo y delimita la validación comercial como trabajo futuro.")
    p("Palabras clave: aprendizaje automático, CRM, recompra, abandono, validación temporal, calibración.")
    h("Organización del documento")
    p("El capítulo 1 establece el problema y los objetivos; el capítulo 2 define datos y método; el capítulo 3 describe la implementación; el capítulo 4 presenta los resultados; el capítulo 5 discute su alcance; y el capítulo 6 expone las conclusiones. Las referencias y el anexo final permiten localizar la evidencia reproducible.")

    page("Capítulo 1 Introducción")
    h("1.1 Problema y delimitación")
    p("Una herramienta de gestión de clientes necesita distinguir entre almacenar información y convertirla en una prioridad de atención útil. En este proyecto se estudia si el historial de compras permite estimar ausencia de recompra y se prepara un mecanismo para comunicar esas estimaciones a un CRM. La pregunta no se resuelve demostrando que una API responde: también es necesario comprobar que el modelo distingue resultados futuros de forma útil.")
    p("El problema de investigación es determinar qué capacidad predictiva y qué viabilidad técnica ofrece un sistema de ML basado en Superstore Sales para apoyar una futura gestión de clientes en un CRM. El título expresa la finalidad de mejorar esa gestión y la fidelización; el alcance ejecutado es retrospectivo y técnico, por lo que no presupone que tal mejora haya ocurrido.")
    h("1.2 Objetivo general")
    p("Evaluar un modelo de predicción de ausencia de recompra a 180 días y desarrollar un prototipo local reproducible de servicio de inferencia para una futura integración con un CRM, identificando su desempeño y limitaciones con el dataset disponible.")
    h("1.3 Objetivos específicos")
    for text in ["Definir una etiqueta futura y variables históricas coherentes, sin utilizar compras posteriores al corte como predictores.", "Comparar tres familias de modelos, con y sin SMOTE, bajo el mismo protocolo temporal y con referencias simples.", "Analizar calibración, umbrales y escenarios hipotéticos de capacidad, sin confundir pérdidas de clasificación con rentabilidad.", "Separar ML del backend y verificar contrato, seguridad, carga y despliegue local.", "Documentar resultados y condiciones necesarias para una futura validación en Krayin."]:
        p(text, "List Bullet")
    h("1.4 Criterio de contraste")
    p("Se examina si el modelo seleccionado aporta una ordenación del riesgo superior a una referencia simple de recencia en el periodo reservado. No se plantea como hipótesis ya contrastada un aumento causal de retención o satisfacción. La conclusión debe admitir un resultado negativo o inconcluso y diferenciarlo del funcionamiento correcto del software.")

    page("Capítulo 2 Metodología de investigación")
    h("2.1 Tipo enfoque y diseño")
    p("El estudio es aplicado en su finalidad tecnológica y cuantitativo en su evaluación. El diseño ejecutado es observacional retrospectivo con evaluación predictiva temporal y pruebas de software. No es un estudio cuasiexperimental pre y posintervención: no se aplicó una intervención comercial, no se asignaron grupos y no se midieron cambios causados por el sistema. Su alcance es descriptivo, predictivo y de viabilidad técnica, sin inferencia causal sobre fidelización.")
    h("2.2 Fuente e instrumentos")
    p("Se analiza el CSV local train.csv cuya fuente indicada es Superstore Sales Dataset, de Rohit Sahoo, en Kaggle [1]. Los metadatos consultados declaran versión 2, actualización en septiembre de 2020 y licencia GPL 2. Se conserva un hash SHA-256 para identificar el archivo analizado; no se comprobó igualdad binaria con una descarga remota. Los instrumentos son funciones de preparación de datos, un protocolo JSON, scripts de evaluación, registros de pruebas y tablas de resultados generadas por código.")
    p("Las columnas observadas corresponden a cliente, pedido, producto, fechas, geografía y ventas. No incluyen satisfacción, tickets de soporte, costos de contacto ni resultados de campañas. Los 11 códigos postales faltantes no se usan como predictores. La auditoría registra cero duplicados exactos eliminados; los errores de dominio no se imputan silenciosamente.")
    h("2.3 Población muestra y selección")
    p("El corpus accesible contiene 9.800 líneas de venta, 4.922 pedidos y 793 clientes entre el 3 de enero de 2015 y el 30 de diciembre de 2018. No es una muestra probabilística de clientes de una empresa identificada. Se utiliza una fuente secundaria disponible y se incluyen determinísticamente los clientes elegibles de cada corte con seguimiento futuro completo. La unidad analítica es cliente-corte; los tamaños de ventanas no deben sumarse como personas distintas.")
    table(["Uso", "Corte", "Observaciones", "Abandonos"], [[s["role"], s["cutoff"], s["n"], s["churn"]] for s in M["splits"]])

    page("Metodología temporal y variables")
    h("2.4 Etiqueta y ventanas")
    p("Se considera abandono operacional la ausencia de compras en el intervalo posterior al corte hasta 180 días inclusive. Las variables usan compras posteriores a corte menos 365 días y hasta el corte inclusive. La población elegible tiene última compra hace 180 días o menos. Clientes sin compras o ya inactivos fuera de ese plazo se excluyen de esta población, sin asignarles una probabilidad ficticia.")
    p("El entrenamiento concatena los cortes de junio y diciembre de 2016. La calibración usa junio de 2017; la validación diciembre de 2017; y el test junio de 2018, con seguimiento hasta el 27 de diciembre de 2018. Cada ventana de resultado termina antes del siguiente corte. Los clientes pueden reaparecer en periodos posteriores, de modo que el diseño evalúa una cartera conocida en el tiempo.")
    h("2.5 Predictores y reglas de calidad")
    table(["Variable", "Definición"], [["Recency", "Días desde la última compra; entre 0 y 180"], ["Frequency", "Pedidos distintos durante la ventana anual"], ["Monetary_Sum", "Suma de ventas por línea"], ["Monetary_Mean", "Media por línea; no ticket medio por pedido"], ["Monetary_Std", "Desviación muestral por línea; cero con una sola línea"], ["Cat_Count", "Categorías distintas"], ["SubCat_Count", "Subcategorías distintas"]])
    p("Las fechas del CSV se interpretan como día/mes/año. Se rechazan fechas inválidas, valores no finitos, importes negativos e inconsistencias de pedido. Las devoluciones deben resolverse en origen antes de usar el contrato. Los identificadores permiten unir datos, pero no se incluyen como predictores. Una compra única se admite con una marca de historial limitado; la cobertura declarada debe verificarse si se integra un origen real.")

    page("Evaluación y consideraciones éticas")
    h("2.6 Entrenamiento y selección")
    p("Se comparan Random Forest, XGBoost y LightGBM, cada uno con y sin SMOTE. El escalado y el sobremuestreo se ajustan dentro del pipeline de entrenamiento, sin aplicarlos a validación o test. Esta separación evita la forma de fuga de información asociada a transformar o sobremuestrear todo el dataset antes de separar la evaluación [2, 3]. Se usa semilla 42 y versiones de dependencias fijadas.")
    p("La calibración sigmoide se ajusta con el estimador congelado y una ventana separada. El candidato se elige por mayor average precision de validación y, en empate, menor Brier. El umbral medio maximiza F2 con desempates por precisión y umbral; el alto se relaciona con el quintil superior de validación y se fuerza a ser mayor que el medio. Las decisiones se guardan antes de calcular las métricas de test en el flujo de entrenamiento.")
    h("2.7 Métricas e incertidumbre")
    p("Se informan precision, recall, F1, F2, accuracy, ROC-AUC, average precision, Brier y matrices de confusión. Average precision resume la curva precisión-recall y no se presenta como un área trapezoidal idéntica. Se comparan la probabilidad constante del entrenamiento y una regla de recencia. Se calculan 500 remuestreos bootstrap de clientes del corte final para intervalos percentiles del 95 %.")
    p("Brier y log-loss evalúan errores de probabilidades y no aíslan por sí solos todos los aspectos de calibración; se complementan con curvas que agrupan predicciones [4]. Los intervalos del test no describen incertidumbre entre años. El análisis posterior de ML-06 es retrospectivo sobre un test ya observado, por lo que no constituye una nueva confirmación independiente.")
    h("2.8 Aspectos éticos y límites de uso")
    p("La disponibilidad pública del CSV no demuestra anonimización: contiene nombres e identificadores. Las evidencias se presentan agregadas o mediante IDs de demostración, sin publicar secretos de API ni datos personales innecesarios. Se registra la licencia declarada de la fuente. No se garantiza ausencia de sesgos ni se automatizan campañas: la respuesta del servicio mantiene estado experimental y automatic_action_allowed=false.")

    page("Capítulo 3 Metodología de implementación")
    h("3.1 Separación y reproducibilidad")
    p("El módulo ML contiene preparación compartida, entrenamiento, evaluación e inferencia. El backend Python expone el modelo mediante HTTP; los prototipos de importación se conservan en integraciones/krayin y no son prueba de una conexión real. El artefacto model.joblib se acompaña de metadata.json, con variables, ventanas, métricas, umbrales, versión y hash. La carga rechaza incompatibilidades de integridad o bibliotecas.")
    h("3.2 Contrato de inferencia")
    p("La API ofrece predicción individual, lote de hasta 500 clientes y cálculo de variables a partir de hasta 5.000 líneas de compra de un cliente. El contrato requiere identificador externo y corte; la respuesta incluye probabilidad, categoría, fecha de inferencia, versión y horizonte. Se rechazan campos extra, duplicados ambiguos, valores fuera de dominio y coberturas inválidas. El código de preparación se comparte con entrenamiento para reducir diferencias de cálculo.")
    h("3.3 Seguridad carga y operación")
    p("El lanzador aplica HTTPS con TLS 1.2 o superior, autenticación por clave, lista de IPs y nombres de servidor permitidos, sin confiar en cabeceras de proxy. El cuerpo máximo es de 2.000.000 bytes. Se admiten cuatro solicitudes de predicción en curso por proceso; el exceso recibe 503 con Retry-After. La recepción del cuerpo vence a los cinco segundos con 408. Este plazo no es un límite duro para terminar un hilo de inferencia.")
    p("El consumidor futuro dispone de una política documentada de timeout, reintentos limitados e idempotencia por cliente, corte y versión. Las entregas de Windows usan entornos aislados y manifiestos. Una tarea periódica recupera el proceso si terminó y conserva la instancia sana; la parada voluntaria deshabilita la tarea. El perfil requiere sesión de usuario. Se verificaron actualización y reversión, sin instalar un servicio externo permanente.")
    h("3.4 Integración futura")
    p("Krayin deberá aportar el mapeo de clientes/compras, cliente PHP, persistencia e interfaz. El plan de validación distingue pruebas de integración, observación predictiva futura y un piloto comercial comparable. Estas actividades no fueron ejecutadas y están fuera del cierre actual limitado al dataset.")

    page("Capítulo 4 Resultados")
    h("4.1 Comparación en validación")
    table(["Candidato", "Average precision", "Brier calibrado"], [[r["model"], f'{r["average_precision"]:.4f}', f'{r["brier"]:.4f}'] for r in M["validation"]])
    p("LightGBM sin SMOTE alcanza la mayor average precision de validación, 0,4746. La diferencia frente a Random Forest sin SMOTE es pequeña y la tabla no demuestra significación estadística. SMOTE no mejora todos los candidatos. La elección del modelo es una decisión entre las alternativas evaluadas, no una certificación de utilidad en datos futuros.")
    figure("ML/artifacts/churn180-v1/figures/02_comparacion_validacion.png", "Figura 1. Comparación en validación temporal. Fuente: resultados generados por el pipeline del proyecto.", 14.5)

    page("Resultados de la prueba temporal")
    h("4.2 Desempeño final")
    p("En el test se observan 431 clientes, de los cuales 101 no recompran en la ventana futura. LightGBM obtiene ROC-AUC 0,4571, average precision 0,2119 y Brier 0,1967. La referencia de recencia obtiene average precision 0,2550. El intervalo bootstrap de ROC-AUC es [0,4007; 0,5188], compatible con 0,5; no demuestra superioridad frente al azar.")
    table(["Regla", "Marcados", "Precisión", "Recall"], [["Medio 0,311218", "429", "23,54 %", "100,00 %"], ["Alto 0,377295", "92", "19,57 %", "17,82 %"], ["Referencia 0,35", "274", "22,63 %", "61,39 %"], ["Referencias 0,50 y 0,70", "0", "No definida", "0,00 %"]])
    figure("ML/artifacts/churn180-v1/figures/03_matriz_confusion_test.png", "Figura 2. Matriz de confusión del test al umbral medio. Los 328 falsos positivos limitan la priorización pese al recall del 100 %.", 12)
    p("A 0,50 todos los clientes se clasifican como no abandono: la accuracy de 76,57 % refleja la clase mayoritaria y no una detección útil de abandono. En los archivos de métricas se registra precisión cero cuando no hay seleccionados como convención de cálculo.")

    page("Calibración y escenarios de capacidad")
    h("4.3 Probabilidades antes y después de calibrar")
    table(["Periodo", "Brier sin calibrar", "Brier calibrado", "Media calibrada / observada"], [["Validación", "0,2701", "0,2524", "36,09 % / 43,92 %"], ["Test", "0,2805", "0,1967", "35,91 % / 23,43 %"]])
    figure("docs/evidencias_ml06/calibration.png", "Figura 3. Calibración retrospectiva en intervalos de 0,10. Raw corresponde al estimador sin calibrar y sigmoid al calibrado. No se muestran intervalos de confianza.")
    p("La calibración reduce el error frente al estimador sin calibrar, pero la media del test todavía sobreestima el abandono en 12,48 puntos porcentuales. Los tamaños por intervalo se conservan en calibration_bins.csv; los puntos con pocos casos deben interpretarse con cautela.")
    h("4.4 Escenarios hipotéticos")
    p("ML-06 explora cupos del 10 %, 20 % y 30 %, con costo de falso positivo igual a una unidad y de falso negativo igual a 1, 2 o 5. Se selecciona una fracción solo en validación y se traslada al test. Son pérdidas abstractas de clasificación, no dinero ni efecto de campañas. Con cupo 20 % y costo FN de 2, el modelo selecciona 85 clientes con precisión de 17,65 %; recencia con el mismo cupo obtiene 24,71 %. Los 90 registros de escenarios no justifican cambiar automáticamente los umbrales de la API.")

    page("Resultados de funcionamiento del servicio")
    h("4.5 Verificación técnica")
    p("Las pruebas reales de HTTPS verificaron certificado, nombre de servidor, TLS 1.2/1.3, rechazo de credenciales inválidas y de IP/Host no permitidos. El ensayo API-06 midió 480 solicitudes HTTPS con tres calentamientos por escenario, conexión TLS nueva y sin reintentos durante la medición. Cliente y servidor se ejecutaron en el mismo equipo Windows, con 16 CPU lógicas.")
    load = json.loads((ROOT / "docs/evidencias_api/09_carga_https.json").read_text(encoding="utf-8"))
    table(["Clientes/lote", "Concurrencia", "HTTP 200 / 503", "p95 exitoso ms"], [[s["batch_size"], s["concurrency"], f'{s["status_counts"].get("200", 0)} / {s["status_counts"].get("503", 0)}', s["successful_latency_ms"]["p95"]] for s in load["scenarios"]])
    p("Los escenarios con concurrencia 1 y 4 completaron las 80 solicitudes de cada combinación. Con 16 solicitudes simultáneas se rechazó el exceso; no debe omitirse ese rechazo al interpretar la latencia de éxitos. Cuatro cuerpos incompletos agotaron los cupos y vencieron con 408; posteriormente el servicio volvió a responder 200. Estos ensayos breves no prueban estabilidad durante horas ni capacidad en otro servidor.")
    p("API-07 verificó reinicio controlado, recuperación tras caída en 50,11 segundos, actualización y rollback entre dos entregas. La tarea temporal se eliminó. La entrega api-2.1.0-api06 incorpora los límites actuales; las pruebas operativas de reversión se realizaron previamente entre entregas API-07. Tras incorporar el análisis académico ML-06, la regresión completa registró 98 pruebas aprobadas y 95,14 % de cobertura Python. La cobertura no mide exactitud del modelo ni cubre los scripts PowerShell, cuyo comportamiento se comprobó mediante ensayos operativos.")

    page("Capítulo 5 Discusión")
    h("5.1 Validez de la predicción")
    p("El desempeño favorable relativo de LightGBM en validación no se sostuvo en test. La caída temporal y el cambio de prevalencia exigen cautela: la evaluación abarca un único corte final y no permite atribuir el resultado a una causa específica. La información agregada de ventas y los candidatos ensayados no bastaron para demostrar una priorización superior a recencia.")
    p("Un recall alto puede obtenerse marcando casi toda la población. En este caso, el umbral medio identifica todos los abandonos pero genera 328 falsas alarmas. La calibración mejora el error de las probabilidades, sin resolver el problema de seleccionar pocos clientes con alta precisión. Las diferencias de escenarios de capacidad son descriptivas; no se evaluó significación de todas las comparaciones ni un beneficio de intervención.")
    h("5.2 Límites del dataset y de las afirmaciones")
    p("La etiqueta mide ausencia de compra, no insatisfacción ni cancelación. No existen campañas, ofertas, costos o márgenes que permitan estimar retorno de inversión. Tampoco se observó el efecto de contactar a un cliente identificado como riesgo. Predecir abandono y modificarlo mediante una acción son problemas diferentes. La aparición de clientes repetidos entre cortes limita la extrapolación a clientes nuevos.")
    p("Los notebooks históricos usan definiciones o particiones diferentes y no se deben combinar sus métricas con el artefacto vigente. El estudio adicional de umbrales utilizó un test ya conocido: aporta sensibilidad retrospectiva, no evidencia independiente para elegir una política. Cualquier cambio guiado por estos resultados requiere otro periodo de evaluación.")
    h("5.3 Alcance técnico y trabajo futuro")
    p("La separación de componentes, el contrato validado y la evidencia de seguridad y carga permiten continuar hacia una integración con Krayin. Sin embargo, una prueba local no certifica operación permanente ni integración completa con PHP. El plan futuro requiere mapeo de datos, persistencia idempotente, interfaz y seguimiento. Para atribuir una mejora a una política apoyada en ML sería necesario un piloto comparable con presupuesto y seguimiento definidos antes de analizar resultados.")
    p("Estas actividades quedan fuera del cierre actual. No se requiere inventar datos comerciales ni cambiar de dataset para presentar la investigación realizada; sí se requiere explicitar sus límites y conservar sus resultados negativos.")

    page("Capítulo 6 Conclusiones")
    for text in [
        "Se estableció una definición prospectiva de abandono a 180 días y un cálculo compartido de siete variables sobre 365 días de historial. El protocolo temporal evita utilizar compras posteriores al corte como predictores y permite reproducir los resultados del dataset disponible.",
        "LightGBM sin SMOTE fue el mejor candidato por average precision de validación, pero su ROC-AUC de 0,4571 y average precision de 0,2119 en test no demostraron utilidad predictiva suficiente. La regla de recencia presentó una average precision descriptivamente mayor. No se sostiene que el modelo mejore la gestión comercial por su desempeño predictivo actual.",
        "La calibración redujo Brier respecto al estimador sin calibrar; aun así, las probabilidades del test sobreestimaron el abandono promedio. El umbral medio marcó el 99,54 % de la cartera y no proporcionó una priorización práctica. Los escenarios de cupo y costos permiten analizar sensibilidad, pero no validan rentabilidad ni sustituyen información del negocio.",
        "El prototipo local logró separar ML y backend, establecer un contrato trazable y verificar seguridad HTTPS, validación, lotes, saturación, recuperación y despliegue versionado. Las 98 pruebas y la cobertura Python de 95,14 % respaldan funcionamiento del software en el alcance ensayado, sin equivaler a eficacia predictiva.",
        "No se demostró mejora de fidelización, recompra o satisfacción causada por el sistema. El estudio no incluyó intervención comercial ni integración real con Krayin. El modelo conserva estado experimental y no autoriza campañas automáticas.",
        "La contribución de la etapa es una evaluación retrospectiva reproducible que expone las limitaciones del modelo y una infraestructura técnica preparada para continuar. La validación prospectiva, el piloto comercial y el despliegue externo constituyen trabajo futuro; no bloquean el cierre académico limitado al dataset actual."
    ]:
        p(text)

    page("Referencias y evidencia del proyecto")
    for text in [
        "[1] Sahoo, R. Superstore Sales Dataset, versión 2. Kaggle. Licencia declarada GPL 2. https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting. Fuente identificada por el usuario; metadatos conservados en docs/dataset_kaggle_metadata.json.",
        "[2] scikit-learn developers. Common pitfalls and recommended practices. Documentación 1.9.1. https://scikit-learn.org/stable/common_pitfalls. Consulta: 28 de octubre de 2026.",
        "[3] imbalanced-learn developers. Common pitfalls and recommended practices. Repositorio oficial de documentación. https://github.com/scikit-learn-contrib/imbalanced-learn/blob/master/doc/common_pitfalls.rst. Consulta: 28 de octubre de 2026.",
        "[4] scikit-learn developers. Probability calibration. Documentación 1.9.1. https://scikit-learn.org/stable/modules/calibration. Consulta: 28 de octubre de 2026."
    ]:
        p(text)
    h("Anexo A Trazabilidad de los resultados")
    table(["Evidencia", "Ubicación en el proyecto"], [["Protocolo", "ML/protocol.json"], ["Métricas y versión", "ML/artifacts/churn180-v1/metadata.json"], ["Calibración y cupos", "docs/evidencias_ml06/"], ["Seguridad HTTPS", "docs/evidencias_api/07_seguridad_https.json"], ["Recuperación y reversión", "docs/evidencias_api/08_despliegue_reversion.json"], ["Carga HTTPS", "docs/evidencias_api/09_carga_https.json"], ["Regresión final", "docs/evidencias_ml06/pruebas.txt"], ["Guía de capturas", "docs/GUIA_CAPTURAS.md"]])
    p("La fuente de las tablas y figuras de resultados es la ejecución local del proyecto. Los escenarios de costos son hipotéticos; los datos de rendimiento corresponden al equipo ensayado. Los archivos originales y los resultados históricos se conservan para auditoría.")
    doc.core_properties.title = "Aplicación de ML para mejorar la gestión y fidelización de clientes en un sistema CRM"
    doc.core_properties.subject = "Evaluación retrospectiva y prototipo local con Superstore Sales"
    doc.save(SOURCE)
    print(SOURCE)
    print("Paragraphs", len(doc.paragraphs), "tables", len(doc.tables))


if __name__ == "__main__":
    build()
