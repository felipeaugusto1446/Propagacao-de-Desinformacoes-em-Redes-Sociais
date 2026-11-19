"""
Testes do carregamento do Twitter15/16: regra de montagem e rótulos.
"""
from collections import Counter

import networkx as nx
import pytest

from src.carregamento_twitter import montar_arvore, ler_rotulos, PASTA_BRUTOS


def test_regra_de_montagem():
    """Vértice com dois pais fica só com o primeiro e laços são descartados."""
    # D aparece com dois pais (B e C) e B tem um laço
    linhas = [
        "['ROOT', 'ROOT', '0.0']->['A', '100', '0.0']",
        "['A', '100', '0.0']->['B', '100', '1.0']",
        "['A', '100', '0.0']->['C', '100', '2.0']",
        "['B', '100', '1.0']->['D', '100', '3.0']",
        "['C', '100', '2.0']->['D', '100', '4.0']",
        "['B', '100', '1.0']->['B', '100', '1.0']",
    ]
    contagem = Counter()
    G = montar_arvore(linhas, "100", "fake", "teste", contagem)
    assert nx.is_arborescence(G)
    assert G.graph["raiz"] == ("A", "100")
    assert list(G.predecessors(("D", "100"))) == [("B", "100")]
    assert contagem == Counter({"segundo_pai_ou_ciclo": 1, "laco": 1})
    assert G.nodes[("D", "100")]["atraso_min"] == 3.0


@pytest.mark.skipif(not (PASTA_BRUTOS / "twitter15").exists(), reason="dados do Twitter15 ausentes")
def test_rotulos_twitter15():
    """Contagem dos rótulos do Twitter15 depois da troca de nomes."""
    rotulos = Counter(ler_rotulos(PASTA_BRUTOS / "twitter15").values())
    assert rotulos == Counter({"fake": 370, "real": 372, "non-rumor": 374, "unverified": 374})
