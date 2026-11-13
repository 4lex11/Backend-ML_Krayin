# Índice final de evidencias y capturas

CRM-06.2, 29/10/2026. Actualizado en MEJ-08. Referencia: `InvestigacionTesis2026.docx`, 28 páginas. La numeración corresponde a la exportación de Word revisada; puede variar con otra configuración de impresión. Guía de operación: [GUIA_FINAL_CRM.md](GUIA_FINAL_CRM.md).

| Qué se demuestra | Archivo que debe abrirse o capturarse | Ubicación en la tesis |
|---|---|---|
| Ventanas y población | [Protocolo](../ML/protocol.json) y [metadatos](../ML/artifacts/churn180-v1/metadata.json) | Páginas 4–6 |
| Comparación y límites predictivos | [Resultados finales](../ML/ML_Resultados_Finales.ipynb) | Páginas 8–10, figuras 1–3 |
| Seguridad y carga | [HTTPS](evidencias_api/07_seguridad_https.json) y [carga](evidencias_api/09_carga_https.json) | Página 11 |
| Coincidencia con ventas originales | [Conciliación](evidencias_crm061/conciliacion_dataset.json) | Página 12 |
| Lote, 401/422/503 y recuperación | [Aceptación HTTPS](evidencias_crm061/aceptacion_https.json) | Página 12, sección 4.6 |
| Pruebas PHP y permisos | [Regresión](evidencias_crm061/regresion_php.txt) y [ACL](evidencias_crm061/permisos.txt) | Página 12 |
| Pruebas Python | [Registro](evidencias_crm061/regresion_python.txt) | Página 12 |
| Detalle, variables y sugerencia | [Escritorio](evidencias_crm061/detalle_escritorio.png) y [móvil](evidencias_crm061/detalle_movil.png) | Sección 4.7, página 13 |
| Actualización manual y progreso | [Pendiente](evidencias_crm061/solicitud_pendiente.png) y [completada](evidencias_crm061/solicitud_completada.png) | Sección 4.7, página 13 |
| Responsable, nota, estado y autor | [Revisión integral](evidencias_crm061/revision_integral.png) | Página 13, figura 4 |
| Comprobaciones del navegador | [Registro JSON](evidencias_crm061/navegador.json) | Página 13 |
| Estado después del rollback y limpieza | [Estado final](evidencias_crm061/estado_final.json) | Página 12 y límites de la página 15 |
| Entorno y huellas de archivos | [Versiones](evidencias_crm061/versiones.json) | Páginas 12 y 17 |
| Cierre documental | [Auditoría](REVISION_COHERENCIA.json) | Referencias/anexo, página 17 |

Para capturas nuevas, seguir la guía de operación, ingresar al módulo, seleccionar **2018-06-30** y abrir **AA-10315**. Capturar listado, detalle, sugerencia y seguimiento según el argumento que se quiera mostrar. Si se registra una nota de demostración, identificarla como tal: el formulario guarda un registro real y no contacta al cliente. Las capturas existentes de QA representan la prueba ya realizada; la cuenta y nota temporal se eliminaron al finalizar.

Pies sugeridos: «Detalle histórico al 30/06/2018; modelo experimental y sugerencia sujeta a revisión humana», «Solicitud persistida antes/después del procesamiento HTTPS» y «Registro manual de demostración; no constituye evidencia de retención». No presentar las capturas como campañas, datos actuales ni resultados de producción.

La [guía de capturas por etapa](GUIA_CAPTURAS.md) conserva evidencia adicional del listado, permisos y reglas. Ocultar credenciales, archivos `.env`, claves y datos personales innecesarios en cualquier nueva captura. Las conclusiones están en las páginas 14–15 y en [CONCLUSIONES_DETALLADAS.md](CONCLUSIONES_DETALLADAS.md).

La sección **Recomendaciones** ocupa la página 16, después de las conclusiones y antes de las referencias. Incluye uso del prototipo, interpretación, evaluación futura, operación, sugerencias y validación comercial condicionada a ampliar el alcance.

## Cierre de la mejora experimental (MEJ-08)

La ronda está cerrada: MEJ-01 a MEJ-06 y MEJ-08 completadas; MEJ-07 no aplica porque el candidato incumplió dos criterios de Brier. Se conserva v1 y la integración existente. La tesis recoge la conclusión en la página 15, el diseño y la calibración en la 18 y la comparación E1 y decisión en la 19. Las recomendaciones y referencias conservan las páginas 16 y 17. Archivos concretos para capturas y límites: [acta de cierre](MEJ08_CIERRE_DOCUMENTAL.md).


Tablas de síntesis añadidas: página 20, tabla B1 (incorporaciones MEJ-01 a MEJ-08); página 21, tablas B2 (v1 frente al candidato), B3 (criterios incumplidos) y B4 (balance de aceptación). Las páginas 18–19 conservan el detalle experimental. Respaldo anterior: `docs/historico/InvestigacionTesis2026_antes_tablas_MEJ.docx`.


Ampliación de variables y mediciones: páginas 22–23, diccionario de las siete variables originales y once temporales; página 24, hiperparámetros; página 25, definición de métricas; página 26, comparación E1 y cupos; página 27, precisión temporal e intervalos bootstrap; página 28, calibración. Gráficas: `docs/evidencias_mej08/graficas/`. Se conserva `docs/historico/InvestigacionTesis2026_antes_mediciones_MEJ.docx`.
