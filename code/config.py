"""Paths. Raw files are read from DADOS (default: ../data); outputs go to ../results."""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.environ.get('DADOS', os.path.join(AQUI, '..', 'data'))
RES = os.path.join(AQUI, '..', 'results')
os.makedirs(RES, exist_ok=True)
