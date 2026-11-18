"""Download municipal expenditure by function (DCA, Anexo I-E) from the Siconfi API (Tesouro Nacional).

For each municipality and year, keeps the committed expenditure ("Despesas Empenhadas") of
function 12 (Educação) and its subfunctions, of subfunction 847 (Transferências para a Educação
Básica, any function) and the total expenditure. One call per municipality and year; the script
can be interrupted and resumed (finished municipalities are skipped).
Usage: python 01_siconfi_dca.py 2017 2019 2023 2025
Output: data/siconfi/dca_<year>.csv (cod_ibge;conta;valor;populacao) and data/siconfi/done_<year>.txt
"""
import csv, json, os, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

BASE = 'https://apidatalake.tesouro.gov.br/ords/siconfi/tt'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'siconfi')
os.makedirs(OUT, exist_ok=True)


def get(url, tries=6):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(2 ** k)


def municipios():
    path = os.path.join(OUT, 'entes.json')
    if not os.path.exists(path):
        json.dump(get(BASE + '/entes'), open(path, 'w'))
    return sorted(e['cod_ibge'] for e in json.load(open(path))['items'] if e['esfera'] == 'M')


def keep(item):
    c = item['conta']
    return item['coluna'] == 'Despesas Empenhadas' and (
        c.startswith('12 ') or c.startswith('12.') or '.847' in c or item['cod_conta'] == 'TotalDespesas' and c.startswith('Despesas Exceto'))


def baixa(ano):
    done_path, csv_path = os.path.join(OUT, f'done_{ano}.txt'), os.path.join(OUT, f'dca_{ano}.csv')
    done = set(open(done_path).read().split()) if os.path.exists(done_path) else set()
    todo = [m for m in municipios() if str(m) not in done]
    lock = Lock()
    new = not os.path.exists(csv_path)
    fcsv, fdone = open(csv_path, 'a', newline=''), open(done_path, 'a')
    w = csv.writer(fcsv, delimiter=';')
    if new:
        w.writerow(['cod_ibge', 'conta', 'valor', 'populacao'])
    q = urllib.parse.urlencode({'an_exercicio': ano, 'no_anexo': 'DCA-Anexo I-E'})
    def one(m):
        items, off = [], 0
        while True:
            d = get(f'{BASE}/dca?{q}&id_ente={m}&offset={off}')
            items += d['items']
            if not d.get('hasMore'):
                return m, items
            off += d['limit']
    t0, n = time.time(), 0
    with ThreadPoolExecutor(12) as ex:
        for fut in as_completed([ex.submit(one, m) for m in todo]):
            m, items = fut.result()
            with lock:
                for i in items:
                    if keep(i):
                        w.writerow([m, i['conta'], i['valor'], i.get('populacao')])
                fdone.write(f'{m}\n'); n += 1
                if n % 500 == 0:
                    fcsv.flush(); fdone.flush(); print(ano, n, len(todo), f'{time.time()-t0:.0f}s', flush=True)
    fcsv.close(); fdone.close()
    # threads finish in any order: sort the file so that the same data always give the same file
    rows = list(csv.reader(open(csv_path, newline=''), delimiter=';'))
    rows = [rows[0]] + sorted(rows[1:], key=lambda r: (int(r[0]), r[1], float(r[2])))
    csv.writer(open(csv_path, 'w', newline=''), delimiter=';').writerows(rows)
    print(ano, 'complete', n, flush=True)


if __name__ == '__main__':
    for a in sys.argv[1:]:
        baixa(int(a))
