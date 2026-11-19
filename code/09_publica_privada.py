"""Public versus private schools in the Saeb 2023, net of the students' socioeconomic level.

Student microdata of the Saeb 2023 (5th and 9th grades of ensino fundamental, 3rd and 4th years of
ensino médio), with Inep's sampling weights (public schools take part as a census, private schools
as a sample). For mathematics and Portuguese, the difference between private and public students is
estimated in four steps, by weighted least squares with standard errors clustered by school:
  1. no control (sample of students with a proficiency score and an INSE);
  2. the student's INSE;
  3. also the mean INSE of the student's school (weighted mean of the students of the school);
  4. also fixed effects of state x location (urban or rural).
Also: weighted means by sector, the student standard deviation, and the difference within each level
of the student's INSE (NU_TIPO_NIVEL_INSE).
The Saeb identifies public and private schools only (IN_PUBLICA); federal, state and municipal schools
cannot be separated, and school identifiers are masked, so the Censo Escolar cannot be linked.
Input: data/inep/microdados_saeb_2023.zip
Outputs: results/09_publica_privada.csv, results/09_medias.csv, results/09_por_nivel_inse.csv
"""
import os, zipfile
import numpy as np
import pandas as pd
from config import DADOS, RES

ARQ = {'5EF': 'TS_ALUNO_5EF', '9EF': 'TS_ALUNO_9EF', 'EM': 'TS_ALUNO_34EM'}
COLS = ['ID_UF', 'ID_ESCOLA', 'IN_PUBLICA', 'ID_LOCALIZACAO', 'IN_PROFICIENCIA_LP', 'IN_PROFICIENCIA_MT',
        'PESO_ALUNO_LP', 'PROFICIENCIA_LP_SAEB', 'PESO_ALUNO_MT', 'PROFICIENCIA_MT_SAEB',
        'INSE_ALUNO', 'NU_TIPO_NIVEL_INSE', 'PESO_ALUNO_INSE']


def ler(z, nome):
    partes = []
    for ch in pd.read_csv(z.open(f'MICRODADOS_SAEB_2023/DADOS/{nome}.csv'), sep=';', encoding='latin1',
                          usecols=COLS, chunksize=500_000, low_memory=False):
        for c in ch.columns:
            if ch[c].dtype == object:
                ch[c] = pd.to_numeric(ch[c].astype(str).str.replace(',', '.'), errors='coerce')
        escola = ch['ID_ESCOLA'].astype('int64')   # keep the school code exact (float32 would round it)
        ch = ch.drop(columns='ID_ESCOLA').astype('float32')
        ch['ID_ESCOLA'] = escola
        partes.append(ch)
    return pd.concat(partes, ignore_index=True)


def mqp(y, X, w, grupo):
    """Weighted least squares with an intercept; standard errors clustered by grupo."""
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in X]); y = np.asarray(y, float)
    sw = np.sqrt(w); Xw = X * sw[:, None]
    XtX = Xw.T @ Xw; b = np.linalg.solve(XtX, Xw.T @ (y * sw)); e = y - X @ b
    s = pd.DataFrame(X * (w * e)[:, None]).groupby(grupo).sum().values
    G, (n, k) = len(s), X.shape
    Bi = np.linalg.inv(XtX)
    V = Bi @ (s.T @ s) @ Bi * G / (G - 1) * (n - 1) / (n - k)
    return b, np.sqrt(np.diag(V))


def media(x, w):
    return float(np.sum(x * w) / np.sum(w))


if __name__ == '__main__':
    z = zipfile.ZipFile(os.path.join(DADOS, 'inep', 'microdados_saeb_2023.zip'))
    regs, medias, niveis = [], [], []
    for etapa, nome in ARQ.items():
        d = ler(z, nome)
        d['privada'] = 1.0 - d['IN_PUBLICA']
        di = d.dropna(subset=['INSE_ALUNO', 'PESO_ALUNO_INSE'])
        d['inse_escola'] = d['ID_ESCOLA'].map((di['INSE_ALUNO'] * di['PESO_ALUNO_INSE']).groupby(di['ID_ESCOLA']).sum()
                                              / di['PESO_ALUNO_INSE'].groupby(di['ID_ESCOLA']).sum())
        for disc in ('MT', 'LP'):
            y, p = f'PROFICIENCIA_{disc}_SAEB', f'PESO_ALUNO_{disc}'
            a = d[(d[f'IN_PROFICIENCIA_{disc}'] == 1) & (d[p] > 0)].dropna(subset=[y, p])
            dp = np.sqrt(media((a[y] - media(a[y], a[p])) ** 2, a[p]))
            for setor, g in a.groupby('privada'):
                medias.append(dict(etapa=etapa, disciplina=disc, setor='privada' if setor else 'publica', alunos=len(g),
                                   media=media(g[y], g[p]), inse=media(g['INSE_ALUNO'].fillna(g['INSE_ALUNO'].mean()), g[p]),
                                   dp_alunos=dp))
            b = a.dropna(subset=['INSE_ALUNO', 'inse_escola']).copy()
            w, grupo, Y = b[p].values.astype(float), b['ID_ESCOLA'].values, b[y].values.astype(float)
            fe = (b['ID_UF'] * 10 + b['ID_LOCALIZACAO']).values

            def desv(v):   # weighted deviation from the state x location mean (absorbs the fixed effects)
                v = pd.Series(np.asarray(v, float))
                ws = pd.Series(w)
                return (v - (v * ws).groupby(fe).transform('sum') / ws.groupby(fe).transform('sum')).values
            pri, ia, ie = b['privada'].values, b['INSE_ALUNO'].values, b['inse_escola'].values
            modelos = [('1 sem controle', [pri], Y), ('2 Inse do aluno', [pri, ia], Y),
                       ('3 e Inse da escola', [pri, ia, ie], Y),
                       ('4 e UF x localizacao', [desv(pri), desv(ia), desv(ie)], desv(Y))]
            for nm, X, yy in modelos:
                c, s = mqp(yy, X, w, grupo)
                regs.append(dict(etapa=etapa, disciplina=disc, modelo=nm, diferenca_privada=c[1], ep=s[1],
                                 em_dp=c[1] / dp, alunos=len(b), escolas=b['ID_ESCOLA'].nunique()))
            for nv, g in b.groupby('NU_TIPO_NIVEL_INSE'):
                pu, pr = g[g['privada'] == 0], g[g['privada'] == 1]
                niveis.append(dict(etapa=etapa, disciplina=disc, nivel_inse=int(nv), alunos_publica=len(pu),
                                   alunos_privada=len(pr), media_publica=media(pu[y], pu[p]) if len(pu) else np.nan,
                                   media_privada=media(pr[y], pr[p]) if len(pr) else np.nan,
                                   parcela_privada=float(pr[p].sum() / g[p].sum())))
        print(etapa, 'ok', flush=True)
    r = pd.DataFrame(regs); print(r.round(2).to_string(index=False))
    r.to_csv(os.path.join(RES, '09_publica_privada.csv'), sep=';', index=False, float_format='%.4f')
    pd.DataFrame(medias).to_csv(os.path.join(RES, '09_medias.csv'), sep=';', index=False, float_format='%.4f')
    n = pd.DataFrame(niveis); n['diferenca'] = n['media_privada'] - n['media_publica']
    n.to_csv(os.path.join(RES, '09_por_nivel_inse.csv'), sep=';', index=False, float_format='%.4f')
