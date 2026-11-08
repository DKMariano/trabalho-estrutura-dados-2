
"""
DGB SIM — Etapa 03
Dados demonstrativos da rede internacional.

Futuramente, a rede será processada com igraph,
e sua representação poderá utilizar Cairo.

Não executa BFS, DFS ou Dijkstra.
Contém apenas o resumo (grau dos vértices) usado no dashboard
administrativo e os resultados PRONTOS da página Rede internacional
(layout para aprovação). Tudo será substituído pelo grafo real
(estruturas/grafo.py com igraph/Cairo).
"""


# Arestas com latências fictícias.
VERTICES_DEMONSTRACAO = [
    "BR", "PT", "FR", "IT"
]

# Posições visuais relativas dos vértices.
POSICOES_GRAFO = {
    "BR": (0.10, 0.55),
    "PT": (0.38, 0.20),
    "FR": (0.68, 0.20),
    "IT": (0.90, 0.55)
}

# Cenários predefinidos para apresentação.
CONEXOES_DEMONSTRACAO = [
    {"origem": "BR", "destino": "PT", "latencia_ms": 75,  "custo": 8},
    {"origem": "PT", "destino": "FR", "latencia_ms": 55,  "custo": 7},
    {"origem": "FR", "destino": "IT", "latencia_ms": 55,  "custo": 7},
    {"origem": "BR", "destino": "IT", "latencia_ms": 220, "custo": 12}
]

# Cenários demonstrativos
CENARIOS_DEMONSTRACAO = {
    ("BR", "IT", "menor_latencia"): {
        "caminho": ["BR", "PT", "FR", "IT"],
        "latencias_trechos": [75, 55, 55],
        "latencia_total_ms": 185,
        "custo_total_usd": 22.00,
        "criterio": "Menor latência",
        "algoritmo_previsto": "Dijkstra",
        "demonstrativo": True
    },
    
    ("BR", "IT", "menor_custo"): {
        "caminho": ["BR", "IT"],
        "latencias_trechos": [220],
        "latencia_total_ms": 220,
        "custo_total_usd": 12.00,
        "criterio": "Menor custo",
        "algoritmo_previsto": "Otimização por custo",
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

def resumo_grafo():
    """Métricas do grafo demonstrativo (trocar por grafo.py na Etapa 3)."""

    graus = {v: 0 for v in VERTICES_DEMONSTRACAO}

    for c in CONEXOES_DEMONSTRACAO:
        graus[c["origem"]] += 1
        graus[c["destino"]] += 1

    maior = max(graus.values(), default=0)

    return {
        "paises": len(VERTICES_DEMONSTRACAO),
        "conexoes": len(CONEXOES_DEMONSTRACAO),
        "isolados": sum(1 for g in graus.values() if g == 0),
        "maior_grau": maior,
        "paises_maior_grau": [v for v, g in graus.items() if g == maior],
        "graus": graus,
    }


# =============================================================================
# PÁGINA REDE INTERNACIONAL (DEMONSTRATIVO)
# =============================================================================
#
# Nada abaixo é calculado: são resultados PRONTOS que mostram como a página
# ficará. Quando existirem estruturas/grafo.py e o desenho com igraph/Cairo:
#   - rede_demonstracao() passa a montar o dicionário a partir do grafo real;
#   - "imagem" recebe a URL do PNG/SVG gerado pelo Cairo (o template então
#     mostra a imagem no lugar do SVG de demonstração);
#   - execucao_demonstrativa() passa a executar BFS, DFS ou Dijkstra e devolver
#     o MESMO formato de dicionário.

NOMES_PAISES_DEMONSTRACAO = {
    "BR": "Brasil",
    "PT": "Portugal",
    "FR": "França",
    "IT": "Itália"
}

ALGORITMOS_REDE = {
    "bfs": {
        "nome": "BFS — Busca em largura",
        "explicacao": (
            "A BFS explora a rede por níveis: primeiro os vizinhos da origem, "
            "depois os vizinhos deles."
        )
    },
    "dfs": {
        "nome": "DFS — Busca em profundidade",
        "explicacao": (
            "A DFS explora cada ramo em profundidade antes de retornar."
        )
    },
    "dijkstra": {
        "nome": "Dijkstra — Menor caminho",
        "explicacao": (
            "O Dijkstra usa o peso do critério escolhido (latência ou custo) "
            "e calcula a rota de menor total."
        )
    }
}

# Rotas possíveis de Brasil até Itália, com as parcelas de cada trecho.
# Mostram POR QUE o Dijkstra escolhe uma rota: compara as somas.
ROTAS_POSSIVEIS_BR_IT = [
    {"caminho": ["BR", "PT", "FR", "IT"],
     "latencias": [75, 55, 55], "latencia_total_ms": 185,
     "custos": [8, 7, 7], "custo_total": 22},
    {"caminho": ["BR", "IT"],
     "latencias": [220], "latencia_total_ms": 220,
     "custos": [12], "custo_total": 12},
]

# Resultados prontos. Chave: (algoritmo, origem) para BFS e DFS;
# (algoritmo, origem, destino, critério) para o Dijkstra.
# Listas (e não tuplas) para o template comparar as arestas.
EXECUCOES_DEMONSTRACAO = {
    ("bfs", "BR"): {
        "algoritmo": "bfs",
        "origem": "BR",
        "ordem": ["BR", "IT", "PT", "FR"],
        "nivel": {"BR": 0, "IT": 1, "PT": 1, "FR": 2},
        "vertices_destacados": ["BR", "IT", "PT", "FR"],
        "arestas_destacadas": [["BR", "IT"], ["BR", "PT"], ["IT", "FR"]]
    },

    ("dfs", "BR"): {
        "algoritmo": "dfs",
        "origem": "BR",
        "ordem": ["BR", "IT", "FR", "PT"],
        "nivel": {"BR": 0, "IT": 1, "FR": 2, "PT": 3},
        "vertices_destacados": ["BR", "IT", "FR", "PT"],
        "arestas_destacadas": [["BR", "IT"], ["IT", "FR"], ["FR", "PT"]]
    },

    ("dijkstra", "BR", "IT", "menor_latencia"): {
        "algoritmo": "dijkstra",
        "origem": "BR",
        "destino": "IT",
        "criterio": "menor_latencia",
        "vertices_destacados": ["BR", "PT", "FR", "IT"],
        "arestas_destacadas": [["BR", "PT"], ["PT", "FR"], ["FR", "IT"]],
        "rota": {
            "criterio_nome": "Menor latência",
            "caminho": ["BR", "PT", "FR", "IT"],
            "trechos": [
                {"origem": "BR", "destino": "PT", "latencia_ms": 75, "custo": 8},
                {"origem": "PT", "destino": "FR", "latencia_ms": 55, "custo": 7},
                {"origem": "FR", "destino": "IT", "latencia_ms": 55, "custo": 7}
            ],
            "latencia_total_ms": 185,
            "custo_total": 22
        },
        "unidade": "ms",
        "alternativas": ROTAS_POSSIVEIS_BR_IT,
        # Cada passo: o vértice de menor distância ainda não fechado e o que
        # ele atualizou nos vizinhos.
        "passos": [
            {"escolhido": "BR", "distancia": 0,
             "atualizacoes": ["PT = 75 (via BR)", "IT = 220 (via BR)"]},
            {"escolhido": "PT", "distancia": 75,
             "atualizacoes": ["FR = 130 (via PT)"]},
            {"escolhido": "FR", "distancia": 130,
             "atualizacoes": ["IT = 185 (via FR), menor que 220"]},
            {"escolhido": "IT", "distancia": 185,
             "atualizacoes": []},
        ],
        "conclusao": (
            "185 ms (com escalas) é menor que 220 ms (rota direta): "
            "por isso o Dijkstra escolhe o caminho BR → PT → FR → IT."
        )
    },

    ("dijkstra", "BR", "IT", "menor_custo"): {
        "algoritmo": "dijkstra",
        "origem": "BR",
        "destino": "IT",
        "criterio": "menor_custo",
        "vertices_destacados": ["BR", "IT"],
        "arestas_destacadas": [["BR", "IT"]],
        "rota": {
            "criterio_nome": "Menor custo",
            "caminho": ["BR", "IT"],
            "trechos": [
                {"origem": "BR", "destino": "IT", "latencia_ms": 220, "custo": 12}
            ],
            "latencia_total_ms": 220,
            "custo_total": 12
        },
        "unidade": "UC",
        "alternativas": ROTAS_POSSIVEIS_BR_IT,
        "passos": [
            {"escolhido": "BR", "distancia": 0,
             "atualizacoes": ["PT = 8 (via BR)", "IT = 12 (via BR)"]},
            {"escolhido": "PT", "distancia": 8,
             "atualizacoes": ["FR = 15 (via PT)"]},
            {"escolhido": "IT", "distancia": 12,
             "atualizacoes": []},
        ],
        "conclusao": (
            "UC 12 (rota direta) é menor que UC 22 (com escalas): a rota "
            "mais barata é BR → IT, embora tenha latência maior (220 ms "
            "contra 185 ms)."
        )
    }
}

# Instrumentação demonstrativa dos algoritmos (médias das execuções com sucesso).
INSTRUMENTACAO_REDE_DEMONSTRACAO = [
    {"algoritmo": "BFS", "execucoes": 3, "sucessos": 3, "falhas": 0,
     "vertices_media": 4.0, "arestas_media": 8.0, "tempo_us": 12.40},
    {"algoritmo": "DFS", "execucoes": 2, "sucessos": 2, "falhas": 0,
     "vertices_media": 4.0, "arestas_media": 8.0, "tempo_us": 11.80},
    {"algoritmo": "Dijkstra", "execucoes": 3, "sucessos": 2, "falhas": 1,
     "vertices_media": 3.5, "arestas_media": 5.0, "tempo_us": 18.60}
]

# Últimas execuções (a mais recente primeiro). As falhas seguem o tratamento
# de situações excepcionais do diferencial: origem/destino indisponível.
EVENTOS_REDE_DEMONSTRACAO = [
    {"hora": "18:55:02", "algoritmo": "Dijkstra", "origem": "BR", "destino": "IT",
     "criterio": "Menor custo", "sucesso": True, "resultado": "Rota encontrada",
     "vertices": 3, "total": "220 ms · UC 12,00"},
    {"hora": "18:54:40", "algoritmo": "Dijkstra", "origem": "BR", "destino": "IT",
     "criterio": "Menor latência", "sucesso": True, "resultado": "Rota encontrada",
     "vertices": 4, "total": "185 ms · UC 22,00"},
    {"hora": "18:53:11", "algoritmo": "BFS", "origem": "BR", "destino": None,
     "criterio": None, "sucesso": True, "resultado": "Concluída",
     "vertices": 4, "total": None},
    {"hora": "18:52:30", "algoritmo": "DFS", "origem": "BR", "destino": None,
     "criterio": None, "sucesso": True, "resultado": "Concluída",
     "vertices": 4, "total": None},
    {"hora": "18:51:05", "algoritmo": "Dijkstra", "origem": "BR", "destino": "XX",
     "criterio": "Menor latência", "sucesso": False, "resultado": "Destino indisponível",
     "vertices": 0, "total": None},
]


# Comparação dos três algoritmos para o mesmo par de países (Brasil → Itália).
# BFS e DFS ignoram os pesos; só o Dijkstra minimiza a latência.
COMPARACAO_ALGORITMOS_BR_IT = {
    "origem": "BR",
    "destino": "IT",
    "linhas": [
        {"algoritmo": "BFS", "regra": "menos conexões (saltos)",
         "caminho": ["BR", "IT"], "saltos": 1,
         "latencia_ms": 220, "custo": 12, "menor_latencia": False},
        {"algoritmo": "DFS", "regra": "primeiro caminho encontrado",
         "caminho": ["BR", "IT"], "saltos": 1,
         "latencia_ms": 220, "custo": 12, "menor_latencia": False},
        {"algoritmo": "Dijkstra", "regra": "menor soma de latência",
         "caminho": ["BR", "PT", "FR", "IT"], "saltos": 3,
         "latencia_ms": 185, "custo": 22, "menor_latencia": True},
    ],
    "conclusao": (
        "BFS e DFS ignoram os pesos e escolhem a rota direta (220 ms). "
        "Só o Dijkstra garante a menor latência: 185 ms, 35 ms mais rápido."
    ),
}


def rede_demonstracao():
    """Grafo para desenhar na página (trocar por grafo.py + igraph/Cairo)."""

    return {
        "vertices": [
            {
                "codigo": codigo,
                "nome": NOMES_PAISES_DEMONSTRACAO[codigo],
                "x": POSICOES_GRAFO[codigo][0],
                "y": POSICOES_GRAFO[codigo][1]
            }
            for codigo in VERTICES_DEMONSTRACAO
        ],
        "arestas": [conexao.copy() for conexao in CONEXOES_DEMONSTRACAO],
        # URL da imagem gerada pelo Cairo. Enquanto for None, o template
        # desenha o SVG de demonstração.
        "imagem": None,
        "comparacao": COMPARACAO_ALGORITMOS_BR_IT
    }


def execucao_demonstrativa(algoritmo, origem, destino=None, criterio=None):
    """Devolve o resultado pronto da execução, ou None se não houver cenário."""

    if algoritmo == "dijkstra":
        chave = (algoritmo, origem, destino, criterio)
    else:
        chave = (algoritmo, origem)

    return EXECUCOES_DEMONSTRACAO.get(chave)
