"""
Comparação estatística das métricas entre cascatas fake e real.

Usa o teste de Mann-Whitney bilateral, que não supõe distribuição normal e por
isso serve para métricas assimétricas como o tamanho. Como várias métricas são
testadas ao mesmo tempo, os p-valores são ajustados pelo método de Holm para
controlar falsos positivos.

O tamanho de efeito é a correlação rank-biserial, que vai de -1 a 1. Valor
positivo indica que o grupo fake tende a ter valores maiores. Leitura usual:
perto de 0,1 é pequeno, perto de 0,3 é médio e a partir de 0,5 é grande.
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def ajuste_holm(p_valores):
    """Ajusta os p-valores pelo método de Holm."""
    p = np.asarray(p_valores, dtype=float)
    m = len(p)
    ordem = np.argsort(p)
    ajustado = np.empty(m)
    acumulado = 0.0

    # do menor para o maior p-valor, multiplicando pelo número de testes restantes
    for posicao, i in enumerate(ordem):
        acumulado = max(acumulado, (m - posicao) * p[i])
        ajustado[i] = min(acumulado, 1.0)
    return ajustado


def comparar_grupos(tabela, metricas, grupo="rotulo", a="fake", b="real"):
    """Compara os dois grupos em cada métrica e devolve uma tabela de resultados."""
    linhas = []
    for m in metricas:
        xa = tabela.loc[tabela[grupo] == a, m].dropna()
        xb = tabela.loc[tabela[grupo] == b, m].dropna()
        u, p = mannwhitneyu(xa, xb, alternative="two-sided")
        linhas.append({
            "metrica": m,
            f"mediana_{a}": xa.median(),
            f"mediana_{b}": xb.median(),
            f"n_{a}": len(xa),
            f"n_{b}": len(xb),
            "U": u,
            "p_valor": p,
            # correlação rank-biserial calculada a partir do U
            "efeito_r": 2 * u / (len(xa) * len(xb)) - 1,
        })
    resultado = pd.DataFrame(linhas)
    resultado["p_holm"] = ajuste_holm(resultado["p_valor"])
    resultado["significativo_5pct"] = resultado["p_holm"] < 0.05
    return resultado
