"""Figuras de metodología y resultados derivadas de evidencia local."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidencias_cap34'
OUT.mkdir(exist_ok=True)
def read(path):
    return json.loads((ROOT/path).read_text())
sel = read('docs/evidencias_mej04/comparacion/selection.json')
v1 = read('ML/artifacts/churn180-v1/metadata.json')
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
best = [next(r for r in sel['ranking'] if r['id'].startswith(f)) for f in ['lightgbm_', 'forest_', 'logistic_']]
recipe = next(r for r in sel['comparators'] if r['id']=='baseline_v1_recipe')
rows = best + [recipe]
fig, axes = plt.subplots(3, 1, figsize=(9, 7.4))
labels = ['LightGBM original a', 'Random Forest original a', 'Logística temporal b', 'Receta v1 reentrenada']
for ax, key, title in zip(axes, ['precision_at_20','average_precision','brier'], ['Precisión al 20 % ↑','Average precision ↑','Brier ↓']):
    vals = [r[key] for r in rows]
    ax.barh(labels, vals, color=['#146B89','#A6B9C0','#BFC9C4','#777777'])
    ax.invert_yaxis()
    ax.set_xlim(0, max(vals)*1.2)
    ax.set_title(title, fontsize=11)
    for i, val in enumerate(vals):
        ax.text(val+.003, i, f'{val:.4f}', va='center')
fig.tight_layout()
fig.savefig(OUT/'comparacion_desarrollo.png',dpi=200)
plt.close(fig)

fig, axes = plt.subplots(1,3,figsize=(11,4.8))
history=sorted(v1['validation'],key=lambda r:r['average_precision'],reverse=True)
for ax,key,title in zip(axes,['average_precision','roc_auc','brier'],['AP ↑','ROC-AUC ↑','Brier ↓']):
    vals=[r[key] for r in history]
    labels=[r['model'].replace('_SMOTE',' + SMOTE') for r in history]
    ax.barh(labels,vals,color=['#146B89' if r['model']=='LightGBM' else '#B8C5CC' for r in history])
    ax.invert_yaxis(); ax.set_title(title); ax.set_xlim(0,max(vals)*1.3)
    for i,value in enumerate(vals): ax.text(value+.003,i,f'{value:.3f}',va='center',fontsize=9)
fig.tight_layout(); fig.savefig(OUT/'comparacion_v1.png',dpi=200); plt.close(fig)

frame = pd.read_csv(ROOT/'docs/evidencias_mej06/aceptacion/E1_predictions.csv')
matrices = {}
for key in ['installed','candidate']:
    selected = frame.sort_values([key,'Customer ID'], ascending=[False,True]).head(87).index
    predictions = frame.index.isin(selected).astype(int)
    matrices[key+'_top20'] = confusion_matrix(frame.Churn, predictions, labels=[0,1]).tolist()
matrices['installed_medium'] = confusion_matrix(frame.Churn, frame.installed.ge(v1['thresholds']['medium']),labels=[0,1]).tolist()
assert matrices['installed_medium']==v1['test']['confusion_matrix']
def cmplot(keys, titles, filename):
    fig, axes = plt.subplots(1,len(keys),figsize=(9 if len(keys)>1 else 5.3,4))
    for ax,key,title in zip(np.atleast_1d(axes),keys,titles):
        matrix = np.array(matrices[key])
        ax.imshow(matrix, cmap='Blues', vmin=0, vmax=330)
        for (i,j), value in np.ndenumerate(matrix):
            ax.text(j,i,str(value),ha='center',va='center',color='white' if value>165 else 'black',fontsize=17)
        ax.set_xticks([0,1],['No abandono','Abandono'])
        ax.set_yticks([0,1],['No abandono','Abandono'])
        ax.set_xlabel('Predicción'); ax.set_ylabel('Observado'); ax.set_title(title,fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT/filename,dpi=200)
    plt.close(fig)
cmplot(['installed_top20','candidate_top20'], ['v1 instalado · cupo 20 %','Candidato · cupo 20 %'], 'matrices_cupo20.png')
cmplot(['installed_medium'], ['v1 instalado · umbral medio 0,311218'], 'matriz_vigente.png')

fig,ax=plt.subplots(figsize=(10,4.2))
ax.axis('off')
steps=[('1 · Validar transacciones','9.800 líneas; fechas día/mes/año\n0 duplicados exactos eliminados'),('2 · Fijar historial','(corte − 365 días, corte]\nElegibilidad: recencia ≤ 180 días'),('3 · Agregar por cliente','7 variables originales\n11 temporales para experimentos'),('4 · Etiquetar futuro','Sin compra en los 180 días siguientes\nCobertura completa del horizonte')]
for i,(title,body) in enumerate(steps):
    x=[.25,.75,.75,.25][i]; y=.78 if i<2 else .25
    ax.text(x,y,title+'\n\n'+body,ha='center',va='center',bbox=dict(boxstyle='round,pad=.8',facecolor='#EFF4F6',edgecolor='#7A939C'),fontsize=11)
ax.annotate('',(.51,.78),(.46,.78),arrowprops=dict(arrowstyle='->',color='#555555'))
ax.annotate('',(.49,.25),(.54,.25),arrowprops=dict(arrowstyle='->',color='#555555'))
ax.annotate('',(.75,.43),(.75,.60),arrowprops=dict(arrowstyle='->',color='#555555'))
# La lectura sigue 1 -> 2 -> 3 -> 4 por numeración, sin sugerir flujo inverso.
ax.text(.5,.01,'Los identificadores y la etiqueta no son predictores. No se usan compras futuras en las variables.',ha='center',fontsize=10)
fig.tight_layout(); fig.savefig(OUT/'preparacion_actual.png',dpi=200); plt.close(fig)

fig,ax=plt.subplots(figsize=(9,3.8))
columns=['jun 2016','dic 2016','jun 2017','dic 2017','jun 2018']
values=np.array([[1,2,3,0,0],[1,1,2,3,0],[1,1,1,2,3]])
from matplotlib.colors import ListedColormap
ax.imshow(values,cmap=ListedColormap(['#FFFFFF','#B6CCD5','#F0D7A1','#497C91']),vmin=0,vmax=3,aspect='auto')
for (i,j), value in np.ndenumerate(values):
    if value: ax.text(j,i,{1:'Entrenar',2:'Calibrar',3:'Evaluar'}[value],ha='center',va='center',color='white' if value==3 else 'black')
ax.set_xticks(range(5),columns); ax.set_yticks(range(3),['D1','D2','E1'])
ax.set_title('Separación temporal de la ronda MEJ')
fig.tight_layout(); fig.savefig(OUT/'cortes_temporales.png',dpi=200); plt.close(fig)
(OUT/'matrices.json').write_text(json.dumps(matrices,indent=2),encoding='utf-8')
print(matrices)
