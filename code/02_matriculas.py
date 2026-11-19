"""Enrollments of each municipal school network, from the Censo Escolar microdata (school file).

Denominator of spending per student, as in Todos Pela Educação (2025): basic-education enrollments
(QT_MAT_BAS) of the municipal network (TP_DEPENDENCIA = 3), plus early-childhood enrollments
(QT_MAT_INF) of private schools under agreement with the municipality (convênio or parceria with
the municipal government, alone or with the state). Schools in activity only.
Usage: python 02_matriculas.py 2017 2019 2023 2025
Input: DADOS/inep/microdados_censo_escolar_<year>.zip (from 2025, enrollments come in a separate
       table, Tabela_Matricula, joined to the school table by school code)
Output: results/02_matriculas.csv (ano;cod_ibge;mat_rede_municipal;mat_infantil_conveniada;matriculas)
"""
import os, sys, zipfile
import pandas as pd
from config import DADOS, RES


def tabela(z, sufixo):
    return [n for n in z.namelist() if n.split('/')[-1].upper().startswith(sufixo.upper())][0]


def ler(ano):
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', f'microdados_censo_escolar_{ano}.zip'))
    unico = [n for n in z.namelist() if n.endswith(f'microdados_ed_basica_{ano}.csv')]
    # up to 2024 one school file; from 2025 the school file has no enrollment counts, which come in a
    # separate table (Tabela_Matricula, one row per school), linked by the school code
    nome = unico[0] if unico else tabela(z, f'Tabela_Matricula_{ano}')
    cab = pd.read_csv(z.open(nome), sep=';', encoding='latin1', nrows=0).columns
    conv = ['IN_PODER_PUBLICO_PARCERIA', 'TP_PODER_PUBLICO_PARCERIA'] if 'TP_PODER_PUBLICO_PARCERIA' in cab else ['IN_CONVENIADA_PP', 'TP_CONVENIO_PODER_PUBLICO']
    cols = ['CO_MUNICIPIO', 'TP_DEPENDENCIA', 'QT_MAT_BAS', 'QT_MAT_INF'] + conv
    if unico:
        d = pd.read_csv(z.open(nome), sep=';', encoding='latin1', low_memory=False,
                        usecols=cols + ['TP_SITUACAO_FUNCIONAMENTO'])
    else:
        d = pd.read_csv(z.open(nome), sep=';', encoding='latin1', low_memory=False, usecols=cols + ['CO_ENTIDADE'])
        e = pd.read_csv(z.open(tabela(z, f'Tabela_Escola_{ano}')), sep=';', encoding='latin1', low_memory=False,
                        usecols=['CO_ENTIDADE', 'TP_SITUACAO_FUNCIONAMENTO'])
        assert e['CO_ENTIDADE'].is_unique and d['CO_ENTIDADE'].is_unique
        n = len(d); d = d.merge(e, on='CO_ENTIDADE', how='left'); assert len(d) == n
        print(ano, 'escolas na tabela de matrículas:', n, '| sem par na tabela de escolas:', d['TP_SITUACAO_FUNCIONAMENTO'].isna().sum())
    d = d[d['TP_SITUACAO_FUNCIONAMENTO'] == 1]
    rede = d[d['TP_DEPENDENCIA'] == 3].groupby('CO_MUNICIPIO')['QT_MAT_BAS'].sum()
    priv = d[(d['TP_DEPENDENCIA'] == 4) & (d[conv[0]] == 1) & d[conv[1]].isin([1, 3])]
    inf = priv.groupby('CO_MUNICIPIO')['QT_MAT_INF'].sum()
    out = pd.DataFrame({'mat_rede_municipal': rede, 'mat_infantil_conveniada': inf}).fillna(0)
    out['matriculas'] = out.sum(axis=1)
    out.index.name = 'cod_ibge'
    return out.reset_index().assign(ano=ano)


if __name__ == '__main__':
    anos = [int(a) for a in sys.argv[1:]] or [2017, 2019, 2023, 2025]
    out = pd.concat([ler(a) for a in anos])
    dest = os.path.join(RES, '02_matriculas.csv')
    if os.path.exists(dest):
        old = pd.read_csv(dest, sep=';'); out = pd.concat([old[~old['ano'].isin(anos)], out])
    out = out[['ano', 'cod_ibge', 'mat_rede_municipal', 'mat_infantil_conveniada', 'matriculas']].sort_values(['ano', 'cod_ibge'])
    out.to_csv(dest, sep=';', index=False)
    print(out.groupby('ano')[['mat_rede_municipal', 'mat_infantil_conveniada', 'matriculas']].sum())
    print(out.groupby('ano')['cod_ibge'].nunique())
