"""2025 update: why the spending coefficient of 2025 rises, and whether it measures an effect of money.

Reproduces the numbers of the essay's paragraphs and footnotes on 2025:
  - the 2023 regression with the 2019 INSE (a lagged proxy, as the 2023 INSE is used for 2025);
  - the coefficient on each component of the Ideb (Saeb score and approval);
  - change of spending per student and of the Ideb from 2023 to 2025 by fifth of the 2023 INSE;
  - "placebo" regressions: the Ideb of the earlier year on the spending of both years. If money
    raised the Ideb, the later spending would not explain the earlier Ideb, once the earlier spending
    is held fixed; if it does, money is going to networks that were already doing well;
  - the 2025 coefficient without the networks with implausible Saeb scores (Ceará, Alagoas and the
    networks with a 5th-grade mathematics mean above 300 in any year) and by median regression;
  - the part of the Fundeb paid by results (complementação VAAR) in 2025, from the annual adjustment
    published in Portaria Interministerial MEC/MF nº 5/2026 (Anexo III), and the coefficient with
    spending net of it;
  - municipal networks with a 5th-grade mathematics mean above 300 and 320, by state, and the national
    mean of private schools (Ideb release for Brazil);
  - enrollment-weighted spending per student and Ideb of the municipal networks, 2017 and 2025.
Spending in 2023 reais (IPCA annual means), as in script 03. Requires pdftotext (poppler) for the
Portaria.
Inputs: results/03_base_municipios.csv, data/inep/divulgacao_*_2025/*.xlsx,
        data/fnde/portaria_interministerial_5_2026.pdf
Outputs: results/08_resultados.csv (one number per row, with its description), results/08_vaar_2025.csv,
         results/08_notas_altas.csv
"""
import os, re, subprocess
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import linprog
from config import DADOS, RES
from importlib import import_module

g03 = import_module('03_gasto_ideb')
mqo, ipca_medio, inse = g03.mqo, g03.ipca_medio, g03.inse
UF = {11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN',
      25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC',
      43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'}
saida = []


def anota(chave, valor, descricao):
    saida.append(dict(chave=chave, valor=valor, descricao=descricao))
    print(f'{chave:38s} {valor:12.4f}  {descricao}', flush=True)


def mediana(y, X):
    """Median (least absolute deviations) regression with an intercept, by linear programming."""
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in X]); y = np.asarray(y, float)
    n, k = X.shape
    c = np.r_[np.zeros(2 * k), 0.5 * np.ones(2 * n)]
    A = sparse.hstack([sparse.csr_matrix(X), sparse.csr_matrix(-X), sparse.eye(n), -sparse.eye(n)])
    z = linprog(c, A_eq=A, b_eq=y, bounds=(0, None), method='highs').x
    return z[:k] - z[k:2 * k]


def divulgacao(etapa):
    f = os.path.join(DADOS, 'inep', f'divulgacao_anos_{etapa}_municipios_2025', f'divulgacao_anos_{etapa}_municipios_2025.xlsx')
    x = pd.read_excel(f, header=9)
    x = x[x['REDE'] == 'Municipal'].copy()
    x['cod_ibge'] = pd.to_numeric(x['CO_MUNICIPIO'], errors='coerce')
    return x.set_index('cod_ibge')


def vaar_2025():
    """Complementação da União-VAAR of 2025 by municipality (Anexo III of the Portaria, column B:
    amount made available during 2025)."""
    pdf = os.path.join(DADOS, 'fnde', 'portaria_interministerial_5_2026.pdf')
    txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True, check=True).stdout
    txt = txt[txt.index('ANEXO III\n'):txt.index('ANEXO IV\n')]
    num = lambda s: float(s.replace(' ', '').replace('.', '').replace(',', '.')) if s.strip() not in ('-', '') else 0.0
    linhas = []
    for l in txt.split('\n'):
        m = re.match(r'\s*\.\s*\.([A-Z]{2})\s+\.(.+?)\s+\.(\d{7}|\d{2})\s+\.([\d\.,\- ]+?)\s+\.([\d\.,\- ]+?)\s+\.([\d\.,\- ]+?)\s*$', l)
        if m:
            linhas.append(dict(uf=m.group(1), ente=m.group(2).strip(), cod_ibge=int(m.group(3)),
                               vaar_devida=num(m.group(4)), vaar_disponibilizada=num(m.group(5)), ajuste=num(m.group(6))))
    v = pd.DataFrame(linhas)
    total = re.search(r'\.TOTAL\s+\.([\d\.,]+)', txt).group(1)
    assert abs(v['vaar_devida'].sum() - num(total)) < 1, 'parsed rows do not add up to the total of Anexo III'
    return v


if __name__ == '__main__':
    ip = ipca_medio()
    b = pd.read_csv(os.path.join(RES, '03_base_municipios.csv'), sep=';')
    b['g'] = b['gasto_aluno'] / 1000
    b['uf'] = (b['cod_ibge'] // 100000).map(UF)
    p = {c: b.pivot_table(index='cod_ibge', columns='ano', values=c) for c in ('g', 'ideb_ai', 'ideb_af', 'inse')}
    ai = divulgacao('iniciais')

    # 1. lagged INSE: 2023 with the 2019 edition
    i19 = inse(2019)
    for a in (2023, 2025):
        d = b[b['ano'] == a].assign(i=lambda x: x['cod_ibge'].map(i19)).dropna(subset=['ideb_ai', 'g', 'i'])
        c, s, _ = mqo(d['ideb_ai'], [d['g'], d['i']])
        anota(f'inse2019_{a}', c[1], f'Ideb 5th grade {a} on spending and the 2019 INSE (lagged proxy)')

    # 1b. which part of the Ideb carries the 2025 coefficient: Saeb score (N) or approval (P)
    for a in (2023, 2025):
        d = b[b['ano'] == a].set_index('cod_ibge')
        for col, nome in (('VL_NOTA_MEDIA', 'score'), ('VL_INDICADOR_REND', 'approval')):
            x = d.assign(y=pd.to_numeric(ai[f'{col}_{a}'], errors='coerce').reindex(d.index)).dropna(subset=['y', 'g', 'inse'])
            c, _, _ = mqo(x['y'], [x['g'], x['inse']])
            anota(f'componente_{nome}_{a}', c[1], f'5th grade {a}: Ideb {nome} component ({col}) on spending and INSE')

    # 2. change 2023-2025 by fifth of the 2023 INSE
    q = pd.DataFrame({'dg': p['g'][2025] - p['g'][2023], 'di': p['ideb_ai'][2025] - p['ideb_ai'][2023],
                      'inse': p['inse'][2023]}).dropna()
    q['quinto'] = pd.qcut(q['inse'], 5, labels=False) + 1
    for k, r in q.groupby('quinto')[['dg', 'di']].mean().iterrows():
        anota(f'var_gasto_2023_2025_q{k}', r['dg'], f'change of spending per student 2023-2025 (R$ thousand), fifth {k} of the 2023 INSE (1 = poorest)')
        anota(f'var_ideb_2023_2025_q{k}', r['di'], f'change of the 5th-grade Ideb 2023-2025, fifth {k} of the 2023 INSE')

    # 3. placebo: earlier Ideb on spending of both years, trimmed 1% tails of the change of spending
    ins = {2017: 2019, 2019: 2019, 2023: 2023}
    for y, et in (('ideb_ai', '5th'), ('ideb_af', '9th')):
        for a0, a1 in ((2017, 2019), (2019, 2023), (2023, 2025)):
            z = pd.DataFrame({'y0': p[y][a0], 'y1': p[y][a1], 'g0': p['g'][a0], 'g1': p['g'][a1],
                              'inse': p['inse'][ins[a0]]}).dropna()
            lo, hi = (z['g1'] - z['g0']).quantile([0.01, 0.99])
            z = z[(z['g1'] - z['g0']).between(lo, hi)]
            c0, _, _ = mqo(z['y0'], [z['g0'], z['g1'], z['inse']])
            c1, _, _ = mqo(z['y1'], [z['g0'], z['g1'], z['inse']])
            anota(f'placebo_{y}_{a0}_{a1}_antes', c0[2], f'{et}-grade Ideb {a0} on spending {a1}, holding spending {a0} and the INSE fixed (n={len(z)})')
            anota(f'placebo_{y}_{a0}_{a1}_depois', c1[2], f'{et}-grade Ideb {a1} on spending {a1}, holding spending {a0} and the INSE fixed')

    # 4. 2025 without implausible scores, and median regression
    mt = {a: pd.to_numeric(ai[f'VL_NOTA_MATEMATICA_{a}'], errors='coerce') for a in (2019, 2023, 2025)}
    susp = ((mt[2019] > 300) | (mt[2023] > 300) | (mt[2025] > 300))
    anota('redes_mat_acima_300_algum_ano', float(susp.sum()), 'municipal networks with a 5th-grade math mean above 300 in 2019, 2023 or 2025')
    for a in (2023, 2025):
        d = b[b['ano'] == a].dropna(subset=['ideb_ai', 'g', 'inse'])
        c, _, _ = mqo(d['ideb_ai'], [d['g'], d['inse']])
        anota(f'base_{a}', c[1], f'Ideb 5th grade {a} on spending and INSE, all municipalities (n={len(d)})')
        k = d[~d['cod_ibge'].map(susp).fillna(False).astype(bool)]
        c, _, _ = mqo(k['ideb_ai'], [k['g'], k['inse']])
        anota(f'sem_mat300_{a}', c[1], f'same, without networks with math above 300 in any year (n={len(k)})')
        k = k[~k['uf'].isin(['CE', 'AL'])]
        c, _, _ = mqo(k['ideb_ai'], [k['g'], k['inse']])
        anota(f'sem_mat300_ce_al_{a}', c[1], f'same, also without Ceará and Alagoas (n={len(k)})')
        anota(f'mediana_{a}', mediana(d['ideb_ai'], [d['g'], d['inse']])[1], f'median regression, all municipalities')

    # 5. VAAR
    v = vaar_2025()
    v.to_csv(os.path.join(RES, '08_vaar_2025.csv'), sep=';', index=False)
    vm = v[v['cod_ibge'] > 99999].set_index('cod_ibge')
    anota('vaar_2025_total_bi', v['vaar_devida'].sum() / 1e9, 'complementação VAAR 2025 due to states and municipalities (R$ billion, nominal)')
    anota('vaar_2025_municipios', float(len(vm)), 'municipalities receiving VAAR in 2025')
    d = b[b['ano'] == 2025].set_index('cod_ibge').copy()
    d['vaar'] = vm['vaar_disponibilizada'].reindex(d.index).fillna(0) / d['matriculas'] * ip[2023] / ip[2025] / 1000
    r = d[d['vaar'] > 0]
    anota('vaar_por_aluno_media', r['vaar'].mean() * 1000, 'VAAR per student among receiving networks in the base, mean (2023 reais)')
    anota('vaar_parcela_gasto', (r['vaar'] / r['g']).mean(), 'VAAR as a share of spending per student, mean among receiving networks')
    x = d.dropna(subset=['ideb_ai', 'g', 'inse'])
    c, _, _ = mqo(x['ideb_ai'], [x['g'] - x['vaar'], x['inse']])
    anota('sem_vaar_2025', c[1], 'Ideb 5th grade 2025 on spending net of VAAR and INSE')

    # 6. very high Saeb scores and the national mean of private schools
    rows = []
    for a in (2019, 2023, 2025):
        for lim in (300, 320):
            cont = ai.loc[mt[a] > lim, 'SG_UF'].value_counts()
            rows += [dict(ano=a, limite=lim, uf=u, redes=int(n)) for u, n in cont.items()]
            anota(f'redes_mat_acima_{lim}_{a}', float((mt[a] > lim).sum()), f'municipal networks with a 5th-grade math mean above {lim} in {a}')
    pd.DataFrame(rows).to_csv(os.path.join(RES, '08_notas_altas.csv'), sep=';', index=False)
    anota('redes_ce_com_nota_2025', float(mt[2025][ai['SG_UF'] == 'CE'].notna().sum()), 'Ceará municipal networks with a math score in 2025')
    br = pd.read_excel(os.path.join(DADOS, 'inep', 'divulgacao_brasil_ideb_2025', 'divulgacao_brasil_ideb_2025.xlsx'),
                       sheet_name='Brasil (Anos Iniciais)', header=9)
    priv = br[br['rede'].astype(str).str.startswith('Privada')]
    anota('privadas_mat_5ano_2025', float(priv['VL_NOTA_MATEMATICA_2025'].iloc[0]), 'national mean of private schools, 5th-grade math, Saeb 2025')
    mun = br[br['rede'].astype(str).str.strip() == 'Municipal']
    for a in (2017, 2025):
        anota(f'ideb_redes_municipais_{a}', float(mun[f'VL_OBSERVADO_{a}'].iloc[0]), f'Ideb 5th grade of all municipal networks, Brazil, {a}')

    # 7. enrollment-weighted spending per student
    for a in (2017, 2025):
        d = b[b['ano'] == a]
        anota(f'gasto_ponderado_{a}', (d['gasto_aluno'] * d['matriculas']).sum() / d['matriculas'].sum(), f'enrollment-weighted spending per student, {a} (2023 reais)')

    pd.DataFrame(saida).to_csv(os.path.join(RES, '08_resultados.csv'), sep=';', index=False, float_format='%.6f')
