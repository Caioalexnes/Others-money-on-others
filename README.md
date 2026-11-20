# Basic education in Brazil: spending per student and learning

Code, intermediate results and data extracts for the section on basic education of the essay
*Dinheiro dos Outros nos Outros: incentivos, custo e desfecho no SUS e na escola pública brasileira*
(Caio A. F. Cunha, in preparation). The companion repositories cover higher education
([higher-education-analysis](https://github.com/Caioalexnes/higher-education-analysis)) and health
([Analysis-of-the-Brazilian-Unified-Health-System-SUS-](https://github.com/Caioalexnes/Analysis-of-the-Brazilian-Unified-Health-System-SUS-)).

The repository does three things:

1. It recomputes, from public data, the relation between spending per student and the Ideb of
   Brazil's municipal school networks reported by Todos Pela Educação (2025), *Relação entre
   investimento por aluno e qualidade do ensino: análises iniciais*, and adds a control for the
   socioeconomic level of the students measured by Inep.
2. It reproduces the arithmetic of the essay's comparison between municipal network spending per
   student and private school tuition (taxes, school meals and transport).
3. It describes the municipal networks with an Ideb of the early grades below 4 or above 8 in 2023
   and uses the Enem as an outside check on the Ideb of Ceará, where part of the municipal share of
   the ICMS is distributed by an education index.
4. It extends the series to 2025 and tests whether the larger 2025 coefficient measures an effect of
   money or money going to networks that were already doing well.
5. It compares public and private schools in the Saeb 2023, net of the students' socioeconomic level.
6. It compares literacy at the end of the 2nd grade in Ceará as measured by the state's own test and by
   the federal Saeb.
7. It compares, state by state, what municipal networks spend per student with private tuition net of
   taxes, and the Saeb scores of private and public students of the same socioeconomic level; and it
   tests whether Ceará's advantage is regional or confined to its public network.
8. It does the same comparison for ensino médio, run by the state networks.
9. It assembles the data of the federal VAAT complementation of the Fundeb (2021 to 2025) and holds the
   pre-analysis plan of a study of its effects on spending, school inputs and learning (`pap/`).

All data are public.

## Main results

Spending per student of the municipal network (2023 reais) and the Ideb of the network's early
grades (5th grade, *anos iniciais*), one observation per municipality. Coefficients are Ideb points
per R$ 1,000 per student per year, with heteroskedasticity-robust standard errors.

| Year | Municipalities | Without controls | With the students' socioeconomic level (INSE) | Todos Pela Educação, without controls |
|---|---|---|---|---|
| 2017 | 5,165 | 0.166 (0.005) | 0.025 (0.004) | 0.16 |
| 2019 | 5,110 | 0.131 (0.005) | 0.012 (0.004) | 0.12 |
| 2023 | 5,229 | 0.053 (0.013) | 0.006 (0.003) | 0.06 |
| 2025 | 5,261 | 0.052 (0.004) | 0.020 (0.003) | |

For the late grades (9th grade, *anos finais*) the coefficients without controls are 0.137, 0.087 and
0.032, against 0.13, 0.08 and 0.05 in Todos Pela Educação; with the INSE, the 2023 coefficient is
0.001 (0.002), and the 2025 coefficients are 0.045 and 0.022 (0.004). The enrollment-weighted mean
spending per student in 2023 is R$ 12,589, against R$ 12,460 in Todos Pela Educação; in 2025 it is
R$ 14,405 (2023 reais), 66% above 2017. Within each band of R$ 2,000 of spending per student, the Ideb of the
early grades varies by about 2 points between the 10th and the 90th percentile, while the mean of the
highest-spending band (above R$ 20,000, mean 6.31) is about 1 point above that of the lowest
(below R$ 8,000, mean 5.28). See `results/03_regressoes.csv` and `results/03_faixas.csv`.

### 2025: the coefficient rises, but money also follows results

The INSE of the 2025 Saeb had not been released in November 2026, so the 2023 edition is used for
2025. The lag does not explain the rise: using the 2019 INSE in 2023 gives 0.009 instead of 0.006.
The 2025 coefficient comes from the Saeb scores, not from approval rates, and it does not depend on
the networks with implausible scores: without Ceará, Alagoas and the 57 networks with a 5th-grade
mathematics mean above 300 in any year, it is 0.018; by median regression, 0.016.

It does not measure an effect of money, though. Holding the 2023 spending and the INSE fixed, the
2025 spending is associated with the Ideb of 2023, measured before the money arrived, almost as much
as with the Ideb of 2025 (0.039 and 0.044 per R$ 1,000); from 2019 to 2023 the pattern is the same
(0.028 for the 2019 Ideb, 0.015 for the 2023 Ideb). Part of this is by design: since Constitutional
Amendment 108 (2020) part of the municipal ICMS is distributed by learning indicators, and the Fundeb
has a part paid by results (complementação VAAR), R$ 5.1 billion in 2025 for 2,833 municipalities.
The VAAR alone is too small to explain it (about R$ 370 per student, 2.5% of spending; spending net of
VAAR gives 0.019). Between 2023 and 2025, spending per student rose R$ 3.2 thousand in the fifth of
networks with the poorest students and R$ 1.3 thousand in the richest fifth, and the Ideb rose 0.57
and 0.22 points. In 2025, 31 municipal networks had a 5th-grade mathematics mean above 320 (none in
2019), 23 of them in Ceará; the national mean of private schools was 254. See
`results/08_resultados.csv`, `results/08_notas_altas.csv` and `results/08_vaar_2025.csv`.

### Networks below 4 and above 8

In 2023, 49 of the 5,229 municipal networks had an Ideb of the early grades above 8 and 106 below 4.
Of the 49, 36 are in the Northeast (24 in Ceará and 9 in Alagoas); of the 106, 103 are in the North
and the Northeast. Both groups have a lower IDHM (medians 0.61 and 0.56, against 0.67 for all
networks) and a lower socioeconomic level of the students (Inse medians 4.38 and 4.32, against 4.92),
and spend less per student (medians of R$ 10,555 and R$ 10,046, against R$ 12,657). In Ceará, 88% of
the networks approve every student in the early grades, against 41% in the South, Southeast and
Centre-West. See `results/06_resumo.csv`, `results/06_extremos.csv` and `results/06_aprovacao.csv`.

### The Enem as an outside check

Among students finishing public high school in 2023, Ceará ranks 21st of 27 states on the simple mean
of the Enem and 6th on the mean of the best students up to 25% of the 3rd-year enrollment, because
78% of its 3rd-year students take the exam, against 34% in São Paulo (`results/07_enem_uf.csv`).
Following the same generation across municipalities: outside Ceará, the municipalities in the top 5%
of the 2015 Ideb of the early grades stand, in 2023, at the 79th percentile of the Enem (median); in
Ceará, at the 46th. In the 9th-grade Saeb of 2019, which counts for the Ideb, the advantage of
Ceará's top networks still shows (`results/07_enem_quintis.csv`, `results/07_enem_topo.csv`).

### Public and private schools in the Saeb 2023

Difference between private and public students in the Saeb 2023, in points of the Saeb scale
(student standard deviation of about 53 points), from the student microdata with Inep's sampling
weights; standard errors clustered by school. The raw means match Inep's release (5th grade
mathematics: 218.3 public, 254.3 private).

| Mathematics | 5th grade | 9th grade | Ensino médio |
|---|---|---|---|
| No control | 34.6 (1.1) | 44.7 (1.5) | 50.1 (3.4) |
| Student's INSE | 18.7 (0.9) | 31.0 (1.2) | 39.1 (2.8) |
| Also the school's mean INSE | 2.4 (0.8) | 17.1 (1.1) | 25.6 (2.2) |
| Also state x location fixed effects | 0.2 (1.2) | 9.1 (1.4) | 11.6 (2.0) |

In Portuguese the last row is 2.2, 4.4 and 4.5. These are not causal estimates, and the selection
biases go both ways: families who pay for school are likely more motivated in ways the INSE does not
measure; the public side includes federal and military schools that select students (the Saeb only
identifies public and private schools); in ensino médio more of the weaker public students have
already left school; and the school's mean INSE also removes the peer group, which is part of what
a private school offers. See `results/09_publica_privada.csv`, `results/09_medias.csv` and
`results/09_por_nivel_inse.csv`.

### Literacy in Ceará: the state test and the federal Saeb

The Indicador Criança Alfabetizada (MEC) is built from each state's own 2nd-grade test; in Ceará, the
SPAECE-Alfa, which also carries 40% of the education index that distributes the municipal ICMS
(Decreto estadual 35.087/2022). By that indicator, 84.5% of Ceará's public-school children were
literate at the end of the 2nd grade in 2023, against 56% in Brazil (press reports of the MEC
release). In the federal Saeb 2023, which tested a sample of 2nd-grade students, the share at or above
the national standard (743 points) is 72.1% in Ceará (standard error 5.2; 646 students in 27 public
schools), still the highest of all states, and 49.3% in Brazil; both match Inep's release. The gap
between the two measures is 12 points in Ceará and 7 in Brazil. Inep advises against comparing
states with this sample. Of the nine Ceará municipalities reported with 100% of children literate in
2024, five are among the 21 Ceará municipal networks with a 5th-grade Ideb of 9.5 or more in 2025.
In 2023 the median Ceará municipal network spent R$ 10,093 per student, against R$ 12,879 in Brazil,
R$ 13,737 in Paraná, R$ 14,973 in Santa Catarina and R$ 16,028 in São Paulo (2023 reais). See
`results/10_alfabetizacao_saeb2023.csv` and `results/10_ceara.csv`.

### Cost and performance by state, and whether Ceará's advantage is regional

Within each state, public and private schools pay the same rents and compete for the same teachers, so
comparing them inside the state removes differences in the cost of living. In 2025, in every one of the
26 states with municipal networks, the network spent more per student than the mean private tuition net
of taxes on revenue and profit (7.5% to 19.5%, as in script 04; tuition weighted by the share of
early-childhood enrollments): from 1.8 to 2.2 times on the mean of the states, from 1.2 to 1.5 in Rio
Grande do Sul, from 2.1 to 2.5 in Ceará and from 2.8 to 3.4 in Paraíba. Comparing students of the same
INSE in the Saeb 2023, private students are ahead in mathematics in every state except Ceará in the 5th
grade: on the mean of the states, 23 points in the 5th grade and 32 in the 9th (Ceará: 1 and 12).
Relative to local earnings (PNAD Contínua, IBGE table 5436), Ceará's networks spent 5.2 months of the
mean monthly earnings per student in 2023, against 4.6 in São Paulo and 4.4 in Paraná and Santa
Catarina. Ceará's advantage is confined to the public network: at the same student INSE, Ceará's public
students score 24 (5th grade) and 22 (9th grade) points above public students in the rest of Brazil, and
its private students 5 points below private students elsewhere (0 and 4 with the school's INSE); in the
2nd-grade literacy sample, 72% of Ceará's public students and 62% of its private students are literate,
against 37.5% and 69.7% in the rest of the Northeast. See `results/11_estados.csv`, `results/11_ceara.csv`,
`results/11_tabela_estados.tex` and `results/11_fig_custo_desempenho.pdf`.

### Ensino médio: state networks

The state accounts do not isolate ensino médio reliably: by the subfunction Ensino Médio (362), spending per
ensino médio student would range from zero (Alagoas) and R$ 0.7 thousand (Paraná) to R$ 25 thousand (Mato
Grosso do Sul), because several states book almost everything under 368 (Educação Básica). Script 12 therefore
does not allocate spending by stage: it divides the spending of each state network (function 12 minus
subfunctions 363 and 364) by its basic-education enrollments and compares it with private tuition weighted by
the network's own mix of ensino fundamental and médio. On the mean of the states the network spends 1.6 to 1.9
times the tuition net of taxes; the range is entirely above 1 in 23 states, around 1 in Rio Grande do Sul, Santa
Catarina and Rio de Janeiro, and below 1 in Minas Gerais. In every state private students are ahead at the end
of ensino médio (Saeb 2023, same student INSE), by 20 to 58 points, 36 on the mean; Minas Gerais, where the
public network is cheaper, has the largest gap. In Ceará, 97% of the state network's students are in ensino
médio. See `results/12_medio.csv`, `results/12_tabela_medio.tex` and `results/12_fig_medio.pdf`.

## Pre-analysis plan: the VAAT complementation

`pap/vaat_pap.tex` (and its PDF) pre-specifies the causal analysis of the VAAT complementation of the
Fundeb: since 2021 the Union tops up every school network whose resources per weighted student fall
below a national minimum. The main design is a difference-in-differences with a continuous dose, the
complementation that the legal formula predicts from the 2021 VAAT of each network, which uses 2019
revenues; a comparison between the municipal and the state network of the same municipality; and a
regression kink at the 2021 threshold for spending. The plan was written before any outcome was
related to the treatment. Scripts 13 and 14 reproduce every number in it and use no outcome data in
relation to the dose. The outcome regressions will be added only after the plan is deposited.

The 2021 VAAT of the 5,234 networks habilitated by mid-2021 comes from the annex of the Câmara's
Estudo Técnico 15/2021, which reproduces Portarias Interministeriais 3/2021 and 4/2021. For the 1,422
recipients that are also in the official December 2021 list (Portaria 10/2021), the two sources agree
to within 0.024%. Another 105 recipients were habilitated later and are kept apart.

## Scripts (`code/`)

| Script | What it does | Output |
|---|---|---|
| `00_download.py` | Downloads the Inep files and the IPCA (see the note on Inep's certificate below) | `data/` |
| `01_siconfi_dca.py` | Downloads, for every municipality, the expenditure by function of the Declaração de Contas Anuais (DCA, Anexo I-E) from the Siconfi API of the Tesouro Nacional, keeping function 12 (Educação), its subfunctions and subfunction 847 | `data/siconfi/dca_<year>.csv` |
| `02_matriculas.py` | Enrollments of each municipal network in the Censo Escolar: basic-education enrollments of municipal schools in activity, plus early-childhood enrollments of private schools under agreement with the municipality | `results/02_matriculas.csv` |
| `03_gasto_ideb.py` | Spending per student, Ideb and INSE by municipality; regressions with and without the INSE; Ideb by band of spending | `results/03_base_municipios.csv`, `results/03_regressoes.csv`, `results/03_faixas.csv` |
| `04_custo_escola.py` | Arithmetic of the table "O que sobra para ensinar" (municipal spending versus private tuition after taxes) | `results/04_custo_escola.csv` |
| `05_figura_ideb.py` | pgfplots code of the essay's figure on the Ideb by band of spending, 5th and 9th grades, 2023 | `results/05_figura_ideb.tex` |
| `06_extremos.py` | Profile of the networks with an Ideb below 4 or above 8 (region, population, IDHM, Inse, spending, approval) and two figures of the essay | `results/06_*.csv`, `results/06_fig_*.pdf` |
| `07_enem.py` | Enem 2023 by state and by municipality of the school, compared with the 2015 Ideb of the municipal network and its 2019 9th-grade Saeb; figure of the essay | `results/07_*.csv`, `results/07_fig_enem.pdf` |
| `08_atualizacao_2025.py` | 2025 checks: lagged INSE, spending and Ideb change by INSE fifth, placebo regressions, samples without implausible scores, median regression, VAAR of 2025, networks with very high Saeb scores | `results/08_*.csv` |
| `09_publica_privada.py` | Public versus private schools in the Saeb 2023, with and without the INSE of the student and of the school | `results/09_*.csv` |
| `10_alfabetizacao.py` | Literacy at the end of the 2nd grade in the federal Saeb 2023 by state, Ceará's networks with very high Ideb, and median spending by state | `results/10_*.csv` |
| `11_custo_desempenho_uf.py` | Cost (municipal spending versus private tuition net of taxes) and Saeb performance by state, spending in months of local earnings, and the test of a regional effect in Ceará; table and figure of the essay | `results/11_*` |
| `12_ensino_medio.py` | Ensino médio: spending per student of the state networks versus private tuition weighted by the network's stage mix, and the Saeb at the end of ensino médio; table and figure of the essay | `results/12_*` |
| `13_vaat.py` | VAAT complementation, 2021 to 2025: the 2021 VAAT of every habilitated network, the recipients and amounts of each year, the validation against the official 2021 list, the position relative to the 2021 threshold, the money received and the dose predicted by the formula, and diagnostics that use no outcome data | `results/13_*` |
| `14_poder.py` | Power calculations of the pre-analysis plan, from pre-2019 outcome changes and the dose, without relating them | `results/14_*` |

Run them in order from `code/` with Python 3 (pandas, numpy, scipy, openpyxl and matplotlib; scripts 08
and 13 also need `pdftotext`, from poppler):

```
python 00_download.py
python 01_siconfi_dca.py 2017 2019 2023 2025
python 02_matriculas.py 2017 2019 2023 2025
python 03_gasto_ideb.py
python 04_custo_escola.py
python 05_figura_ideb.py
python 06_extremos.py
python 07_enem.py
python 08_atualizacao_2025.py
python 09_publica_privada.py
python 10_alfabetizacao.py
python 11_custo_desempenho_uf.py
python 12_ensino_medio.py
python 13_vaat.py
python 14_poder.py
```

Script 01 makes one API call per municipality and year (about 22,000 calls for four years; a few
minutes per year with the 12 parallel requests it uses) and can be interrupted and resumed. Its extracts for
2017, 2019, 2023 and 2025 are included in `data/siconfi/`, so scripts 02 to 08 can be run without it.
Municipalities may correct their DCA after the deadline, so a new download may differ slightly.

## Definitions

- **Spending**: committed expenditure (*despesas empenhadas*) in function 12 (Educação), minus
  subfunction 364 (Ensino Superior), plus subfunction 847 (Transferências para a Educação Básica)
  recorded outside function 12, as described by Todos Pela Educação (2025, p. 4). Subfunction 847
  outside function 12 appears in only three municipalities in 2023. Todos Pela Educação does not say
  whether it excluded anything else (such as pensions of retired staff); nothing else is excluded here.
- **Enrollments**: `QT_MAT_BAS` of municipal schools (`TP_DEPENDENCIA` = 3) in activity, plus
  `QT_MAT_INF` of private schools under agreement (*convênio* or *parceria*) with the municipal
  government, alone or with the state. From 2025 the Censo Escolar puts the enrollment counts in a
  separate table (`Tabela_Matricula`), joined to the school table by school code.
- **Prices**: 2023 reais, deflated by the annual mean of the IPCA (IBGE, table 1737). Todos Pela
  Educação states that it uses the IPCA at 2023 values but not how the index is averaged.
- **Ideb**: observed Ideb of the municipal network (`REDE` = Municipal) in the Inep file released
  in 2026 with the series from 2005 to 2025.
- **INSE**: mean Indicador de Nível Socioeconômico of the municipal network's students (Saeb), all
  locations (`TP_TIPO_REDE` = 3, `TP_LOCALIZACAO` = 0). There is no municipal INSE for 2017; the
  2019 edition is used for 2017 and 2019, and the 2023 edition for 2023 and 2025 (the 2025 edition
  had not been released in November 2026). The 2023 file repeats each
  stratum on several rows; one row per municipality is kept.
- **Samples**: all municipalities with spending, enrollments and an Ideb. A second sample drops the
  1% tails of spending per student, where very small enrollment counts or accounting errors produce
  implausible values; it gives larger coefficients without controls in 2023 (0.081) and the same
  conclusion with the INSE (0.010).
- **School cost table** (script 04): only taxes on revenue and profit are deducted from private tuition,
  from 7.5% (Simples Nacional, Anexo III, revenue of R$ 1.26 million, without the employer social
  security contribution, 43.4% of the payment) to 19.5% (lucro presumido, ISS of 5%). The employer
  contribution on payroll is left on both sides, because it is also part of the public spending. The
  municipal spending of 2023 is put in 2025 reais (IPCA, annual means), the year of the tuition survey.
- **Approving every student**: flow indicator of the Ideb (`VL_INDICADOR_REND_2023`) of 1.00.
- **VAAR**: complementação da União-VAAR of 2025 made available to each municipality during the year
  (Anexo III of Portaria Interministerial MEC/MF nº 5/2026, column B), divided by the enrollments of
  script 02 and put in 2023 reais.
- **Implausible scores**: municipal networks with a 5th-grade Saeb mathematics mean above 300 in
  2019, 2023 or 2025; the national mean of private schools was 254 in 2025.
- **IDHM**: 2010, from the Atlas do Desenvolvimento Humano (Ipeadata, series `ADH_IDHM`).
  **Population**: Censo 2022 (IBGE, table 4709).
- **Enem**: students finishing public high school in 2023 (`TP_ST_CONCLUSAO` = 2, `TP_ESCOLA` = 2)
  present on both days; the score is the mean of the four objective tests. Because the share of
  students who take the exam varies a lot, states and municipalities are compared by the mean of the
  best students up to a fixed share of the 3rd-year enrollment in public high schools (25%; 20% and
  30% as checks), from the Censo Escolar 2023. Only 64% of the students name the municipality of their
  school (90% in Ceará, 43% to 73% elsewhere); at the municipal level the share is scaled by that
  proportion in each state. Municipal sample: at least 50 students in the 3rd year, students naming
  the school at least a quarter of them, and an Ideb of the municipal network in 2015 (1,871
  municipalities, 181 in Ceará).

## Data

| File | Source |
|---|---|
| `data/siconfi/dca_estados_2025.csv` | Tesouro Nacional, Siconfi, DCA-Anexo I-E of the 26 states and the Distrito Federal, function 12, downloaded by script 12 in November 2026 |
| `data/siconfi/dca_<year>.csv` | Tesouro Nacional, Siconfi, API de dados abertos, `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca` (DCA-Anexo I-E), downloaded in November 2026 |
| `microdados_censo_escolar_<year>.zip` | Inep, Microdados do Censo Escolar da Educação Básica, `https://download.inep.gov.br/dados_abertos/` |
| `divulgacao_anos_{iniciais,finais}_municipios_2025.zip` | Inep, Ideb, resultados 2005-2025, `https://download.inep.gov.br/ideb/resultados/` |
| `INSE_2019_MUNICIPIOS.xlsx`, `INSE_2023_municipios.xlsx` | Inep, Indicador de Nível Socioeconômico, `https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/` |
| `ipca_1737.json` | IBGE, SIDRA, table 1737 (IPCA, número-índice), `https://apisidra.ibge.gov.br/` |
| `pop_censo2022.json` | IBGE, SIDRA, table 4709 (resident population, Censo 2022), `https://apisidra.ibge.gov.br/` |
| `pnad_5436.json` | IBGE, SIDRA, table 5436 (PNAD Contínua, mean monthly earnings by state), `https://apisidra.ibge.gov.br/` |
| `ipca_1737_2026.json` | IBGE, SIDRA, table 1737 (IPCA), January 2023 to October 2026, `https://apisidra.ibge.gov.br/` |
| Private tuition by state | Melhor Escola, mean monthly tuition by state, 2025, written in `code/11_custo_desempenho_uf.py` (`https://www.melhorescola.com.br/artigos/descubra-o-valor-medio-da-mensalidade-de-escolas-particulares-no-brasil`) |
| `idhm_ipeadata.json` | Ipea, Ipeadata, series ADH_IDHM (IDHM 2010, Atlas do Desenvolvimento Humano), `https://www.ipeadata.gov.br/api/` |
| `microdados_enem_2023.zip` | Inep, Microdados do Enem 2023, `https://download.inep.gov.br/microdados/` |
| `microdados_saeb_2023.zip` | Inep, Microdados do Saeb 2023 (student files of the 2nd, 5th and 9th grades and of ensino médio), `https://download.inep.gov.br/microdados/` |
| `divulgacao_brasil_ideb_2025.zip` | Inep, Ideb, resultados 2005-2025 for Brazil by network (national mean of private schools), `https://download.inep.gov.br/ideb/resultados/` |
| `data/fnde/portaria_interministerial_5_2026.pdf` | MEC/MF, Portaria Interministerial nº 5, de 29 de abril de 2026 (Fundeb annual adjustment of 2025, VAAF, VAAT and VAAR by government), FNDE site |
| `data/fnde/vaat/et15_2021.pdf` | Câmara dos Deputados, Consultoria de Orçamento, Estudo Técnico nº 15/2021 (C. R. Tanno, August 2021); its annex gives the 2021 VAAT, revenues and weighted enrollment of every habilitated network |
| `data/fnde/vaat/portaria_10_2021.pdf`, `portaria_6_2022.pdf` | Diário Oficial da União, Portarias Interministeriais nº 10/2021 and nº 6/2022 (Annex III: VAAT complementation by network), FNDE site |
| `data/fnde/vaat/anexo3_portaria_*.pdf` | FNDE, Annex III of the December portarias of 2023 (nº 7), 2024 (nº 13) and 2025 (nº 13) |
| `data/fnde/vaat/acerto_vaat_2023_portaria_7_2026.xlsx`, `ajuste_vaat_2024_portaria_3_2025.xlsx` | FNDE, adjustments of the VAAT complementation of 2023 and 2024 (Annex II) |

SHA-256 checksums of the files used are in `DATA_SHA256SUMS.txt`. The Inep files, the Portarias and the
Câmara study are not included because of their size; the VAAR extracted from the Portaria is in `results/08_vaar_2025.csv`.

**Inep's certificate.** `download.inep.gov.br` does not send the intermediate certificate of its TLS
chain, so command-line downloads fail certificate verification (browsers fetch the missing
certificate on their own). `certs/rnp_icpedu_gr46_ov_tls_ca_2025.pem` is that public intermediate
certificate (RNP ICPEdu GR46 OV TLS CA 2025, issued by GlobalSign Root R46, available at
`http://secure.globalsign.com/cacert/rnpicpedugr46ovtlsca2025.crt`); script 00 adds it to the usual
root certificates and keeps verification on. If the download fails in your environment, download the
files with a browser into `data/inep/`.

## Limits

The regressions describe associations across municipalities; they are not causal estimates. Since
2023 part of the money follows the indicators (ICMS by education indicators, VAAR), so the
association also runs from results to spending; the placebo regressions of script 08 show it. The INSE
measures the students who took the Saeb, not the whole network. Very high Ideb values in networks
with low socioeconomic level are concentrated in Ceará, which distributes 18% of the municipal share
of the ICMS by an education index (state law 14,023/2007); the essay discusses this policy and the
checks for manipulation. The Enem is taken at the end of high school, which is run by the state;
part of the difference in Ceará may come from the state high schools (some of which select students
by their grades) and not from the municipal networks. The correction for the students who do not name
their school assumes that, within a state, they do not differ from those who do.

## License

MIT (code). Data belong to their original publishers and are used under Brazil's open government data
policy (Decreto nº 8.777/2016).
