"""Download the public files used by the scripts into DADOS (default: ../data).

Inep's download server (download.inep.gov.br) does not send the intermediate certificate of its TLS
chain, so a plain download fails certificate verification. The intermediate certificate, issued by
GlobalSign to RNP, is public and included in certs/; it is added to the usual root certificates, and
verification stays on. Siconfi spending is downloaded by script 01; the IPCA and the population of
the 2022 Census come from IBGE's API and the IDHM from Ipea's. The Fundeb annual adjustment of 2025
(Portaria Interministerial MEC/MF nº 5/2026, with the VAAR by municipality) comes from the FNDE site.
Usage: python 00_download.py
"""
import os, ssl, urllib.request
from config import DADOS

AQUI = os.path.dirname(os.path.abspath(__file__))
INEP = 'https://download.inep.gov.br/'
ARQUIVOS = {
    'inep/microdados_censo_escolar_2017.zip': INEP + 'dados_abertos/microdados_censo_escolar_2017.zip',
    'inep/microdados_censo_escolar_2019.zip': INEP + 'dados_abertos/microdados_censo_escolar_2019.zip',
    'inep/microdados_censo_escolar_2023.zip': INEP + 'dados_abertos/microdados_censo_escolar_2023.zip',
    # the 2025 file name on Inep's server ends with an underscore
    'inep/microdados_censo_escolar_2025.zip': INEP + 'dados_abertos/microdados_censo_escolar_2025_.zip',
    'inep/divulgacao_anos_iniciais_municipios_2025.zip': INEP + 'ideb/resultados/divulgacao_anos_iniciais_municipios_2025.zip',
    'inep/divulgacao_anos_finais_municipios_2025.zip': INEP + 'ideb/resultados/divulgacao_anos_finais_municipios_2025.zip',
    'inep/divulgacao_brasil_ideb_2025.zip': INEP + 'ideb/resultados/divulgacao_brasil_ideb_2025.zip',
    'inep/INSE_2019_MUNICIPIOS.xlsx': INEP + 'informacoes_estatisticas/indicadores_educacionais/2019/nivel_socioeconomico/INSE_2019_MUNICIPIOS.xlsx',
    'inep/INSE_2023_municipios.xlsx': INEP + 'informacoes_estatisticas/indicadores_educacionais/2023/nivel_socioeconomico/INSE_2023_municipios.xlsx',
    'inep/microdados_enem_2023.zip': INEP + 'microdados/microdados_enem_2023.zip',
    'inep/microdados_saeb_2023.zip': INEP + 'microdados/microdados_saeb_2023.zip',
    'ipca_1737.json': 'https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/201612-202512',
    'pop_censo2022.json': 'https://apisidra.ibge.gov.br/values/t/4709/n6/all/v/93/p/2022',
    'fnde/portaria_interministerial_5_2026.pdf': 'https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/'
        'fundeb/legislacao/2026/portaria-interministerial-mec-mf-no-5-de-29-de-abril-de-2026/@@download/file',
    'idhm_ipeadata.json': "https://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='ADH_IDHM')",
}

if __name__ == '__main__':
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(os.path.join(AQUI, '..', 'certs', 'rnp_icpedu_gr46_ov_tls_ca_2025.pem'))
    for destino, url in ARQUIVOS.items():
        caminho = os.path.join(DADOS, destino)
        if os.path.exists(caminho):
            continue
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with urllib.request.urlopen(url, context=ctx, timeout=600) as r, open(caminho, 'wb') as f:
            f.write(r.read())
        print('ok', destino)
    for z in ('divulgacao_anos_iniciais_municipios_2025', 'divulgacao_anos_finais_municipios_2025', 'divulgacao_brasil_ideb_2025'):
        import zipfile
        zipfile.ZipFile(os.path.join(DADOS, 'inep', z + '.zip')).extractall(os.path.join(DADOS, 'inep'))
