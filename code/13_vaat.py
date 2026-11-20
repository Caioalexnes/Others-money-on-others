"""Fundeb VAAT complementation, 2021 to 2025: treatment data for the pre-analysis plan.

1. The VAAT before the complementation in 2021 of every network that was habilitated by June 2021
   (Portaria Interministerial MEC/ME nº 3/2021), as reproduced in the annex of the Câmara's
   Estudo Técnico nº 15/2021 (5,234 networks, with revenues and weighted enrollment).
2. The official lists of recipients in the December portaria of each year (2021: nº 10/2021;
   2022: nº 6/2022; 2023: nº 7/2023; 2024: nº 13/2024; 2025: nº 13/2025), Anexo III.
3. Validation of (1) against the official 2021 list, and the networks habilitated after June 2021.
4. For the municipal networks of (1): the position relative to the 2021 threshold,
   x = VAAT_2021 / VAAT-MIN_2021 - 1; the complementation actually received per weighted student in
   each year; and the complementation predicted by the formula from 2021 data only,
   Z_t = max(0, VAAT-MIN_t - g_t * VAAT_2021), where g_t is set so that the number of sample networks
   with Z_t > 0 equals the number that actually received in year t. The dose is the sum of Z_t over
   2021-2025, in thousand reais per weighted student (nominal and at 2025 prices, IPCA annual mean).
5. Diagnostics that use no outcome data: density of x near the threshold, the share of the 2021
   money in the 2021-2025 total near the threshold, the slopes of later money on each side, and the
   partial F of the predicted dose once a cubic in x is controlled for.
Inputs: data/fnde/vaat/*.pdf (see 00_download.py), data/ipca_1737.json
Outputs: results/13_vaat_redes.csv, results/13_vaat_anos.csv, results/13_diagnosticos.csv
"""
import os, re, json, subprocess
import numpy as np
import pandas as pd
from config import DADOS, RES

V = os.path.join(DADOS, 'fnde', 'vaat')
NUM = r'\d{1,3}(?:\.\d{3})*,\d{2}'
INT = r'\d{1,3}(?:\.\d{3})*'
OFICIAIS = {2021: ('portaria_10_2021.pdf', '. ANEXO III', '. ANEXO IV'),
            2022: ('portaria_6_2022.pdf', '. ANEXO III', '. ANEXO IV'),
            2023: ('anexo3_portaria_7_2023.pdf', None, None),
            2024: ('anexo3_portaria_13_2024.pdf', None, None),
            2025: ('anexo3_portaria_13_2025.pdf', None, None)}


def br(s):
    s = s.strip()
    return 0.0 if s in ('', '-') else float(s.replace('.', '').replace(',', '.'))


def texto(pdf, modo='-raw'):
    return subprocess.run(['pdftotext', modo, os.path.join(V, pdf), '-'], capture_output=True, text=True,
                          check=True).stdout


def lista_2021_junho():
    """Annex of ET 15/2021: one line per habilitated network."""
    pat = re.compile(rf'^\s*({INT})\s+([A-Z]{{2}}) - (.+?)\s{{2,}}({INT})\s+({INT})\s+({INT})\s+({INT})\s+({INT})\s+'
                     rf'({INT},\d{{2}})\s+({INT}|-)\s+({INT},\d{{2}})\s*$')
    linhas = []
    for l in texto('et15_2021.pdf', '-layout').splitlines():
        m = pat.match(l)
        if m:
            a = m.groups()
            linhas.append(dict(ibge=int(br(a[3])), uf=a[1], ente=a[2].strip(), receitas=br(a[4]), mat_censo=br(a[5]),
                               mat_vaat=br(a[7]), vaat2021=br(a[8])))
    return pd.DataFrame(linhas)


def lista_oficial(ano):
    pdf, ini, fim = OFICIAIS[ano]
    t = texto(pdf)
    if ini:
        i = t.find(ini); t = t[i:t.find(fim, i + 1)]
    r = re.findall(rf'\b([1-5]\d{{6}}|[1-5]\d)\s+({NUM})\s+({NUM})\s+({NUM}|-)(?:\s+(\d{{1,3}},\d+)\s*%)?', t)
    o = pd.DataFrame([dict(ibge=int(a), pre=br(b), pos=br(c), comp=br(d), iei=br(e) if e else np.nan) for a, b, c, d, e in r])
    return o[o['comp'] > 0].drop_duplicates('ibge')


def deflator():
    d = pd.DataFrame(json.load(open(os.path.join(DADOS, 'ipca_1737.json'), encoding='utf-8'))[1:])
    d['ano'] = d['D3C'].str[:4].astype(int); d['V'] = d['V'].astype(float)
    m = d.groupby('ano')['V'].mean()
    return {a: m[2025] / m[a] for a in range(2021, 2026)}


if __name__ == '__main__':
    jun = lista_2021_junho()
    assert len(jun) == jun['ibge'].nunique()
    anos = {a: lista_oficial(a) for a in OFICIAIS}
    resumo = pd.DataFrame([dict(ano=a, vaat_min=o['pos'].max(), recebem=len(o), total_bi=o['comp'].sum() / 1e9,
                                municipios=(o['ibge'] >= 100).sum(),
                                iei_ponderado=np.average(o['iei'].dropna(), weights=o.loc[o['iei'].notna(), 'comp'])
                                if o['iei'].notna().any() else np.nan) for a, o in anos.items()])
    assert all(np.allclose(o['pos'], o['pos'].max()) for o in anos.values())   # everyone ends at VAAT-MIN
    resumo.to_csv(os.path.join(RES, '13_vaat_anos.csv'), sep=';', index=False, float_format='%.4f')
    print(resumo.round(2).to_string(index=False))

    # validation of the June 2021 list against the official December 2021 list
    MIN21 = anos[2021]['pos'].max()
    v = anos[2021].merge(jun, on='ibge', how='left')
    rel = (v['vaat2021'] / v['pre'] - 1).abs()
    tarde = v[v['vaat2021'].isna()]
    print(f'June list: {len(jun)} networks ({(jun.ibge >= 100).sum()} municipal) | official 2021 recipients: {len(v)}, '
          f'in the June list: {v.vaat2021.notna().sum()}, max relative difference {rel.max():.5f} | '
          f'habilitated later: {len(tarde)}, of which within 10% below the threshold: {(tarde.pre > 0.9 * MIN21).sum()} '
          f'| June-list networks below the threshold that did not receive: {((jun.vaat2021 < MIN21) & ~jun.ibge.isin(v.ibge)).sum()}')

    # municipal panel
    r = jun[jun['ibge'] >= 100].copy()
    r['x'] = r['vaat2021'] / MIN21 - 1
    r['habilitado_tarde'] = 0
    t = tarde[tarde['ibge'] >= 100][['ibge', 'pre']].rename(columns={'pre': 'vaat2021'})
    t = t.assign(x=t['vaat2021'] / MIN21 - 1, habilitado_tarde=1)
    r = pd.concat([r, t], ignore_index=True)
    defl = deflator()
    principal = r['habilitado_tarde'] == 0
    for a, o in anos.items():
        r[f'recebido_{a}'] = r['ibge'].map((o['pos'] - o['pre']).set_axis(o['ibge'])).fillna(0.0)
        parcela = (r.loc[principal, f'recebido_{a}'] > 0).mean()
        corte = np.quantile(r.loc[principal, 'vaat2021'], parcela)
        g = resumo.set_index('ano').loc[a, 'vaat_min'] / corte
        r[f'previsto_{a}'] = np.maximum(0.0, resumo.set_index('ano').loc[a, 'vaat_min'] - g * r['vaat2021'])
        resumo.loc[resumo['ano'] == a, ['g', 'parcela_amostra']] = g, parcela
    for tipo in ('recebido', 'previsto'):
        r[f'dose_{tipo}'] = sum(r[f'{tipo}_{a}'] for a in anos) / 1000
        r[f'dose_{tipo}_2025'] = sum(r[f'{tipo}_{a}'] * defl[a] for a in anos) / 1000
    r.to_csv(os.path.join(RES, '13_vaat_redes.csv'), sep=';', index=False, float_format='%.6f')
    resumo.to_csv(os.path.join(RES, '13_vaat_anos.csv'), sep=';', index=False, float_format='%.4f')
    print(resumo[['ano', 'g', 'parcela_amostra']].round(3).to_string(index=False))

    # diagnostics (no outcome data)
    m = r[principal]
    diag = {}
    pos = m.loc[m.dose_previsto_2025 > 0, 'dose_previsto_2025']
    diag['municipios_amostra'] = len(m)
    diag['parcela_dose_zero'] = (m.dose_previsto_2025 == 0).mean()
    for q in (.5, .75, .9):
        diag[f'dose_positiva_p{int(q * 100)}'] = pos.quantile(q)
    diag['correlacao_prevista_recebida'] = np.corrcoef(m.dose_previsto_2025, m.dose_recebido_2025)[0, 1]
    diag['matricula_ponderada_sobre_censo_x_menor_0_2'] = (m.loc[m.x.abs() <= 0.2, 'mat_vaat'] / m.loc[m.x.abs() <= 0.2, 'mat_censo']).median()
    perto = m['x'].abs() < 0.1
    diag['parcela_2021_no_total_x_menor_0_1'] = m.loc[perto, 'recebido_2021'].sum() / m.loc[perto, [f'recebido_{a}' for a in anos]].sum().sum()
    for lado, sel in (('esquerda', (m.x > -.1) & (m.x <= 0)), ('direita', (m.x > 0) & (m.x <= .1))):
        s = m[sel]; X = np.column_stack([np.ones(len(s)), s.x])
        diag[f'inclinacao_2022_2025_{lado}'] = np.linalg.lstsq(X, sum(s[f'recebido_{a}'] for a in range(2022, 2026)), rcond=None)[0][1]
    for h in (0.1, 0.2, 0.3):
        s = m[m.x.abs() <= h]; x = s.x.values
        y = s.dose_recebido_2025.values; z = s.dose_previsto_2025.values
        X0 = np.column_stack([np.ones(len(s)), x, x ** 2, x ** 3]); X1 = np.column_stack([X0, z])
        e0 = y - X0 @ np.linalg.lstsq(X0, y, rcond=None)[0]; e1 = y - X1 @ np.linalg.lstsq(X1, y, rcond=None)[0]
        diag[f'F_parcial_h{h}'] = (e0 @ e0 - e1 @ e1) / (e1 @ e1 / (len(s) - X1.shape[1]))
    faixas = pd.cut(m.x, np.round(np.arange(-0.12, 0.1201, 0.02), 2)).value_counts().sort_index()
    for k, n in faixas.items():
        diag[f'densidade_{k.left:+.2f}_{k.right:+.2f}'] = n
    d = pd.Series(diag)
    d.to_csv(os.path.join(RES, '13_diagnosticos.csv'), sep=';', header=['valor'], float_format='%.4f')
    print(d.round(3).to_string())
