
"""
DGB SIM — Serviço de conectividade.

Coordena a consulta integrada do PDF (Etapa 2):

    Árvore B (cliente) -> pacote do cliente -> Tabela Hash (destino)
    -> decisão de cobertura

e, separadamente, a rota demonstrativa da Etapa 3.

Nesta versão:
- Clientes: busca simulada (mesma interface da Árvore B real).
- Países: Tabela Hash existente (operação real).
- Pacotes: catálogo pacotes.json.
- Rotas: cenários demonstrativos predefinidos (Etapa 3).

A consulta da Etapa 2 NÃO depende da rota: funciona para qualquer
cliente e qualquer destino.

Não executa algoritmos de grafos.
"""

# Backend de clientes da Etapa 2: buscas pelas Árvores B (ID e e-mail).
from dados_site.dados_etapa02 import buscar_cliente_por_id, buscar_cliente_por_email

from dados_site.regras_planos import (
    plano_vigente,
    cobertura_do_plano,
    planos_compativeis,
)

from dados_site.dados_etapa03 import CENARIOS_DEMONSTRACAO


# =====================================================================
# ETAPA 2 — CLIENTE × DESTINO
# =====================================================================

def _dados_publicos(cliente):
    """Cópia do registro sem a senha, para enviar ao template."""
    return {campo: valor for campo, valor in cliente.items() if campo != "senha"}


def consultar_cobertura_cliente(identificador, destino, tabela_paises, pacotes):
    """
    Consulta integrada da Etapa 2.

    identificador: ID do cliente ou e-mail (com "@").
    destino: código do país.

    Devolve um dicionário com:
    - sucesso: a consulta chegou à decisão de cobertura;
    - coberto: o plano do cliente cobre o destino;
    - situacao: código curto do resultado (usado pelos templates);
    - mensagem, cliente, pacote, destino, planos_compativeis;
    - passos: o que cada estrutura respondeu, na ordem;
    - instrumentacao: dados da busca na Árvore B.
    """
    identificador = str(identificador or "").strip()
    destino = str(destino or "").strip().upper()

    resposta = {
        "sucesso": False,
        "coberto": False,
        "situacao": None,
        "mensagem": "",
        "cliente": None,
        "pacote": None,
        "destino": None,
        "planos_compativeis": [],
        "passos": [],
        "instrumentacao": None,
    }

    def encerrar(situacao, mensagem, sucesso=False):
        resposta["situacao"] = situacao
        resposta["mensagem"] = mensagem
        resposta["sucesso"] = sucesso
        return resposta

    if not identificador or not destino:
        return encerrar("dados_incompletos", "Informe o cliente (ID ou e-mail) e o destino.")

    # -----------------------------------------------------------------
    # 1. ÁRVORE B: localizar o cliente (por e-mail ou por ID)
    # -----------------------------------------------------------------
    if "@" in identificador:
        cliente, instrumentacao = buscar_cliente_por_email(identificador)
        estrutura = "Árvore B de e-mail"
    else:
        cliente, instrumentacao = buscar_cliente_por_id(identificador)
        estrutura = "Árvore B de ID"

    resposta["instrumentacao"] = instrumentacao
    resposta["passos"].append({
        "estrutura": estrutura,
        "operacao": f"buscar({instrumentacao['chave']!r})",
        "resultado": (f"posição {instrumentacao['posicao']} no arquivo"
                      if instrumentacao["encontrado"] else "chave não encontrada"),
        "simulado": instrumentacao["simulado"],
    })

    if cliente is None:
        return encerrar("nao_encontrado", "Cadastro não localizado.")

    resposta["cliente"] = _dados_publicos(cliente)

    # -----------------------------------------------------------------
    # 2. STATUS: cliente inativo encerra a consulta
    # -----------------------------------------------------------------
    if cliente["status"] != "ativo":
        return encerrar(
            "inativo",
            "Cliente inativo: a consulta de conectividade está bloqueada."
        )

    # -----------------------------------------------------------------
    # 3. TABELA HASH: consultar o destino pela chave
    # -----------------------------------------------------------------
    pais = tabela_paises.buscar(destino)

    resposta["passos"].append({
        "estrutura": "Tabela Hash",
        "operacao": f"buscar({destino!r})",
        "resultado": "país encontrado" if pais else "chave não encontrada",
        "simulado": False,
    })

    if pais is None:
        return encerrar(
            "destino_inexistente",
            f"O país {destino} não está cadastrado como atendido."
        )

    resposta["destino"] = {"codigo": destino, **pais}
    compativeis = planos_compativeis(pais, pacotes)

    # -----------------------------------------------------------------
    # 4. PACOTE do cliente no catálogo
    # -----------------------------------------------------------------
    if cliente["pacote"] is None:
        resposta["planos_compativeis"] = compativeis
        return encerrar("sem_plano", "O cliente não possui plano contratado.", sucesso=True)

    pacote = pacotes.get(str(cliente["pacote"]))

    resposta["passos"].append({
        "estrutura": "Catálogo de pacotes (JSON)",
        "operacao": f"pacote {cliente['pacote']}",
        "resultado": pacote["nome"] if pacote else "não existe no catálogo",
        "simulado": False,
    })

    if pacote is None:
        return encerrar(
            "pacote_inexistente",
            f"Inconsistência cadastral: o pacote {cliente['pacote']} não existe no catálogo."
        )

    resposta["pacote"] = {"codigo": str(cliente["pacote"]), **pacote}

    # -----------------------------------------------------------------
    # 5. VIGÊNCIA (plano expirado não desativa o cliente)
    # -----------------------------------------------------------------
    if not plano_vigente(cliente):
        resposta["planos_compativeis"] = compativeis
        return encerrar(
            "expirado",
            "O plano do cliente expirou. É necessária uma nova contratação.",
            sucesso=True
        )

    # -----------------------------------------------------------------
    # 6. DECISÃO DE COBERTURA
    # -----------------------------------------------------------------
    if cobertura_do_plano(pacote, cliente, destino, pais):
        resposta["coberto"] = True
        return encerrar(
            "coberto",
            f"Cobertura disponível em {pais['nome']} pelo plano {pacote['nome']}.",
            sucesso=True
        )

    resposta["planos_compativeis"] = compativeis

    if pacote.get("categoria") == "Basic":
        mensagem = (f"{pais['nome']} não está entre os 3 países escolhidos "
                    f"no plano {pacote['nome']}.")
    else:
        mensagem = f"O plano {pacote['nome']} não cobre {pais['nome']}."

    if not compativeis:
        mensagem += " Nenhum plano compatível com este destino."

    return encerrar("sem_cobertura", mensagem, sucesso=True)


# =====================================================================
# ETAPA 3 — ROTA DEMONSTRATIVA (sem grafo real)
# =====================================================================

def rota_demonstrativa(origem, destino, criterio):
    """
    Devolve a rota simulada da combinação, ou None se não houver cenário.

    Apenas BR -> IT possui cenário. O cálculo real (grafo + Dijkstra)
    será implementado na Etapa 3.
    """
    origem = str(origem or "").strip().upper()
    destino = str(destino or "").strip().upper()
    criterio = str(criterio or "").strip()

    cenario = CENARIOS_DEMONSTRACAO.get((origem, destino, criterio))

    if cenario is None:
        return None

    caminho = cenario["caminho"]
    latencias = cenario["latencias_trechos"]

    trechos = [
        {"origem": caminho[i], "destino": caminho[i + 1], "latencia_ms": latencias[i]}
        for i in range(len(caminho) - 1)
    ]

    return {
        "origem": origem,
        "destino": destino,
        "criterio": cenario["criterio"],
        "algoritmo_previsto": cenario["algoritmo_previsto"],
        "caminho": caminho.copy(),
        "trechos": trechos,
        "latencia_total_ms": cenario["latencia_total_ms"],
        "custo_total_usd": cenario["custo_total_usd"],
        "calculada": False,
    }
