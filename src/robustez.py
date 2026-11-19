"""
Robustez das cascatas: o efeito de remover contas, simulando a moderação.

Suspender uma conta remove todos os vértices dela na cascata. Numa árvore,
todo vértice que não é folha é um vértice de corte, então a remoção derruba
também tudo o que estava abaixo dele. A medida é o alcance restante: a fração
dos compartilhamentos originais que ainda são alcançáveis a partir da raiz.

Estratégias comparadas:
centrais: remove as contas de maior grau de saída (os amplificadores).
aleatoria: remove contas ao acaso, servindo de baseline (média de várias repetições).

Referência:
Albert, R., Jeong, H., Barabási, A.-L. (2000). Error and attack tolerance of
complex networks. Nature, 406, 378-382. https://doi.org/10.1038/35019019
"""
from collections import defaultdict

import networkx as nx
import numpy as np
import pandas as pd

from src.metricas import raiz_de


def vertices_por_usuario(G):
    """Agrupa os vértices de cada usuário, sem contar a raiz."""
    # o mesmo usuário pode aparecer várias vezes na mesma cascata
    grupos = defaultdict(list)
    raiz = raiz_de(G)
    for v, dados in G.nodes(data=True):
        if v != raiz and dados.get("usuario") is not None:
            grupos[dados["usuario"]].append(v)
    return grupos


def estrutura_da_arvore(G):
    """Devolve o pai e o tamanho da subárvore de cada vértice."""
    pai = {f: p for p, f in G.edges()}

    # tamanho da subárvore calculado das folhas para a raiz
    tamanho_sub = {}
    for v in reversed(list(nx.topological_sort(G))):
        tamanho_sub[v] = 1 + sum(tamanho_sub[f] for f in G.successors(v))
    return pai, tamanho_sub


def alcance_restante(G, removidos, estrutura=None):
    """Fração dos compartilhamentos que continuam alcançáveis após as remoções."""
    total = G.number_of_nodes() - 1
    if total == 0:
        return 1.0
    pai, tamanho_sub = estrutura or estrutura_da_arvore(G)
    removidos = set(removidos)
    perdidos = 0
    for v in removidos:
        # sobe pelos pais para ver se v já caiu junto com outro removido
        u, coberto = pai.get(v), False
        while u is not None:
            if u in removidos:
                coberto = True
                break
            u = pai.get(u)

        # se não caiu junto, perde a subárvore inteira dele
        if not coberto:
            perdidos += tamanho_sub[v]
    return (total - perdidos) / total


def usuarios_centrais(G, grupos):
    """Ordena os usuários pela soma do grau de saída, do maior para o menor."""
    pontuacao = {u: sum(G.out_degree(v) for v in vs) for u, vs in grupos.items()}
    return sorted(pontuacao, key=lambda u: (-pontuacao[u], str(u)))


def curva_remocao(G, k_max=10, repeticoes=20, semente=42):
    """Alcance restante após remover de 0 até k_max contas nas duas estratégias."""
    grupos = vertices_por_usuario(G)
    ordem_central = usuarios_centrais(G, grupos)
    estrutura = estrutura_da_arvore(G)
    usuarios = list(grupos)

    # sorteios feitos uma vez, com semente fixa para o resultado ser reproduzível
    rng = np.random.default_rng(semente)
    sorteios = [rng.permutation(len(usuarios)) for _ in range(repeticoes)]

    linhas = []
    for k in range(k_max + 1):
        removidos = [v for u in ordem_central[:k] for v in grupos[u]]
        linhas.append({"k": k, "estrategia": "centrais",
                       "alcance": alcance_restante(G, removidos, estrutura)})
        alcances = []
        for perm in sorteios:
            escolhidos = [usuarios[i] for i in perm[:k]]
            removidos = [v for u in escolhidos for v in grupos[u]]
            alcances.append(alcance_restante(G, removidos, estrutura))
        linhas.append({"k": k, "estrategia": "aleatoria", "alcance": float(np.mean(alcances))})
    return pd.DataFrame(linhas)


def simular_remocoes(cascatas, k_max=10, repeticoes=20, semente=42):
    """Aplica a curva de remoção em todas as cascatas."""
    partes = []
    for i, (arvore_id, G) in enumerate(cascatas.items()):
        curva = curva_remocao(G, k_max, repeticoes, semente + i)
        curva.insert(0, "rotulo", G.graph.get("rotulo"))
        curva.insert(0, "arvore", arvore_id)
        partes.append(curva)
    return pd.concat(partes, ignore_index=True)
