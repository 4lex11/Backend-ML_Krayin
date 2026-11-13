"""Actualiza las referencias documentales del cierre MEJ-08."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
replacements = {
    'README.md': [('17 páginas revisadas', '19 páginas revisadas')],
    'docs/GUIA_FINAL_CRM.md': [('contiene 17 páginas', 'contiene 19 páginas')],
    'docs/INDICE_EVIDENCIAS_FINAL.md': [('Referencia: `InvestigacionTesis2026.docx`, 17 páginas', 'Actualizado en MEJ-08. Referencia: `InvestigacionTesis2026.docx`, 19 páginas')],
    'docs/GUIA_CAPTURAS.md': [('Actualización CRM-06.2: la tesis tiene 17 páginas', 'Actualización MEJ-08: la tesis tiene 19 páginas')],
    'docs/TAREAS_PENDIENTES.md': [
        ('Queda pendiente MEJ-08.', 'MEJ-08 está completada; no quedan tareas pendientes de esta ronda dentro del alcance acordado.'),
        ('Esta etapa no altera el modelo ni el CRM hasta que las evaluaciones posteriores lo justifiquen.', 'El resultado final conserva v1 y la integración actual. Véase [MEJ08_CIERRE_DOCUMENTAL.md](MEJ08_CIERRE_DOCUMENTAL.md).'),
        ('DOCX ampliado a 17 páginas en CRM-06.2, actualizado y revisado', 'DOCX actualizado y revisado, ahora de 19 páginas tras MEJ-08'),
    ],
}
for name, pairs in replacements.items():
    path = ROOT / name
    value = path.read_text(encoding='utf-8')
    for old, new in pairs:
        value = value.replace(old, new)
    path.write_text(value, encoding='utf-8')

for name in ['README.md', 'docs/GUIA_FINAL_CRM.md', 'docs/INDICE_EVIDENCIAS_FINAL.md', 'docs/GUIA_CAPTURAS.md']:
    path = ROOT / name
    value = path.read_text(encoding='utf-8')
    target = 'docs/MEJ08_CIERRE_DOCUMENTAL.md' if name == 'README.md' else 'MEJ08_CIERRE_DOCUMENTAL.md'
    if '## Cierre de la mejora experimental (MEJ-08)' not in value:
        value += '\n## Cierre de la mejora experimental (MEJ-08)\n\nLa ronda está cerrada: MEJ-01 a MEJ-06 y MEJ-08 completadas; MEJ-07 no aplica porque el candidato incumplió dos criterios de Brier. Se conserva v1 y la integración existente. La tesis recoge la conclusión en la página 15, el diseño y la calibración en la 18 y la comparación E1 y decisión en la 19. Las recomendaciones y referencias conservan las páginas 16 y 17. Archivos concretos para capturas y límites: [acta de cierre](' + target + ').\n'
    path.write_text(value, encoding='utf-8')
