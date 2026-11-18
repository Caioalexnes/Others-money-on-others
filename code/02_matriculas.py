"""Enrollments of each municipal school network, from the Censo Escolar microdata (school file).

Denominator of spending per student, as in Todos Pela Educação (2025): basic-education enrollments
(QT_MAT_BAS) of the municipal network (TP_DEPENDENCIA = 3), plus early-childhood enrollments
(QT_MAT_INF) of private schools under agreement with the municipality (convênio or parceria with
the municipal government, alone or with the state). Schools in activity only.
Usage: python 02_matriculas.py 2017 2019 2023
Input: DADOS/inep/microdados_censo_escolar_<year>.zip
Output: results/02_matriculas.csv (ano;cod_ibge;mat_rede_municipal;mat_infantil_conveniada;matriculas)
"""
import os, sys, zipfile
import pandas as pd
from config import DADOS, RES


def ler(ano):
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', f'microdados_censo_escolar_{ano}.zip'))
    nome = [n for n in z.namelist() if n.endswith(f'microdados_ed_basica_{ano}.csv')][0]
    cab = pd.read_csv(z.open(nome), sep=';', encoding='latin1', nrows=0).columns
    conv = ['IN_PODER_PUBLICO_PARCERIA', 'TP_PODER_PUBLICO_PARCERIA'] if 'TP_PODER_PUBLICO_PARCERIA' in cab else ['IN_CONVENIADA_PP', 'TP_CONVENIO_PODER_PUBLICO']
    d = pd.read_csv(z.open(nome), sep=';', encoding='latin1', low_memory=False,
                    usecols=['CO_MUNICIPIO', 'TP_DEPENDENCIA', 'TP_SITUACAO_FUNCIONAMENTO', 'QT_MAT_BAS', 'QT_MAT_INF'] + conv)
    d = d[d['TP_SITUACAO_FUNCIONAMENTO'] == 1]
    rede = d[d['TP_DEPENDENCIA'] == 3].groupby('CO_MUNICIPIO')['QT_MAT_BAS'].sum()
    priv = d[(d['TP_DEPENDENCIA'] == 4) & (d[conv[0]] == 1) & d[conv[1]].isin([1, 3])]
    inf = priv.groupby('CO_MUNICIPIO')['QT_MAT_INF'].sum()
    out = pd.DataFrame({'mat_rede_municipal': rede, 'mat_infantil_conveniada': inf}).fillna(0)
    out['matriculas'] = out.sum(axis=1)
    out.index.name = 'cod_ibge'
    return out.reset_index().assign(ano=ano)


if __name__ == '__main__':
    anos = [int(a) for a in sys.argv[1:]] or [2017, 2019, 2023]
    out = pd.concat([ler(a) for a in anos])
    dest = os.path.join(RES, '02_matriculas.csv')
    if os.path.exists(dest):
        old = pd.read_csv(dest, sep=';'); out = pd.concat([old[~old['ano'].isin(anos)], out])
    out = out[['ano', 'cod_ibge', 'mat_rede_municipal', 'mat_infantil_conveniada', 'matriculas']].sort_values(['ano', 'cod_ibge'])
    out.to_csv(dest, sep=';', index=False)
    print(out.groupby('ano')[['mat_rede_municipal', 'mat_infantil_conveniada', 'matriculas']].sum())
    print(out.groupby('ano')['cod_ibge'].nunique())
