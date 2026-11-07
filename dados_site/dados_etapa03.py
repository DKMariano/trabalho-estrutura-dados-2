
"""
DGB SIM — Etapa 03
Dados demonstrativos da rede internacional.

Futuramente, a rede será processada com igraph,
e sua representação poderá utilizar Cairo.

Não executa BFS, DFS ou Dijkstra.
"""

# Vértices da rede demonstrativa.
VERTICES_DEMONSTRACAO = [
    "BR", "FR", "ES", "PT", "US"
]

# Arestas com latências fictícias.
CONEXOES_DEMONSTRACAO = [
    {"origem": "BR", "destino": "FR", "latencia_ms": 32},
    {"origem": "FR", "destino": "ES", "latencia_ms": 48},
    {"origem": "ES", "destino": "PT", "latencia_ms": 35},
    {"origem": "BR", "destino": "US", "latencia_ms": 180},
    {"origem": "FR", "destino": "US", "latencia_ms": 150},
    {"origem": "ES", "destino": "US", "latencia_ms": 210}
]

# Posições visuais relativas dos vértices.
POSICOES_GRAFO = {
    "BR": (0.10, 0.55),
    "FR": (0.38, 0.20),
    "ES": (0.68, 0.35),
    "PT": (0.90, 0.55),
    "US": (0.40, 0.85)
}

# Cenários predefinidos para apresentação.
# Chave: (origem, destino, criterio)
CENARIOS_DEMONSTRACAO = {
    ("BR", "PT", "menor_latencia"): {
        "caminho": ["BR", "FR", "ES", "PT"],
        "latencias_trechos": [32, 48, 35],
        "latencia_total_ms": 115,
        "custo_total_usd": 12.50,
        "criterio": "Menor latência",
        "algoritmo_previsto": "Dijkstra",
        "demonstrativo": True
    }
}

# Informações para os cards de exploração.
ALGORITMOS_DEMONSTRACAO = {
    "bfs": {
        "nome": "BFS",
        "descricao": "Busca em Largura",
        "disponivel": False
    },
    "dfs": {
        "nome": "DFS",
        "descricao": "Busca em Profundidade",
        "disponivel": False
    }
}
