"""
Leitura do Twitter15/16 como cascatas no mesmo formato do UPFD.

Cada arquivo tree/<id do tweet fonte>.txt tem uma linha por aresta, no formato
['uid_pai', 'tweet_pai', 'atraso_pai']->['uid_filho', 'tweet_filho', 'atraso_filho'].
O atraso está em minutos desde o tweet fonte e a primeira linha liga ROOT à fonte.

Os arquivos brutos têm vértices com mais de um pai, ciclos e laços, então a
árvore é montada com uma regra fixa: o vértice é o par (usuário, tweet) e uma
aresta só entra se o pai já está na árvore e o filho ainda não está. Assim cada
vértice fica com o primeiro pai válido e o resultado é sempre uma árvore. As
arestas descartadas são contadas para o relatório de qualidade.

Rótulos: false vira "fake" e true vira "real" (boato desmentido e boato
confirmado), non-rumor e unverified ficam com o nome original.

Fonte do dataset:
Ma, J., Gao, W., Wong, K.-F. (2017). Detect Rumors in Microblog Posts Using
Propagation Structure via Kernel Learning. ACL 2017.
https://doi.org/10.18653/v1/P17-1066
"""
import ast
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd

PASTA_BRUTOS = Path(__file__).resolve().parent.parent / "dados" / "brutos"
ROTULOS = {"false": "fake", "true": "real"}

# data de referência artificial, só as diferenças de tempo importam
INICIO = pd.Timestamp("2000-01-01")


def ler_rotulos(pasta):
    """Lê o label.txt e devolve o rótulo de cada tweet fonte."""
    rotulos = {}
    # cada linha tem o formato rotulo:id
    for linha in (pasta / "label.txt").read_text().split():
        rotulo, tweet = linha.split(":")
        rotulos[tweet] = ROTULOS.get(rotulo, rotulo)
    return rotulos


def ler_arvore(arquivo, rotulo, origem, contagem):
    """Lê um arquivo de árvore e monta a cascata."""
    return montar_arvore(arquivo.read_text().splitlines(), arquivo.stem, rotulo, origem, contagem)


def montar_arvore(linhas, fonte, rotulo, origem, contagem):
    """Monta a cascata a partir das linhas pai->filho e conta os descartes."""
    pares = []
    for linha in linhas:
        pai, filho = (ast.literal_eval(parte) for parte in linha.split("->"))
        pares.append((pai, filho))

    # a raiz é o filho da linha que sai de ROOT
    raiz = next((filho[0], filho[1]) for pai, filho in pares if pai[0] == "ROOT")
    G = nx.DiGraph(arvore=fonte, raiz=raiz, noticia=fonte, rotulo=rotulo, origem=origem)
    G.add_node(raiz, usuario=None, horario=pd.NaT, atraso_min=0.0)

    # faz várias passadas porque a ordem do arquivo nem sempre segue a árvore
    pendentes = [(p, f) for p, f in pares if p[0] != "ROOT"]
    mudou = True
    while pendentes and mudou:
        mudou, restantes = False, []
        for pai, filho in pendentes:
            chave_pai, chave_filho = (pai[0], pai[1]), (filho[0], filho[1])
            if chave_pai == chave_filho:
                contagem["laco"] += 1
            elif chave_filho in G:
                # o filho já tem pai, aceitar a aresta criaria segundo pai ou ciclo
                contagem["segundo_pai_ou_ciclo"] += 1
            elif chave_pai in G:
                atraso = float(filho[2])
                G.add_node(chave_filho, usuario=filho[0], atraso_min=atraso,
                           horario=INICIO + pd.Timedelta(minutes=atraso))
                G.add_edge(chave_pai, chave_filho)
                mudou = True
            else:
                # o pai ainda não entrou na árvore, tenta de novo na próxima passada
                restantes.append((pai, filho))
        pendentes = restantes
    contagem["pai_inexistente"] += len(pendentes)
    return G


def carregar_cascatas_twitter(datasets=("twitter15", "twitter16"), pasta=PASTA_BRUTOS):
    """Devolve as cascatas do Twitter15/16 e a contagem de descartes."""
    cascatas, contagem = {}, Counter()
    for ds in datasets:
        rotulos = ler_rotulos(pasta / ds)
        for arquivo in sorted((pasta / ds / "tree").glob("*.txt")):
            # 169 fontes aparecem nos dois datasets com o mesmo rótulo, entram uma vez só
            if arquivo.stem in cascatas:
                contagem["fonte_repetida_entre_datasets"] += 1
                continue
            if arquivo.stem not in rotulos:
                contagem["arquivo_sem_rotulo"] += 1
                continue
            cascatas[arquivo.stem] = ler_arvore(arquivo, rotulos[arquivo.stem], ds, contagem)
    return cascatas, contagem
