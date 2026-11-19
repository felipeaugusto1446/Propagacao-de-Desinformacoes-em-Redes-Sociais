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
**UPFD Politifact** — o FakeNewsNet (Shu et al., 2020) já organizado em 314
árvores de propagação de retweets (157 fake, 157 real), com o horário de cada
retweet. Os pais de cada retweet foram reconstruídos pelos autores a partir do
horário e das relações de seguidores.
Fonte: Dou et al. (2021), *User Preference-aware Fake News Detection*, SIGIR '21.
https://arxiv.org/abs/2104.12259 · https://github.com/safe-graph/GNN-FakeNews

Arquivos usados (em `dados/brutos/politifact/`): `A.txt` (arestas pai,filho),
`node_graph_id.npy`, `graph_labels.npy` (1 = fake, 0 = real),
`pol_news_list.txt`, `pol_id_twitter_mapping.pkl`, `pol_id_time_mapping.pkl`.
A notícia `politifact14940` é excluída da análise por aparecer nas listas fake e
real do FakeNewsNet.

**Twitter15/16** (análise complementar) — árvores de propagação de boatos
(Ma, Gao & Wong, 2017, https://doi.org/10.18653/v1/P17-1066), em
`dados/brutos/twitter15` e `twitter16`. Na comparação usamos `false` (boato
desmentido → "fake") × `true` (boato confirmado → "real").

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
Requisitos: Python 3.13.

```bash
py -3.13 -m venv .venv          # Linux/Mac: python3.13 -m venv .venv
# Windows (Git Bash): source .venv/Scripts/activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Sempre a partir da raiz do repositório:

1. Análise completa (tabelas e figuras em `resultados/<dataset>/`):
   `python executar_analise.py --dataset politifact` (padrão), `--dataset twitter` ou `--dataset todos`
2. Testes: `pytest testes/`
3. Exploração interativa: notebooks `01_exploracao`, `02_metricas`,
   `03_comparacao_robustez` (VS Code, kernel do `.venv`).

| Módulo (`src/`) | Função |
|---|---|
| `carregamento.py` | Lê os 6 arquivos brutos em tabelas de vértices, arestas e árvores |
| `cascata.py` | Monta uma árvore (`networkx.DiGraph`) por notícia |
| `carregamento_twitter.py` | Lê o Twitter15/16 no mesmo formato de cascata (1º pai válido; descartes contados) |
| `metricas.py` | Tamanho, profundidade, largura máxima, viralidade estrutural, fração direto da raiz, maior amplificador, tempo até metade, fração nas 1ªs 24 h |
| `estatistica.py` | Mann-Whitney fake × real, ajuste de Holm, tamanho de efeito |
| `robustez.py` | Remoção de contas centrais × aleatória e alcance restante |
| `visualizacao.py` | Desenho das cascatas, boxplots e curvas de robustez |

## Equipe
| Integrante | Papel |
|---|---|
| Felipe Augusto | Desenvolvedor |
| Gustavo Raponi | _a definir_ |
| Thayane | _a definir_ |
| Giovana | _a definir_ |
| _a definir_ | _a definir_ |

Projeto desenvolvido apenas para fins acadêmicos
