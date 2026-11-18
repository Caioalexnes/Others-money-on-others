"""What is left to teach: municipal network spending per student versus private school tuition
(Table "O que sobra para ensinar" of the essay, Section "Quanto custa a escola de bairro").

All inputs are parameters taken from the sources listed next to each one; the script only does the
arithmetic, so that every number in the table and in the text around it can be checked.
Output: results/04_custo_escola.csv and a printout of the numbers quoted in the text.
"""
import json, os
import pandas as pd
from config import DADOS, RES

# --- Public side ---------------------------------------------------------------------------
GASTO_MUNICIPAL_2023 = 12_460      # R$ per student per year, municipal networks, 2023 (Todos Pela Educação 2025, p. 5)
VAAT_MIN_2025 = 8_024.31           # R$ per student per year (Portaria Interministerial MEC/MF nº 5/2026)
PNAE_DIA = 0.57                    # R$ per student per school day, ensino fundamental (Resolução FNDE, fev. 2026)
DIAS_LETIVOS = 200
PNATE_TOTAL, PNATE_ALUNOS = 872e6, 4.6e6   # federal school transport transfer and students transported (Brasil 61, 2023)
ALUNOS_FUNDEB = 39.3e6             # students in the Fundeb networks (Agência Gov, 2026)
MERENDA_TRANSPORTE_MAX = 700       # assumed ceiling, more than three times the federal transfers

# --- Private side --------------------------------------------------------------------------
MENSALIDADE_2025 = {'RS': 1_096.60, 'SP': 1_010.93, 'PB': 402.04}   # mean monthly tuition, ensino fundamental (Melhor Escola, 2025)

# Simples Nacional, Anexo III (LC 123/2006, as amended by LC 155/2016): (upper limit of the band, nominal rate, deduction)
# Share of the employer social security contribution (CPP) in the Simples payment, Anexo III, bands 1 to 5
CPP_ANEXO_III = 0.434
ANEXO_III = [(180e3, .06, 0), (360e3, .112, 9_360), (720e3, .135, 17_640), (1.8e6, .16, 35_640), (3.6e6, .21, 125_640), (4.8e6, .33, 648_000)]


def simples(receita):
    """Effective Simples Nacional rate for annual gross revenue (Anexo III): (RBT12 x nominal - deduction) / RBT12."""
    for teto, aliq, ded in ANEXO_III:
        if receita <= teto:
            return (receita * aliq - ded) / receita
    raise ValueError('above the Simples Nacional ceiling')


def ipca_2023_para_2025():
    """Ratio of the annual mean of the IPCA index in 2025 to that of 2023 (IBGE, table 1737)."""
    d = json.load(open(os.path.join(DADOS, 'ipca_1737.json'), encoding='utf-8'))[1:]
    v = {r['D3C']: float(r['V']) for r in d}
    media = lambda a: sum(v[f'{a}{m:02d}'] for m in range(1, 13)) / 12
    return media(2025) / media(2023)


def presumido(iss, adicional_irpj, folha_sobre_receita, encargos_folha):
    """Tax burden on revenue under lucro presumido: ISS, PIS (0.65%), Cofins (3%), IRPJ 15% (+10% surcharge)
    and CSLL 9% on a presumed profit of 32% of revenue, plus payroll contributions."""
    base = 0.32
    return iss + 0.0065 + 0.03 + base * (0.15 + (0.10 if adicional_irpj else 0)) + base * 0.09 + folha_sobre_receita * encargos_folha


if __name__ == '__main__':
    s_lo, s_hi = simples(1.26e6), simples(3.24e6)
    p_lo = presumido(0.02, False, 0, 0); p_hi = presumido(0.05, True, 0, 0)
    t_lo, t_hi = presumido(0.02, False, 0.5, 0.26), presumido(0.05, True, 0.5, 0.30)
    print(f'Simples Anexo III, revenue R$1.26-3.24 million: {s_lo:.1%} to {s_hi:.1%}; without the CPP: {s_lo * (1 - CPP_ANEXO_III):.1%} to {s_hi * (1 - CPP_ANEXO_III):.1%}')
    print(f'Lucro presumido, taxes on revenue and profit: {p_lo:.1%} to {p_hi:.1%}; with payroll (half of revenue, 26-30%): {t_lo:.1%} to {t_hi:.1%}')
    # Only taxes on revenue and profit are deducted: the employer social security contribution is also part of
    # the public spending, so it is left in both sides. Low end: Simples without the CPP; high end: lucro presumido.
    carga_min, carga_max = s_lo * (1 - CPP_ANEXO_III), p_hi
    # Public spending of 2023 in 2025 reais, the year of the tuition survey
    fator = ipca_2023_para_2025()
    gasto = GASTO_MUNICIPAL_2023 * fator
    print(f'IPCA 2025/2023 (annual means): {fator:.4f}; municipal spending in 2025 reais: R$ {gasto:,.0f}')
    pub_lo, pub_hi = gasto - MERENDA_TRANSPORTE_MAX, gasto
    linhas = [dict(rede='municipal', gasto_anual=gasto, impostos_min=0, impostos_max=0,
                   merenda_transporte=MERENDA_TRANSPORTE_MAX, sobra_min=pub_lo, sobra_max=pub_hi)]
    for uf in ('RS', 'SP'):
        anual = MENSALIDADE_2025[uf] * 12
        linhas.append(dict(rede=f'privada {uf}', gasto_anual=anual, impostos_min=anual * carga_min, impostos_max=anual * carga_max,
                           merenda_transporte=0, sobra_min=anual * (1 - carga_max), sobra_max=anual * (1 - carga_min)))
    t = pd.DataFrame(linhas)
    t.to_csv(os.path.join(RES, '04_custo_escola.csv'), sep=';', index=False, float_format='%.2f')
    print(t.round(0).to_string(index=False))
    for uf in ('RS', 'SP'):
        r = t[t.rede == f'privada {uf}'].iloc[0]
        print(f'municipal spends {pub_lo / r.sobra_max - 1:.0%} to {pub_hi / r.sobra_min - 1:.0%} more than private {uf}')
    print(f'municipal per month (2025 reais): R$ {gasto / 12:.0f}; VAAT-MIN per month: R$ {VAAT_MIN_2025 / 12:.0f};'
          f' VAAT-MIN / PB tuition: {VAAT_MIN_2025 / 12 / MENSALIDADE_2025["PB"]:.2f}')
    print(f'PNAE per year: R$ {PNAE_DIA * DIAS_LETIVOS:.0f}; PNATE per transported student: R$ {PNATE_TOTAL / PNATE_ALUNOS:.0f};'
          f' per student of the networks: R$ {PNATE_TOTAL / ALUNOS_FUNDEB:.0f}; federal sum: R$ {PNAE_DIA * DIAS_LETIVOS + PNATE_TOTAL / ALUNOS_FUNDEB:.0f}'
          f' (ceiling {MERENDA_TRANSPORTE_MAX} = {MERENDA_TRANSPORTE_MAX / (PNAE_DIA * DIAS_LETIVOS + PNATE_TOTAL / ALUNOS_FUNDEB):.1f} times)')
