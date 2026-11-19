"""
Leitura do dataset UPFD Politifact em tabelas pandas.

Junta os 6 arquivos brutos em três tabelas: vértices, arestas e árvores.

Fonte do dataset:
Dou, Y., Shu, K., Xia, C., Yu, P. S., Sun, L. (2021). User Preference-aware
Fake News Detection. SIGIR 2021. https://arxiv.org/abs/2104.12259
"""
from pathlib import Path
import pickle

import numpy as np
import pandas as pd

# pasta dos dados brutos, montada a partir da localização deste arquivo
PASTA_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "brutos" / "politifact"

# rótulos do graph_labels.npy, conferidos com as listas oficiais do FakeNewsNet
ROTULOS = {0: "real", 1: "fake"}


def carregar_arestas(pasta=PASTA_PADRAO):
    """Lê as arestas do A.txt, uma por linha no formato pai, filho."""
    return pd.read_csv(pasta / "A.txt", header=None, names=["pai", "filho"],
                       skipinitialspace=True)


def carregar_vertices(pasta=PASTA_PADRAO):
    """Monta a tabela de vértices com árvore, raiz, usuário e horário."""
    arvore = np.load(pasta / "node_graph_id.npy")
    with open(pasta / "pol_id_twitter_mapping.pkl", "rb") as f:
        ids_twitter = pickle.load(f)
    with open(pasta / "pol_id_time_mapping.pkl", "rb") as f:
        horarios = pickle.load(f)

    vertices = pd.DataFrame({"vertice": np.arange(len(arvore)), "arvore": arvore})

    # o primeiro vértice de cada árvore é a raiz (a notícia)
    vertices["eh_raiz"] = vertices["arvore"].ne(vertices["arvore"].shift())

    # na raiz o id é o código da notícia, não um usuário, por isso fica vazio
    vertices["usuario"] = vertices["vertice"].map(ids_twitter).where(~vertices["eh_raiz"])

    # horário em segundos unix vira data, a raiz não tem horário e fica vazia
    segundos = pd.to_numeric(vertices["vertice"].map(horarios), errors="coerce")
    vertices["horario"] = pd.to_datetime(segundos, unit="s")
    return vertices


def carregar_arvores(pasta=PASTA_PADRAO):
    """Monta a tabela de árvores com o id da notícia e o rótulo."""
    rotulos = np.load(pasta / "graph_labels.npy").astype(int)

    # a linha i da lista de notícias corresponde à árvore i
    noticias = (pasta / "pol_news_list.txt").read_text().split()
    return pd.DataFrame({
        "arvore": np.arange(len(rotulos)),
        "noticia": noticias,
        "rotulo": pd.Series(rotulos).map(ROTULOS),
    })


def carregar_upfd(pasta=PASTA_PADRAO):
    """Devolve as tabelas de vértices, arestas e árvores."""
    return carregar_vertices(pasta), carregar_arestas(pasta), carregar_arvores(pasta)
