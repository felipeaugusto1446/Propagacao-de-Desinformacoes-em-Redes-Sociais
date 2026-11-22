"""
Análise de sensibilidade do UPFD Politifact: período comum a falsas e verdadeiras.

Motivo: as falsas começam quase todas em 2017-2018 e as verdadeiras, em sua maioria,
antes de 2015, e a coleta termina em dezembro de 2018. Parte da diferença entre os
grupos pode vir da época e do tempo de observação, e não do rótulo.

O que faz:
1. Mostra a distribuição das cascatas por ano de início e o tempo de observação.
2. Repete o Mann-Whitney (com Holm) das métricas só com cascatas iniciadas entre
   ANO_MIN e ANO_MAX (padrão 2016 a 2018).
3. Repete a remoção de contas (centrais x aleatória) no mesmo recorte e compara
   falsas e verdadeiras no alcance restante com k = 10.

Uso, na raiz do repositório e com o .venv ativado:
    python analise_periodo_comum.py
    python analise_periodo_comum.py --ano-min 2017 --ano-max 2018

Saída: resultados/politifact/periodo_comum/ (tabelas em CSV). Não altera as
tabelas existentes. A remoção usa a mesma semente do executar_analise.py.
"""
import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import mannwhitneyu

from src.cascata import carregar_cascatas
from src.estatistica import comparar_grupos
from src.metricas import METRICAS, calcular_metricas
from src.robustez import simular_remocoes

EXCLUIDAS = {"politifact14940"}  # aparece nas listas fake e real (igual ao executar_analise.py)


def inicio_e_fim(G):
    """Primeiro e último horário da cascata (a raiz não tem horário)."""
    h = [d["horario"] for _, d in G.nodes(data=True) if pd.notna(d.get("horario"))]
    return (min(h), max(h)) if h else (pd.NaT, pd.NaT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano-min", type=int, default=2016)
    ap.add_argument("--ano-max", type=int, default=2018)
    args = ap.parse_args()

    saida = Path("resultados/politifact/periodo_comum")
    saida.mkdir(parents=True, exist_ok=True)

    todas = carregar_cascatas()
    cascatas = {k: G for k, G in todas.items()
                if G.graph["rotulo"] in ("fake", "real") and G.graph["noticia"] not in EXCLUIDAS}

    # 1. época das cascatas
    linhas = []
    for k, G in cascatas.items():
        ini, fim = inicio_e_fim(G)
        linhas.append({"arvore": k, "rotulo": G.graph["rotulo"], "inicio": ini, "fim": fim})
    epoca = pd.DataFrame(linhas)
    epoca["ano_inicio"] = epoca["inicio"].dt.year
    fim_coleta = epoca["fim"].max()
    epoca["anos_observacao"] = (fim_coleta - epoca["inicio"]).dt.days / 365
    por_ano = pd.crosstab(epoca["ano_inicio"], epoca["rotulo"])
    por_ano.to_csv(saida / "cascatas_por_ano.csv")
    obs = epoca.groupby("rotulo")["anos_observacao"].median().round(1)
    print("Cascatas por ano de início:\n", por_ano, sep="")
    print(f"\nFim da coleta: {fim_coleta:%d/%m/%Y}")
    print("Tempo mediano de observação (anos):", obs.to_dict())

    # 2. métricas no período comum
    ids = set(epoca.loc[epoca["ano_inicio"].between(args.ano_min, args.ano_max), "arvore"])
    sub = {k: G for k, G in cascatas.items() if k in ids}
    tabela = calcular_metricas(sub)
    n = tabela["rotulo"].value_counts().to_dict()
    print(f"\nPeríodo {args.ano_min}-{args.ano_max}: {n}")
    comp = comparar_grupos(tabela, list(METRICAS))
    comp.to_csv(saida / "comparacao_fake_real_periodo_comum.csv", index=False)
    print(comp[["metrica", "mediana_fake", "mediana_real", "efeito_r", "p_valor", "p_holm"]]
          .round(4).to_string(index=False))

    # 3. robustez no período comum
    sim = simular_remocoes(sub, k_max=10)
    sim.to_csv(saida / "robustez_por_cascata_periodo_comum.csv", index=False)
    k10 = sim[sim["k"] == 10]
    resumo = k10.groupby(["rotulo", "estrategia"])["alcance"].agg(["mean", "count"]).round(3)
    resumo.to_csv(saida / "robustez_k10_periodo_comum.csv")
    print("\nAlcance restante com 10 contas removidas:\n", resumo, sep="")
    # teste isolado, sem correção (são 2 estratégias)
    for estrategia in ("centrais", "aleatoria"):
        x = k10[k10["estrategia"] == estrategia]
        a = x.loc[x["rotulo"] == "fake", "alcance"]
        b = x.loc[x["rotulo"] == "real", "alcance"]
        u, p = mannwhitneyu(a, b, alternative="two-sided")
        print(f"{estrategia}: r = {2 * u / (len(a) * len(b)) - 1:+.2f}, p = {p:.4f} (sem correção)")


if __name__ == "__main__":
    main()
