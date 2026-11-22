# Propagação de Desinformação em Redes Sociais

Projeto da disciplina **SMAC03 - Grafos** (UNIFEI, 2º semestre de 2026),
Cenário 2. Prof. Rafael Frinhani.

## Objetivo
Investigar como a estrutura das cascatas de compartilhamento difere entre
notícias falsas e verdadeiras no Twitter, e o que essa estrutura revela sobre
onde intervenções de moderação teriam maior efeito.

## Metodologia
O projeto segue a **CRISP-NET** (Acuña-Cid et al., 2025), que integra as
fases da CRISP-DM com atividades de análise de redes.
https://doi.org/10.3390/make7030101

O fluxo da solução está em `docs/diagramas/fluxo_solucao.png`.

## Modelagem
Cada notícia é uma **árvore direcionada com raiz**:
- **Raiz:** a notícia (tweet original)
- **Vértice:** um compartilhamento (retweet), com o usuário e o horário como atributos
- **Aresta:** de quem passou o conteúdo para quem compartilhou
- **Atributo da árvore:** rótulo, falsa ou verdadeira

Métricas analisadas: tamanho, profundidade, largura máxima, viralidade
estrutural, fração de compartilhamentos vindos direto da fonte, maior
amplificador e velocidade, além da simulação de remoção das contas centrais
(robustez).

## Datasets
**UPFD Politifact** (análise principal): o FakeNewsNet (Shu et al., 2020) já
organizado em 314 árvores de propagação de retweets (157 falsas e 157
verdadeiras), com o horário de cada retweet. Os pais de cada retweet foram
reconstruídos pelos autores a partir do horário e das relações de seguidores.
A notícia `politifact14940` é excluída por aparecer nas listas fake e real do
FakeNewsNet.

Fonte: Dou et al. (2021), *User Preference-aware Fake News Detection*, SIGIR 2021.
https://arxiv.org/abs/2104.12259 e https://github.com/safe-graph/GNN-FakeNews

**Twitter15/16** (análise complementar): árvores de propagação de boatos
rotulados (`false`, `true`, `unverified`, `non-rumor`). Na comparação usamos
`false` (boato desmentido) e `true` (boato confirmado).

Fonte: Ma, Gao e Wong (2017). https://doi.org/10.18653/v1/P17-1066

## Estrutura do repositório
| Pasta | Conteúdo |
|---|---|
| `dados/` | Datasets brutos (não alterados) |
| `src/` | Núcleo do protótipo: carregamento, cascatas, métricas, estatística, robustez, visualização |
| `notebooks/` | Exploração e análises interativas |
| `testes/` | Testes das métricas e do carregamento com resultados conhecidos |
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
2. Análise de sensibilidade por época (Politifact, só cascatas iniciadas em 2016 a 2018):
   `python analise_periodo_comum.py` (tabelas em `resultados/politifact/periodo_comum/`;
   outro recorte com `--ano-min 2017 --ano-max 2018`)
3. Figuras do artigo (depois do passo 1 com `--dataset todos`):
   `python analises_complementares.py` (figuras em `resultados/complementar/`)
4. Testes: `pytest testes/`
5. Notebooks (VS Code, kernel do `.venv`):

| Notebook | Conteúdo |
|---|---|
| `01_exploracao` | Qualidade dos dados do Politifact |
| `02_metricas` | Métricas e comparação estatística no Politifact |
| `03_comparacao_robustez` | Remoção de contas no Politifact |
| `experimento_twitter15` | Experimento complementar no Twitter15, com ramificação média e conta central pelo maior galho |
| `exemplo_cascatas_x_y.py` | Exemplo didático das cascatas estrela e cadeia |

| Módulo (`src/`) | Função |
|---|---|
| `carregamento.py` | Lê os 6 arquivos brutos do UPFD em tabelas de vértices, arestas e árvores |
| `cascata.py` | Monta uma árvore (`networkx.DiGraph`) por notícia do UPFD |
| `carregamento_twitter.py` | Lê o Twitter15/16 no mesmo formato de cascata (primeiro pai válido, descartes contados) |
| `metricas.py` | Tamanho, profundidade, largura máxima, viralidade estrutural, fração direto da raiz, maior amplificador, tempo até metade, fração nas primeiras 24 h |
| `estatistica.py` | Teste de Mann-Whitney entre fake e real, ajuste de Holm, tamanho de efeito |
| `robustez.py` | Remoção de contas centrais e aleatórias e alcance restante |
| `visualizacao.py` | Desenho das cascatas, boxplots e curvas de robustez |
| `experimento_twitter15.py` | Funções do notebook `experimento_twitter15` |

**Sobre as duas análises do Twitter15:** o fluxo principal (`carregamento_twitter.py`)
usa o par usuário e tweet como vértice, junta o Twitter15 e o Twitter16 e escolhe
as contas centrais pelo grau de saída. O experimento (`experimento_twitter15.py`)
usa só o usuário como vértice, apenas o Twitter15 e escolhe as contas centrais
pelo maior galho. As duas chegam às mesmas conclusões: estruturas parecidas entre
boatos falsos e verdadeiros e remoção de contas centrais mais eficaz que a aleatória.

**Sobre a análise por época:** no Politifact, a maior parte das notícias falsas
começa em 2017 e 2018 e a maior parte das verdadeiras antes de 2015, e a coleta
termina em dezembro de 2018. Por isso `analise_periodo_comum.py` repete a comparação
e a remoção de contas só com as cascatas iniciadas em 2016 a 2018, para separar o
efeito do rótulo do efeito da época e do tempo de observação.

## Equipe
| Integrante | Papel |
|---|---|
| Felipe Augusto | Coordenador |
| Gustavo Raponi | Desenvolvedor |
| Thayane | Desenvolvedora |
| Giovana | Modelagem |
| Isabela | Modelagem |

Projeto desenvolvido apenas para fins acadêmicos.
