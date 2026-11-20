"""Power calculations for the pre-analysis plan of the VAAT study. No outcome is related to the dose.

1. Approximate minimum detectable effects (MDE) of the dose coefficient in a long-difference regression
   with state fixed effects: SE ~ sd(dY) / (sd(D) * sqrt(n)), with dY the change of the outcome over a
   pre-treatment window and D the predicted dose (script 13), both demeaned within state;
   MDE = 2.8 * SE (5% two-sided, 80% power). The 2013-2019 window has the length of 2019-2025.
2. Whether averaging two baseline rounds would reduce the MDE (2019 minus the mean of 2011 and 2013).
3. The effect expected at the 75th percentile of the dose if returns were those of the U.S. meta-analysis
   of Jackson and Mackevicius (2024), once half of the money is earmarked to early childhood, and the
   implied power.
4. The MDE of the spending kink at the 2021 threshold, from the dispersion of the 2017-2019 change in
   spending per student (local linear on each side, uniform weights; robust bias-corrected intervals are
   taken as twice as wide), as a share of the mechanical first stage.
5. The number of municipalities where the municipal and the state network both have the outcome in 2019
   and 2025 (within-municipality comparison).
Inputs: results/13_vaat_redes.csv, results/13_vaat_anos.csv, results/13_diagnosticos.csv,
        data/inep/divulgacao_anos_*_municipios_2025/*.xlsx, results/09_medias.csv, results/03_base_municipios.csv,
        data/ipca_1737.json
Output: results/14_mde.csv, results/14_poder.csv
"""
import os, json, warnings
import numpy as np
import pandas as pd
from scipy.stats import norm
from config import DADOS, RES

ARQ = {'5th': 'divulgacao_anos_iniciais_municipios_2025', '9th': 'divulgacao_anos_finais_municipios_2025'}
DP_ALUNO = {'5th': '5EF', '9th': '9EF'}   # student SD of Saeb math in public schools, 2023 (script 09)
JM_EFEITO, JM_PARCELA = 0.0316, 0.075    # Jackson and Mackevicius (2024): $1,000 for 4 years, ~7.5% of spending
warnings.simplefilter('ignore', pd.errors.PerformanceWarning)


def num(m, c):
    return pd.to_numeric(m[c], errors='coerce')


def mde(s, dy):
    s = s.assign(dy=dy).dropna(subset=['dy'])
    u = s.dy - s.groupby('uf').dy.transform('mean')
    z = s.dose_previsto_2025 - s.groupby('uf').dose_previsto_2025.transform('mean')
    return 2.8 * u.std() / (z.std() * np.sqrt(len(s))), len(s)


if __name__ == '__main__':
    r = pd.read_csv(os.path.join(RES, '13_vaat_redes.csv'), sep=';')
    r = r[r['habilitado_tarde'] == 0]
    anos = pd.read_csv(os.path.join(RES, '13_vaat_anos.csv'), sep=';')
    diag = pd.read_csv(os.path.join(RES, '13_diagnosticos.csv'), sep=';', index_col=0)['valor']
    p75 = r.loc[r.dose_previsto_2025 > 0, 'dose_previsto_2025'].quantile(.75)
    dp = pd.read_csv(os.path.join(RES, '09_medias.csv'), sep=';')
    linhas, extra = [], {}
    for etapa, nome in ARQ.items():
        x = pd.read_excel(os.path.join(DADOS, 'inep', nome, nome + '.xlsx'), header=9)
        x['ibge'] = pd.to_numeric(x['CO_MUNICIPIO'], errors='coerce')
        mun = x[x['REDE'] == 'Municipal']
        m = r.merge(mun, on='ibge', how='inner')
        m['uf'] = m['ibge'] // 100000
        sd_aluno = dp[(dp.etapa == DP_ALUNO[etapa]) & (dp.disciplina == 'MT') & (dp.setor == 'publica')]['dp_alunos'].iloc[0]
        for y in ('VL_NOTA_MEDIA', 'VL_NOTA_MATEMATICA', 'VL_OBSERVADO'):
            for a0, a1 in ((2013, 2019), (2017, 2019)):
                v, n = mde(m, num(m, f'{y}_{a1}') - num(m, f'{y}_{a0}'))
                linhas.append(dict(etapa=etapa, resultado=y, janela=f'{a0}-{a1}', redes=n, mde_por_mil=v, mde_dose_p75=v * p75,
                                   mde_dose_p75_dp_aluno=v * p75 / sd_aluno if y == 'VL_NOTA_MATEMATICA' else np.nan))
        um, _ = mde(m, num(m, 'VL_NOTA_MEDIA_2019') - num(m, 'VL_NOTA_MEDIA_2013'))
        dois, _ = mde(m, num(m, 'VL_NOTA_MEDIA_2019') - (num(m, 'VL_NOTA_MEDIA_2011') + num(m, 'VL_NOTA_MEDIA_2013')) / 2)
        extra[f'{etapa}_reducao_mde_media_de_duas_bases'] = 1 - dois / um
        ok = lambda rede: set(x[(x.REDE == rede) & num(x, 'VL_NOTA_MEDIA_2019').notna() & num(x, 'VL_NOTA_MEDIA_2025').notna()].ibge)
        ambas = ok('Municipal') & ok('Estadual') & set(r.ibge)
        extra[f'{etapa}_municipios_com_as_duas_redes'] = len(ambas)
        extra[f'{etapa}_municipios_com_as_duas_redes_dose_positiva'] = int((r[r.ibge.isin(ambas)].dose_previsto_2025 > 0).sum())
    t = pd.DataFrame(linhas)
    t.to_csv(os.path.join(RES, '14_mde.csv'), sep=';', index=False, float_format='%.4f')

    # expected effect under U.S. returns, at the 75th percentile of the dose
    base = pd.read_csv(os.path.join(RES, '03_base_municipios.csv'), sep=';')
    d = pd.DataFrame(json.load(open(os.path.join(DADOS, 'ipca_1737.json'), encoding='utf-8'))[1:])
    d['ano'] = d['D3C'].str[:4].astype(int); d['V'] = d['V'].astype(float)
    ipca = d.groupby('ano')['V'].mean()
    g23 = base[(base.ano == 2023) & base.cod_ibge.isin(r.ibge[r.dose_previsto_2025 > 0])]['gasto_aluno'].median()
    g25 = g23 * ipca[2025] / ipca[2023]                                   # median spending per student, 2025 reais
    iei = anos['iei_ponderado'].dropna().mean() / 100
    parcela_anual = p75 * 1000 / 5 / g25                                    # dose p75 per year as a share of spending
    parcela_ef = parcela_anual * (1 - iei)                                  # net of the early-childhood earmark
    esperado = JM_EFEITO * parcela_ef / JM_PARCELA
    mde_mt5 = t[(t.etapa == '5th') & (t.resultado == 'VL_NOTA_MATEMATICA') & (t.janela == '2013-2019')]['mde_dose_p75_dp_aluno'].iloc[0]
    extra.update(dict(dose_p75=p75, gasto_aluno_mediano_dose_positiva_2025=g25, iei_medio=iei,
                      dose_p75_anual_sobre_gasto=parcela_anual, dose_p75_anual_sobre_gasto_sem_infantil=parcela_ef,
                      efeito_esperado_dp_aluno=esperado, mde_5ano_dp_aluno=mde_mt5,
                      poder_para_efeito_esperado=norm.cdf(esperado / (mde_mt5 / 2.8) - 1.96)))

    # spending kink at the 2021 threshold
    s = base.pivot_table(index='cod_ibge', columns='ano', values='gasto_aluno')
    k = r.merge((s[2019] - s[2017]).rename('ds'), left_on='ibge', right_index=True)
    inclinacao = 4846.26 * diag['matricula_ponderada_sobre_censo_x_menor_0_2'] * ipca[2023] / ipca[2021]   # 2023 reais
    extra['kink_inclinacao_mecanica_2023'] = inclinacao
    for h in (0.1, 0.2):
        w = k[k.x.abs() <= h]
        se = np.sqrt(sum((w.ds.std() / (l.x.std() * np.sqrt(len(l)))) ** 2 for l in (w[w.x <= 0], w[w.x > 0])))
        extra[f'kink_h{h}_mde_repasse_robusto'] = 2.8 * 2 * se / inclinacao
    e = pd.Series(extra)
    e.to_csv(os.path.join(RES, '14_poder.csv'), sep=';', header=['valor'], float_format='%.4f')
    print('p75 of positive dose (thousand 2025 reais per weighted student):', round(p75, 2))
    print(t.round(3).to_string(index=False)); print(e.round(4).to_string())
