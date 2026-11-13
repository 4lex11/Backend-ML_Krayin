"""Genera gráficas descriptivas desde resultados guardados, sin entrenar."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidencias_mej08/graficas'
OUT.mkdir(parents=True, exist_ok=True)
def read(path):
    return json.loads((ROOT / path).read_text())
m = read('docs/evidencias_mej06/aceptacion/metrics.json')
b = read('docs/evidencias_mej06/aceptacion/bootstrap.json')
bins = read('docs/evidencias_mej05/calibracion/calibration_bins.json')
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
models = ['candidate', 'installed', 'recipe', 'recency', 'constant']
names = ['Candidato', 'v1 instalado', 'Receta v1', 'Recencia', 'Constante']
colors = ['#146B89', '#696969', '#A1BBC9', '#AAB89B', '#D4C6A8']
fig, axes = plt.subplots(1, 3, figsize=(11, 4.1))
for ax, metric, title in zip(axes, ['precision_at_20', 'average_precision', 'brier'], ['Precisión al 20 % ↑', 'Average precision ↑', 'Brier ↓']):
    vals = [m['E1'][k][metric] for k in models]
    ax.barh(names, vals, color=colors)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlim(0, max(vals)*1.3)
    for i, v in enumerate(vals):
        ax.text(v+.004, i, f'{v:.3f}', va='center', fontsize=10)
fig.tight_layout()
fig.savefig(OUT/'comparacion_e1.png', dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 3.5))
for k, label, col in zip(['candidate','recipe','recency'], ['Candidato', 'Receta v1', 'Recencia'], ['#146B89','#696969','#81975C']):
    ax.plot(['D1 · jun 2017','D2 · dic 2017','E1 · jun 2018'], [m[f][k]['precision_at_20']*100 for f in m], marker='o', label=label, color=col)
ax.set_ylabel('Precisión al 20 % (%)')
ax.set_ylim(0, 65)
ax.grid(axis='y', alpha=.2)
ax.legend(ncol=3, loc='lower left')
fig.tight_layout()
fig.savefig(OUT/'precision_temporal.png', dpi=200)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(9, 3.1))
for ax, key, title in zip(axes, ['precision_at_20_ci95', 'ap_ci95'], ['Diferencia media de precisión al 20 %', 'Diferencia media de AP']):
    for i, base in enumerate(['recency','recipe']):
        lo, hi = b[base][key]
        point = np.mean([m[f]['candidate']['precision_at_20' if key.startswith('precision') else 'average_precision']-m[f][base]['precision_at_20' if key.startswith('precision') else 'average_precision'] for f in m])
        ax.hlines(i, lo, hi, color='#146B89', linewidth=3)
        ax.plot(point, i, 'o', color='#146B89')
    ax.axvline(0, color='#888888', linestyle='--')
    ax.set_yticks([0,1], ['vs. recencia','vs. receta v1'])
    ax.set_ylim(-.6,1.6)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel('Diferencia absoluta · IC descriptivo del 95 %')
fig.tight_layout()
fig.savefig(OUT/'intervalos_bootstrap.png', dpi=200)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(9, 4.3))
for ax, fold in zip(axes,['D1','D2']):
    ax.plot([0,1],[0,1], '--', color='#999999', label='Referencia ideal')
    for variant, label, col in [('raw','Sin calibrar','#696969'),('sigmoid','Sigmoide','#146B89')]:
        rows = [r for r in bins if r['fold']==fold and r['variant']==variant and r['n']>0]
        ax.plot([r['mean_probability'] for r in rows],[r['observed_rate'] for r in rows], '-o', color=col, label=label)
    ax.set(xlim=(0,1), ylim=(0,1), title=fold, xlabel='Probabilidad media predicha', ylabel='Proporción observada de abandono')
    ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(OUT/'calibracion_desarrollo.png', dpi=200)
plt.close(fig)
print(OUT)
