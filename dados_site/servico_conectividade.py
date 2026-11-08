
"""
DGB SIM — Serviço de conectividade.

Reúne dados das Etapas 01, 02 e 03 para
a página Minha conectividade.

Nesta versão:
- Países: Tabela Hash existente.
- Clientes e eSIMs: dados demonstrativos.
- Pacotes: catálogo existente.
- Rotas: cenários demonstrativos predefinidos.

Não executa algoritmos de grafos.
"""

from dados_site.dados_etapa02 import CLIENTES_DEMONSTRACAO

from dados_site.dados_etapa03 import (
    VERTICES_DEMONSTRACAO,
    CONEXOES_DEMONSTRACAO,
    POSICOES_GRAFO,
    CENARIOS_DEMONSTRACAO,
    ALGORITMOS_DEMONSTRACAO
)


def criar_resposta(sucesso, mensagem, dados=None):
    """Padroniza a resposta enviada ao Flask."""

    return {
        "sucesso": sucesso,
        "mensagem": mensagem,
        "demonstrativo": True,
        "dados": dados
    }


def consultar_conectividade(
    cliente_id,
    origem,
    destino,
    criterio,
    tabela_paises,
    pacotes
):
    """
    Consulta os dados disponíveis para um cenário
    demonstrativo de conectividade.
    """

    # --------------------------------------
    # 1. Normalizar os dados do formulário
    # --------------------------------------

    cliente_id = str(cliente_id or "").strip()
    origem = str(origem or "").strip().upper()
    destino = str(destino or "").strip().upper()
    criterio = str(criterio or "").strip()

    if not all([cliente_id, origem, destino, criterio]):
        return criar_resposta(
            False,
            "Preencha todos os campos da consulta."
        )

    # --------------------------------------
    # 2. Buscar cliente da Etapa 02
    # --------------------------------------

    cliente = CLIENTES_DEMONSTRACAO.get(cliente_id)

    if cliente is None:
        return criar_resposta(
            False,
            "Cliente não encontrado nos dados demonstrativos."
        )

    # --------------------------------------
    # 3. Buscar países na Tabela Hash
    # --------------------------------------

    pais_origem = tabela_paises.buscar(origem)
    pais_destino = tabela_paises.buscar(destino)

    if pais_origem is None:
        return criar_resposta(
            False,
            "País de origem não encontrado no cadastro."
        )

    if pais_destino is None:
        return criar_resposta(
            False,
            "País de destino não encontrado no cadastro."
        )

    # --------------------------------------
    # 4. Buscar pacote associado ao cliente
    # --------------------------------------

    # O eSIM agora é armazenado como uma string.
    esim = cliente["esim"]

    # O pacote é um campo direto do cliente.
    codigo_pacote = str(cliente["pacote"])

    # Busca o pacote no catálogo existente.
    pacote = pacotes.get(codigo_pacote)

    if pacote is None:
        return criar_resposta(
            False,
            "Pacote associado ao cliente não encontrado."
        )

    # --------------------------------------
    # 5. Buscar cenário da Etapa 03
    # --------------------------------------

    chave = (origem, destino, criterio)

    cenario = CENARIOS_DEMONSTRACAO.get(chave)

    if cenario is None:
        return criar_resposta(
            False,
            "Esta combinação ainda não possui "
            "um cenário demonstrativo disponível."
        )

    # --------------------------------------
    # 6. Preparar informações da rota
    # --------------------------------------

    caminho = cenario["caminho"]
    latencias = cenario["latencias_trechos"]

    trechos = []

    for i in range(len(caminho) - 1):
        trechos.append({
            "origem": caminho[i],
            "destino": caminho[i + 1],
            "latencia_ms": latencias[i]
        })

    # --------------------------------------
    # 7. Preparar os dados para o HTML
    # --------------------------------------

    resultado = {
        "cliente": {
            "id": cliente["id"],
            "nome": cliente["nome"],
            "status": cliente["status"]
        },

        "esim": {
            "codigo": esim
        },

        "pacote": {
            "codigo": codigo_pacote,
            "nome": pacote["nome"],
            "dados_gb": pacote["dados_gb"],
            "validade_dias": pacote["validade_dias"]
        },

        "origem": {
            "codigo": origem,
            "nome": pais_origem["nome"]
        },

        "cobertura": {
            "codigo": destino,
            "pais": pais_destino["nome"],
            "regiao": pais_destino["regiao"],
            "tecnologia": pais_destino["tecnologia"],
            "operadoras": [pais_destino["operadora"]],
            "status": "Cadastrada"
        },

        "rota": {
            "origem": origem,
            "destino": destino,
            "criterio": cenario["criterio"],
            "algoritmo_previsto": cenario["algoritmo_previsto"],
            "caminho": caminho.copy(),
            "trechos": trechos,
            "latencia_total_ms": cenario["latencia_total_ms"],
            "custo_total_usd": cenario["custo_total_usd"],
            "calculada": False
        },

        "grafo": {
            "vertices": VERTICES_DEMONSTRACAO.copy(),
            "conexoes": [
                conexao.copy()
                for conexao in CONEXOES_DEMONSTRACAO
            ],
            "posicoes": POSICOES_GRAFO.copy()
        },

        "exploracao": {
            chave: algoritmo.copy()
            for chave, algoritmo
            in ALGORITMOS_DEMONSTRACAO.items()
        }
    }

    return criar_resposta(
        True,
        "Consulta demonstrativa realizada.",
        resultado
    )
