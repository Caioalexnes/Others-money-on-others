"""Ensino médio: cost of the state networks versus private tuition, and the Saeb at the end of ensino médio.

Ensino médio is run by the states, whose networks also have ensino fundamental schools. The state accounts do
not isolate it reliably: the subfunction Ensino Médio (362) is used very differently across states (several
book almost everything under 368, Educação Básica), so this script does not allocate spending by stage.
Cost, 2025, in 2025 reais:
  - spending of each state network: function 12 (Educação) minus subfunctions 363 (Ensino Profissional) and 364
    (Ensino Superior), committed expenditure in the state's DCA (Siconfi, Anexo I-E), divided by the
    basic-education enrollments (QT_MAT_BAS) of the state's schools in activity (Censo Escolar 2025);
  - private tuition: mean monthly tuition of ensino fundamental and ensino médio of the state (Melhor Escola,
    2025), weighted by the enrollments of each stage in the state network, times 12, net of taxes on revenue
    and profit (7.5% to 19.5%) as in scripts 04 and 11; the low end of the ratio also removes up to R$ 700 of
    school meals and transport from the public spending.
  - for transparency, spending per ensino médio student by subfunction 362 (plus a proportional share of
    administration), which shows why that subfunction is not used.
Performance: difference between private and public students of the same state at the end of ensino médio
(Saeb 2023, 3rd and 4th years), mathematics, with the student's INSE (the public side includes the federal
institutes).
Inputs: data/siconfi/dca_estados_2025.csv (downloaded by this script if missing), data/inep/microdados_censo_escolar_2025.zip,
        data/inep/microdados_saeb_2023.zip
Outputs: results/12_medio.csv, results/12_tabela_medio.tex, results/12_fig_medio.pdf
"""
import csv, json, os, time, urllib.parse, urllib.request, zipfile
from importlib import import_module
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import DADOS, RES

g04, g09, g11 = (import_module(m) for m in ('04_custo_escola', '09_publica_privada', '11_custo_desempenho_uf'))
UF, NOME = g11.UF, dict(g11.NOME, DF='Distrito Federal')
# Mean monthly tuition of ensino médio in 2025 (R$), Melhor Escola (same source as script 11)
MEDIO = {'AC': 1420.65, 'AL': 663.17, 'AM': 1025.00, 'AP': 1179.54, 'BA': 1221.07, 'CE': 1152.31, 'DF': 1668.55,
         'ES': 1356.19, 'GO': 1222.73, 'MA': 949.95, 'MG': 1775.93, 'MS': 1509.05, 'MT': 1352.58, 'PA': 895.16,
         'PB': 756.84, 'PE': 966.01, 'PI': 1140.20, 'PR': 1343.36, 'RJ': 1675.22, 'RN': 1112.58, 'RO': 836.33,
         'RR': 678.85, 'RS': 1328.51, 'SC': 1580.04, 'SE': 1095.07, 'SP': 1840.06, 'TO': 1475.75}
ROTULADOS = ('CE', 'MG', 'SP', 'RS', 'MA')
ABAIXO = ('RS',)   # labels below the bar, where the right side is crowded
ARQ_DCA = os.path.join(DADOS, 'siconfi', 'dca_estados_2025.csv')


def baixa_dca_estados(ano=2025):
    """Committed expenditure of function 12 of the 26 states and the Distrito Federal (Siconfi, DCA, Anexo I-E)."""
    base = 'https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca'
    linhas = []
    for uf in sorted(UF):
        q = urllib.parse.urlencode({'an_exercicio': ano, 'no_anexo': 'DCA-Anexo I-E', 'id_ente': uf})
        off = 0
        while True:
            for k in range(6):
                try:
                    with urllib.request.urlopen(f'{base}?{q}&offset={off}', timeout=60) as r:
                        d = json.load(r)
                    break
                except Exception:
                    time.sleep(2 ** k)
            linhas += [[uf, i['conta'], i['valor']] for i in d['items']
                       if i['coluna'] == 'Despesas Empenhadas' and (i['conta'].startswith('12 ') or i['conta'].startswith('12.'))]
            if not d.get('hasMore'):
                break
            off += d['limit']
    with open(ARQ_DCA, 'w', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['cod_uf', 'conta', 'valor'])
        w.writerows(sorted(linhas, key=lambda x: (x[0], x[1])))


def matriculas_estaduais():
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_censo_escolar_2025.zip'))
    nm = [n for n in z.namelist() if n.split('/')[-1].upper().startswith('TABELA_MATRICULA_2025')][0]
    ne = [n for n in z.namelist() if n.split('/')[-1].upper().startswith('TABELA_ESCOLA_2025')][0]
    m = pd.read_csv(z.open(nm), sep=';', encoding='latin1',
                    usecols=['CO_UF', 'CO_ENTIDADE', 'TP_DEPENDENCIA', 'QT_MAT_BAS', 'QT_MAT_FUND', 'QT_MAT_MED'])
    e = pd.read_csv(z.open(ne), sep=';', encoding='latin1', usecols=['CO_ENTIDADE', 'TP_SITUACAO_FUNCIONAMENTO'])
    m = m.merge(e, on='CO_ENTIDADE')
    m = m[(m['TP_SITUACAO_FUNCIONAMENTO'] == 1) & (m['TP_DEPENDENCIA'] == 2)]
    return m.groupby('CO_UF')[['QT_MAT_BAS', 'QT_MAT_FUND', 'QT_MAT_MED']].sum()


def custo():
    if not os.path.exists(ARQ_DCA):
        baixa_dca_estados()
    d = pd.read_csv(ARQ_DCA, sep=';')
    d['sub'] = d['conta'].str.extract(r'^12\.(\d{3})')[0]
    p = d.dropna(subset=['sub']).pivot_table(index='cod_uf', columns='sub', values='valor', aggfunc='sum').fillna(0)
    p['f12'] = d[d['conta'].str.startswith('12 - ')].set_index('cod_uf')['valor']
    m = matriculas_estaduais()
    t = pd.DataFrame(index=p.index)
    t['gasto'] = p['f12'] - p['363'] - p['364']
    t['matriculas'] = m['QT_MAT_BAS']
    t['por_aluno'] = t['gasto'] / t['matriculas']
    t['parcela_medio'] = m['QT_MAT_MED'] / (m['QT_MAT_MED'] + m['QT_MAT_FUND'])
    t['medio_pela_362'] = p['362'] * (1 + p['122'] / (t['gasto'] - p['122'])) / m['QT_MAT_MED']
    t.index = t.index.map(UF)
    t['particular'] = [12 * (s * MEDIO[u] + (1 - s) * g11.MENSALIDADE[u][1]) for u, s in t['parcela_medio'].items()]
    cmin = g04.simples(1.26e6) * (1 - g04.CPP_ANEXO_III)
    cmax = g04.presumido(0.05, True, 0, 0)
    t['particular_liq_min'], t['particular_liq_max'] = t['particular'] * (1 - cmax), t['particular'] * (1 - cmin)
    t['razao_min'] = (t['por_aluno'] - g04.MERENDA_TRANSPORTE_MAX) / t['particular_liq_max']
    t['razao_max'] = t['por_aluno'] / t['particular_liq_min']
    return t


def desempenho():
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_saeb_2023.zip'))
    d = g09.ler(z, 'TS_ALUNO_34EM')
    d['privada'] = 1.0 - d['IN_PUBLICA']
    y, w = 'PROFICIENCIA_MT_SAEB', 'PESO_ALUNO_MT'
    a = d[(d['IN_PROFICIENCIA_MT'] == 1) & (d[w] > 0)].dropna(subset=[y, w, 'INSE_ALUNO'])
    out = {}
    for cod, b in a.groupby('ID_UF'):
        c, s = g09.mqp(b[y].values.astype(float), [b['privada'].values, b['INSE_ALUNO'].values.astype(float)],
                       b[w].values.astype(float), b['ID_ESCOLA'].values)
        out[UF[int(cod)]] = {'saeb_medio': c[1], 'ep_medio': s[1], 'escolas_privadas_medio': b.loc[b['privada'] == 1, 'ID_ESCOLA'].nunique()}
    return pd.DataFrame(out).T


def tabela_tex(t):
    n = lambda v, k=1: f'{v:.{k}f}'.replace('.', ',')
    linhas = []
    for u, r in sorted(t.iterrows(), key=lambda x: g11.ordem(x[1]['nome'])):
        linhas.append(f"{r['nome']} & {n(r['por_aluno'] / 1000)} & {n(100 * r['parcela_medio'], 0)}\\% & "
                      f"{n(r['particular_liq_min'] / 1000)} a {n(r['particular_liq_max'] / 1000)} & "
                      f"{n(r['razao_min'])} a {n(r['razao_max'])} & {n(r['saeb_medio'], 0)} \\\\")
    m = t.mean(numeric_only=True)
    linhas.append('\\midrule')
    linhas.append(f"\\textbf{{Média dos estados}} & \\textbf{{{n(m['por_aluno'] / 1000)}}} & & \\textbf{{{n(m['particular_liq_min'] / 1000)} a "
                  f"{n(m['particular_liq_max'] / 1000)}}} & \\textbf{{{n(m['razao_min'])} a {n(m['razao_max'])}}} & "
                  f"\\textbf{{{n(m['saeb_medio'], 0)}}} \\\\")
    open(os.path.join(RES, '12_tabela_medio.tex'), 'w', encoding='utf-8').write('\n'.join(linhas) + '\n')


def figura(t):
    import_module('06_extremos').fonte()
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    ax.fill_between([0.5, 3.2], 0, 65, color='#f3efe6', zorder=0, lw=0)
    ax.fill_between([1, 3.2], 0, 65, color='#ebe5d6', zorder=0, lw=0)
    ax.axhline(0, color='#999999', lw=0.6)
    ax.axvline(1, color='#999999', lw=0.6)
    for u, r in t.iterrows():
        cor = '#E07B39' if u == 'CE' else '#2A78D6'
        meio = (r['razao_min'] + r['razao_max']) / 2
        ax.plot([r['razao_min'], r['razao_max']], [r['saeb_medio']] * 2, color=cor, lw=1.2, alpha=0.6, zorder=2)
        ax.plot(meio, r['saeb_medio'], 'o', color=cor, ms=3.4, zorder=3)
        if u in ROTULADOS:
            baixo = u in ABAIXO
            ax.text(r['razao_min'] if baixo else r['razao_max'] + 0.04, r['saeb_medio'] - (2.6 if baixo else 0), r['nome'],
                    fontsize=5.8, va='center', color='#E07B39' if u == 'CE' else '#33322f')
    ax.set_xlim(0.5, 3.2)
    ax.set_ylim(-8, 65)
    ax.set_xlabel('Gasto da rede estadual ÷ mensalidade sem impostos', fontsize=7, color='#52514E')
    ax.set_ylabel('Pontos que a particular fica à frente no Saeb\n(fim do ensino médio, alunos de mesmo nível socioeconômico)',
                  fontsize=6.6, color='#52514E')
    ax.tick_params(labelsize=7, colors='#52514E', length=0)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#bbbbbb')
    ax.text(3.15, 63, 'particular mais barata\ne com nota maior', ha='right', va='top', fontsize=6, color='#8a8578')
    ax.text(0.53, 16, 'pública mais barata,\nparticular com\nnota maior', ha='left', va='top', fontsize=6, color='#8a8578')
    ax.text(0.97, 2, 'mesmo custo', fontsize=5.6, color='#8a8578', rotation=90, va='bottom', ha='right')
    ax.text(3.15, 0.8, 'mesma nota', fontsize=5.6, color='#8a8578', ha='right', va='bottom')
    fig.tight_layout()
    fig.savefig(os.path.join(RES, '12_fig_medio.pdf'), bbox_inches='tight', metadata={'CreationDate': None})


if __name__ == '__main__':
    t = custo().join(desempenho())
    t['nome'] = t.index.map(NOME)
    t.to_csv(os.path.join(RES, '12_medio.csv'), sep=';', float_format='%.4f')
    tabela_tex(t)
    figura(t)
    pd.set_option('display.width', 200)
    print(t[['por_aluno', 'parcela_medio', 'medio_pela_362', 'razao_min', 'razao_max', 'saeb_medio', 'ep_medio']].round(2).to_string())
    m = t.mean(numeric_only=True)
    print(f"mean of states: ratio {m['razao_min']:.2f} to {m['razao_max']:.2f}; Saeb end of ensino médio {m['saeb_medio']:.1f}"
          f" (min {t['saeb_medio'].min():.1f}, max {t['saeb_medio'].max():.1f}); ratio range entirely above 1 in"
          f" {(t['razao_min'] > 1).sum()} of {len(t)}; entirely below 1 in {(t['razao_max'] < 1).sum()}")
