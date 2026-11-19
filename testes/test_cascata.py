"""
Testes de integridade das cascatas montadas a partir do UPFD Politifact.
"""
import networkx as nx
import pytest

from src.cascata import carregar_cascatas


@pytest.fixture(scope="module")
def cascatas():
    """Carrega as cascatas uma vez para todos os testes do arquivo."""
    return carregar_cascatas()


def test_quantidade_e_rotulos(cascatas):
    """São 314 cascatas, 157 de cada rótulo."""
    rotulos = [G.graph["rotulo"] for G in cascatas.values()]
    assert len(cascatas) == 314
    assert rotulos.count("fake") == 157 and rotulos.count("real") == 157


def test_todas_sao_arvores(cascatas):
    """Toda cascata é uma árvore direcionada válida."""
    assert all(nx.is_arborescence(G) for G in cascatas.values())


def test_raiz_sem_pai_e_sem_horario(cascatas):
    """A raiz não tem pai nem horário."""
    for G in cascatas.values():
        raiz = G.graph["raiz"]
        assert G.in_degree(raiz) == 0
        # um horário vazio (NaT) nunca é igual a ele mesmo
        assert G.nodes[raiz]["horario"] != G.nodes[raiz]["horario"]


def test_exemplo_conhecido(cascatas):
    """Confere uma cascata que já verificamos manualmente."""
    G = cascatas[1]
    assert G.graph["noticia"] == "politifact6657" and G.graph["raiz"] == 497
    assert G.number_of_nodes() == 21
    assert G.nodes[517]["usuario"] == "60532319"
