# Plan de mejora experimental del modelo

29/10/2026. Nueva etapa autorizada después del cierre ML/API/CRM. Se conserva el dataset Superstore Sales, abandono a 180 días y prototipo local. No hay garantía de mejora. La integración existente sigue completa.

| ID | Tarea y criterio de cierre | Estado |
|---|---|---|
| MEJ-01 | Fijar objetivos, cortes, comparadores, métricas, reglas de selección y aceptación; identificar datos y versión vigente mediante hashes. | Completada; protocolo y verificación en los enlaces siguientes. |
| MEJ-02 | Implementar variables temporales, definiciones y tratamiento de historial insuficiente; verificar límites de ventana y ausencia de datos futuros. | Completada: 11 variables en `ML/features_v2.py`, pruebas de límites/fuga y verificación sobre el CSV. Véase MEJ02_VARIABLES_TEMPORALES.md. |
| MEJ-03 | Implementar evaluación por cortes según el protocolo, con controles de cobertura, etiquetas y población común. | Completada: nueve CSV D1/D2/E1, manifiesto de integridad y 11 pruebas aprobadas con MEJ-02; véase MEJ03_EVALUACION_TEMPORAL.md. |
| MEJ-04 | Comparar modelos simples y regularizados, con búsqueda acotada y ablación de variables; registrar todas las ejecuciones. | Completada: 18 candidatos en D1/D2, tres referencias y selección de lightgbm_original_a; sin promoción. Véase MEJ04_COMPARACION_MODELOS.md. |
| MEJ-05 | Analizar calibración y políticas de selección/umbrales sin ajustarlas al corte final; conservar curvas y conteos de errores. | Completada: crudo/sigmoide, intervalos de calibración, doce casos de umbral y política congelada; sin promoción. Véase MEJ05_CALIBRACION_UMBRALES.md. |
| MEJ-06 | Aplicar los criterios prefijados; declarar mejora experimental, resultado insuficiente o inconcluso y justificarlo. | Completada: E1 y 1000 remuestreos; candidato rechazado por dos criterios de Brier. Conservar v1. Véase MEJ06_ACEPTACION.md. |
| MEJ-07 | Solo si supera los criterios: integrar una versión experimental nueva con API/Krayin, pruebas de contrato/paridad, historial separado y reversión a v1. | No aplica en esta ronda: MEJ-06 no autorizó promover el candidato. |
| MEJ-08 | Actualizar tesis, conclusiones y evidencias con resultados positivos o negativos y límites de la evaluación. | Completada: tesis de 42 páginas, conclusiones, capturas y auditoría; véase MEJ08_CIERRE_DOCUMENTAL.md. |

Protocolo: [MEJ01_PROTOCOLO.md](MEJ01_PROTOCOLO.md). Configuración declarativa: [protocol.json](../ML/experiments/churn180-v2/protocol.json). Verificación: [verificacion.json](evidencias_mej01/verificacion.json). El protocolo v2 no es compatible como entrada del entrenador v1 y todavía no entrena modelos. MEJ-01 no cambia la API, las predicciones guardadas ni el documento de investigación.



Reestructura de capítulos 3 y 4 (30/10/2026): metodología en páginas 7–18 y resultados en 19–27, con las cuatro imágenes originales indicadas. Ubicaciones y archivos para capturas: [índice vigente](INDICE_EVIDENCIAS_FINAL.md).
