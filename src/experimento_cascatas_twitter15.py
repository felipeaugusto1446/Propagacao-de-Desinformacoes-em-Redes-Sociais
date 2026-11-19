"""
Cada cascata é uma árvore dirigida T = (V, E, t):

* V = usuários que participaram da cascata
* (u, v) ∈ E se v compartilhou o conteúdo a partir de u
* t(v) = atraso, em minutos, da primeira participação de v

Separamos o arquivo em três partes para facilitar
a compreensão dos códigos. A princípio iremos dividir
da seguinte forma:

1. Leitura dos dados do dataset e construção das árvores
2. As 4 métricas de cada cascata: 
    - tamanho;
    - profundidade;
    - ramificação;
    - velocidade.
3. Simulação de remoção de contas (centrais x aleatórias)
"""

from __future__ import annotations

import ast
import random
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

# 1. Leitura dos dados e construção das árvores
def carregar_rotulos(pasta_dataset: Path) -> dict[str, str]:
    rotulos = {}
    with open(Path(pasta_dataset) / "label.txt", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                rotulo, id_cascata = linha.split(":")
                rotulos[id_cascata] = rotulo
    return rotulos

def _ler_linhas(arquivo: Path):
    raiz, arestas = None, []
    with open(arquivo, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            pai, filho = linha.split("->")
            pai, filho = ast.literal_eval(pai), ast.literal_eval(filho)
            if pai[0].strip() == "ROOT":
                raiz = filho[0].strip()
                continue
            arestas.append((float(filho[2]), pai[0].strip(), filho[0].strip()))
    return raiz, arestas

def construir_arvore(arquivo: Path, rotulo: str | None = None) -> nx.DiGraph:
    arquivo = Path(arquivo)
    raiz, arestas = _ler_linhas(arquivo)
    if raiz is None:
        raiz = min(arestas)[1]

    arestas.sort()  # ordem temporal
    T = nx.DiGraph(id_cascata=arquivo.stem, rotulo=rotulo, raiz=raiz)
    T.add_node(raiz, t=0.0)

    for atraso, u, v in arestas:
        if u != v and v not in T and u in T:
            T.add_edge(u, v)
            T.nodes[v]["t"] = max(atraso, 0.0)
    return T

def carregar_cascatas(pasta_dataset: Path, classes=("false", "true")) -> dict[str, nx.DiGraph]:
    pasta_dataset = Path(pasta_dataset)
    rotulos = carregar_rotulos(pasta_dataset)
    cascatas = {}
    for arquivo in sorted((pasta_dataset / "tree").glob("*.txt")):
        rotulo = rotulos.get(arquivo.stem)
        if rotulo in classes:
            cascatas[arquivo.stem] = construir_arvore(arquivo, rotulo)
    return cascatas

# 2. Métricas de cada cascata
def metricas_cascata(T: nx.DiGraph) -> dict:
    raiz = T.graph["raiz"]
    distancias = nx.single_source_shortest_path_length(T, raiz)
    repasses = [grau for _, grau in T.out_degree() if grau > 0]
    tempos = [T.nodes[v]["t"] for v in T if v != raiz]

    return {
        "id_cascata": T.graph["id_cascata"],
        "rotulo": T.graph["rotulo"],
        "tamanho": T.number_of_nodes(),
        "profundidade": max(distancias.values()),
        "ramificacao": float(np.mean(repasses)) if repasses else 0.0,
        "velocidade_min": float(np.median(tempos)) if tempos else 0.0,
    }

def tabela_metricas(cascatas: dict[str, nx.DiGraph]) -> pd.DataFrame:
    return pd.DataFrame([metricas_cascata(T) for T in cascatas.values()])

# 3. Remoção das contas centrais e aleatórias
def tamanho_galho(T: nx.DiGraph, removidos=()) -> dict:
    raiz = T.graph["raiz"]
    ordem = [v for v in nx.dfs_preorder_nodes(T, raiz)]
    removidos = set(removidos)
    alcancados = {raiz}
    for v in ordem[1:]:
        pai = next(T.predecessors(v))
        if pai in alcancados and v not in removidos:
            alcancados.add(v)
    galho = {v: 1 for v in alcancados}
    for v in reversed(ordem):
        if v in alcancados and v != raiz:
            galho[next(T.predecessors(v))] += galho[v]
    return galho

def alcance_apos_remocao(T: nx.DiGraph, removidos) -> int:
    return tamanho_galho(T, removidos)[T.graph["raiz"]]

def contas_centrais(T: nx.DiGraph, k: int) -> list:
    raiz = T.graph["raiz"]
    escolhidas = []
    for _ in range(k):
        galho = tamanho_galho(T, escolhidas)
        candidatas = {v: g for v, g in galho.items() if v != raiz}
        if not candidatas:
            break
        escolhidas.append(max(candidatas, key=candidatas.get))
    return escolhidas

def simular_remocao(cascatas: dict[str, nx.DiGraph], ks=(1, 3, 5),
                    repeticoes_aleatorias: int = 20, semente: int = 42) -> pd.DataFrame:
    sorteio = random.Random(semente)
    linhas = []
    for id_cascata, T in cascatas.items():
        raiz = T.graph["raiz"]
        n = T.number_of_nodes()
        outras = [v for v in T if v != raiz]
        centrais = contas_centrais(T, max(ks))

        for k in ks:
            perda_central = 1 - alcance_apos_remocao(T, centrais[:k]) / n

            perdas = [1 - alcance_apos_remocao(T, sorteio.sample(outras, min(k, len(outras)))) / n
                      for _ in range(repeticoes_aleatorias)]

            for estrategia, perda in [("centrais", perda_central), ("aleatorias", np.mean(perdas))]:
                linhas.append({
                    "id_cascata": id_cascata,
                    "rotulo": T.graph["rotulo"],
                    "k": k,
                    "estrategia": estrategia,
                    "perda_pct": 100 * perda
                })
    return pd.DataFrame(linhas)
