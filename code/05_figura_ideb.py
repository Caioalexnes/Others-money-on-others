"""Figure of the essay: lowest and highest Ideb, 10th to 90th percentile and mean (early grades) of the municipal networks in each
band of spending per student, 2023. Writes the pgfplots code used in the essay (results/05_figura_ideb.tex).
Input: results/03_faixas.csv (script 03)."""
import os
import pandas as pd
from config import RES

ROT = {'até 8': 'até R\\$ 8 mil', '8-10': 'R\\$ 8 a 10 mil', '10-12': 'R\\$ 10 a 12 mil', '12-14': 'R\\$ 12 a 14 mil',
       '14-16': 'R\\$ 14 a 16 mil', '16-18': 'R\\$ 16 a 18 mil', '18-20': 'R\\$ 18 a 20 mil', 'acima de 20': 'acima de R\\$ 20 mil'}
num = lambda v: f'{v:.1f}'.replace('.', ',')

f = pd.read_csv(os.path.join(RES, '03_faixas.csv'), sep=';')
f = f[(f['ano'] == 2023) & (f['etapa'] == 'ideb_ai')].set_index('faixa').loc[list(ROT)]
n = len(f)
s = [r'\begin{tikzpicture}', r'\begin{axis}[estilo,', '  scale only axis, width=0.62\\textwidth, height=6.4cm,',
     f'  xmin=0, xmax=10, ymin=0.4, ymax={n + 0.6},', '  xtick={0,2,4,6,8,10},',
     '  ytick={' + ','.join(str(i) for i in range(1, n + 1)) + '}, yticklabels={' + ','.join('{' + ROT[k] + '}' for k in f.index) + '},',
     '  xlabel={Ideb do 5º ano em 2023},', '  xmajorgrids, grid style={draw=tinta!15},', '  axis x line*=bottom, axis y line*=left,', '  clip=false]']
for i, (k, r) in enumerate(f.iterrows(), start=1):
    s += [f'\\draw[tinta!45, line width=0.6pt] (axis cs:{r["min"]:.1f},{i}) -- (axis cs:{r["max"]:.1f},{i});',
          f'\\draw[serie, line width=4pt] (axis cs:{r["p10"]:.2f},{i}) -- (axis cs:{r["p90"]:.2f},{i});',
          f'\\node[left=2pt, font=\\footnotesize, text=tinta] at (axis cs:{r["min"]:.1f},{i}) {{{num(r["min"])}}};',
          f'\\node[right=2pt, font=\\footnotesize, text=tinta] at (axis cs:{r["max"]:.1f},{i}) {{{num(r["max"])}}};',
          f'\\filldraw[fill=white, draw=serie, line width=1pt] (axis cs:{r["mean"]:.2f},{i}) circle (2.6pt);']
s += [f'\\node[above=4pt, font=\\footnotesize, text=tinta] at (axis cs:{f.iloc[-1]["mean"]:.2f},{n}) {{média}};', r'\end{axis}', r'\end{tikzpicture}']
open(os.path.join(RES, '05_figura_ideb.tex'), 'w').write('\n'.join(s) + '\n')
print(f[['count', 'min', 'p10', 'mean', 'p90', 'max']].round(2).to_string())
