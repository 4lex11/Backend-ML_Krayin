# Conclusiones de la evaluación de ML y del prototipo CRM

Actualización del 29 de octubre de 2026. Alcance completado: dataset Superstore Sales y prototipo integrado localmente con Krayin, CRM-01 a CRM-06. La evaluación comercial queda fuera del alcance. Guía: [GUIA_FINAL_CRM.md](GUIA_FINAL_CRM.md). Capturas y ubicación en la tesis: [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md).

## Resultado principal

**Actualización MEJ-08:** la ronda experimental MEJ-01 a MEJ-06 está concluida y documentada en el anexo B de la tesis (páginas 34–35). Se conserva el artefacto v1. Los resultados originales que siguen corresponden a ese modelo; el candidato experimental no fue integrado. Véase [el cierre documental](MEJ08_CIERRE_DOCUMENTAL.md).

La comparación de 18 configuraciones seleccionó LightGBM con siete variables originales; las once variables temporales nuevas no formaron parte de la combinación ganadora. En E1, la precisión en el 20 % prioritario fue 33,33 % (29 abandonos entre 87 seleccionados), frente a 25,29 % de recencia y 17,24 % del modelo instalado. La AP del candidato fue 0,275907. La mejora de ordenación no basta para aprobar el reemplazo: el Brier medio de 0,252908 excedió al constante en 0,011289; en E1, el Brier de 0,221384 excedió al instalado en 0,024680. Ambos excesos superaron la tolerancia preestablecida de 0,01.

Los 1000 remuestreos pareados dieron intervalos descriptivos positivos para la mejora media de precisión frente a recencia y a la receta v1 reentrenada. Los intervalos de AP incluyeron cero. No corrigen la selección previa de modelos ni convierten E1 en evidencia independiente. La sigmoide favoreció la priorización según la regla fijada, pero empeoró el Brier medio de desarrollo. Por ello se recomienda conservar los resultados desfavorables, evaluar conjuntamente ordenación y probabilidades y exigir evidencia temporal independiente antes de afirmar utilidad comercial. Fuentes para capturas: [métricas](evidencias_mej06/aceptacion/metrics.json), [remuestreo](evidencias_mej06/aceptacion/bootstrap.json) y [decisión](evidencias_mej06/aceptacion/decision.json); tesis, página 35.

El proyecto produjo un proceso reproducible de preparación, entrenamiento, evaluación y servicio de inferencia. Sin embargo, el modelo seleccionado no demostró utilidad predictiva suficiente en el periodo temporal de prueba. La conclusión válida combina un resultado técnico favorable —software funcional y comprobado— con un resultado predictivo limitado. No se midió una mejora real de fidelización ni satisfacción.

El título del proyecto expresa una finalidad de aplicación. No debe interpretarse como una mejora ya demostrada: la evidencia actual permite estudiar la viabilidad del enfoque, sus límites y el funcionamiento de la integración local realizada.

## Datos y unidad de análisis

El CSV contiene 9.800 líneas de venta, 4.922 pedidos y 793 clientes distintos, con fechas entre el 3 de enero de 2015 y el 30 de diciembre de 2018. Son unidades diferentes: no hay 9.800 clientes. La unidad predictiva es un cliente observado en una fecha de corte, de modo que un cliente puede aparecer en periodos diferentes.

La fuente indicada por el usuario es el Superstore Sales Dataset publicado por Rohit Sahoo en Kaggle. Los metadatos consultados declaran versión 2 y licencia GPL 2. La procedencia se documenta junto con el hash del archivo local; no se ha demostrado identidad binaria con una descarga remota. El CSV no contiene historial de campañas, costos de contacto, márgenes, satisfacción ni tickets de soporte. No corresponde imputar esas variables o presentarlas como observadas.

Capturas: `ML/artifacts/churn180-v1/metadata.json`, bloques `quality` y `splits`; `docs/dataset_kaggle_metadata.json`, campos de fuente y licencia. La guía general indica cómo evitar mostrar datos personales innecesarios.

## Definición de abandono y corrección metodológica

Abandono significa ausencia de compras durante los 180 días posteriores al corte, no baja contractual. Las variables usan únicamente los 365 días anteriores e incluyen clientes con última compra hace 180 días o menos. La recencia puede emplearse como predictor porque se calcula antes del resultado futuro; no se utiliza para definir una etiqueta contemporánea que el propio modelo pueda reconstruir trivialmente.

Se separaron entrenamiento, calibración, validación y prueba final. Los dos cortes de entrenamiento aportan 286 y 444 observaciones cliente-corte; no equivalen necesariamente a 730 personas diferentes. Calibración contiene 351, validación 510 y test 431 clientes. Los 101 abandonos del test representan el 23,43 %.

Las ventanas de resultado cierran antes del siguiente corte. Los mismos clientes pueden reaparecer: el estudio representa una cartera conocida a través del tiempo y no demuestra generalización a una cartera completamente nueva. La corrección de fechas y ventanas hace que las métricas actuales no sean intercambiables con las de notebooks históricos.

Capturas: `ML/protocol.json` y `ML/artifacts/churn180-v1/figures/01_periodos_y_clases.png`.

## Selección del modelo y prueba final

Se compararon Random Forest, XGBoost y LightGBM, con y sin SMOTE, usando el mismo protocolo. El procesamiento y SMOTE se ajustaron dentro del entrenamiento. Las probabilidades se calibraron en una ventana independiente. La elección se basó en average precision de validación; el menor Brier fue criterio secundario de desempate.

LightGBM sin SMOTE obtuvo la mayor average precision de validación: 0,4746, frente a 0,4719 de Random Forest sin SMOTE. Esto justificó su selección entre los candidatos evaluados, pero no anticipó un buen desempeño en test. SMOTE no fue una mejora universal y no se incorporó al artefacto elegido.

En test, LightGBM obtuvo ROC-AUC 0,4571, average precision 0,2119 y Brier 0,1967. La regla de recencia alcanzó average precision 0,2550, superior descriptivamente al modelo. El intervalo bootstrap del 95 % del ROC-AUC fue aproximadamente [0,4007; 0,5188]; incluye 0,5. No se demuestra superioridad frente al azar ni debe afirmarse inferioridad estadística solo porque la estimación puntual es menor de 0,5.

Estos intervalos se calculan sobre clientes del único corte final y no representan la variación entre años ni un efecto causal. El test no debe reutilizarse para escoger repetidamente modelos hasta lograr un resultado favorable.

Capturas: `validation_comparison.csv`, `selection_before_test.json` y figuras `02_comparacion_validacion.png` y `04_curvas_test.png` dentro de `ML/artifacts/churn180-v1/`.

## Interpretación de umbrales y calibración

El umbral medio de 0,311218, elegido por F2 en validación, marca 429 de 431 clientes del test. Detecta los 101 abandonos, pero genera 328 falsos positivos; solo quedan dos verdaderos negativos. Su recall del 100 % convive con una precisión de 23,54 % y con una selección del 99,54 % de la cartera. Por ello no ofrece una priorización práctica cuando el contacto está limitado.

El umbral alto de 0,377295 marca 92 clientes: 18 verdaderos positivos y 74 falsos positivos, con precisión de 19,57 % y recall de 17,82 %. Las categorías de puntuación no garantizan un orden perfecto de precisión observada. A 0,50 y 0,70 no se marca ningún cliente; la precisión es indefinida, aunque el código utilice cero como convención.

La calibración sigmoide reduce el Brier del test desde 0,2805 hasta 0,1967. Aun así, la probabilidad media calibrada es 35,91 %, mientras que el abandono observado es 23,43 %. Un menor Brier no acredita por sí solo calibración perfecta, discriminación útil o rentabilidad de campañas.

ML-06 añadió escenarios de cupo del 10 %, 20 % y 30 %, con pérdidas de clasificación en unidades abstractas. En el ejemplo del 20 % y penalización FN de dos unidades, el modelo selecciona 85 clientes y obtiene precisión de 17,65 %, frente al 24,71 % de recencia con el mismo cupo. Es una comparación retrospectiva descriptiva, no un nuevo test independiente ni una estimación del beneficio de una oferta.

Capturas: `docs/evidencias_ml06/calibration.png`, `thresholds.csv` y `capacity_scenarios.csv`; interpretación completa en `docs/ML06_CALIBRACION_UMBRALES.md`.

## Conclusión sobre el backend

La separación de `ML/`, `backend/` e `integraciones/krayin/` permite evaluar el modelo sin depender de PHP o de escrituras en el CRM. El contrato vigente conserva identificador de cliente, fecha de corte, versión y horizonte; comparte el cálculo de variables con entrenamiento y rechaza entradas fuera de dominio.

El servicio local usa HTTPS, autenticación por clave, restricciones de IP y Host, trazabilidad de solicitudes y límites de entrada. Admite lotes de hasta 500 clientes y cuatro solicitudes de predicción simultáneas. La saturación produce 503 y los cuerpos incompletos vencen a los cinco segundos con 408. No existe un límite duro de terminación del cómputo de un hilo; ese plazo de cinco segundos corresponde a recepción, no a inferencia.

API-06 midió 480 solicitudes HTTPS. Con cuatro solicitudes simultáneas y lotes de 500 clientes, el p95 de éxitos fue 158,48 ms en el equipo local. Con 16 simultáneas se observaron rechazos controlados: no debe presentarse la latencia de éxitos omitiendo la tasa de rechazo. El ensayo fue breve, con datos sintéticos repetidos y cliente/servidor en la misma máquina; no garantiza capacidad en otro destino.

API-07 comprobó entregas aisladas, actualización, reversión y recuperación del proceso en 50,11 segundos mediante una tarea periódica de Windows. El perfil requiere sesión de usuario, no constituye un servicio externo permanente. La entrega `api-2.1.0-api06` incluye los límites actuales; las entregas anteriores se preservaron. Tras ML-06, la suite registró 98 pruebas aprobadas y 95,14 % de cobertura Python. Ese porcentaje no mide exactitud predictiva ni incluye la cobertura de scripts PowerShell.

Capturas: `docs/evidencias_api/09_carga_https.json`, `08_despliegue_reversion.json` y `docs/evidencias_ml06/pruebas.txt`.

## Alcance de la fidelización y cierre académico

Al cierre de la etapa ML/API todavía no se había conectado Krayin. La integración local posterior se describe abajo; no se ejecutaron campañas ni se observó un cambio atribuible al sistema en recompra o satisfacción. Los escenarios de costos no reemplazan esa evidencia. El cierre académico no exige inventar una validación comercial: exige presentar con claridad qué se comprobó y qué no.

El plan `docs/PLAN_VALIDACION_CRM.md` describe pruebas de integración, observación predictiva futura y un piloto comparativo condicionado a resultados favorables. La validación comercial prospectiva y el servidor definitivo siguen siendo trabajo futuro. La integración local y su cierre documental CRM-01 a CRM-06 están completados. El modelo conserva estado experimental y no autoriza acciones automáticas.

La contribución de esta etapa consiste en un protocolo temporal reproducible, una evaluación que expone los límites del dataset/modelo y una infraestructura local comprobada para continuar la investigación. La evidencia disponible no permite concluir que ML ya mejoró la fidelización de clientes.


## Ampliación: detalle y operación en Krayin (29/10/2026)

CRM-04.3 y CRM-04.4 completaron la consulta individual y la actualización controlada desde el módulo local. Es posible revisar el resultado histórico, diferenciar la fecha de corte de la fecha del cálculo, recorrer versiones previas y consultar las variables del año anterior. La comparación del payload con su huella almacenada evita presentar una reconstrucción no verificada como si fuera la entrada original. Las siete variables de 431 clientes coincidieron con el test temporal, con diferencia máxima inferior a 10⁻¹².

La actualización se separó de la petición web mediante una cola persistente. Las solicitudes individuales y por lote respetan permisos, registran estados y se procesan con un comando acotado. Tres solicitudes concurrentes generaron una sola tarea. El ensayo HTTPS con autenticación incorrecta produjo 401 sin modificar la predicción existente; después de corregir la configuración, el procesamiento reutilizó el resultado válido manteniendo la fecha original. Esto demuestra trazabilidad y conservación de resultados en el flujo probado.

La regresión del módulo y las pruebas aisladas de acceso sumaron 125 casos y 348 aserciones sin fallos. Se verificó el navegador en escritorio y móvil, el rechazo CSRF, la consistencia del progreso y la conservación de contactos. Persisten avisos de deprecación PDO de la instalación y no se midió cobertura PHP. La prueba real procesó un cliente; no es una medición de rendimiento del lote completo ni una certificación de producción.

Estas evidencias prueban integración técnica, no mejora predictiva ni fidelización. El modelo conserva sus limitaciones; el mensaje orientativo actual exige revisión humana. Las reglas específicas de sugerencias, el registro manual de seguimiento y la aceptación integral corresponden a CRM-05/06. Las capturas y los archivos que sustentan estas conclusiones están identificados en `docs/GUIA_CAPTURAS.md`, `docs/CRM04_PANEL.md` y `docs/CRM044_ACTUALIZACIONES.md`.


## Ampliación: sugerencias orientativas (CRM-05.1)

El panel ya presenta reglas explícitas para orientar la revisión, compartidas entre listado y detalle. La elegibilidad, disponibilidad y calidad del historial prevalecen sobre la categoría de riesgo; cuando esos controles se cumplen, la categoría devuelta por la API determina el texto. Cada orientación explica su motivo y exige evaluación humana. La verificación abarcó 44 casos y 152 aserciones sin fallos, además de revisión en navegador. Esta capacidad facilita interpretar la demostración, pero no acredita que las acciones sugeridas mejoren la fidelización. Evidencias y capturas: `docs/CRM051_SUGERENCIAS.md`. El registro manual CRM-05.2 y el cierre integral CRM-06 se completaron posteriormente.


## Ampliación: seguimiento manual (CRM-05.2)

El módulo permite registrar decisiones de revisión con responsable, nota, estado, autor y fecha, separadas por cliente/corte/versión. El historial conserva cada entrada y el control de formularios desactualizados evita sobrescrituras silenciosas. El registro exige un permiso independiente de la actualización de predicciones y respeta el ámbito de clientes del usuario. La validación sumó 65 casos y 218 aserciones sin fallos, junto con pruebas reales de navegador, CSRF y lectura sin permisos de escritura. Esta capacidad aporta trazabilidad de la demostración; registrar «Revisado» o «Descartado» no demuestra mejora en fidelización ni intervención comercial. Capturas y alcance: `docs/CRM052_SEGUIMIENTO.md`. El cierre integral CRM-06 se completó posteriormente.


## Ampliación: aceptación técnica integral (CRM-06.1)

Se verificó el flujo completo de la demostración local: dataset, consumidor PHP, API HTTPS, persistencia, panel, sugerencias y revisión manual. La regresión final aprobó 161 casos PHP con 477 aserciones y 98 casos Python. Un lote funcional procesó 793 clientes: 431 recibieron predicción y 362 quedaron no elegibles; las 431 probabilidades coincidieron con el test temporal, con diferencia máxima de 4,9960 × 10⁻¹⁵. Las escrituras de ese lote se revirtieron, conservando el estado de la demostración.

Los ensayos HTTPS reales verificaron 401 y 422 sin reintentos adicionales, 503 con tres intentos acotados, caída y recuperación del servicio. Los errores conservaron el resultado válido anterior. La prueba de navegador confirmó el progreso, la sugerencia de calidad y el registro manual. Se documentó un intento inicial fallido por MariaDB detenido y la repetición satisfactoria después de iniciar el servicio. Esto demuestra funcionamiento técnico en el entorno y alcance probados; no modifica la conclusión sobre la utilidad predictiva limitada del modelo ni demuestra fidelización. Evidencia, límites y capturas en `docs/CRM061_VALIDACION_INTEGRAL.md`. CRM-06.2 está completada: guía operativa, índice de evidencia y tesis de 17 páginas revisadas. Se conserva una copia anterior en `docs/historico/InvestigacionTesis2026_antes_CRM062.docx`. La revisión documental no cambió el modelo ni volvió a medir cobertura.


Capturas de Krayin añadidas el 30/10/2026: páginas 18–19, listado del módulo, datos del cliente y sugerencia de revisión por historial limitado. Capítulo 3: 7–20; capítulo 4: 21–29.
