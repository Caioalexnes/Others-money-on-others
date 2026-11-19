"""Literacy at the end of the 2nd grade in the federal Saeb 2023, by state, and checks on Ceará.

The Indicador Criança Alfabetizada (MEC) is built from the states' own 2nd-grade tests; in Ceará, the
SPAECE-Alfa, which also carries 40% of the education index that distributes the municipal ICMS.
The federal Saeb tested a sample of 2nd-grade students in 2023. This script computes, from the Saeb
student microdata with Inep's sampling weights, the share of students at or above the national
literacy standard (743 points; IN_ALFABETIZADO = 1), by state and network, with standard errors
clustered by school. Inep advises against comparing states with this sample.
It also lists the Ceará municipal networks with a 5th-grade Ideb of 9.5 or more in 2025, checks which
of the nine municipalities reported by the press with 100% of children literate in 2024 are among
them, and gives the median spending per student of the municipal networks by state in 2023.
Inputs: data/inep/microdados_saeb_2023.zip, data/inep/divulgacao_anos_iniciais_municipios_2025/*.xlsx,
        results/03_base_municipios.csv
Outputs: results/10_alfabetizacao_saeb2023.csv, results/10_ceara.csv
"""
import os, zipfile
import numpy as np
import pandas as pd
from config import DADOS, RES

UF = {11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN',
      25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC',
      43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'}
# Diário do Nordeste, 19 Jul. 2025: municipalities of Ceará with 100% of children literate in 2024 (ICA)
CEM_POR_CENTO_2024 = ['Catunda', 'Coreaú', 'Forquilha', 'Graça', 'Novo Oriente', 'Pacujá', 'Piquet Carneiro',
                      'Pires Ferreira', 'Poranga']


def proporcao(g):
    """Weighted share of literate students and its standard error clustered by school."""
    w, y = g['PESO_ALUNO_LP'], g['IN_ALFABETIZADO']
    p = (w * y).sum() / w.sum()
    u = (w * (y - p)).groupby(g['ID_ESCOLA']).sum()
    ep = np.sqrt(len(u) / (len(u) - 1) * (u ** 2).sum()) / w.sum()
    return pd.Series({'alunos': len(g), 'escolas': g['ID_ESCOLA'].nunique(), 'alfabetizados_pct': 100 * p, 'ep_pct': 100 * ep})


if __name__ == '__main__':
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_saeb_2023.zip'))
    d = pd.read_csv(z.open('MICRODADOS_SAEB_2023/DADOS/TS_ALUNO_2EF.csv'), sep=';', encoding='latin1', low_memory=False,
                    usecols=['ID_UF', 'ID_ESCOLA', 'IN_PUBLICA', 'IN_PROFICIENCIA_LP', 'PESO_ALUNO_LP', 'IN_ALFABETIZADO',
                             'PROFICIENCIA_LP_SAEB'])
    for c in d.columns:
        if d[c].dtype == object:
            d[c] = pd.to_numeric(d[c].astype(str).str.replace(',', '.'), errors='coerce')
    a = d[(d['IN_PROFICIENCIA_LP'] == 1)].dropna(subset=['PESO_ALUNO_LP', 'IN_ALFABETIZADO'])
    assert ((a['PROFICIENCIA_LP_SAEB'] >= 743) == (a['IN_ALFABETIZADO'] == 1)).all()
    linhas = []
    for rede, sel in (('publica', a['IN_PUBLICA'] == 1), ('total', a['IN_PUBLICA'].notna())):
        linhas.append(proporcao(a[sel]).to_frame().T.assign(uf='BR', rede=rede))
        t = a[sel].groupby('ID_UF').apply(proporcao)
        t['uf'] = [UF[int(i)] for i in t.index]
        linhas.append(t.assign(rede=rede))
    r = pd.concat(linhas, ignore_index=True)[['uf', 'rede', 'alunos', 'escolas', 'alfabetizados_pct', 'ep_pct']]
    r.to_csv(os.path.join(RES, '10_alfabetizacao_saeb2023.csv'), sep=';', index=False, float_format='%.2f')
    print(r[r['rede'] == 'publica'].sort_values('alfabetizados_pct', ascending=False).round(1).to_string(index=False))

    x = pd.read_excel(os.path.join(DADOS, 'inep', 'divulgacao_anos_iniciais_municipios_2025',
                                   'divulgacao_anos_iniciais_municipios_2025.xlsx'), header=9)
    x = x[(x['REDE'] == 'Municipal') & (x['SG_UF'] == 'CE')].copy()
    for c in ('VL_OBSERVADO_2023', 'VL_OBSERVADO_2025', 'VL_NOTA_MATEMATICA_2025', 'VL_NOTA_PORTUGUES_2025'):
        x[c] = pd.to_numeric(x[c], errors='coerce')
    x['ideb_2025_9_5_ou_mais'] = x['VL_OBSERVADO_2025'] >= 9.5
    x['cem_por_cento_alfabetizados_2024'] = x['NO_MUNICIPIO'].isin(CEM_POR_CENTO_2024)
    assert x['cem_por_cento_alfabetizados_2024'].sum() == len(CEM_POR_CENTO_2024)
    x[['CO_MUNICIPIO', 'NO_MUNICIPIO', 'VL_OBSERVADO_2023', 'VL_OBSERVADO_2025', 'VL_NOTA_MATEMATICA_2025',
       'VL_NOTA_PORTUGUES_2025', 'ideb_2025_9_5_ou_mais', 'cem_por_cento_alfabetizados_2024']].to_csv(
        os.path.join(RES, '10_ceara.csv'), sep=';', index=False)
    print('Ceará networks:', len(x), '| Ideb 2025 >= 9.5:', int(x['ideb_2025_9_5_ou_mais'].sum()),
          '| of the nine with 100% in 2024, with Ideb 2025 >= 9.5:',
          x.loc[x['cem_por_cento_alfabetizados_2024'] & x['ideb_2025_9_5_ou_mais'], 'NO_MUNICIPIO'].tolist())

    b = pd.read_csv(os.path.join(RES, '03_base_municipios.csv'), sep=';')
    b = b[b['ano'] == 2023]
    med = b.groupby((b['cod_ibge'] // 100000).map(UF))['gasto_aluno'].median()
    ce = b[b['cod_ibge'] // 100000 == 23]['gasto_aluno']
    print('median spending per student 2023 (2023 reais): Brazil', round(b['gasto_aluno'].median()),
          '| CE', round(med['CE']), '| PR', round(med['PR']), '| SC', round(med['SC']), '| SP', round(med['SP']),
          '| CE networks below the national median:', f"{(ce < b['gasto_aluno'].median()).mean():.0%}")
