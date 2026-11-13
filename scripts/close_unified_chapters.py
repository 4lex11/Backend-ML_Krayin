from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'docs/INDICE_EVIDENCIAS_FINAL.md'
s=p.read_text(encoding='utf-8')
s=s.replace('[Configuraciones MEJ]', '[Configuraciones evaluadas]')
s=s.replace('evidencias_cap34/preparacion_actual.png','evidencias_proyecto_final/preparacion_actual.png').replace('evidencias_cap34/cortes_temporales.png','evidencias_proyecto_final/cortes_temporales.png')
for name in ['comparacion_desarrollo','matrices_cupo20','matriz_vigente','comparacion_v1']:
    s=s.replace(f'evidencias_cap34/{name}.png',f'evidencias_proyecto_final/{name}.png')
s=s.replace('evidencias_mej08/graficas/','evidencias_proyecto_final/')
s=s.replace('Comparación E1 y decisión de uso | 21','Evaluación E1 | 23').replace('Comparación histórica v1 | 22','Comparación de algoritmos y balanceo | 21').replace('Dieciocho candidatos MEJ | 23','Configuraciones y variables | 22')
s=s.replace('[Matriz v1]','[Matriz del modelo integrado]').replace('[Gráfica v1]','[Comparación de algoritmos]')
s=s.replace('resaltados en la página 21. Se conserva v1','resaltados en la página 23. La decisión se explica en la página 24. Se conserva el modelo integrado')
s=s.replace('sus etapas se indican en los pies','sus archivos de evidencia se indican en los pies')
s += '\nLos capítulos 3 y 4 describen un único proyecto en orden metodológico. Las etiquetas de versiones permanecen solo en identificadores técnicos, rutas de evidencia y anexos históricos. Figuras con etiquetas unificadas: `docs/evidencias_proyecto_final/`.\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'docs/GUIA_CAPTURAS.md'; s=p.read_text(encoding='utf-8')
s=s.replace('7–20 y 19–27','7–20 y 21–29').replace('`docs/evidencias_cap34/` y `docs/evidencias_mej08/graficas/`','`docs/evidencias_proyecto_final/`')
s=s.replace('Páginas 17–18: matrices','Páginas 17 y 20: matrices').replace('Páginas 19–24: resultados E1, comparación histórica v1, 18 candidatos, calibración, incertidumbre y cupos.','Páginas 21–26: algoritmos, configuraciones y variables, evaluación E1, calibración, incertidumbre y cupos.').replace('Páginas 25–27: aceptación','Páginas 27–29: aceptación')
p.write_text(s,encoding='utf-8')
(ROOT/'docs/REVISION_COHERENCIA.md').write_text('''# Revisión de capítulos 3 y 4

30/10/2026. El documento tiene 44 páginas. Los capítulos 3 y 4 presentan el proyecto de forma continua, sin división narrativa entre versiones o tareas de mejora. Se conserva la estructura 3.1, 3.2 y 3.3 y sus seis fases; la selección no se adelanta al definir las variables o preparar los datos.

Los resultados siguen el orden: algoritmos y balanceo (21), configuraciones y variables (22), evaluación E1 (23), calibración y aceptación (24), incertidumbre (25), cupos (26) y verificación técnica e integración (27–29). Las métricas mantienen sus poblaciones y criterios originales. Se distingue la configuración candidata del modelo integrado y de la referencia reentrenada.

Las diez figuras de metodología y resultados usan etiquetas unificadas en `docs/evidencias_proyecto_final/`. Se preservaron las cuatro imágenes originales y las capturas reales de Krayin. No se modificaron los modelos ni se repitieron los ensayos de software.

Se revisaron visualmente las páginas modificadas 7–18 y 20–27; las páginas 1–6, 19 y 28–44 son idénticas píxel a píxel a la exportación anterior revisada. Evidencia: `.local/docqa/proyecto_final/`. Las 44 comprobaciones documentales incluyen cifras, matrices, imágenes, secuencia narrativa y uso efectivo de las figuras unificadas. Resultado: [REVISION_COHERENCIA.json](REVISION_COHERENCIA.json).

Respaldo previo: `docs/historico/InvestigacionTesis2026_antes_redaccion_proyecto_final.docx`. Ubicaciones para capturas: [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md).
''',encoding='utf-8')
