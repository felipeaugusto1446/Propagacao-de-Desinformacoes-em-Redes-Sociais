"""
Executa a análise completa e salva tabelas e figuras em resultados/<dataset>/.

Uso, na raiz do repositório e com o .venv ativado:
    python executar_analise.py                     (UPFD Politifact, padrão)
    python executar_analise.py --dataset twitter   (Twitter15/16)
    python executar_analise.py --dataset todos     (os dois)

Etapas, seguindo a CRISP-NET:
1. Preparação: carrega o dataset e monta as cascatas.
2. Qualidade: verificações e exclusões justificadas.
3. Modelagem: métricas estruturais e temporais por cascata.
4. Avaliação: teste de Mann-Whitney fake contra real, com ajuste de Holm.
5. Robustez: remoção de contas centrais comparada com remoção aleatória.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from src.cascata import carregar_cascatas
from src.carregamento_twitter import carregar_cascatas_twitter
from src.estatistica import comparar_grupos
from src.metricas import METRICAS, calcular_metricas, raiz_de
from src.robustez import simular_remocoes
from src.visualizacao import boxplots_metricas, curvas_robustez, desenhar_cascata

RAIZ = Path(__file__).resolve().parent

# notícias excluídas e o motivo, a metodologia pede justificar toda exclusão
EXCLUIDAS = {"politifact14940": "aparece nas listas fake e real do FakeNewsNet"}


def carregar(dataset):
    """Carrega as cascatas do dataset escolhido e as contagens do carregamento."""
    if dataset == "politifact":
        return carregar_cascatas(), Counter()
    return carregar_cascatas_twitter()


def verificar_qualidade(cascatas, extras):
    """Monta o relatório de qualidade a partir das cascatas."""
    arestas_usuarios = invertidas = sem_horario = repetidos = vertices = 0
    for G in cascatas.values():
        raiz = raiz_de(G)
        h = nx.get_node_attributes(G, "horario")

        # arestas que saem da raiz não entram, porque a raiz não tem horário
        for p, f in G.edges():
            if p != raiz:
                arestas_usuarios += 1
                invertidas += int(h[f] < h[p])

        # conta usuários que aparecem mais de uma vez na mesma cascata
        usuarios = [d["usuario"] for v, d in G.nodes(data=True) if v != raiz]
        vertices += len(usuarios)
        repetidos += len(usuarios) - len(set(usuarios))
        sem_horario += sum(pd.isna(h[v]) for v in G if v != raiz)

    tamanhos = pd.Series([G.number_of_nodes() for G in cascatas.values()])
    linhas = [
        ("cascatas", len(cascatas)),
        ("cascatas que são árvores válidas", sum(nx.is_arborescence(G) for G in cascatas.values())),
        ("vértices sem horário (fora a raiz)", sem_horario),
        ("arestas entre usuários", arestas_usuarios),
        ("arestas com filho antes do pai", invertidas),
        ("vértices com usuário repetido na cascata", repetidos),
        ("% vértices com usuário repetido", round(100 * repetidos / max(vertices, 1), 1)),
        ("cascatas com menos de 10 vértices", int((tamanhos < 10).sum())),
    ]
    linhas += [(f"descartado no carregamento: {k}", v) for k, v in extras.items()]
    return pd.DataFrame(linhas, columns=["verificacao", "valor"])


def escolher_exemplos(tabela, alvo=100):
    """Escolhe uma cascata fake e uma real com tamanho perto do alvo."""
    escolhidas = {}
    for rotulo in ("fake", "real"):
        sub = tabela[tabela["rotulo"] == rotulo]
        escolhidas[rotulo] = sub.loc[(sub["tamanho"] - alvo).abs().idxmin(), "arvore"]
    return escolhidas


def analisar(dataset):
    """Roda todas as etapas para um dataset e salva os resultados."""
    tabelas = RAIZ / "resultados" / dataset / "tabelas"
    figuras = RAIZ / "resultados" / dataset / "figuras"
    tabelas.mkdir(parents=True, exist_ok=True)
    figuras.mkdir(parents=True, exist_ok=True)
    print(f"\n######## {dataset} ########")

    print("1/5 Carregando e montando cascatas...")
    todas, extras = carregar(dataset)

    print("2/5 Verificando qualidade...")
    qualidade = verificar_qualidade(todas, extras)
    qualidade.to_csv(tabelas / "qualidade.csv", index=False)

    # a análise principal usa só fake e real, sem as notícias excluídas
    cascatas = {k: G for k, G in todas.items()
                if G.graph["rotulo"] in ("fake", "real") and G.graph["noticia"] not in EXCLUIDAS}

    print("3/5 Calculando métricas...")
    tabela = calcular_metricas(cascatas)
    tabela.to_csv(tabelas / "metricas_por_cascata.csv", index=False)

    print("4/5 Comparando fake e real...")
    comparacao = comparar_grupos(tabela, list(METRICAS))
    comparacao.to_csv(tabelas / "comparacao_fake_real.csv", index=False)

    print("5/5 Simulando remoção de contas...")
    simulacao = simular_remocoes(cascatas, k_max=10)
    simulacao.to_csv(tabelas / "robustez_por_cascata.csv", index=False)
    resumo_rob = (simulacao.groupby(["rotulo", "estrategia", "k"])["alcance"]
                  .mean().unstack("k").round(3))
    resumo_rob.to_csv(tabelas / "robustez_resumo.csv")

    # figuras
    fig = boxplots_metricas(tabela, list(METRICAS),
                            escala_log={"tamanho", "largura_maxima", "grau_max_usuario",
                                        "tempo_ate_metade_h"})
    fig.savefig(figuras / "metricas_fake_real.png", dpi=150)
    curvas_robustez(simulacao).savefig(figuras / "robustez.png", dpi=150)

    exemplos = escolher_exemplos(tabela)
    fig, eixos = plt.subplots(1, 2, figsize=(14, 5))
    for ax, rotulo in zip(eixos, ("fake", "real")):
        desenhar_cascata(cascatas[exemplos[rotulo]], ax=ax)
    fig.tight_layout()
    fig.savefig(figuras / "exemplo_cascatas_fake_real.png", dpi=150)
    plt.close("all")

    # resumo no terminal
    print("\n=== Qualidade ===")
    print(qualidade.to_string(index=False))
    print(f"\n=== Comparação fake e real ({len(cascatas)} cascatas, Mann-Whitney com ajuste de Holm) ===")
    print(comparacao[["metrica", "mediana_fake", "mediana_real", "p_holm", "efeito_r",
                      "significativo_5pct"]].round(4).to_string(index=False))
    print("\n=== Alcance médio restante após remover k contas ===")
    print(resumo_rob[[0, 1, 3, 5, 10]].to_string())
    print(f"\nResultados em {RAIZ / 'resultados' / dataset}")


def main():
    """Lê a opção --dataset e roda a análise."""
    # garante acentos no terminal do Windows
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 160)
    parser = argparse.ArgumentParser(description="Análise das cascatas de desinformação.")
    parser.add_argument("--dataset", choices=["politifact", "twitter", "todos"], default="politifact")
    escolha = parser.parse_args().dataset
    for dataset in (["politifact", "twitter"] if escolha == "todos" else [escolha]):
        analisar(dataset)


if __name__ == "__main__":
    main()
