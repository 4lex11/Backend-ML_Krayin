"""Reproduce las cifras de las figuras con etiquetas de proyecto, sin reentrenar."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for filename in ['plot_chapters34.py','plot_mej_results.py']:
    code=(ROOT/'scripts'/filename).read_text(encoding='utf-8')
    code=code.replace("ROOT / 'docs/evidencias_cap34'", "ROOT / 'docs/evidencias_proyecto_final'")
    code=code.replace("ROOT / 'docs/evidencias_mej08/graficas'", "ROOT / 'docs/evidencias_proyecto_final'")
    code=code.replace('Receta v1 reentrenada','Referencia reentrenada').replace('Receta v1','Referencia').replace('receta v1','referencia')
    code=code.replace('v1 instalado','Integrado').replace('Separación temporal de la ronda MEJ','Separación temporal de los datos')
    code=code.replace('7 variables originales','7 variables de comportamiento').replace('11 temporales para experimentos','11 variables temporales')
    exec(compile(code, str(ROOT/'scripts'/filename), 'exec'), {'__file__':str(ROOT/'scripts'/filename),'__name__':'__main__'})
