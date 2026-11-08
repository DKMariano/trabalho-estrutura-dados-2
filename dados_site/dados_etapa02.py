
"""
DGB SIM — Etapa 02
Dados demonstrativos de clientes e eSIMs.

Futuramente, estes dados serão gerenciados
pela estrutura Árvore B e este arquivo será 
excluído.

Também reúne os números demonstrativos da página Árvore B (layout para
aprovação). Nenhum deles é calculado: simulam o funcionamento esperado.
"""


CLIENTES_DEMONSTRACAO = {
    "1001": {
        "id": 1001,
        "nome": "Ines",
        "email": "ines@ed2.com",
        "senha": "123456",
        "esim": "ESIM-83921",
        "pacote": 102,
        "status": "ativo"
    },

    "58373": {
        "id": 58373,
        "nome": "Bruno Lima",
        "email": "bruno@example.com",
        "senha": "123456",
        "esim": "ESIM-01002",
        "pacote": 202,
        "status": "ativo"
    },

    "58374": {
        "id": 58374,
        "nome": "Carla Mendes",
        "email": "carla@example.com",
        "senha": "123456",
        "esim": "ESIM-01003",
        "pacote": 301,
        "status": "ativo"
    },

    "58375": {
        "id": 58375,
        "nome": "Diego Santos",
        "email": "diego@example.com",
        "senha": "123456",
        "esim": "ESIM-01004",
        "pacote": 101,
        "status": "ativo"
    },

    "58376": {
        "id": 58376,
        "nome": "Elisa Costa",
        "email": "elisa@example.com",
        "senha": "123456",
        "esim": "ESIM-01005",
        "pacote": 201,
        "status": "ativo"
    }
}


# =============================================================================
# ÁRVORE B (DEMONSTRATIVO)
# =============================================================================
#
# A Árvore B guarda APENAS a chave (ID do cliente) e a posição do registro
# no arquivo. Todos os demais dados ficam no arquivo clientes.json.

ARVORE_B_DEMONSTRACAO = {
    "grau": 12,                 # grau mínimo: até 23 chaves por nó
    "clientes": 1000,
    "altura": 2,                # raiz no nível 0
    "nos": 64,
    "divisoes": 61,             # divisões de nó durante a carga
    "media_nos_visitados": 2.9,

    # Exemplo de entradas do índice: chave + posição (nº do registro).
    "indice": [
        {"id": 53082, "posicao": 267},
        {"id": 54042, "posicao": 216},
        {"id": 58372, "posicao": 412},
        {"id": 65880, "posicao": 946},
        {"id": 71279, "posicao": 656},
    ],

    # Registro lido do arquivo na posição 412 (fora da árvore).
    "registro": {
        "posicao": 412,
        "id": 58372,
        "nome": "Maria Silva",
        "email": "maria@email.com",
        "esim": "ESIM-83921",
        "pacote": 102,
        "status": "ativo",
    },

    # Operações que descem a árvore até a chave.
    "operacoes": [
        {"operacao": "inserir", "chamadas": 3, "sucessos": 3, "falhas": 0,
         "nos_media": 3.0, "tempo_us": 14.20},
        {"operacao": "buscar", "chamadas": 14, "sucessos": 12, "falhas": 2,
         "nos_media": 2.9, "tempo_us": 6.80},
        {"operacao": "alterar", "chamadas": 2, "sucessos": 2, "falhas": 0,
         "nos_media": 3.0, "tempo_us": 9.40},
    ],

    # Últimas operações (a mais recente primeiro).
    "eventos": [
        {"hora": "18:52:10", "operacao": "buscar", "id": 58372,
         "sucesso": True, "resultado": "Encontrado", "nos": 3, "posicao": 412},
        {"hora": "18:51:47", "operacao": "buscar", "id": 12345,
         "sucesso": False, "resultado": "Não encontrado", "nos": 3, "posicao": None},
        {"hora": "18:50:05", "operacao": "alterar", "id": 58372,
         "sucesso": True, "resultado": "Sucesso", "nos": 3, "posicao": 412},
        {"hora": "18:49:31", "operacao": "inserir", "id": 80001,
         "sucesso": True, "resultado": "Sucesso", "nos": 3, "posicao": 1001},
        {"hora": "18:48:12", "operacao": "buscar", "id": 71279,
         "sucesso": True, "resultado": "Encontrado", "nos": 3, "posicao": 656},
    ],

    # Exemplo do enunciado: Árvore B (cliente) seguida da Tabela Hash (destino).
    "consulta_integrada": {
        "cliente_id": 58372,
        "destino": "IT",
        "pais": "Itália",
        "tecnologia": "5G",
    },
}


def resumo_arvore_b():
    """Números demonstrativos da Árvore B (trocar por arvore_b.py na Etapa 2)."""
    return ARVORE_B_DEMONSTRACAO
