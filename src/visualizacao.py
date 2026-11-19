"""
Figuras do projeto: desenho de cascatas, distribuições das métricas e curvas
de robustez.
"""
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns

from src.metricas import niveis, raiz_de

CORES = {"fake": "#d1495b", "real": "#2e86ab"}


def posicoes_em_arvore(G):
    """Calcula as posições para desenhar a cascata em níveis, com a raiz no topo."""
    raiz = raiz_de(G)
    nivel = niveis(G)
    pos, proxima_folha = {}, [0]

    # percorre a árvore em profundidade: cada folha recebe a próxima posição x
    # e cada pai fica no meio dos seus filhos
    def visitar(v):
        filhos = sorted(G.successors(v))
        if not filhos:
            x = proxima_folha[0]
            proxima_folha[0] += 1
        else:
            xs = [visitar(f) for f in filhos]
            x = (xs[0] + xs[-1]) / 2
        pos[v] = (x, -nivel[v])
        return x

    visitar(raiz)
    return pos


def desenhar_cascata(G, ax=None, titulo=None):
    """Desenha uma cascata com a raiz destacada."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5))
    raiz = raiz_de(G)
    cor = CORES.get(G.graph.get("rotulo"), "gray")
    pos = posicoes_em_arvore(G)
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=False, width=0.6, alpha=0.6)
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=[v for v in G if v != raiz],
                           node_size=14, node_color=cor)

    # a raiz (notícia) aparece como um quadrado preto
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=[raiz], node_size=80,
                           node_color="black", node_shape="s")
    ax.set_title(titulo or f"{G.graph.get('noticia')} ({G.graph.get('rotulo')}), "
                           f"{G.number_of_nodes()} vértices")
    ax.set_axis_off()
    return ax


def boxplots_metricas(tabela, metricas, escala_log=()):
    """Desenha um boxplot por métrica comparando fake e real."""
    colunas = 4
    linhas = -(-len(metricas) // colunas)
    fig, eixos = plt.subplots(linhas, colunas, figsize=(4 * colunas, 3.4 * linhas))
    for ax, m in zip(eixos.flat, metricas):
        sns.boxplot(data=tabela, x="rotulo", y=m, hue="rotulo", palette=CORES,
                    order=["fake", "real"], ax=ax, legend=False)

        # escala logarítmica para métricas com valores muito espalhados
        if m in escala_log:
            ax.set_yscale("log")
        ax.set_xlabel("")
        ax.set_title(m)
        ax.set_ylabel("")

    # esconde os quadros que sobraram sem métrica
    for ax in list(eixos.flat)[len(metricas):]:
        ax.set_axis_off()
    fig.tight_layout()
    return fig


def curvas_robustez(simulacao):
    """Desenha o alcance médio restante pelo número de contas removidas."""
    media = simulacao.groupby(["rotulo", "estrategia", "k"])["alcance"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for (rotulo, estrategia), d in media.groupby(["rotulo", "estrategia"]):
        # linha cheia para contas centrais e tracejada para remoção aleatória
        nome = "contas centrais" if estrategia == "centrais" else "aleatório"
        ax.plot(d["k"], d["alcance"], color=CORES.get(rotulo, "gray"),
                linestyle="-" if estrategia == "centrais" else "--", marker="o", markersize=3,
                label=f"{rotulo}, {nome}")
    ax.set_xlabel("Contas removidas (k)")
    ax.set_ylabel("Alcance restante (fração dos compartilhamentos)")
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig
