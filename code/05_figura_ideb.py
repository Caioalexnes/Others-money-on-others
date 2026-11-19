"""Figure of the essay: lowest and highest Ideb, 10th to 90th percentile and mean of the municipal networks in
each band of spending per student, 2023, in two panels: early grades (5th grade) and late grades (9th grade).
Writes the pgfplots code used in the essay (results/05_figura_ideb.tex).
Input: results/03_faixas.csv (script 03)."""
import os
import pandas as pd
from config import RES

ROT = {'até 8': 'até R\\$ 8 mil', '8-10': 'R\\$ 8 a 10 mil', '10-12': 'R\\$ 10 a 12 mil', '12-14': 'R\\$ 12 a 14 mil',
       '14-16': 'R\\$ 14 a 16 mil', '16-18': 'R\\$ 16 a 18 mil', '18-20': 'R\\$ 18 a 20 mil', 'acima de 20': 'acima de R\\$ 20 mil'}
num = lambda v: f'{v:.1f}'.replace('.', ',')
ANO = 2023
PAINEIS = [('ideb_ai', '5º ano', 'p5'), ('ideb_af', '9º ano', 'p9')]

f = pd.read_csv(os.path.join(RES, '03_faixas.csv'), sep=';')
n = len(ROT)
s = [r'\begin{tikzpicture}']
for j, (etapa, titulo, nome) in enumerate(PAINEIS):
    t = f[(f['ano'] == ANO) & (f['etapa'] == etapa)].set_index('faixa').loc[list(ROT)]
    pos = '' if j == 0 else f'  at={{({PAINEIS[j - 1][2]}.south east)}}, anchor=south west, xshift=1.15cm,\n'
    rotulos = ('  ytick={' + ','.join(str(i) for i in range(1, n + 1)) + '}, yticklabels={'
               + ','.join('{' + ROT[k] + '}' for k in t.index) + '},') if j == 0 else '  ytick=\\empty,'
    s += [r'\begin{axis}[estilo, name=' + nome + ',', pos.rstrip('\n') if pos else None,
          '  scale only axis, width=4.95cm, height=6.4cm,',
          f'  xmin=0, xmax=10, ymin=0.4, ymax={n + 0.6},', '  xtick={0,2,4,6,8,10},', rotulos,
          f'  title={{{titulo}}}, title style={{font=\\small, text=tinta}},',
          f'  xlabel={{Ideb em {ANO}}},', '  xmajorgrids, grid style={draw=tinta!15},', '  axis x line*=bottom, axis y line*=left,',
          '  clip=false]']
    s = [x for x in s if x is not None]
    for i, (k, r) in enumerate(t.iterrows(), start=1):
        s += [f'\\draw[tinta!45, line width=0.6pt] (axis cs:{r["min"]:.1f},{i}) -- (axis cs:{r["max"]:.1f},{i});',
              f'\\draw[serie, line width=4pt] (axis cs:{r["p10"]:.2f},{i}) -- (axis cs:{r["p90"]:.2f},{i});',
              f'\\node[left=1pt, font=\\scriptsize, text=tinta] at (axis cs:{r["min"]:.1f},{i}) {{{num(r["min"])}}};',
              f'\\node[right=1pt, font=\\scriptsize, text=tinta] at (axis cs:{r["max"]:.1f},{i}) {{{num(r["max"])}}};',
              f'\\filldraw[fill=white, draw=serie, line width=1pt] (axis cs:{r["mean"]:.2f},{i}) circle (2.4pt);']
    s += [f'\\node[above=3pt, font=\\scriptsize, text=tinta] at (axis cs:{t.iloc[-1]["mean"]:.2f},{n}) {{média}};', r'\end{axis}']
s += [r'\end{tikzpicture}']
open(os.path.join(RES, '05_figura_ideb.tex'), 'w').write('\n'.join(s) + '\n')
for etapa, titulo, _ in PAINEIS:
    print(titulo); print(f[(f['ano'] == ANO) & (f['etapa'] == etapa)].set_index('faixa').loc[list(ROT)][['count', 'min', 'p10', 'mean', 'p90', 'max']].round(2).to_string())
