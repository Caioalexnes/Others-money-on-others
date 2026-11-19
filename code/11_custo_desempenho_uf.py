"""Cost and performance of municipal networks and private schools, state by state; and whether Ceará's
advantage is regional (both sectors) or confined to the public network.

Cost, 2025, in 2025 reais:
  - spending per student of the municipal networks of each state (script 03, enrollment-weighted mean);
  - mean monthly private tuition of the state (Melhor Escola, 2025), times 12, weighted by the share of
    early-childhood (creche and pré-escola) enrollments in the state's municipal networks (Censo Escolar 2025);
  - taxes on revenue and profit removed from the tuition, from 7.5% (Simples Nacional, Anexo III, without the
    employer social security contribution) to 19.5% (lucro presumido), as in script 04;
  - ratio of public spending to the tuition net of taxes; the low end also removes up to R$ 700 of school
    meals and transport from the public spending, as in script 04.
Performance, Saeb 2023 (student microdata, sampling weights, standard errors clustered by school):
  - difference between private and public students of the same state in mathematics, 5th and 9th grades,
    controlling for the student's INSE (the public side includes state and federal schools).
Ceará: the Ceará coefficient, with the student's INSE (and also the school's mean INSE), estimated
separately for public and for private students, against the rest of Brazil and the rest of the Northeast;
and the share of literate 2nd-grade students (Saeb 2023 sample) by sector in Ceará and in the rest of the
Northeast. If Ceará's advantage came from a regional culture, its private schools would also stand out.
Also: spending per student in months of the state's mean monthly earnings (PNAD Contínua, IBGE table 5436).
Inputs: results/03_base_municipios.csv, data/inep/microdados_censo_escolar_2025.zip,
        data/inep/microdados_saeb_2023.zip, data/pnad_5436.json, data/ipca_1737.json
Outputs: results/11_estados.csv, results/11_ceara.csv, results/11_tabela_estados.tex,
         results/11_fig_custo_desempenho.pdf
"""
import json, os, unicodedata, zipfile
from importlib import import_module
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import DADOS, RES

g03, g04, g09, g10 = (import_module(m) for m in ('03_gasto_ideb', '04_custo_escola', '09_publica_privada', '10_alfabetizacao'))
UF = {11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN',
      25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC',
      43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'}
NOME = {'AC': 'Acre', 'AL': 'Alagoas', 'AM': 'Amazonas', 'AP': 'Amapá', 'BA': 'Bahia', 'CE': 'Ceará', 'ES': 'Espírito Santo',
        'GO': 'Goiás', 'MA': 'Maranhão', 'MG': 'Minas Gerais', 'MS': 'Mato Grosso do Sul', 'MT': 'Mato Grosso', 'PA': 'Pará',
        'PB': 'Paraíba', 'PE': 'Pernambuco', 'PI': 'Piauí', 'PR': 'Paraná', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RO': 'Rondônia', 'RR': 'Roraima', 'RS': 'Rio Grande do Sul', 'SC': 'Santa Catarina', 'SE': 'Sergipe',
        'SP': 'São Paulo', 'TO': 'Tocantins'}
NORDESTE = [21, 22, 23, 24, 25, 26, 27, 28, 29]
ROTULADOS = ('CE', 'SP', 'RS', 'PB')
# in the crowded part of the 9th-grade panel, labels go to an empty area with a thin line to the point
CHAMADAS = {('saeb_9', 'RS'): (1.06, 27.5), ('saeb_9', 'SP'): (1.06, 24.0)}
# Mean monthly tuition in 2025 (R$): educação infantil, ensino fundamental. Melhor Escola, "Descubra o valor médio da
# mensalidade de escolas particulares no Brasil", updated 30 Apr. 2025 (more than 7 thousand partner schools).
MENSALIDADE = {'AC': (973.60, 842.40), 'AL': (524.73, 714.76), 'AM': (822.75, 680.11), 'AP': (773.75, 866.82),
               'BA': (595.40, 650.93), 'CE': (673.79, 558.22), 'DF': (1319.24, 1008.89), 'ES': (995.24, 954.58),
               'GO': (992.84, 604.95), 'MA': (845.90, 484.51), 'MG': (935.00, 956.78), 'MS': (792.10, 729.15),
               'MT': (1073.09, 763.97), 'PA': (677.63, 448.99), 'PB': (570.89, 402.04), 'PE': (545.82, 558.88),
               'PI': (740.48, 605.73), 'PR': (1099.74, 812.81), 'RJ': (1049.71, 724.95), 'RN': (512.96, 527.58),
               'RO': (747.40, 622.25), 'RR': (741.67, 678.85), 'RS': (1159.74, 1096.60), 'SC': (1172.53, 963.21),
               'SE': (653.52, 678.33), 'SP': (1183.56, 1010.93), 'TO': (676.70, 872.75)}


def custo():
    ip = g03.ipca_medio()
    f = ip[2025] / ip[2023]
    b = pd.read_csv(os.path.join(RES, '03_base_municipios.csv'), sep=';')
    b['uf'] = (b['cod_ibge'] // 100000).map(UF)
    out = {}
    for a in (2023, 2025):
        d = b[b['ano'] == a]
        out[a] = d.groupby('uf').apply(lambda g: (g['gasto'] * ip[2023] / ip[a]).sum() / g['matriculas'].sum() * f)
        out[f'br{a}'] = (d['gasto'] * ip[2023] / ip[a]).sum() / d['matriculas'].sum() * f
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_censo_escolar_2025.zip'))
    nome = [n for n in z.namelist() if n.split('/')[-1].upper().startswith('TABELA_MATRICULA_2025')][0]
    m = pd.read_csv(z.open(nome), sep=';', encoding='latin1', usecols=['CO_UF', 'TP_DEPENDENCIA', 'QT_MAT_INF', 'QT_MAT_FUND'])
    m = m[m['TP_DEPENDENCIA'] == 3].groupby('CO_UF')[['QT_MAT_INF', 'QT_MAT_FUND']].sum()
    m.index = m.index.map(UF)
    t = pd.DataFrame({'publica': out[2025], 'publica_2023': out[2023]})
    t['parcela_infantil'] = m['QT_MAT_INF'] / (m['QT_MAT_INF'] + m['QT_MAT_FUND'])
    t['particular'] = [12 * (s * MENSALIDADE[u][0] + (1 - s) * MENSALIDADE[u][1]) for u, s in t['parcela_infantil'].items()]
    cmin = g04.simples(1.26e6) * (1 - g04.CPP_ANEXO_III)
    cmax = g04.presumido(0.05, True, 0, 0)
    t['particular_liq_min'], t['particular_liq_max'] = t['particular'] * (1 - cmax), t['particular'] * (1 - cmin)
    t['razao_min'] = (t['publica'] - g04.MERENDA_TRANSPORTE_MAX) / t['particular_liq_max']
    t['razao_max'] = t['publica'] / t['particular_liq_min']
    # mean monthly earnings, PNAD Contínua (IBGE table 5436, variable 5933), mean of the four quarters. The table gives
    # real values at the mean prices of its last quarter (3rd quarter of 2026 when downloaded, 19 Nov. 2026); spending
    # in 2025 reais is brought to those prices with the IPCA (table 1737, July to September 2026 over the 2025 mean)
    v = {i['D3C']: float(i['V']) for i in json.load(open(os.path.join(DADOS, 'ipca_1737_2026.json'), encoding='utf-8'))[1:]}
    para_ref = (sum(v[f'2026{k:02d}'] for k in (7, 8, 9)) / 3) / (sum(v[f'2025{k:02d}'] for k in range(1, 13)) / 12)
    r = json.load(open(os.path.join(DADOS, 'pnad_5436.json'), encoding='utf-8'))[1:]
    e = pd.DataFrame({'cod': [int(i['D1C']) for i in r], 'ano': [int(i['D3C'][:4]) for i in r],
                      'v': [float(i['V']) for i in r]}).groupby(['cod', 'ano'])['v'].mean().unstack()
    for a in (2023, 2025):
        t[f'meses_renda_{a}'] = t['publica' if a == 2025 else 'publica_2023'] * para_ref / e[a].rename(index=UF).reindex(t.index)
        t.loc['BR', f'meses_renda_{a}'] = out[f'br{a}'] * para_ref / e.loc[1, a]
    return t, cmin, cmax


def wls(b, y, w, X):
    return g09.mqp(b[y].values.astype(float), [np.asarray(x, float) for x in X], b[w].values.astype(float), b['ID_ESCOLA'].values)


def desempenho(z):
    gaps, ce = {}, []
    for etapa, nome in (('5', 'TS_ALUNO_5EF'), ('9', 'TS_ALUNO_9EF')):
        d = g09.ler(z, nome)
        d['privada'] = 1.0 - d['IN_PUBLICA']
        di = d.dropna(subset=['INSE_ALUNO', 'PESO_ALUNO_INSE'])
        d['inse_escola'] = d['ID_ESCOLA'].map((di['INSE_ALUNO'] * di['PESO_ALUNO_INSE']).groupby(di['ID_ESCOLA']).sum()
                                              / di['PESO_ALUNO_INSE'].groupby(di['ID_ESCOLA']).sum())
        y, w = 'PROFICIENCIA_MT_SAEB', 'PESO_ALUNO_MT'
        a = d[(d['IN_PROFICIENCIA_MT'] == 1) & (d[w] > 0)].dropna(subset=[y, w, 'INSE_ALUNO', 'inse_escola'])
        for cod, b in a.groupby('ID_UF'):
            c, s = wls(b, y, w, [b['privada'], b['INSE_ALUNO']])
            gaps.setdefault(UF[int(cod)], {}).update({f'saeb_{etapa}': c[1], f'ep_{etapa}': s[1],
                                                      f'escolas_privadas_{etapa}': b.loc[b['privada'] == 1, 'ID_ESCOLA'].nunique()})
        for setor in (0, 1):
            for ref, sel in (('resto do Brasil', a['privada'] == setor),
                             ('resto do Nordeste', (a['privada'] == setor) & a['ID_UF'].isin(NORDESTE))):
                b = a[sel]
                dce = (b['ID_UF'] == 23).astype(float)
                c1, s1 = wls(b, y, w, [dce, b['INSE_ALUNO']])
                c2, s2 = wls(b, y, w, [dce, b['INSE_ALUNO'], b['inse_escola']])
                ce.append(dict(etapa=f'{etapa}º ano', setor='privada' if setor else 'publica', comparacao=ref,
                               ceara_inse_aluno=c1[1], ep1=s1[1], ceara_inse_aluno_e_escola=c2[1], ep2=s2[1]))
    # 2nd grade, literacy (Saeb 2023 sample)
    d = pd.read_csv(z.open('MICRODADOS_SAEB_2023/DADOS/TS_ALUNO_2EF.csv'), sep=';', encoding='latin1', low_memory=False,
                    usecols=['ID_UF', 'ID_ESCOLA', 'IN_PUBLICA', 'IN_PROFICIENCIA_LP', 'PESO_ALUNO_LP', 'IN_ALFABETIZADO'])
    for c in d.columns:
        if d[c].dtype == object:
            d[c] = pd.to_numeric(d[c].astype(str).str.replace(',', '.'), errors='coerce')
    a = d[d['IN_PROFICIENCIA_LP'] == 1].dropna(subset=['PESO_ALUNO_LP', 'IN_ALFABETIZADO'])
    for pub, setor in ((1, 'publica'), (0, 'privada')):
        for ref, sel in (('Ceará', a['ID_UF'] == 23), ('resto do Nordeste', a['ID_UF'].isin(NORDESTE) & (a['ID_UF'] != 23))):
            g = a[sel & (a['IN_PUBLICA'] == pub)]
            p = g10.proporcao(g)
            ce.append(dict(etapa='2º ano', setor=setor, comparacao=ref, alfabetizados_pct=p['alfabetizados_pct'],
                           ep_pct=p['ep_pct'], escolas=p['escolas']))
    return pd.DataFrame(gaps).T, pd.DataFrame(ce)


def ordem(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()


def tabela_tex(t):
    n = lambda v, k=1: f'{v:.{k}f}'.replace('.', ',')
    linhas = []
    for u, r in sorted(t.iterrows(), key=lambda x: ordem(x[1]['nome'])):
        linhas.append(f"{r['nome']} & {n(r['publica'] / 1000)} & {n(r['particular_liq_min'] / 1000)} a {n(r['particular_liq_max'] / 1000)}"
                      f" & {n(r['razao_min'])} a {n(r['razao_max'])} & {n(r['saeb_5'], 0)} & {n(r['saeb_9'], 0)} \\\\")
    m = t.mean(numeric_only=True)
    linhas.append('\\midrule')
    linhas.append(f"\\textbf{{Média dos estados}} & \\textbf{{{n(m['publica'] / 1000)}}} & \\textbf{{{n(m['particular_liq_min'] / 1000)} a "
                  f"{n(m['particular_liq_max'] / 1000)}}} & \\textbf{{{n(m['razao_min'])} a {n(m['razao_max'])}}} & "
                  f"\\textbf{{{n(m['saeb_5'], 0)}}} & \\textbf{{{n(m['saeb_9'], 0)}}} \\\\")
    open(os.path.join(RES, '11_tabela_estados.tex'), 'w', encoding='utf-8').write('\n'.join(linhas) + '\n')


def figura(t):
    g06 = import_module('06_extremos')
    g06.fonte()
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.5), sharey=True)
    for ax, (col, titulo) in zip(axes, (('saeb_5', '5º ano'), ('saeb_9', '9º ano'))):
        ax.fill_between([1, 3.6], 0, 52, color='#f3efe6', zorder=0, lw=0)
        ax.axhline(0, color='#999999', lw=0.6)
        ax.axvline(1, color='#999999', lw=0.6)
        for u, r in t.iterrows():
            cor = '#E07B39' if u == 'CE' else '#2A78D6'
            meio = (r['razao_min'] + r['razao_max']) / 2
            ax.plot([r['razao_min'], r['razao_max']], [r[col], r[col]], color=cor, lw=1.2, alpha=0.6, zorder=2)
            ax.plot(meio, r[col], 'o', color=cor, ms=3.4, zorder=3)
            if u in ROTULADOS:   # only the states named in the text, to keep the labels legible
                if (col, u) in CHAMADAS:
                    ax.annotate(NOME[u], (meio, r[col]), xytext=CHAMADAS[(col, u)], fontsize=5.8, va='center',
                                color='#33322f', arrowprops=dict(arrowstyle='-', color='#8a8578', lw=0.5))
                else:
                    ax.text(r['razao_max'] + 0.04, r[col], NOME[u], fontsize=5.8, va='center',
                            color='#E07B39' if u == 'CE' else '#33322f')
        ax.set_xlim(0.8, 3.6)
        ax.set_ylim(-8, 52)
        ax.set_title(titulo, fontsize=8.5, color='#52514E')
        ax.set_xlabel('Gasto da rede municipal ÷ mensalidade sem impostos', fontsize=7, color='#52514E')
        ax.tick_params(labelsize=7, colors='#52514E', length=0)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        for s in ('left', 'bottom'):
            ax.spines[s].set_color('#bbbbbb')
        ax.text(3.55, 50.5, 'particular mais barata\ne com nota maior', ha='right', va='top', fontsize=6, color='#8a8578')
        ax.text(0.97, 51, 'mesmo custo', fontsize=5.6, color='#8a8578', rotation=90, va='top', ha='right')
        ax.text(3.55, 0.8, 'mesma nota', fontsize=5.6, color='#8a8578', ha='right', va='bottom')
    axes[0].set_ylabel('Pontos que a particular fica à frente no Saeb\n(alunos de mesmo nível socioeconômico)', fontsize=7, color='#52514E')
    fig.tight_layout(w_pad=1.2)
    fig.savefig(os.path.join(RES, '11_fig_custo_desempenho.pdf'), bbox_inches='tight', metadata={'CreationDate': None})


if __name__ == '__main__':
    t, cmin, cmax = custo()
    print(f'taxes on tuition: {cmin:.1%} to {cmax:.1%}')
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_saeb_2023.zip'))
    gaps, ce = desempenho(z)
    br = t.loc[['BR'], ['meses_renda_2023', 'meses_renda_2025']]
    t = t.drop(index='BR').join(gaps, how='left')
    t['nome'] = t.index.map(NOME)
    t.to_csv(os.path.join(RES, '11_estados.csv'), sep=';', float_format='%.4f')
    ce.to_csv(os.path.join(RES, '11_ceara.csv'), sep=';', index=False, float_format='%.4f')
    tabela_tex(t)
    figura(t)
    pd.set_option('display.width', 200)
    print(t[['publica', 'particular_liq_min', 'particular_liq_max', 'razao_min', 'razao_max', 'saeb_5', 'saeb_9']].round(2).to_string())
    m = t.mean(numeric_only=True)
    print(f"mean of states: ratio {m['razao_min']:.2f} to {m['razao_max']:.2f}; Saeb 5th {m['saeb_5']:.1f}, 9th {m['saeb_9']:.1f}")
    print('months of mean earnings per student:', t.loc[['CE', 'SP', 'PR', 'SC', 'RS'], ['meses_renda_2023', 'meses_renda_2025']].round(2).to_dict(),
          'Brazil', br.round(2).to_dict('records'))
    print(ce.round(1).to_string(index=False))
