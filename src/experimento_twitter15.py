"""
Experimento com o Twitter15: estrutura das cascatas e remoção de contas.

Cada cascata é uma árvore direcionada T = (V, E, t):
V são os usuários que participaram da cascata;
(u, v) pertence a E se v compartilhou o conteúdo a partir de u;
t(v) é o atraso, em minutos, da primeira participação de v.

O arquivo está dividido em três partes:
1. Leitura dos dados e construção das árvores.
2. As 4 métricas de cada cascata: tamanho, profundidade, ramificação e velocidade.
3. Simulação de remoção de contas, centrais e aleatórias.

Diferenças em relação ao fluxo principal (src/carregamento_twitter.py):
aqui o vértice é só o usuário (e não usuário e tweet), usa-se apenas o
Twitter15 e a conta central é a que tem o maior galho, escolhida de forma
gulosa, uma de cada vez.

Fonte do dataset:
Ma, J., Gao, W., Wong, K.-F. (2017). Detect Rumors in Microblog Posts Using
Propagation Structure via Kernel Learning. ACL 2017.
https://doi.org/10.18653/v1/P17-1066
"""
import ast
import random
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd


# 1. leitura dos dados e construção das árvores

def carregar_rotulos(pasta_dataset):
    """Lê o label.txt e devolve o rótulo de cada cascata."""
    rotulos = {}
    with open(Path(pasta_dataset) / "label.txt", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                # cada linha tem o formato rotulo:id
                rotulo, id_cascata = linha.split(":")
                rotulos[id_cascata] = rotulo
    return rotulos


def _ler_linhas(arquivo):
    """Lê um arquivo de árvore e devolve a raiz e a lista de arestas com atraso."""
    raiz, arestas = None, []
    with open(arquivo, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            pai, filho = linha.split("->")
            pai, filho = ast.literal_eval(pai), ast.literal_eval(filho)

            # a linha que sai de ROOT indica a conta que publicou primeiro
            if pai[0].strip() == "ROOT":
                raiz = filho[0].strip()
                continue
            arestas.append((float(filho[2]), pai[0].strip(), filho[0].strip()))
    return raiz, arestas


def construir_arvore(arquivo, rotulo=None):
    """Monta a árvore de uma cascata a partir do arquivo."""
    arquivo = Path(arquivo)
    raiz, arestas = _ler_linhas(arquivo)

    # sem linha ROOT, a raiz é o pai da aresta mais antiga
    if raiz is None:
        raiz = min(arestas)[1]

    # ordena as arestas pelo atraso para seguir a ordem do tempo
    arestas.sort()
    T = nx.DiGraph(id_cascata=arquivo.stem, rotulo=rotulo, raiz=raiz)
    T.add_node(raiz, t=0.0)

    # cada conta entra uma vez só, ligada à primeira conta de quem recebeu
    for atraso, u, v in arestas:
        if u != v and v not in T and u in T:
            T.add_edge(u, v)
            T.nodes[v]["t"] = max(atraso, 0.0)
    return T


def carregar_cascatas(pasta_dataset, classes=("false", "true")):
    """Monta as árvores das cascatas das classes escolhidas."""
    pasta_dataset = Path(pasta_dataset)
    rotulos = carregar_rotulos(pasta_dataset)
    cascatas = {}
    for arquivo in sorted((pasta_dataset / "tree").glob("*.txt")):
        rotulo = rotulos.get(arquivo.stem)
        if rotulo in classes:
            cascatas[arquivo.stem] = construir_arvore(arquivo, rotulo)
    return cascatas


# 2. métricas de cada cascata

def metricas_cascata(T):
    """Calcula tamanho, profundidade, ramificação e velocidade de uma cascata."""
    raiz = T.graph["raiz"]
    distancias = nx.single_source_shortest_path_length(T, raiz)

    # ramificação: média de repasses entre as contas que repassaram para alguém
    repasses = [grau for _, grau in T.out_degree() if grau > 0]
    tempos = [T.nodes[v]["t"] for v in T if v != raiz]

    return {
        "id_cascata": T.graph["id_cascata"],
        "rotulo": T.graph["rotulo"],
        "tamanho": T.number_of_nodes(),
        "profundidade": max(distancias.values()),
        "ramificacao": float(np.mean(repasses)) if repasses else 0.0,
        # velocidade: minutos até a cascata alcançar metade das contas
        "velocidade_min": float(np.median(tempos)) if tempos else 0.0,
    }


def tabela_metricas(cascatas):
    """Monta uma tabela com as métricas de todas as cascatas."""
    return pd.DataFrame([metricas_cascata(T) for T in cascatas.values()])


# 3. remoção das contas centrais e aleatórias

def tamanho_galho(T, removidos=()):
    """Calcula o tamanho do galho de cada conta que continua alcançada após as remoções."""
    raiz = T.graph["raiz"]
    ordem = [v for v in nx.dfs_preorder_nodes(T, raiz)]
    removidos = set(removidos)

    # uma conta só continua alcançada se o pai dela foi alcançado e ela não foi removida
    alcancados = {raiz}
    for v in ordem[1:]:
        pai = next(T.predecessors(v))
        if pai in alcancados and v not in removidos:
            alcancados.add(v)

    # soma o galho de baixo para cima, das folhas até a raiz
    galho = {v: 1 for v in alcancados}
    for v in reversed(ordem):
        if v in alcancados and v != raiz:
            galho[next(T.predecessors(v))] += galho[v]
    return galho


def alcance_apos_remocao(T, removidos):
    """Número de contas alcançadas a partir da raiz após as remoções."""
    return tamanho_galho(T, removidos)[T.graph["raiz"]]


def contas_centrais(T, k):
    """Escolhe as k contas de maior galho, uma de cada vez."""
    raiz = T.graph["raiz"]
    escolhidas = []
    for _ in range(k):
        # recalcula os galhos sem as contas já escolhidas
        galho = tamanho_galho(T, escolhidas)
        candidatas = {v: g for v, g in galho.items() if v != raiz}
        if not candidatas:
            break
        escolhidas.append(max(candidatas, key=candidatas.get))
    return escolhidas


def simular_remocao(cascatas, ks=(1, 3, 5), repeticoes_aleatorias=20, semente=42):
    """Calcula a perda de alcance ao remover contas centrais e aleatórias."""
    # semente fixa para o sorteio dar sempre o mesmo resultado
    sorteio = random.Random(semente)
    linhas = []
    for id_cascata, T in cascatas.items():
        raiz = T.graph["raiz"]
        n = T.number_of_nodes()
        outras = [v for v in T if v != raiz]
        centrais = contas_centrais(T, max(ks))

        for k in ks:
            perda_central = 1 - alcance_apos_remocao(T, centrais[:k]) / n

            # média de várias remoções aleatórias de k contas
            perdas = [1 - alcance_apos_remocao(T, sorteio.sample(outras, min(k, len(outras)))) / n
                      for _ in range(repeticoes_aleatorias)]

            for estrategia, perda in [("centrais", perda_central), ("aleatorias", np.mean(perdas))]:
                linhas.append({
                    "id_cascata": id_cascata,
                    "rotulo": T.graph["rotulo"],
                    "k": k,
                    "estrategia": estrategia,
                    "perda_pct": 100 * perda,
                })
    return pd.DataFrame(linhas)
