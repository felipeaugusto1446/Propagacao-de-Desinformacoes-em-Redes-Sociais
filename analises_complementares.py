"""
Figuras complementares usadas na seção de Resultados do artigo.

Gera, em resultados/complementar/ (PDF e PNG):
- dinamica_temporal: fração acumulada dos compartilhamentos ao longo do tempo, em
  três painéis (Politifact completo, Politifact só com cascatas iniciadas em
  2016 a 2018 e Twitter15/16);
- robustez_comparada: alcance restante após remover k contas, centrais contra
  aleatórias, nos dois datasets;
- par_mesma_estrutura: duas cascatas do Politifact com a mesma profundidade e
  viralidade e tamanhos muito diferentes.

Uso, na raiz do repositório e com o .venv ativado:
    python analises_complementares.py

Requer que executar_analise.py --dataset todos já tenha gerado
resultados/<dataset>/tabelas/. Os testes do período comum estão em
analise_periodo_comum.py.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from src import metricas
from src.carregamento_twitter import carregar_cascatas_twitter
from src.cascata import carregar_cascatas
from src.metricas import _horas_desde_primeiro
from src.visualizacao import desenhar_cascata

RESULTADOS = Path("resultados")
SAIDA = RESULTADOS / "complementar"
EXCLUIDAS = {"politifact14940"}  # aparece nas listas fake e real (igual ao executar_analise.py)
CORES = {"fake": "#d1495b", "real": "#2e86ab"}
NOMES = {"fake": "Falsa", "real": "Verdadeira"}
TITULOS = {"politifact": "UPFD Politifact (157 fake, 156 real)",
           "twitter": "Twitter15/16 (575 fake, 579 real)"}

# par da figura 2: árvore 203 (politifact15210, falsa, 464 vértices) e
# árvore 81 (politifact339, verdadeira, 35 vértices), ambas com profundidade 5
PAR = (203, 81)

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#555", "axes.linewidth": 0.7,
    "grid.color": "#dddddd", "grid.linewidth": 0.5, "savefig.bbox": "tight",
})


def salvar(fig, nome):
    """Salva a figura em PDF e PNG na pasta de saída."""
    fig.savefig(SAIDA / f"{nome}.pdf")
    fig.savefig(SAIDA / f"{nome}.png", dpi=200)
    plt.close(fig)


def inicio(G):
    """Horário do primeiro compartilhamento da cascata."""
    # a raiz não tem horário e fica de fora
    horarios = [d["horario"] for _, d in G.nodes(data=True) if pd.notna(d.get("horario"))]
    return min(horarios) if horarios else pd.NaT


def figura_robustez():
    """Curvas de alcance restante a partir dos resumos já salvos."""
    fig, eixos = plt.subplots(1, 2, figsize=(7, 2.5), sharey=True)
    ks = list(range(11))
    for ax, dataset in zip(eixos, ["politifact", "twitter"]):
        resumo = pd.read_csv(RESULTADOS / dataset / "tabelas" / "robustez_resumo.csv")
        for _, linha in resumo.iterrows():
            # linha cheia para contas centrais, tracejada para aleatórias
            estilo = "-" if linha.estrategia == "centrais" else "--"
            ax.plot(ks, [linha[str(k)] for k in ks], color=CORES[linha.rotulo], ls=estilo,
                    lw=1.6, marker="o", ms=3, mfc=CORES[linha.rotulo], mec="white", mew=0.6)
        ax.set_title(TITULOS[dataset], loc="left")
        ax.set_xlabel("Contas removidas (k)")
        ax.grid(axis="y")
        ax.set_ylim(0.3, 1.01)
        ax.set_xticks(range(0, 11, 2))
    eixos[0].set_ylabel("Alcance restante (fração)")

    legenda = [Line2D([], [], color=CORES["fake"], lw=1.6, label="fake"),
               Line2D([], [], color=CORES["real"], lw=1.6, label="real"),
               Line2D([], [], color="#444", lw=1.6, ls="-", label="contas centrais"),
               Line2D([], [], color="#444", lw=1.6, ls="--", label="contas aleatórias")]
    eixos[1].legend(handles=legenda, loc="lower left", frameon=False, ncol=2)
    fig.tight_layout()
    salvar(fig, "robustez_comparada")


def figura_tempo(politifact, twitter):
    """Fração acumulada dos compartilhamentos ao longo do tempo, em três painéis."""
    grade = np.logspace(-3, 4, 200)  # dias, em escala log
    paineis = [("UPFD Politifact\n(157 fake, 156 real)", politifact, None),
               ("Politifact, início em 2016-2018\n(143 fake, 32 real)", politifact, (2016, 2018)),
               ("Twitter15/16\n(575 fake, 579 real)", twitter, None)]

    fig, eixos = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
    for ax, (titulo, cascatas, faixa) in zip(eixos, paineis):
        curvas = {"fake": [], "real": []}
        for G in cascatas.values():
            rotulo = G.graph["rotulo"]
            # o twitter também tem non-rumor e unverified, que ficam de fora
            if rotulo not in curvas:
                continue
            if faixa and not faixa[0] <= inicio(G).year <= faixa[1]:
                continue
            dias = _horas_desde_primeiro(G) / 24
            if dias.size:
                # fração dos compartilhamentos que já aconteceram em cada ponto da grade
                curvas[rotulo].append(np.searchsorted(dias, grade, side="right") / dias.size)

        # mediana das cascatas com a faixa entre os quartis
        for rotulo, lista in curvas.items():
            todas = np.array(lista)
            baixo, alto = np.percentile(todas, [25, 75], axis=0)
            ax.fill_between(grade, baixo, alto, color=CORES[rotulo], alpha=0.13, lw=0)
            ax.plot(grade, np.median(todas, axis=0), color=CORES[rotulo], lw=1.8, label=rotulo)

        ax.set_xscale("log")
        ax.set_title(titulo, loc="left", fontsize=7.5)
        ax.set_xlabel("Dias desde o 1º compartilhamento (log)")
        ax.grid(axis="y")
        # marcas de 1 dia e 1 semana
        for dia in (1, 7):
            ax.axvline(dia, color="#999", lw=0.6, ls=":")
        ax.set_ylim(0, 1.02)

    eixos[0].set_ylabel("Fração acumulada dos compartilhamentos\n(mediana e quartis das cascatas)")
    eixos[0].legend(frameon=False, loc="upper left")
    fig.tight_layout()
    salvar(fig, "dinamica_temporal")


def figura_par(politifact):
    """Duas cascatas com a mesma forma e tamanhos muito diferentes."""
    fig, eixos = plt.subplots(1, 2, figsize=(7, 3.0))
    for ax, arvore in zip(eixos, PAR):
        G = politifact[arvore]
        titulo = (f"{NOMES[G.graph['rotulo']]}: {G.number_of_nodes()} vértices\n"
                  f"profundidade {metricas.profundidade(G)}, "
                  f"viralidade {metricas.viralidade_estrutural(G):.2f}").replace(".", ",")
        # título próprio abaixo, para não repetir o título padrão do desenho
        desenhar_cascata(G, ax=ax, titulo=" ")
        ax.set_title(titulo, fontsize=8.5, loc="left")

        print(G.graph["noticia"], G.graph["rotulo"], G.number_of_nodes(),
              metricas.profundidade(G), round(metricas.viralidade_estrutural(G), 2),
              round(metricas.fracao_direto_da_raiz(G), 2), metricas.grau_max_usuario(G),
              round(metricas.tempo_ate_metade(G), 1))
    fig.tight_layout()
    salvar(fig, "par_mesma_estrutura")


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    politifact = {k: G for k, G in carregar_cascatas().items()
                  if G.graph["noticia"] not in EXCLUIDAS}
    twitter, _ = carregar_cascatas_twitter()

    figura_robustez()
    figura_tempo(politifact, twitter)
    figura_par(politifact)
    print(f"Figuras salvas em {SAIDA}/")


if __name__ == "__main__":
    main()
