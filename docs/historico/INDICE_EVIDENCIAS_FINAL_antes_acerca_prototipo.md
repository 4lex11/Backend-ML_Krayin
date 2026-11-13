# Índice final de evidencias y capturas

Actualizado el 30/10/2026. Tesis: `InvestigacionTesis2026.docx`, **44 páginas**. La numeración corresponde a la exportación de Word revisada. Los capítulos 3 y 4 siguen la estructura solicitada a partir de `InvestigacionTesis2026Original.pdf`. La versión previa y sus guías se conservan en `docs/historico/`.

| Contenido | Páginas | Archivo fuente o figura para captura |
|---|---:|---|
| Métodos e hiperparámetros con definición | 7 | [Configuraciones evaluadas](../ML/experiments/churn180-v2/candidates_mej04.json) |
| Métricas e interpretación | 8 | [Evaluación](../ML/evaluation.py) y [comparación](../ML/compare_v2.py) |
| Diseño del sistema | 9 | [Imagen original](evidencias_cap34/originales/pagina_20_imagen_1.jpg) |
| Fases y comprensión del negocio | 10 | [Imagen original de fases](evidencias_cap34/originales/pagina_21_imagen_1.jpg) |
| Variables derivadas y objetivo | 11–12 | [Originales](../ML/features.py) y [temporales](../ML/features_v2.py) |
| Comprensión de datos | 13 | [Archivo plano original](evidencias_cap34/originales/pagina_23_imagen_1.jpg) y [tabla original](evidencias_cap34/originales/pagina_23_imagen_2.png) |
| Preparación actual | 14 | [Flujo](evidencias_proyecto_final/preparacion_actual.png) y [cortes temporales](evidencias_proyecto_final/cortes_temporales.png) |
| Modelado y configuraciones | 15 | [Manifiesto temporal](evidencias_mej03/preparacion/manifest.json) |
| Evaluación y mejor candidato | 16 | [Comparación por métrica](evidencias_proyecto_final/comparacion_desarrollo.png) y [selección](evidencias_mej04/comparacion/selection.json) |
| Integración y matrices con cupo común | 17 | [Matrices al 20 %](evidencias_proyecto_final/matrices_cupo20.png) |
| Matriz del umbral vigente | 20 | [Matriz del modelo integrado](evidencias_proyecto_final/matriz_vigente.png) y [metadatos](../ML/artifacts/churn180-v1/metadata.json) |
| Evaluación E1 | 23 | [Gráfica E1](evidencias_proyecto_final/comparacion_e1.png), [métricas](evidencias_mej06/aceptacion/metrics.json) y [decisión](evidencias_mej06/aceptacion/decision.json) |
| Comparación de algoritmos y balanceo | 21 | [Comparación de algoritmos](evidencias_proyecto_final/comparacion_v1.png) |
| Configuraciones y variables | 22 | [Clasificación completa](evidencias_mej04/comparacion/selection.json) |
| Calibración y criterios incumplidos | 24 | [Gráfica](evidencias_proyecto_final/calibracion_desarrollo.png) y [conteos](evidencias_mej05/calibracion/calibration_bins.json) |
| Variación temporal e incertidumbre | 25 | [Precisión temporal](evidencias_proyecto_final/precision_temporal.png), [intervalos](evidencias_proyecto_final/intervalos_bootstrap.png), [bootstrap](evidencias_mej06/aceptacion/bootstrap.json) |
| Cupos y errores | 26 | [Matrices recalculadas](evidencias_cap34/matrices.json) |
| Seguridad, carga y recuperación | 27 | [HTTPS](evidencias_api/07_seguridad_https.json), [carga](evidencias_api/09_carga_https.json), [recuperación](evidencias_api/08_despliegue_reversion.json) |
| Aceptación de la integración | 28 | [Lote HTTPS](evidencias_crm061/aceptacion_https.json), [conciliación](evidencias_crm061/conciliacion_dataset.json), [PHP](evidencias_crm061/regresion_php.txt), [Python](evidencias_crm061/regresion_python.txt) |
| Panel, sugerencias y revisión manual | 29 | [Detalle](evidencias_crm061/detalle_escritorio.png), [revisión](evidencias_crm061/revision_integral.png), [navegador](evidencias_crm061/navegador.json) |
| Discusión y conclusiones | 30–31 | [Conclusiones detalladas](CONCLUSIONES_DETALLADAS.md) |
| Recomendaciones y referencias | 32–33 | Tesis y [auditoría](REVISION_COHERENCIA.json) |
| Anexo B y detalle de mejoras | 34–44 | [Cierre MEJ-08](MEJ08_CIERRE_DOCUMENTAL.md) |

El mejor candidato experimental y el modelo instalado están resaltados en la página 23. La decisión se explica en la página 24. Se conserva el modelo integrado porque el candidato incumplió dos criterios de Brier. Las gráficas originales de diseño incluyen funciones conceptuales no implementadas; el texto lo aclara sin modificar la imagen.

Las capturas de Krayin son evidencia de QA local, no de campañas. El lote de 793 clientes produjo 431 predicciones y 362 no elegibles durante una prueba revertida. Los resultados del lote no permanecieron cargados; se conservó una predicción original y 792 clientes sin resultado. Las cuentas y notas temporales de QA se eliminaron.

Para capturas nuevas, seguir [la guía de operación](GUIA_FINAL_CRM.md), seleccionar el corte 2018-06-30 y el cliente AA-10315. Una revisión manual guarda un registro real, pero no contacta al cliente. No mostrar credenciales ni presentar los datos históricos como actuales. Véase [la guía de capturas](GUIA_CAPTURAS.md).

## Capturas añadidas del módulo

| Contenido | Página | Fuente |
|---|---:|---|
| Listado y predicción guardada | 18 | [Listado](evidencias_crm042/prediccion_guardada.png) |
| Probabilidad, riesgo y sugerencia | 19 | [Detalle con sugerencia](evidencias_crm051/sugerencia_detalle.png) |
| Siete variables históricas | 19 | [Variables del cliente](evidencias_crm043/detalle_escritorio.png) |

Las ampliaciones son recortes de visualización en Word; los PNG originales se conservan intactos. Las imágenes pertenecen a las pruebas locales históricas y sus archivos de evidencia se indican en los pies.

Los capítulos 3 y 4 describen un único proyecto en orden metodológico. Las etiquetas de versiones permanecen solo en identificadores técnicos, rutas de evidencia y anexos históricos. Figuras con etiquetas unificadas: `docs/evidencias_proyecto_final/`.
