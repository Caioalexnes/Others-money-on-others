"""Who are the municipal networks with an Ideb of the early grades below 4 or above 8 in 2023.

Adds to the 2023 base of script 03 the state, the region, the population (Censo 2022), the IDHM
(2010) and the flow indicator of the Ideb (share of students approved), and writes:
  results/06_redes_2023.csv     one row per municipal network
  results/06_extremos.csv       networks with Ideb below 4 or above 8
  results/06_resumo.csv         profile of the two groups and of all networks
  results/06_aprovacao.csv      share of networks that approve every student in the early grades
  results/06_fig_faixas_regiao.pdf, results/06_fig_ideb_idhm.pdf   figures of the essay
Usage: python 06_extremos.py
"""
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from config import DADOS, RES

REGIAO = {'1': 'NO', '2': 'NE', '3': 'SE', '4': 'SU', '5': 'CO'}
NOME_REGIAO = {'NO': 'Norte', 'NE': 'Nordeste', 'CO': 'Centro-Oeste', 'SE': 'Sudeste', 'SU': 'Sul'}


def fonte():
    """Use the essay's typeface (TeX Gyre Pagella) when it is installed."""
    for p in font_manager.findSystemFonts():
        if 'texgyrepagella-regular' in p.lower():
            font_manager.fontManager.addfont(p)
            plt.rcParams['font.family'] = font_manager.FontProperties(fname=p).get_name()
            return
    plt.rcParams['font.family'] = 'serif'


def base():
    b = pd.read_csv(os.path.join(RES, '03_base_municipios.csv'), sep=';')
    b = b[b.ano == 2023].dropna(subset=['gasto_aluno', 'ideb_ai']).copy()
    ai = pd.read_excel(os.path.join(DADOS, 'inep', 'divulgacao_anos_iniciais_municipios_2025',
                                    'divulgacao_anos_iniciais_municipios_2025.xlsx'), header=9)
    ai = ai[ai.REDE == 'Municipal'].copy()
    ai['cod_ibge'] = pd.to_numeric(ai.CO_MUNICIPIO, errors='coerce')
    for c in ('VL_INDICADOR_REND_2023', 'VL_NOTA_MEDIA_2023', 'VL_OBSERVADO_2019', 'VL_OBSERVADO_2025'):
        ai[c] = pd.to_numeric(ai[c], errors='coerce')
    ai = ai.rename(columns={'SG_UF': 'uf', 'NO_MUNICIPIO': 'nome', 'VL_INDICADOR_REND_2023': 'rendimento',
                            'VL_NOTA_MEDIA_2023': 'saeb', 'VL_OBSERVADO_2019': 'ideb_ai_2019',
                            'VL_OBSERVADO_2025': 'ideb_ai_2025'})
    b = b.merge(ai[['cod_ibge', 'uf', 'nome', 'rendimento', 'saeb', 'ideb_ai_2019', 'ideb_ai_2025']],
                on='cod_ibge', how='left')
    b['regiao'] = b.cod_ibge.astype(int).astype(str).str[0].map(REGIAO)
    pop = json.load(open(os.path.join(DADOS, 'pop_censo2022.json'), encoding='utf-8'))[1:]
    pop = pd.DataFrame({'cod_ibge': [int(r['D1C']) for r in pop], 'pop2022': [float(r['V']) for r in pop]})
    idhm = json.load(open(os.path.join(DADOS, 'idhm_ipeadata.json'), encoding='utf-8'))['value']
    idhm = pd.DataFrame([{'cod_ibge': int(r['TERCODIGO']), 'idhm': r['VALVALOR']} for r in idhm
                         if r['VALDATA'].startswith('2010') and r['NIVNOME'] == 'Municípios'])
    return b.merge(pop, on='cod_ibge', how='left').merge(idhm, on='cod_ibge', how='left')


def resumo(b):
    b = b.copy()
    b['grupo'] = np.select([b.ideb_ai > 8, b.ideb_ai < 4], ['acima de 8', 'abaixo de 4'], 'de 4 a 8')
    linhas = []
    for nome, s in [('acima de 8', b[b.grupo == 'acima de 8']), ('abaixo de 4', b[b.grupo == 'abaixo de 4']),
                    ('todas', b)]:
        r = {'grupo': nome, 'redes': len(s), 'gasto_aluno_mediana': s.gasto_aluno.median(),
             'populacao_mediana': s.pop2022.median(), 'menos_de_20_mil_hab': (s.pop2022 < 20000).mean(),
             'idhm_mediana': s.idhm.median(), 'inse_mediana': s.inse.median(),
             'ideb_2019_mediana': s.ideb_ai_2019.median(), 'ideb_2025_mediana': s.ideb_ai_2025.median()}
        r.update({f'regiao_{k}': (s.regiao == k).sum() for k in NOME_REGIAO})
        r.update({f'uf_{k}': v for k, v in s.uf.value_counts().head(6).items()} if nome != 'todas' else {})
        linhas.append(r)
    return pd.DataFrame(linhas)


def aprovacao(b):
    g = np.where(b.uf == 'CE', 'Ceará', np.where(b.uf == 'AL', 'Alagoas',
                 np.where(b.regiao == 'NE', 'outros do Nordeste',
                 np.where(b.regiao == 'NO', 'Norte', 'Sul, Sudeste e Centro-Oeste'))))
    a = b.assign(grupo=g, todos_aprovados=b.rendimento >= 0.995)
    return a.groupby('grupo').agg(redes=('todos_aprovados', 'size'),
                                  aprovam_todos=('todos_aprovados', 'mean')).reset_index()


def figura_faixas(b, arq):
    cortes = [-np.inf, 8, 10, 12, 14, 16, 18, 20, np.inf]
    rot = ['até R\\$ 8 mil', 'R\\$ 8 a 10 mil', 'R\\$ 10 a 12 mil', 'R\\$ 12 a 14 mil', 'R\\$ 14 a 16 mil',
           'R\\$ 16 a 18 mil', 'R\\$ 18 a 20 mil', 'acima de R\\$ 20 mil']
    b = b.dropna(subset=['idhm', 'pop2022']).copy()
    b['f'] = pd.cut(b.gasto_aluno / 1000, cortes, labels=range(8), right=False).astype(int)
    cmap = LinearSegmentedColormap.from_list('idh', ['#c0392b', '#e67e22', '#f2c14e', '#7fb3e0', '#1f5fae'])
    norm = Normalize(0.45, 0.80)
    forma = {'NO': '^', 'NE': 'o', 'CO': 'D', 'SE': 's', 'SU': 'v'}
    tam = lambda p: 1.5 + np.sqrt(np.minimum(p, 1.5e6)) / 16
    rng = np.random.default_rng(1)
    b['y'] = b.f + rng.uniform(-0.33, 0.33, len(b))
    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    b = b.sort_values('pop2022', ascending=False)
    for r, m in forma.items():
        s = b[b.regiao == r]
        ax.scatter(s.ideb_ai, s.y, s=tam(s.pop2022), c=s.idhm, cmap=cmap, norm=norm, marker=m, alpha=0.8,
                   linewidths=0.15, edgecolors='white')
    for i in range(8):
        v = b.loc[b.f == i, 'ideb_ai']
        p10, p90 = np.percentile(v, [10, 90])
        ax.plot([p10, p90], [i + 0.43, i + 0.43], color='#33322f', lw=1.6, solid_capstyle='butt')
        ax.plot(v.mean(), i + 0.43, 'o', ms=3.4, mfc='white', mec='#33322f', mew=0.9)
    for x in (4, 8):
        ax.axvline(x, color='#999999', lw=0.5, ls=':')
    ax.set_yticks(range(8))
    ax.set_yticklabels(rot, fontsize=7.5)
    ax.set_xlim(2, 10)
    ax.set_ylim(-0.6, 7.75)
    ax.tick_params(labelsize=7.5)
    ax.set_xlabel('Ideb do 5º ano em 2023 (rede municipal)', fontsize=8)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.015)
    cb.set_label('IDHM 2010', fontsize=7.5)
    cb.ax.tick_params(labelsize=6.5)
    h = [Line2D([], [], marker=m, ls='', color='#777777', ms=4.5, label=NOME_REGIAO[r]) for r, m in forma.items()]
    h += [Line2D([], [], marker='o', ls='', color='#aaaaaa', ms=np.sqrt(tam(p)),
                 label=f'{p / 1000:,.0f} mil hab.'.replace(',', '.')) for p in (5e3, 50e3, 500e3)]
    h += [Line2D([], [], color='#33322f', lw=1.6, label='10º ao 90º percentil')]
    ax.legend(handles=h, fontsize=6.8, loc='upper left', bbox_to_anchor=(0, -0.1), ncol=5, frameon=False)
    fig.savefig(arq, bbox_inches='tight', metadata={'CreationDate': None})
    plt.close(fig)


def figura_idhm(b, arq):
    b = b.dropna(subset=['idhm', 'pop2022'])
    cor = {'NO': '#1b9e77', 'NE': '#e07b39', 'CO': '#8c6bb1', 'SE': '#2a78d6', 'SU': '#9a9a9a'}
    tam = lambda p: 1.2 + np.sqrt(np.minimum(p, 1.5e6)) / 14
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    ax.axhspan(8, 10.3, color='#f3efe6', zorder=0)
    ax.axhspan(1.8, 4, color='#f3efe6', zorder=0)
    bb = b.sort_values('pop2022', ascending=False)
    for r in ['SU', 'SE', 'CO', 'NO', 'NE']:
        s = bb[bb.regiao == r]
        ax.scatter(s.idhm, s.ideb_ai, s=tam(s.pop2022), color=cor[r], alpha=0.55 if r in ('SU', 'SE', 'CO') else 0.75,
                   linewidths=0.15, edgecolors='white', zorder=2)
    bins = np.arange(0.42, 0.87, 0.02)
    m = b.groupby(pd.cut(b.idhm, bins), observed=False).ideb_ai.agg(['mean', 'size'])
    xc = np.array([iv.mid for iv in m.index])
    ok = (m['size'] >= 15).values
    ax.plot(xc[ok], m['mean'].values[ok], color='#33322f', lw=1.6, zorder=3)
    rotulos = {('Sobral', 'CE'): (6, 3), ('Pires Ferreira', 'CE'): (-70, -2), ('Breves', 'PA'): (5, -8),
               ('Melgaço', 'PA'): (6, -3), ('Manaquiri', 'AM'): (6, -3), ('Coruripe', 'AL'): (6, 0)}
    for (n, uf), (dx, dy) in rotulos.items():
        r = b[(b.nome == n) & (b.uf == uf)]
        if len(r):
            r = r.iloc[0]
            ax.annotate(f'{n} ({uf})', (r.idhm, r.ideb_ai), xytext=(dx, dy), textcoords='offset points',
                        fontsize=6.5, color='#33322f')
    ax.set_xlim(0.41, 0.87)
    ax.set_ylim(1.8, 10.3)
    ax.tick_params(labelsize=7.5)
    ax.set_xlabel('IDHM 2010 do município', fontsize=8)
    ax.set_ylabel('Ideb do 5º ano em 2023 (rede municipal)', fontsize=8)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    h = [Line2D([], [], marker='o', ls='', color=cor[r], ms=5, label=NOME_REGIAO[r]) for r in ['NO', 'NE', 'CO', 'SE', 'SU']]
    h += [Line2D([], [], marker='o', ls='', color='#bbbbbb', ms=np.sqrt(tam(p)),
                 label=f'{p / 1000:,.0f} mil hab.'.replace(',', '.')) for p in (5e3, 50e3, 500e3)]
    h += [Line2D([], [], color='#33322f', lw=1.6, label='média do Ideb por nível de IDHM')]
    ax.legend(handles=h, fontsize=6.8, loc='upper left', bbox_to_anchor=(0, -0.11), ncol=5, frameon=False)
    fig.savefig(arq, bbox_inches='tight', metadata={'CreationDate': None})
    plt.close(fig)


if __name__ == '__main__':
    fonte()
    b = base()
    b.to_csv(os.path.join(RES, '06_redes_2023.csv'), sep=';', index=False)
    ext = b[(b.ideb_ai < 4) | (b.ideb_ai > 8)].sort_values('ideb_ai')
    ext[['cod_ibge', 'nome', 'uf', 'regiao', 'pop2022', 'idhm', 'inse', 'gasto_aluno', 'rendimento', 'saeb',
         'ideb_ai_2019', 'ideb_ai', 'ideb_ai_2025']].to_csv(os.path.join(RES, '06_extremos.csv'), sep=';', index=False)
    r = resumo(b)
    r.to_csv(os.path.join(RES, '06_resumo.csv'), sep=';', index=False)
    a = aprovacao(b)
    a.to_csv(os.path.join(RES, '06_aprovacao.csv'), sep=';', index=False)
    figura_faixas(b, os.path.join(RES, '06_fig_faixas_regiao.pdf'))
    figura_idhm(b, os.path.join(RES, '06_fig_ideb_idhm.pdf'))
    print(r.T.to_string())
    print(a.to_string(index=False))
