"""
Montagem das cascatas do UPFD Politifact.

Cada notícia vira uma árvore direcionada (DiGraph) com a raiz, o rótulo e o id
da notícia guardados como atributos do grafo, e o usuário e o horário de cada
compartilhamento guardados como atributos de vértice.
"""
import networkx as nx

from src.carregamento import carregar_upfd


def montar_cascatas(vertices, arestas, arvores):
    """Monta um dicionário com uma cascata (DiGraph) para cada árvore."""
    # descobre a árvore de cada aresta olhando a árvore do pai
    arvore_do_vertice = vertices.set_index("vertice")["arvore"]
    arestas = arestas.assign(arvore=arestas["pai"].map(arvore_do_vertice))

    # separa as arestas por árvore uma vez só, em vez de filtrar dentro do laço
    arestas_por_arvore = dict(tuple(arestas.groupby("arvore")))
    info = arvores.set_index("arvore")

    cascatas = {}
    for arvore_id, vs in vertices.groupby("arvore"):
        raiz = int(vs.loc[vs["eh_raiz"], "vertice"].iloc[0])

        # cria o grafo já com os atributos da notícia
        G = nx.DiGraph(arvore=arvore_id, raiz=raiz,
                       noticia=info.at[arvore_id, "noticia"],
                       rotulo=info.at[arvore_id, "rotulo"])

        # adiciona os vértices antes das arestas para garantir os atributos
        G.add_nodes_from(
            (v.vertice, {"usuario": v.usuario, "horario": v.horario})
            for v in vs.itertuples(index=False)
        )

        # cada par (pai, filho) vira uma aresta
        es = arestas_por_arvore.get(arvore_id)
        if es is not None:
            G.add_edges_from(zip(es["pai"], es["filho"]))
        cascatas[arvore_id] = G
    return cascatas


def carregar_cascatas():
    """Lê o dataset e devolve as 314 cascatas montadas."""
    return montar_cascatas(*carregar_upfd())
