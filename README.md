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

For the late grades (9th grade, *anos finais*) the coefficients without controls are 0.137, 0.087 and
0.032, against 0.13, 0.08 and 0.05 in Todos Pela Educação; with the INSE, the 2023 coefficient is
0.001 (0.002). The enrollment-weighted mean spending per student in 2023 is R$ 12,589, against
R$ 12,460 in Todos Pela Educação. Within each band of R$ 2,000 of spending per student, the Ideb of the
early grades varies by about 2 points between the 10th and the 90th percentile, while the mean of the
highest-spending band (above R$ 20,000, mean 6.31) is about 1 point above that of the lowest
(below R$ 8,000, mean 5.28). See `results/03_regressoes.csv` and `results/03_faixas.csv`.

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

## Scripts (`code/`)

| Script | What it does | Output |
|---|---|---|
| `00_download.py` | Downloads the Inep files and the IPCA (see the note on Inep's certificate below) | `data/` |
| `01_siconfi_dca.py` | Downloads, for every municipality, the expenditure by function of the Declaração de Contas Anuais (DCA, Anexo I-E) from the Siconfi API of the Tesouro Nacional, keeping function 12 (Educação), its subfunctions and subfunction 847 | `data/siconfi/dca_<year>.csv` |
| `02_matriculas.py` | Enrollments of each municipal network in the Censo Escolar: basic-education enrollments of municipal schools in activity, plus early-childhood enrollments of private schools under agreement with the municipality | `results/02_matriculas.csv` |
| `03_gasto_ideb.py` | Spending per student, Ideb and INSE by municipality; regressions with and without the INSE; Ideb by band of spending | `results/03_base_municipios.csv`, `results/03_regressoes.csv`, `results/03_faixas.csv` |
| `04_custo_escola.py` | Arithmetic of the table "O que sobra para ensinar" (municipal spending versus private tuition after taxes) | `results/04_custo_escola.csv` |
| `05_figura_ideb.py` | pgfplots code of the essay's figure on the Ideb by band of spending | `results/05_figura_ideb.tex` |
| `06_extremos.py` | Profile of the networks with an Ideb below 4 or above 8 (region, population, IDHM, Inse, spending, approval) and two figures of the essay | `results/06_*.csv`, `results/06_fig_*.pdf` |
| `07_enem.py` | Enem 2023 by state and by municipality of the school, compared with the 2015 Ideb of the municipal network and its 2019 9th-grade Saeb; figure of the essay | `results/07_*.csv`, `results/07_fig_enem.pdf` |

Run them in order from `code/` with Python 3 (pandas, numpy, openpyxl and matplotlib):

```
python 00_download.py
python 01_siconfi_dca.py 2017 2019 2023
python 02_matriculas.py 2017 2019 2023
python 03_gasto_ideb.py
python 04_custo_escola.py
python 05_figura_ideb.py
python 06_extremos.py
python 07_enem.py
```

Script 01 makes one API call per municipality and year (about 17,000 calls for three years; about seven
minutes per year with the 12 parallel requests it uses) and can be interrupted and resumed. Its extracts for
2017, 2019 and 2023 are included in `data/siconfi/`, so scripts 02 to 05 can be run without it.
Municipalities may correct their DCA after the deadline, so a new download may differ slightly.

## Definitions

- **Spending**: committed expenditure (*despesas empenhadas*) in function 12 (Educação), minus
  subfunction 364 (Ensino Superior), plus subfunction 847 (Transferências para a Educação Básica)
  recorded outside function 12, as described by Todos Pela Educação (2025, p. 4). Subfunction 847
  outside function 12 appears in only three municipalities in 2023. Todos Pela Educação does not say
  whether it excluded anything else (such as pensions of retired staff); nothing else is excluded here.
- **Enrollments**: `QT_MAT_BAS` of municipal schools (`TP_DEPENDENCIA` = 3) in activity, plus
  `QT_MAT_INF` of private schools under agreement (*convênio* or *parceria*) with the municipal
  government, alone or with the state.
- **Prices**: 2023 reais, deflated by the annual mean of the IPCA (IBGE, table 1737). Todos Pela
  Educação states that it uses the IPCA at 2023 values but not how the index is averaged.
- **Ideb**: observed Ideb of the municipal network (`REDE` = Municipal) in the Inep file released
  in 2026 with the series from 2005 to 2025.
- **INSE**: mean Indicador de Nível Socioeconômico of the municipal network's students (Saeb), all
  locations (`TP_TIPO_REDE` = 3, `TP_LOCALIZACAO` = 0). There is no municipal INSE for 2017; the
  2019 edition is used for 2017 and 2019, and the 2023 edition for 2023. The 2023 file repeats each
  stratum on several rows; one row per municipality is kept.
- **Samples**: all municipalities with spending, enrollments and an Ideb. A second sample drops the
  1% tails of spending per student, where very small enrollment counts or accounting errors produce
  implausible values; it gives larger coefficients without controls in 2023 (0.081) and the same
  conclusion with the INSE (0.010).
- **Approving every student**: flow indicator of the Ideb (`VL_INDICADOR_REND_2023`) of 1.00.
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
| `data/siconfi/dca_<year>.csv` | Tesouro Nacional, Siconfi, API de dados abertos, `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca` (DCA-Anexo I-E), downloaded in November 2026 |
| `microdados_censo_escolar_<year>.zip` | Inep, Microdados do Censo Escolar da Educação Básica, `https://download.inep.gov.br/dados_abertos/` |
| `divulgacao_anos_{iniciais,finais}_municipios_2025.zip` | Inep, Ideb, resultados 2005-2025, `https://download.inep.gov.br/ideb/resultados/` |
| `INSE_2019_MUNICIPIOS.xlsx`, `INSE_2023_municipios.xlsx` | Inep, Indicador de Nível Socioeconômico, `https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/` |
| `ipca_1737.json` | IBGE, SIDRA, table 1737 (IPCA, número-índice), `https://apisidra.ibge.gov.br/` |
| `pop_censo2022.json` | IBGE, SIDRA, table 4709 (resident population, Censo 2022), `https://apisidra.ibge.gov.br/` |
| `idhm_ipeadata.json` | Ipea, Ipeadata, series ADH_IDHM (IDHM 2010, Atlas do Desenvolvimento Humano), `https://www.ipeadata.gov.br/api/` |
| `microdados_enem_2023.zip` | Inep, Microdados do Enem 2023, `https://download.inep.gov.br/microdados/` |

SHA-256 checksums of the files used are in `DATA_SHA256SUMS.txt`. The Inep files are not included
because of their size.

**Inep's certificate.** `download.inep.gov.br` does not send the intermediate certificate of its TLS
chain, so command-line downloads fail certificate verification (browsers fetch the missing
certificate on their own). `certs/rnp_icpedu_gr46_ov_tls_ca_2025.pem` is that public intermediate
certificate (RNP ICPEdu GR46 OV TLS CA 2025, issued by GlobalSign Root R46, available at
`http://secure.globalsign.com/cacert/rnpicpedugr46ovtlsca2025.crt`); script 00 adds it to the usual
root certificates and keeps verification on. If the download fails in your environment, download the
files with a browser into `data/inep/`.

## Limits

The regressions describe associations across municipalities; they are not causal estimates. The INSE
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
