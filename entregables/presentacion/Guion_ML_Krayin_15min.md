# Guion de exposición

Aplicación de ML para la gestión y fidelización de clientes en un CRM

Duración: **15 minutos**. Presentación: 15 diapositivas. El texto también está en las notas del presentador del PowerPoint. Los tiempos incluyen pausas para señalar las imágenes. Ensayar con cronómetro y mantener las aclaraciones sobre el alcance.

## 1. Machine Learning para la gestión de clientes

**Tiempo:** 0:00–0:30 (30 segundos).

**Qué decir**

Buenos días. Presentamos nuestro proyecto sobre la aplicación de Machine Learning para mejorar la gestión y fidelización de clientes en un CRM. Desarrollamos un prototipo integrado en Krayin que estima el riesgo de no volver a comprar y muestra sugerencias para revisión humana. Durante la exposición explicaré cómo definimos el problema, cómo construimos y evaluamos los modelos y cómo llevamos las predicciones a la interfaz web. El estudio utiliza exclusivamente datos históricos de Superstore Sales.

**Qué señalar:** Presenta el objetivo sin anunciar una mejora comercial demostrada.

## 2. Problema y conceptos principales

**Tiempo:** 0:30–1:20 (50 segundos).

**Qué decir**

El problema consiste en convertir el historial de ventas en información que ayude a revisar y priorizar clientes. Un CRM organiza las relaciones y el seguimiento comercial. Machine Learning permite aprender patrones a partir de ejemplos y asignar una probabilidad a un evento futuro. En este proyecto ese evento es la ausencia de recompra. La fidelización, en cambio, requiere una intervención y medir si el cliente permanece o vuelve a comprar. Nuestro prototipo apoya esa gestión, pero el dataset no contiene campañas ni sus resultados. Por eso formulamos un objetivo verificable: estimar el riesgo, evaluar su utilidad para priorizar y mostrarlo de forma trazable en Krayin.

**Qué señalar:** Distingue CRM, predicción y fidelización.

## 3. Datos disponibles y alcance

**Tiempo:** 1:20–2:20 (60 segundos).

**Qué decir**

Utilizamos Superstore Sales, descargado de Kaggle. El archivo contiene 9.800 líneas de venta, 4.922 pedidos y 793 clientes, con registros entre enero de 2015 y diciembre de 2018. Una compra puede contener varias líneas, por eso distinguimos líneas, pedidos y clientes. Revisamos fechas, identificadores, valores de venta y duplicados antes de transformar los datos. Conservamos las 9.800 líneas y encontramos once códigos postales ausentes, que no afectan al modelo porque ese campo no se usa como predictor. La decisión de trabajar solo con este dataset define el alcance: podemos estudiar recompra histórica, pero no atribuir beneficios económicos ni efectos de campañas que nunca observamos.

**Qué señalar:** Señala que una línea de venta no equivale a un cliente.

## 4. Definición de abandono a 180 días

**Tiempo:** 2:20–3:25 (65 segundos).

**Qué decir**

Necesitábamos una definición medible de abandono. Adoptamos como etiqueta positiva que el cliente no realice ninguna compra durante los 180 días posteriores a una fecha de corte. Para calcular sus características usamos únicamente los 365 días anteriores. Además, evaluamos clientes cuya última compra conocida se encuentra dentro de los últimos 180 días. Esto evita confundir un cliente ya inactivo con el evento futuro que queremos anticipar. Por ejemplo, al corte del 30 de junio de 2018 describimos el año anterior y verificamos la existencia de compras en los siguientes 180 días. El horizonte es un supuesto explícito de la investigación, no una duración óptima demostrada para una empresa.

**Qué señalar:** Explica el corte: pasado para predecir y futuro para verificar.

## 5. Preparación y variables del cliente

**Tiempo:** 3:25–4:20 (55 segundos).

**Qué decir**

Después de validar las transacciones, agregamos la información por cliente y fecha de corte. El conjunto básico tiene siete variables: recencia, frecuencia, suma, media y desviación de ventas, y cantidad de categorías y subcategorías. Frecuencia cuenta pedidos distintos. La media y la desviación monetaria se calculan por línea de venta. También evaluamos once variables temporales, como pedidos y ventas de los últimos 30, 90 y 180 días y los intervalos entre compras. Comparamos los conjuntos de siete, once y dieciocho variables para comprobar si esa información adicional ayudaba. Los identificadores sirven para unir resultados con el CRM, pero no entran como predictores. Ninguna variable utiliza compras futuras.

**Qué señalar:** Relaciona recencia, frecuencia y monto con comportamiento de compra.

## 6. Validación temporal

**Tiempo:** 4:20–5:25 (65 segundos).

**Qué decir**

La separación temporal reproduce el orden en que conoceríamos la información. Primero entrenamos el modelo, después ajustamos la calibración con un bloque posterior y finalmente evaluamos en otro corte. El entrenamiento aprende relaciones entre variables y etiqueta. La calibración transforma las puntuaciones en probabilidades y se ajusta con datos reservados. Utilizamos dos cortes de desarrollo, junio y diciembre de 2017, para seleccionar configuraciones. Después evaluamos junio de 2018. No mezclamos aleatoriamente observaciones de todos los periodos porque eso dificultaría representar el uso futuro del sistema. También dejamos una limitación explícita: el periodo final ya había sido examinado durante el estudio y su evaluación es exploratoria, no una prueba prospectiva independiente.

**Qué señalar:** Lee una fila de la tabla y explica entrenamiento, calibración y evaluación.

## 7. Modelos e hiperparámetros

**Tiempo:** 5:25–6:30 (65 segundos).

**Qué decir**

Comparamos inicialmente Random Forest, XGBoost y LightGBM, con y sin SMOTE. Random Forest combina árboles y los modelos de boosting incorporan árboles sucesivos para corregir errores. SMOTE genera ejemplos sintéticos para explorar el efecto del balanceo, siempre dentro del entrenamiento. Luego evaluamos dieciocho configuraciones: tres familias, dos ajustes por familia y tres conjuntos de variables. Incluimos regresión logística como alternativa más sencilla. Los hiperparámetros son decisiones de configuración, como el número de árboles, la profundidad o la regularización. Los limitamos para controlar complejidad y sobreajuste. En esta comparación de dieciocho candidatos no usamos SMOTE y mantuvimos las mismas particiones para que la comparación fuera consistente.

**Qué señalar:** Define hiperparámetro y explica el propósito de limitar árboles y profundidad.

## 8. Métricas para tomar decisiones

**Tiempo:** 6:30–7:25 (55 segundos).

**Qué decir**

No elegimos un modelo por una sola cifra de accuracy. La precisión al veinte por ciento indica cuántos abandonos reales aparecen entre los clientes de mayor puntuación que caben en ese cupo. Average Precision, o AP, resume la relación entre precisión y cobertura a lo largo del ranking. Brier mide el error de las probabilidades y cuanto menor es su valor, mejor. Recall indica qué proporción de todos los abandonos detectamos. Estas métricas responden a necesidades diferentes: ordenar clientes, cubrir casos y estimar probabilidades fiables. Los cupos del diez, veinte y treinta por ciento son escenarios académicos de capacidad. No representan un presupuesto ni una capacidad de contacto observada en una empresa.

**Qué señalar:** Usa el ejemplo de un cupo de 87 clientes para explicar precisión.

## 9. Resultados de priorización

**Tiempo:** 7:25–8:40 (75 segundos).

**Qué decir**

En el corte de junio de 2018 encontramos 431 clientes elegibles y 101 casos de ausencia futura de compra. El cupo del veinte por ciento equivale a 87 clientes. La configuración candidata de LightGBM obtiene una precisión del 33,33 por ciento, frente al 25,29 por ciento de la referencia basada en recencia y al 17,24 por ciento del modelo integrado. En términos concretos, identifica 29 abandonos dentro del cupo, mientras el modelo integrado identifica 15. Eso representa catorce aciertos adicionales con la misma cantidad de clientes seleccionados. Sin embargo, todavía quedan 58 falsas alarmas y 72 abandonos fuera del cupo. El resultado mejora la priorización en este corte, pero no demuestra por sí solo suficiente fiabilidad probabilística ni una mejora de fidelización.

**Qué señalar:** Compara los tres valores y luego los 29 aciertos entre 87 seleccionados.

## 10. Decisión sobre el modelo integrado

**Tiempo:** 8:40–9:50 (70 segundos).

**Qué decir**

La decisión de integración debía cumplir todos los criterios establecidos, no solo mejorar la precisión. El candidato incumplió dos controles de Brier. El exceso medio frente al predictor constante fue 0,011289 y el exceso frente al modelo integrado en el corte final fue 0,024680. Ambos superan el máximo permitido de 0,01. Por eso conservamos el artefacto integrado: LightGBM sin SMOTE calibrado con sigmoide, con siete variables, 150 árboles, profundidad tres, siete hojas y tasa de aprendizaje 0,05. Ese modelo había obtenido la mayor AP en la comparación inicial de validación. Mantenerlo conserva la implementación comprobada, pero no significa que su utilidad predictiva sea suficiente. Esta decisión muestra la importancia de separar funcionamiento técnico y desempeño del modelo.

**Qué señalar:** Explica por qué ganar en precisión no basta para reemplazar el modelo.

## 11. Arquitectura y herramientas

**Tiempo:** 9:50–10:50 (60 segundos).

**Qué decir**

Organizamos la solución en componentes separados. Python prepara las variables, entrena los modelos y conserva los artefactos. pandas y NumPy permiten trabajar con los datos, y scikit-learn y las librerías de árboles permiten entrenar y evaluar. El backend publica la inferencia mediante FastAPI y Uvicorn, y Pydantic valida las entradas. Krayin funciona con PHP y Laravel y guarda datos en MariaDB. El módulo solicita predicciones por HTTPS, conserva probabilidad, fecha de corte y versión y las presenta en el panel. Elegimos esta separación para que el CRM no tenga que ejecutar el entrenamiento y para comprobar el contrato entre ambos lenguajes. Las solicitudes se procesan fuera de la petición web mediante una cola propia.

**Qué señalar:** Describe el recorrido de datos entre las tres responsabilidades.

## 12. Interfaz del módulo de predicciones

**Tiempo:** 10:50–11:55 (65 segundos).

**Qué decir**

Esta es una captura real del módulo creado en Krayin. El usuario puede filtrar por corte, categoría de riesgo y estado, consultar indicadores y localizar un cliente. La fila muestra la probabilidad guardada y permite abrir el detalle. En el ejemplo, el cliente presenta 34,01 por ciento y categoría Medio para el corte histórico del 30 de junio de 2018. El mensaje de actualización fallida pertenece a una prueba de recuperación: el sistema conservó la predicción anterior en lugar de borrarla. Las fechas de corte y cálculo cumplen funciones distintas. La primera indica hasta cuándo observamos compras y la segunda cuándo ejecutamos el servicio. La pantalla muestra datos históricos de demostración, no la situación actual del cliente.

**Qué señalar:** Señala filtros, indicadores y fila del cliente. Aclara el aviso de recuperación.

## 13. Sugerencias y seguimiento manual

**Tiempo:** 11:55–13:00 (65 segundos).

**Qué decir**

En el detalle aparecen la probabilidad, el horizonte, las variables y la orientación para revisar el caso. Las sugerencias proceden de reglas explícitas, no de un segundo modelo que haya aprendido acciones comerciales. Por ejemplo, el historial limitado tiene prioridad y recomienda comprobar la cobertura antes de considerar seguimiento, incluso si existe una categoría de riesgo. El formulario permite guardar estado, responsable y nota. Cada registro conserva autor y fecha para mantener trazabilidad. Esta fue una decisión de alcance: apoyar la revisión humana y explicar el contexto del resultado sin enviar ofertas ni campañas automáticamente. La captura de seguimiento utiliza una cuenta y una nota de prueba, que no acreditan un contacto comercial real.

**Qué señalar:** Señala la advertencia de historial limitado y después el registro de revisión.

## 14. Validación de la integración

**Tiempo:** 13:00–14:00 (60 segundos).

**Qué decir**

Validamos el recorrido completo desde el dataset hasta la consulta HTTPS, la persistencia, el panel y la revisión manual. La regresión de Krayin registró 161 casos y 477 aserciones sin fallos. La de Python registró 98 casos aprobados. En el ensayo por lote procesamos 793 clientes: 431 completaron la predicción y 362 no resultaron elegibles para ese corte. Las probabilidades coincidieron con las de la evaluación, con una diferencia numérica máxima cercana a cinco por diez elevado a menos quince. También comprobamos permisos, solicitudes duplicadas y conservación del resultado ante errores. El lote se ejecutó dentro de una prueba revertida, por lo que no dejó 431 predicciones cargadas. Estas evidencias verifican integración local, no producción permanente ni eficacia comercial.

**Qué señalar:** Relaciona cada cifra con una comprobación técnica concreta.

## 15. Conclusiones y próximos pasos

**Tiempo:** 14:00–15:00 (60 segundos).

**Qué decir**

El proyecto entrega una definición reproducible de abandono a 180 días, un procedimiento temporal de evaluación y un módulo funcional en Krayin para consultar predicciones y registrar revisiones. La comparación mostró que una configuración puede mejorar el ranking y aun así incumplir los requisitos sobre probabilidades. Por eso la selección debe considerar varias métricas y respetar los criterios definidos antes de revisar el resultado. La principal limitación es que solo contamos con ventas históricas y no observamos campañas, costos ni respuestas de clientes. Para avanzar se necesitaría un periodo nuevo de validación y, si se quiere medir fidelización, un piloto con intervención y comparación de resultados. Nuestro aporte comprobado es metodológico y técnico. Gracias por su atención.

**Qué señalar:** Cierra con el aporte verificable y dos condiciones para una validación futura.

## Preguntas posibles de sustentación

**¿Por qué 180 días?** Es una definición operacional aceptada para la investigación. Permite construir una etiqueta futura con la cobertura del dataset. No se demuestra que sea el horizonte óptimo de un negocio.

**¿Cuál es el mejor modelo?** Depende del criterio. LightGBM sin SMOTE obtuvo la mayor AP inicial de validación. Otra configuración LightGBM logró mayor precisión al 20 % en E1, pero no cumplió dos controles de Brier. El CRM conserva el artefacto integrado.

**¿Por qué no reemplazaron el modelo si la precisión mejoró?** Porque la regla de aceptación también evalúa el error de las probabilidades. Cambiar el criterio después de ver el resultado favorecería una conclusión sesgada.

**¿Qué significa calibrar?** Ajustar la relación entre puntuaciones y probabilidades usando un bloque reservado. Su efecto debe comprobarse fuera de ese bloque. En desarrollo, la sigmoide mejoró el ranking medio pero aumentó Brier.

**¿Qué representa SMOTE?** Es una técnica para generar ejemplos sintéticos de la clase minoritaria durante el entrenamiento. Se exploró en la comparación inicial, pero el modelo integrado no la utiliza.

**¿Cómo evitaron fuga de información?** Las variables usan compras anteriores o iguales al corte y la etiqueta utiliza compras posteriores. Entrenamiento, calibración y evaluación siguen el orden temporal. E1 sigue siendo exploratorio por su uso previo.

**¿Las sugerencias las aprende el modelo?** No. El modelo estima riesgo. Las sugerencias proceden de reglas explícitas que priorizan elegibilidad y calidad del historial y requieren revisión humana.

**¿Demostraron fidelización?** No se midió un efecto de intervención. El dataset solo contiene ventas. Se demostró un procedimiento de evaluación y una integración funcional local.

**¿Por qué no usar accuracy como criterio principal?** Con el umbral 0,50, el modelo integrado no marca abandonos y alcanza 76,57 % de accuracy por la clase mayoritaria. Eso no acredita capacidad de priorizar.

**¿Qué significa no elegible?** El cliente no cumple las condiciones de población para ese corte. No debe interpretarse como riesgo cero ni como error del servicio.

**¿Qué faltaría para uso real?** Un periodo nuevo de validación, verificación en el entorno de despliegue y un piloto con capacidad, costos y resultados de intervención observados.

## Recordatorios al exponer

- Distinguir porcentaje de precisión, probabilidad individual y mejora de fidelización.
- Las capturas corresponden a pruebas locales con observaciones históricas.
- El cupo del 20 % selecciona 87 clientes, no indica una probabilidad de abandono del 20 %.
- No presentar los 161 casos de software como pruebas de exactitud predictiva.
- Mantener el relato como un solo proyecto, sin etapas llamadas v1 o MEJ. Los identificadores técnicos de las capturas se conservan.

## Fuentes para preparar las respuestas

- Tesis: InvestigacionTesis2026.docx.
- Dataset: https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting.
- Métricas: docs/evidencias_mej06/aceptacion/metrics.json.
- Decisión: docs/evidencias_mej06/aceptacion/decision.json.
- Modelo integrado: ML/artifacts/churn180-v1/metadata.json.
- Validación local: docs/CRM061_VALIDACION_INTEGRAL.md.
- Capturas: docs/evidencias_crm042/, docs/evidencias_crm051/ y docs/evidencias_crm061/.
