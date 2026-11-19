import networkx as nx

# cria um grafo direcionado
X = nx.DiGraph(rotulo="exemplo", nome="estrela")

# recebe uma lista de pares, cada par vira uma aresta
X.add_edges_from([("A", "B"), ("A", "C"), ("A", "D"), ("A", "E"), ("A", "F")])

Y = nx.DiGraph(rotulo="exemplo", nome="cadeia")
Y.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")])

# simulando o envio de twts, y = nome do grafo, A:0 significa que o vértice A postou no minuto 0
nx.set_node_attributes(Y, {"A": 0, "B": 5, "C": 9, "D": 30, "E": 31, "F": 60}, "horario")

# percorre os dois grafos e le os atributos
for G in (X, Y):
    print(G.graph["nome"])
    print("  vértices:", G.number_of_nodes(), "| arestas:", G.number_of_edges())
    print("  é árvore direcionada?", nx.is_arborescence(G))
    print("  densidade:", nx.density(G))                              # 1/6 nas duas
    print("  profundidade:", max(nx.shortest_path_length(G, "A").values()))
    print("  lista de adjacência:", dict(G.adjacency()))

print("horário de D em Y:", Y.nodes["D"]["horario"])
