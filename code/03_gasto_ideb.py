"""Spending per student of municipal school networks and learning outcomes (Ideb), by municipality.

Replicates and extends Todos Pela Educação (2025), "Relação entre investimento por aluno e qualidade
do ensino": spending = committed expenditure (despesas empenhadas) in function 12 (Educação) plus
subfunction 847 (Transferências para a Educação Básica) recorded outside function 12, minus
subfunction 364 (Ensino Superior), from the municipal DCA (Siconfi, Anexo I-E); divided by the
enrollments of script 02; in 2023 reais, deflated by the annual mean of the IPCA (IBGE, table 1737).
Outcomes: Ideb of the municipal network, early grades (anos iniciais, 5th grade) and late grades
(anos finais, 9th grade), Inep. Socioeconomic level: Inep's INSE of the municipal network's students
(Saeb), 2019 and 2023 (the 2023 edition is also used for 2025).
Inputs: data/siconfi/dca_<year>.csv (script 01), results/02_matriculas.csv, data/ipca_1737.json,
        data/inep/divulgacao_anos_{iniciais,finais}_municipios_2025/*.xlsx, data/inep/INSE_*_municipios.xlsx
Outputs: results/03_base_municipios.csv, results/03_regressoes.csv, results/03_faixas.csv
"""
import json, os
import numpy as np
import pandas as pd
from config import DADOS, RES

ANOS = (2017, 2019, 2023, 2025)
# INSE edition used for each year: there is no municipal INSE for 2017, and the INSE of the 2025 Saeb
# had not been released in November 2026, so the nearest edition is used
INSE = {2017: 2019, 2019: 2019, 2023: 2023, 2025: 2023}


def mqo(y, X):
    """OLS with an intercept; returns coefficients, HC1 standard errors and R2."""
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in X]); y = np.asarray(y, float)
    b, *_ = np.linalg.lstsq(X, y, rcond=None); e = y - X @ b
    n, k = X.shape; XtXi = np.linalg.inv(X.T @ X)
    V = XtXi @ (X.T * e**2) @ X @ XtXi * n / (n - k)
    return b, np.sqrt(np.diag(V)), 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))


def ipca_medio():
    d = json.load(open(os.path.join(DADOS, 'ipca_1737.json')))[1:]
    v = pd.DataFrame({'ano': [int(x['D3C'][:4]) for x in d], 'indice': [float(x['V']) for x in d]})
    return v.groupby('ano')['indice'].mean()


def gasto(ano):
    d = pd.read_csv(os.path.join(DADOS, 'siconfi', f'dca_{ano}.csv'), sep=';')
    f12 = d[d['conta'] == '12 - Educação'].groupby('cod_ibge')['valor'].sum()
    sup = d[d['conta'].str.startswith('12.364')].groupby('cod_ibge')['valor'].sum()
    t847 = d[d['conta'].str.contains(r'\.847') & ~d['conta'].str.startswith('12.')].groupby('cod_ibge')['valor'].sum()
    g = pd.DataFrame({'funcao12': f12, 'ensino_superior': sup, 'transf_847': t847}).fillna(0)
    g = g[g.index.isin(f12.index)]
    g['gasto'] = g['funcao12'] - g['ensino_superior'] + g['transf_847']
    return g


def ideb(etapa):
    f = os.path.join(DADOS, 'inep', f'divulgacao_anos_{etapa}_municipios_2025', f'divulgacao_anos_{etapa}_municipios_2025.xlsx')
    x = pd.read_excel(f, header=9)
    x = x[x['REDE'] == 'Municipal'].copy()
    x['cod_ibge'] = pd.to_numeric(x['CO_MUNICIPIO'], errors='coerce')
    cols = {}
    for a in (2017, 2019, 2023, 2025):
        cols[f'ideb_{etapa}_{a}'] = pd.to_numeric(x[f'VL_OBSERVADO_{a}'], errors='coerce')
    return pd.DataFrame(cols).set_index(x['cod_ibge'])


def inse(ed):
    nome = {2019: 'INSE_2019_MUNICIPIOS.xlsx', 2023: 'INSE_2023_municipios.xlsx'}[ed]
    x = pd.read_excel(os.path.join(DADOS, 'inep', nome), header=2 if ed == 2019 else 0)
    x.columns = [str(c).rstrip('*') for c in x.columns]
    x = x[(x['TP_TIPO_REDE'] == 3) & (x['TP_LOCALIZACAO'] == 0)]
    if 'TP_CAPITAL' in x:   # 2023 file repeats each stratum; one row per municipality
        x = x.drop_duplicates(['CO_MUNICIPIO', 'TP_TIPO_REDE', 'TP_LOCALIZACAO'])
    return pd.to_numeric(x.set_index('CO_MUNICIPIO')['MEDIA_INSE'], errors='coerce').rename(f'inse_{ed}')


if __name__ == '__main__':
    import sys
    if sys.argv[1:]:
        ANOS = tuple(int(a) for a in sys.argv[1:])
    ip = ipca_medio()
    mat = pd.read_csv(os.path.join(RES, '02_matriculas.csv'), sep=';')
    ii, af = ideb('iniciais'), ideb('finais')
    ins = {e: inse(e) for e in (2019, 2023)}
    base, regs, faixas = [], [], []
    for a in ANOS:
        g = gasto(a)
        m = mat[mat['ano'] == a].set_index('cod_ibge')
        b = g.join(m[['matriculas']], how='inner')
        b = b[b['matriculas'] > 0]
        b['gasto_aluno'] = b['gasto'] / b['matriculas'] * ip[2023] / ip[a]
        b['ideb_ai'] = ii[f'ideb_iniciais_{a}']
        b['ideb_af'] = af[f'ideb_finais_{a}']
        b['inse'] = ins[INSE[a]]
        b['ano'] = a
        base.append(b.reset_index())
        mil = b['gasto_aluno'] / 1000
        # trimmed sample: drop the 1% tails of spending per student (data errors such as tiny enrollments)
        lo, hi = mil.quantile([0.01, 0.99])
        for etapa in ('ideb_ai', 'ideb_af'):
            for amostra, sel in (('all', mil.notna()), ('trimmed 1%', mil.between(lo, hi))):
                x = b[sel].assign(g=mil[sel]).dropna(subset=[etapa, 'g'])
                c, s, r2 = mqo(x[etapa], [x['g']])
                linha = dict(ano=a, etapa=etapa, amostra=amostra, n=len(x), coef=c[1], ep=s[1], r2=r2)
                xi = x.dropna(subset=['inse'])
                c, s, r2 = mqo(xi[etapa], [xi['g'], xi['inse']])
                linha.update(n_inse=len(xi), coef_inse=c[1], ep_inse=s[1], coef_do_inse=c[2], r2_inse=r2)
                regs.append(linha)
        # spending bands of R$ 2 thousand, as in TPE (até 8, 8-10, ..., acima de 20)
        cortes = [-np.inf, 8, 10, 12, 14, 16, 18, 20, np.inf]
        rot = ['até 8', '8-10', '10-12', '12-14', '14-16', '16-18', '18-20', 'acima de 20']
        b['faixa'] = pd.cut(mil, cortes, labels=rot, right=False)
        for etapa in ('ideb_ai', 'ideb_af'):
            gr = b.dropna(subset=[etapa]).groupby('faixa', observed=False)[etapa]
            t = gr.agg(['count', 'min', 'max', 'mean', 'median'])
            for q in (0.10, 0.25, 0.75, 0.90):
                t[f'p{int(q * 100)}'] = gr.quantile(q)
            t['ano'], t['etapa'] = a, etapa
            faixas.append(t.reset_index())
        print(a, 'municípios com gasto e matrículas:', len(b), '| média simples R$', round(b['gasto_aluno'].mean()), '| ponderada R$',
              round((b['gasto'] * ip[2023] / ip[a]).sum() / b['matriculas'].sum()), '| mediana R$', round(b['gasto_aluno'].median()), flush=True)
    base = pd.concat(base)
    base.to_csv(os.path.join(RES, '03_base_municipios.csv'), sep=';', index=False, float_format='%.4f')
    pd.DataFrame(regs).to_csv(os.path.join(RES, '03_regressoes.csv'), sep=';', index=False, float_format='%.6f')
    pd.concat(faixas).to_csv(os.path.join(RES, '03_faixas.csv'), sep=';', index=False, float_format='%.3f')
    print(pd.DataFrame(regs).round(4).to_string(index=False))
