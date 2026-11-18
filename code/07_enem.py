"""Enem 2023 as an outside check on the Ideb of the municipal networks, with a focus on Ceará.

The Enem is applied by Inep, not by the municipality, and the municipal network does not teach high
school; it is used here to see whether a high Ideb in the early grades shows up later in an exam the
network neither applies nor prepares for. Students: those finishing public high school in 2023
(TP_ST_CONCLUSAO = 2, TP_ESCOLA = 2) present on both days; score: mean of the four objective tests.

Because the share of students who take the Enem varies a lot between states (78% of the 3rd-year
public enrollment in Ceará, 34% in São Paulo), the comparison uses the mean of the best students up to
a fixed share of the 3rd-year enrollment (20%, 25% or 30%), not the simple mean, which penalizes the
places where almost everyone takes the exam.

Writes:
  results/07_enem_uf.csv          by state: takers, participation, simple mean, mean of the best 20/25/30%
  results/07_enem_municipios.csv  by municipality of the school, with the Ideb of the municipal network
  results/07_enem_quintis.csv     median national percentile by quintile of the 2015 (and 2017) Ideb
  results/07_enem_topo.csv        municipalities in the top 5% and 10% of the 2015 Ideb
  results/07_fig_enem.pdf         figure of the essay
Usage: python 07_enem.py
"""
import os, zipfile
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import DADOS, RES
from importlib import import_module

EXTREMOS = import_module('06_extremos')   # module names starting with a digit need import_module
fonte = EXTREMOS.fonte

UF = {11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN',
      25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC',
      43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'}
NOTAS = ['NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT']
PRESENCA = ['TP_PRESENCA_CN', 'TP_PRESENCA_CH', 'TP_PRESENCA_LC', 'TP_PRESENCA_MT']


def enem():
    cols = ['TP_ST_CONCLUSAO', 'TP_ESCOLA', 'CO_MUNICIPIO_ESC', 'SG_UF_ESC', 'SG_UF_PROVA', 'Q006'] + NOTAS + PRESENCA
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_enem_2023.zip'))
    nome = [n for n in z.namelist() if n.split('/')[-1].upper().startswith('MICRODADOS_ENEM')][0]
    partes = []
    for ch in pd.read_csv(z.open(nome), sep=';', encoding='latin1', usecols=lambda c: c in cols,
                          chunksize=500_000, low_memory=False):
        ch = ch[(ch.TP_ST_CONCLUSAO == 2) & (ch.TP_ESCOLA == 2)]
        ch = ch[(ch[PRESENCA] == 1).all(axis=1)].copy()
        ch['nota'] = ch[NOTAS].mean(axis=1)
        partes.append(ch[['SG_UF_ESC', 'SG_UF_PROVA', 'CO_MUNICIPIO_ESC', 'Q006', 'nota']])
    e = pd.concat(partes, ignore_index=True)
    e['uf'] = e.SG_UF_ESC.fillna(e.SG_UF_PROVA)   # state of the school, or of the exam when the school is not given
    return e


def matriculas_3ano():
    with zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_censo_escolar_2023.zip')) as z:
        c = pd.read_csv(z.open('microdados_censo_escolar_2023/dados/microdados_ed_basica_2023.csv'), sep=';',
                        encoding='latin1', usecols=['SG_UF', 'CO_MUNICIPIO', 'TP_DEPENDENCIA',
                                                    'TP_SITUACAO_FUNCIONAMENTO', 'QT_MAT_MED_PROP_3',
                                                    'QT_MAT_MED_CT_3', 'QT_MAT_MED_NM_3'])
    c = c[c.TP_DEPENDENCIA.isin([1, 2, 3]) & (c.TP_SITUACAO_FUNCIONAMENTO == 1)]
    c['mat3'] = c[['QT_MAT_MED_PROP_3', 'QT_MAT_MED_CT_3', 'QT_MAT_MED_NM_3']].fillna(0).sum(axis=1)
    return c.groupby('SG_UF').mat3.sum(), c.groupby('CO_MUNICIPIO').mat3.sum()


def media_topo(notas, k):
    """Mean of the k best scores (k rounded); NaN if there are fewer than k scores."""
    s = np.sort(np.asarray(notas, dtype=float))[::-1]
    k = int(round(k))
    return s[:k].mean() if 0 < k <= len(s) else np.nan


def por_uf(e, mat_uf):
    g = e.groupby('uf')
    t = pd.DataFrame({'participantes': g.size(), 'media_simples': g['nota'].mean()})
    t['matriculas_3ano'] = mat_uf.reindex(t.index)
    t['participacao'] = t.participantes / t.matriculas_3ano
    for sh in (0.20, 0.25, 0.30):
        t[f'media_melhores_{int(sh * 100)}'] = [media_topo(e.loc[e.uf == u, 'nota'], sh * t.loc[u, 'matriculas_3ano'])
                                                for u in t.index]
        t[f'posicao_{int(sh * 100)}'] = t[f'media_melhores_{int(sh * 100)}'].rank(ascending=False)
    t['posicao_media_simples'] = t.media_simples.rank(ascending=False)
    baixa = e[e.Q006.isin(['A', 'B'])].groupby('uf')['nota'].agg(['size', 'mean'])  # family income up to 1 minimum wage
    t['participantes_renda_ate_1sm'] = baixa['size']
    t['media_renda_ate_1sm'] = baixa['mean']
    t.index.name = 'uf'
    return t.sort_values('media_melhores_25', ascending=False)


def ideb_municipal():
    def le(arq):
        x = pd.read_excel(os.path.join(DADOS, 'inep', arq, arq + '.xlsx'), header=9)
        x = x[x.REDE == 'Municipal'].copy()
        x['cod_ibge'] = pd.to_numeric(x.CO_MUNICIPIO, errors='coerce')
        return x
    ai = le('divulgacao_anos_iniciais_municipios_2025')
    af = le('divulgacao_anos_finais_municipios_2025')
    out = pd.DataFrame({'cod_ibge': ai.cod_ibge, 'uf': ai.SG_UF, 'nome': ai.NO_MUNICIPIO})
    for y in (2015, 2017, 2023):
        out[f'ideb_ai_{y}'] = pd.to_numeric(ai[f'VL_OBSERVADO_{y}'], errors='coerce').values
    af = af.assign(saeb_af_2019=pd.to_numeric(af.VL_NOTA_MEDIA_2019, errors='coerce'))[['cod_ibge', 'saeb_af_2019']]
    return out.merge(af, on='cod_ibge', how='left')


def por_municipio(e, mat_mun):
    preenchido = e.groupby('uf').CO_MUNICIPIO_ESC.apply(lambda s: s.notna().mean())  # share that names the school
    em = e.dropna(subset=['CO_MUNICIPIO_ESC']).copy()
    em['cod_ibge'] = em.CO_MUNICIPIO_ESC.astype(int)
    grupos = dict(tuple(em.groupby('cod_ibge')['nota']))
    m = pd.DataFrame({'participantes': em.groupby('cod_ibge').size(), 'media_simples': em.groupby('cod_ibge')['nota'].mean()})
    m['matriculas_3ano'] = mat_mun.reindex(m.index)
    m = m.reset_index().merge(ideb_municipal().drop(columns='uf'), on='cod_ibge', how='left')
    m['uf'] = (m.cod_ibge // 100000).map(UF)
    idhm = EXTREMOS.base()[['cod_ibge', 'idhm']]
    m = m.merge(idhm, on='cod_ibge', how='left')
    # the best students up to 25% of the 3rd-year enrollment, scaled by the share of takers in the state
    # who name their school (90% in Ceará, 43% to 73% elsewhere), so that states are comparable
    m['media_melhores_25'] = [media_topo(grupos[c], 0.25 * mt * preenchido[u]) if mt > 0 else np.nan
                              for c, mt, u in zip(m.cod_ibge, m.matriculas_3ano, m.uf)]
    # sample: at least 50 students in the 3rd year, takers naming the school at least a quarter of them,
    # Ideb of the municipal network in 2015 and IDHM available
    a = m[(m.matriculas_3ano >= 50) & (m.participantes >= (0.25 * m.matriculas_3ano).round())].dropna(
        subset=['ideb_ai_2015', 'idhm', 'media_melhores_25']).copy()
    a['ceara'] = np.where(a.uf == 'CE', 'Ceará', 'fora do Ceará')
    a['pct_ideb_2015'] = a.ideb_ai_2015.rank(pct=True)
    a['pct_enem'] = a.media_melhores_25.rank(pct=True)
    a['pct_saeb_af_2019'] = a.saeb_af_2019.rank(pct=True)
    a['quinto_ideb_2015'] = pd.qcut(a.pct_ideb_2015, 5, labels=[1, 2, 3, 4, 5]).astype(int)
    b = a.dropna(subset=['ideb_ai_2017']).copy()
    b['pct_ideb_2017'] = b.ideb_ai_2017.rank(pct=True)
    a['quinto_ideb_2017'] = pd.qcut(b.pct_ideb_2017, 5, labels=[1, 2, 3, 4, 5]).astype(float).reindex(a.index)
    return a, preenchido


def quintis(a):
    linhas = []
    for q_col in ('quinto_ideb_2015', 'quinto_ideb_2017'):
        for (q, ce), s in a.dropna(subset=[q_col]).groupby([q_col, 'ceara']):
            linhas.append({'ideb_de': q_col[-4:], 'quinto': int(q), 'grupo': ce, 'municipios': len(s),
                           'pct_mediano_enem_2023': s.pct_enem.median() * 100,
                           'pct_mediano_saeb_9ano_2019': s.pct_saeb_af_2019.median() * 100})
    return pd.DataFrame(linhas)


def topo(a):
    linhas = []
    for corte in (0.90, 0.95):
        for ce, s in a[a.pct_ideb_2015 >= corte].groupby('ceara'):
            linhas.append({'ideb_2015_no_topo': f'{int(round((1 - corte) * 100))}%', 'grupo': ce, 'municipios': len(s),
                           'pct_mediano_ideb_2015': s.pct_ideb_2015.median() * 100,
                           'pct_mediano_enem_2023': s.pct_enem.median() * 100,
                           'media_melhores_25_mediana': s.media_melhores_25.median()})
    return pd.DataFrame(linhas)


def figura(q, arq):
    q = q[(q.ideb_de == '2015') & (q.municipios >= 10)]
    cor = {'fora do Ceará': '#2a78d6', 'Ceará': '#e07b39'}
    rot = {'fora do Ceará': 'Fora do Ceará', 'Ceará': 'Ceará'}
    fig, axs = plt.subplots(1, 2, figsize=(6.3, 3.0), sharey=True)
    titulos = ['9º ano, Saeb 2019', 'Fim do ensino médio, Enem 2023']
    for ax, col, tit in zip(axs, ('pct_mediano_saeb_9ano_2019', 'pct_mediano_enem_2023'), titulos):
        for g in ('fora do Ceará', 'Ceará'):
            s = q[q.grupo == g].sort_values('quinto')
            ax.plot(s.quinto, s[col], color=cor[g], lw=1.6, marker='o', ms=5, markeredgecolor='white',
                    markeredgewidth=1.2, zorder=3)
            ult = s.iloc[-1]
            ax.annotate(f'{rot[g]}: {ult[col]:.0f}', (ult.quinto, ult[col]), xytext=(6, 0),
                        textcoords='offset points', va='center', fontsize=7, color='#0b0b0b')
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(['1º\n(menor)', '2º', '3º', '4º', '5º\n(maior)'], fontsize=7, color='#52514e')
        ax.set_xlim(0.7, 6.4)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.tick_params(labelsize=7, colors='#52514e', length=0)
        ax.grid(axis='y', color='#e6e5e0', lw=0.6)
        ax.set_axisbelow(True)
        for sp in ('top', 'right', 'left'):
            ax.spines[sp].set_visible(False)
        ax.spines['bottom'].set_color('#c9c8c2')
        ax.set_title(tit, fontsize=8, loc='left', color='#0b0b0b')
        ax.set_xlabel('Quinto do Ideb do 5º ano em 2015', fontsize=7.5, color='#52514e')
    axs[0].set_ylabel('Percentil mediano no Brasil', fontsize=7.5, color='#52514e')
    fig.tight_layout()
    fig.savefig(arq, bbox_inches='tight', metadata={'CreationDate': None})
    plt.close(fig)


if __name__ == '__main__':
    fonte()
    e = enem()
    mat_uf, mat_mun = matriculas_3ano()
    t = por_uf(e, mat_uf)
    t.to_csv(os.path.join(RES, '07_enem_uf.csv'), sep=';')
    a, preenchido = por_municipio(e, mat_mun)
    a.to_csv(os.path.join(RES, '07_enem_municipios.csv'), sep=';', index=False)
    q = quintis(a)
    q.to_csv(os.path.join(RES, '07_enem_quintis.csv'), sep=';', index=False)
    tp = topo(a)
    tp.to_csv(os.path.join(RES, '07_enem_topo.csv'), sep=';', index=False)
    figura(q, os.path.join(RES, '07_fig_enem.pdf'))
    print('takers', len(e), 'municipalities', len(a), 'Ceará', (a.uf == 'CE').sum())
    print('share naming the school:', preenchido.round(2).to_dict())
    print(t.round(3).to_string())
    print(q.round(1).to_string(index=False))
    print(tp.round(2).to_string(index=False))
