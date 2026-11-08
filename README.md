# Propagação de Desinformação em Redes Sociais

Projeto da disciplina **SMAC03 – Grafos** (UNIFEI, 2º semestre de 2026),
Cenário 2. Prof. Rafael Frinhani.

## Objetivo
Investigar como a **estrutura das cascatas de compartilhamento** difere entre
boatos falsos e verdadeiros no Twitter, e o que essa estrutura revela sobre
onde intervenções de moderação teriam maior efeito.

## Modelagem
Cada cascata é uma **árvore direcionada com raiz**:
- **Raiz:** o tweet original
- **Vértice:** um compartilhamento (ID do usuário + ID do tweet)
- **Aresta:** de quem passou o conteúdo para quem compartilhou

Métricas analisadas: tamanho, profundidade, largura máxima, viralidade
estrutural, velocidade e centralidade das contas, além da simulação de
remoção das contas centrais (robustez).

## Dataset
**Twitter15/16** — árvores de propagação de tweets rotulados
(`false`, `true`, `unverified`, `non-rumor`).
Fonte: Ma, Gao & Wong (2017). https://doi.org/10.18653/v1/P17-1066
Instruções de download em `dados/brutos/` (ver seção "Como rodar").

## Metodologia
O projeto segue a **CRISP-NET** (Acuña-Cid et al., 2025), que integra as
fases da CRISP-DM com atividades de análise de redes.
https://doi.org/10.3390/make7030101

## Estrutura do repositório
| Pasta | Conteúdo |
|---|---|
| `dados/` | Dataset bruto (não alterado) e processado |
| `notebooks/` | Exploração e análises, numeradas na ordem de execução |
| `src/` | Núcleo do protótipo: carregamento, cascatas, métricas, robustez, visualização |
| `testes/` | Testes das métricas em cascatas com resultado conhecido |
| `resultados/` | Figuras e tabelas geradas |
| `docs/` | Relatório, slides e diagramas |        

## Como rodar
Requisitos: Python 3.11.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

1. Coloque os arquivos do Twitter15/16 em `dados/brutos/`.
2. Execute os notebooks na ordem numérica (`01`, `02`, `03`).
3. Para testar as métricas: `pytest testes/`

## Equipe
| Integrante | Papel |
|---|---|
| Felipe Augusto | Desenvolvedor |
| Gustavo Raponi | _a definir_ |
| Thayane | _a definir_ |
| Giovana | _a definir_ |
| _a definir_ | _a definir_ |

Projeto desenvolvido apenas para fins acadêmicos
