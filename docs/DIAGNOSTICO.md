# Diagnóstico de ML y backend

Revisión del 27 de octubre de 2026. Hay modelos entrenados y una API funcional básica. La separación de responsabilidades está implementada; la validez experimental, la elección definitiva del modelo y la preparación para despliegue aún necesitan trabajo. El alcance y las tareas se basan en el DOCX del proyecto, los ocho notebooks, los cuatro artefactos, los CSV/JSON y la API local.

## Estado comprobado

| Componente | Evidencia | Estado |
|---|---|---|
| Dataset | `ML/Datasets/train.csv`: 9.800 filas, 18 columnas, 793 clientes y 4.922 pedidos | Disponible; cada fila es una línea de venta, no un cliente |
| Exploración y variables | `ML_Principal.ipynb`, `ML_RandomForest.ipynb`, `ML_XGBoost.ipynb`, `ML_LightGBM.ipynb` | Implementadas, con discrepancias en fechas y corte |
| Entrenamiento | RF, XGBoost y LightGBM; búsqueda de hiperparámetros y variantes con SMOTE | Ejecutado según notebooks; cuatro artefactos cargados en esta revisión |
| Comparación | `ML_Comparacion.ipynb` | Tabla escrita manualmente; coincide con métricas reproducidas para los tres modelos SMOTE |
| Inferencia HTTP | `backend/main.py`, antes `ML/main.py` | `POST /predict`; sin autenticación ni persistencia de resultados |
| Exportaciones | `ML/predicciones_crm_churn.csv` y `.json` | 793 clientes; modelo base de `ML_Principal.ipynb` |
| Importación CRM | `integraciones/krayin/mandar_data.ipynb` | Prototipo de inserción directa en MySQL; salida histórica declara 793 inserciones, no verificadas contra una base actual |
| Krayin PHP | No hay aplicación PHP en la carpeta examinada | Integración definitiva pendiente |

## Hallazgos que afectan la conclusión sobre los modelos

### Fechas y etiquetas distintas

`ML_Principal.ipynb` convierte fechas con `%d/%m/%Y` y calcula recencia al día siguiente de la última compra. Los tres notebooks de comparación usan `format="mixed"` y el mismo día de la última compra. Ambos criterios contribuyen a diferencias de etiqueta.

Comprobación directa sobre el CSV:

| Lectura y corte | Clientes etiquetados como churn |
|---|---:|
| `%d/%m/%Y`, último día registrado | 202 |
| `%d/%m/%Y`, último día + 1, usado por el principal | 205 |
| `mixed` sin `dayfirst=True`, último día, usado por los comparados | 240 |

Las dos conversiones interpretan de forma distinta 3.613 fechas. Entre el flujo principal y la comparación cambian 81 etiquetas de cliente. Esto impide comparar directamente sus métricas como si evaluaran el mismo problema. La documentación de [pandas](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html) advierte que `mixed` infiere formatos individualmente; para este dataset corresponde fijar su formato explícito.

### El 100 % inicial reproduce la regla de la etiqueta

En `ML_Principal.ipynb`, la celda inicial de entrenamiento usa `Recency` y define `Churn = Recency > 180`. El modelo aprende una regla que ya está contenida en sus entradas; su 100 % no demuestra anticipación del abandono. La celda posterior excluye recencia y es la que guarda `modelo_churn_rf.pkl`, por lo que el artefacto actual no es ese experimento de 100 %.

Excluir recencia resuelve esa dependencia directa, pero los modelos actuales siguen clasificando inactividad al final del historial. Para anticipar abandono hay que construir variables previas al corte y etiquetas en una ventana futura. `PruebaFallida.ipynb` ya contiene un intento de separar historial hasta 2018-06-30 y compras posteriores; no debería descartarse solo por su nombre. Véase la explicación de [fuga de información en scikit-learn](https://scikit-learn.org/stable/common_pitfalls).

### La API sirve un modelo distinto de los comparados

El modelo heredado de la API es `modelo_churn_rf.pkl`, un RF sin SMOTE guardado por `ML_Principal.ipynb`. El candidato de mayor recall en la tabla de tres modelos es `modelo_randomforest_smote.pkl`. Se conservó el modelo de la API durante la separación para no cambiar silenciosamente sus resultados.

Las siguientes métricas se reprodujeron cargando los artefactos y reconstruyendo la partición 80/20 con `random_state=42` y estratificación descrita en cada notebook. No hubo reentrenamiento ni validación temporal nueva.

| Artefacto | Precision | Recall | F1 | ROC-AUC | Etiquetado |
|---|---:|---:|---:|---:|---|
| `modelo_churn_rf.pkl` | 0,7500 | 0,1463 | 0,2449 | 0,7338 | Principal |
| `modelo_randomforest_smote.pkl` | 0,4861 | 0,7292 | 0,5833 | 0,7173 | Comparación |
| `modelo_xgboost_smote.pkl` | 0,4912 | 0,5833 | 0,5333 | 0,6776 | Comparación |
| `modelo_lightgbm_smote.pkl` | 0,4902 | 0,5208 | 0,5051 | 0,6749 | Comparación |

El RF de la API detecta 6 de 41 positivos en su test con el umbral de clasificación del estimador. El RF con SMOTE detecta 35 de 48, con 37 falsos positivos. Los valores no validan automáticamente los umbrales comerciales 0,35 y 0,70 usados por la API. Evidencia numérica y hashes: `docs/auditoria_ml.json`.

## Contrato de características

Las seis entradas se calculan agrupando por cliente. Deben conservar este significado cuando se conecte Krayin:

| Campo | Cálculo observado |
|---|---|
| `Frequency` | Número de `Order ID` distintos |
| `Monetary_Sum` | Suma de `Sales` por cliente |
| `Monetary_Mean` | Media de `Sales` por línea de venta; no monto total dividido entre pedidos |
| `Monetary_Std` | Desviación estándar muestral de `Sales` por línea; nulo convertido a 0 |
| `Cat_Count` | Número de categorías distintas |
| `SubCat_Count` | Número de subcategorías distintas |

La API recibe estos agregados; no los calcula desde las compras. La generación compartida de características sigue pendiente. Los CSV de exportación contienen frecuencia y suma, pero no todas las seis entradas: importar esos CSV a contactos no basta para recalcular una predicción.

## Comportamiento observado y requisitos de conservación

- Cuando recibe las seis variables, el módulo ML debe devolver la probabilidad de la clase 1, respetando el orden de variables del entrenamiento.
- Cuando la API procesa una predicción válida, debe devolver la probabilidad redondeada a cuatro decimales, categoría y sugerencia comercial.
- Cuando falta un campo requerido, FastAPI debe rechazar la solicitud con 422.
- Cuando el artefacto no puede cargarse o no coincide con el contrato de variables/clases, la API debe fallar al arrancar.
- Mientras se ejecuta inferencia, no debe haber escrituras a MySQL ni dependencias del módulo ML sobre el backend.

La inferencia es síncrona; FastAPI ejecuta el endpoint `def` en su conjunto de hilos. La carga ocurre en el ciclo de arranque. Los errores de procesamiento se registran en el servidor y se responde 500 con un mensaje genérico. Siguen pendientes validación de dominio, autenticación, versión del resultado, salud y lotes.

## Alcance de la separación

Se creó `ML/inference.py` para carga y predicción, se trasladó `main.py` a `backend/`, y se trasladaron los notebooks de importación y su CSV enriquecido a `integraciones/krayin/`. Se conservaron los notebooks de investigación, datasets, figuras, modelos y exportaciones de ML. No se ejecutaron escrituras al CRM ni se reentrenaron modelos.

Los modelos se cargaron con scikit-learn 1.9.1, que coincide con la versión encontrada en los artefactos sklearn. Los archivos de dependencias reflejan el entorno local verificado, no un historial completo del entrenamiento original. Falta probar su reconstrucción limpia; la [documentación de persistencia de scikit-learn](https://scikit-learn.org/stable/model_persistence.html) recomienda conservar las mismas versiones y metadatos del entrenamiento.

### Verificación de la reorganización

`python -m unittest discover -s tests -v`: 8 pruebas aprobadas con Python 3.14.6. Incluyen equivalencia con la predicción original, orden de campos, contrato del artefacto, límites de riesgo, HTTP real desde otro directorio, respuesta 422 y fallo de arranque ante modelo ausente. La ejecución inicial dentro del sandbox de Windows falló por restricciones locales; la repetición autorizada fuera de ese aislamiento aprobó las ocho pruebas.

Se comprobó mediante SHA-256 que los archivos originales, salvo la API y los dos notebooks adaptados, mantuvieran su contenido. Las pruebas no constituyen una reevaluación de calidad predictiva ni una prueba de integración con una instalación real de Krayin.

## Relación con la tesis e incertidumbres

`InvestigacionTesis2026.docx` plantea una investigación aplicada, cuantitativa, cuasiexperimental y con comparación pre/posintervención. El documento todavía deja N sin completar y las secciones de análisis de datos e implementación sin desarrollar. Además, describe tickets de soporte y permanencia que no aparecen como columnas observadas en el CSV.

Las métricas de clasificación son evidencia técnica, pero no demuestran por sí solas una mejora real de retención o satisfacción. Se necesitan intervenciones y resultados observados para sostener esa parte del alcance. Quedan por definir el horizonte de abandono, ventanas, población real, fuente transaccional, versión de Krayin, origen/licencia exactos del dataset y criterio de aceptación comercial.

Las tareas concretas y sus condiciones de cierre están en `docs/TAREAS_PENDIENTES.md`.
