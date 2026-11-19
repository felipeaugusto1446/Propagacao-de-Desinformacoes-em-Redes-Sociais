"""
Testes das métricas com cascatas de resultado conhecido, calculado à mão.

X é a estrela (A espalha para B, C, D, E e F) e Y é a cadeia (A para B, B para
C e assim por diante). Rodar a partir da raiz do repositório com pytest testes/.
"""
import pandas as pd
import networkx as nx
import pytest

from src import metricas as m
from src.robustez import alcance_restante, curva_remocao


@pytest.fixture
def estrela():
    """Cascata X em forma de estrela."""
    G = nx.DiGraph(raiz="A")
    G.add_edges_from([("A", f) for f in "BCDEF"])
    nx.set_node_attributes(G, {v: f"u{v}" for v in "BCDEF"}, "usuario")
    return G


@pytest.fixture
def cadeia():
    """Cascata Y em forma de cadeia, com horários."""
    G = nx.DiGraph(raiz="A")
    G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")])
    nx.set_node_attributes(G, {v: f"u{v}" for v in "BCDEF"}, "usuario")

    # B compartilha na hora 0, C uma hora depois e assim por diante
    inicio = pd.Timestamp("2020-01-01 12:00")
    horas = {"B": 0, "C": 1, "D": 2, "E": 30, "F": 100}
    nx.set_node_attributes(G, {v: inicio + pd.Timedelta(hours=h) for v, h in horas.items()},"horario")
    return G


def test_estrutura_estrela(estrela):
    """Valores conhecidos da estrela."""
    assert m.tamanho(estrela) == 6
    assert m.profundidade(estrela) == 1
    assert m.largura_maxima(estrela) == 5
    # 25 dividido por 15 pares, cerca de 1,67
    assert m.viralidade_estrutural(estrela) == pytest.approx(25 / 15)
    assert m.fracao_direto_da_raiz(estrela) == 1.0
    assert m.grau_max_usuario(estrela) == 0


def test_estrutura_cadeia(cadeia):
    """Valores conhecidos da cadeia."""
    assert m.tamanho(cadeia) == 6
    assert m.profundidade(cadeia) == 5
    assert m.largura_maxima(cadeia) == 1
    # 35 dividido por 15 pares, cerca de 2,33
    assert m.viralidade_estrutural(cadeia) == pytest.approx(35 / 15)
    assert m.fracao_direto_da_raiz(cadeia) == pytest.approx(1 / 5)
    assert m.grau_max_usuario(cadeia) == 1


def test_viralidade_igual_ao_networkx(cadeia, estrela):
    """A viralidade bate com a distância média calculada pelo networkx."""
    for G in (cadeia, estrela):
        esperado = nx.average_shortest_path_length(G.to_undirected())
        assert m.viralidade_estrutural(G) == pytest.approx(esperado)


def test_tempo(cadeia):
    """Métricas de tempo na cadeia."""
    # horas desde o primeiro compartilhamento: 0, 1, 2, 30, 100, então a mediana é 2
    assert m.tempo_ate_metade(cadeia) == pytest.approx(2)
    assert m.fracao_primeiras_24h(cadeia) == pytest.approx(3 / 5)


def test_robustez(cadeia, estrela):
    """Alcance restante após remover vértices."""
    # remover C na cadeia derruba C, D, E e F, sobra só B (1 de 5)
    assert alcance_restante(cadeia, ["C"]) == pytest.approx(1 / 5)

    # na estrela, remover um usuário tira só ele (sobram 4 de 5)
    assert alcance_restante(estrela, ["C"]) == pytest.approx(4 / 5)

    # a conta mais central da cadeia é B, removê-la corta a cadeia inteira
    curva = curva_remocao(cadeia, k_max=1, repeticoes=5)
    centrais_k1 = curva.query("estrategia == 'centrais' and k == 1")["alcance"].item()
    assert centrais_k1 == 0.0
