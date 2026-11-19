"""
Métricas estruturais e temporais de uma cascata.

Toda função recebe uma cascata (DiGraph em forma de árvore com o atributo de
grafo raiz) e devolve um número.

Referências:
Vosoughi, S., Roy, D., Aral, S. (2018). The spread of true and false news
online. Science, 359(6380), 1146-1151. https://doi.org/10.1126/science.aap9559
(tamanho, profundidade, largura máxima e viralidade estrutural)

Goel, S., Anderson, A., Hofman, J., Watts, D. J. (2016). The structural
virality of online diffusion. Management Science, 62(1), 180-196.
https://doi.org/10.1287/mnsc.2015.2158 (viralidade estrutural)
"""
from collections import Counter

import networkx as nx
import numpy as np
import pandas as pd


def raiz_de(G):
    """Devolve a raiz da cascata."""
    if "raiz" in G.graph:
        return G.graph["raiz"]
    # sem o atributo, a raiz é o único vértice sem pai
    return next(v for v in G if G.in_degree(v) == 0)


def niveis(G):
    """Devolve a distância da raiz até cada vértice."""
    return nx.single_source_shortest_path_length(G, raiz_de(G))


# métricas de estrutura

def tamanho(G):
    """Número de vértices da cascata, o alcance."""
    return G.number_of_nodes()


def profundidade(G):
    """Maior distância entre a raiz e um vértice."""
    return max(niveis(G).values())


def largura_maxima(G):
    """Maior número de vértices num mesmo nível, sem contar a raiz."""
    contagem = Counter(n for n in niveis(G).values() if n > 0)
    return max(contagem.values()) if contagem else 0


def viralidade_estrutural(G):
    """Distância média entre todos os pares de vértices."""
    n = G.number_of_nodes()
    if n < 2:
        return 0.0

    # tamanho da subárvore de cada vértice, calculado das folhas para a raiz
    tamanho_subarvore = {}
    for v in reversed(list(nx.topological_sort(G))):
        tamanho_subarvore[v] = 1 + sum(tamanho_subarvore[f] for f in G.successors(v))

    # cada aresta separa a subárvore do filho (s vértices) do resto (n - s),
    # então ela aparece no caminho de s * (n - s) pares; somando tudo temos a
    # soma de todas as distâncias sem calcular caminho por caminho
    soma = sum(tamanho_subarvore[f] * (n - tamanho_subarvore[f]) for _, f in G.edges())
    return soma / (n * (n - 1) / 2)


def fracao_direto_da_raiz(G):
    """Fração dos compartilhamentos que vieram direto da fonte."""
    n = G.number_of_nodes()
    return G.out_degree(raiz_de(G)) / (n - 1) if n > 1 else 0.0


def grau_max_usuario(G):
    """Maior grau de saída entre os usuários, a força do maior amplificador."""
    raiz = raiz_de(G)
    graus = [g for v, g in G.out_degree() if v != raiz]
    return max(graus) if graus else 0


# métricas de tempo

def _horas_desde_primeiro(G):
    """Horas de cada compartilhamento desde o primeiro compartilhamento."""
    # a raiz não tem horário e sai no dropna
    horarios = pd.Series([d.get("horario") for _, d in G.nodes(data=True)]).dropna()
    if horarios.empty:
        return np.array([])
    return np.sort(((horarios - horarios.min()).dt.total_seconds() / 3600).to_numpy())


def tempo_ate_metade(G):
    """Horas até acontecer metade dos compartilhamentos."""
    horas = _horas_desde_primeiro(G)
    return float(np.median(horas)) if horas.size else np.nan


def fracao_primeiras_24h(G):
    """Fração dos compartilhamentos que aconteceram nas primeiras 24 horas."""
    horas = _horas_desde_primeiro(G)
    return float((horas <= 24).mean()) if horas.size else np.nan


# tabela com todas as métricas

METRICAS = {
    "tamanho": tamanho,
    "profundidade": profundidade,
    "largura_maxima": largura_maxima,
    "viralidade_estrutural": viralidade_estrutural,
    "fracao_direto_da_raiz": fracao_direto_da_raiz,
    "grau_max_usuario": grau_max_usuario,
    "tempo_ate_metade_h": tempo_ate_metade,
    "fracao_primeiras_24h": fracao_primeiras_24h,
}


def calcular_metricas(cascatas):
    """Monta uma tabela com uma linha por cascata e todas as métricas."""
    linhas = []
    for arvore_id, G in cascatas.items():
        linha = {"arvore": arvore_id,
                 "noticia": G.graph.get("noticia"),
                 "rotulo": G.graph.get("rotulo")}
        linha.update({nome: f(G) for nome, f in METRICAS.items()})
        linhas.append(linha)
    return pd.DataFrame(linhas)
