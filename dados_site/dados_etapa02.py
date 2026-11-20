
"""
DGB SIM — Etapa 02
Dados SIMULADOS de clientes e eSIMs (temporários).

ATENÇÃO: este arquivo NÃO é a Árvore B.

Ele existe apenas para que as telas da Etapa 2 possam ser montadas antes
do backend definitivo. As funções abaixo têm os mesmos nomes e o mesmo
formato de retorno que o backend real deverá oferecer. Quando a Árvore B
e o arquivos/clientes.json estiverem prontos, basta trocar o import no
app.py e no servico_conectividade.py, e este arquivo poderá ser excluído.

Organização (decisões D1, D2 e D8):
- CLIENTES_DEMONSTRACAO é uma LISTA. O índice de cada registro simula a
  "posição no arquivo" que a Árvore B guardará (chave -> posição).
- Uma posição com None simula um registro excluído fisicamente: as
  demais posições não se deslocam.
- O campo do pacote se chama "pacote" (como no PDF oficial).

As buscas daqui percorrem a lista, o que NÃO é permitido no backend real.
Por isso toda instrumentação devolvida traz "simulado": True e não
inventa métricas: comparações, nós visitados, altura e divisões ficam
None até a Árvore B existir.

Também reúne os números demonstrativos da página Árvore B (layout para
aprovação). Nenhum deles é calculado: simulam o funcionamento esperado.
"""

STATUS_VALIDOS = ("ativo", "inativo")


# =============================================================================
# CLIENTES (SIMULADOS)
# =============================================================================
#
# Casos cobertos, para demonstrar as telas:
#   posição 0 a 4 -> ativos com plano vigente (Plus, Global e Basic)
#   posição 5     -> ativo com plano expirado
#   posição 6     -> ativo sem plano
#   posição 7     -> inativo com plano vigente (a inativação preserva tudo)
#   posição 8     -> inativo sem plano

CLIENTES_DEMONSTRACAO = [
    {   # posição 0
        "id": 1001,
        "nome": "Ines",
        "email": "ines@ed2.com",
        "senha": "123456",
        "esim": "ESIM-10001",
        "pacote": 102,
        "paises_ativos": [],
        "contratacao_inicio": "2026-11-10T10:00:00-03:00",
        "contratacao_fim": "2026-12-10T10:00:00-03:00",
        "status": "ativo",
    },
    {   # posição 1 — cliente do exemplo do enunciado (Árvore B × Tabela Hash)
        "id": 58372,
        "nome": "Maria Silva",
        "email": "maria@email.com",
        "senha": "123456",
        "esim": "ESIM-83921",
        "pacote": 102,
        "paises_ativos": [],
        "contratacao_inicio": "2026-11-10T10:00:00-03:00",
        "contratacao_fim": "2026-12-10T10:00:00-03:00",
        "status": "ativo",
    },
    {   # posição 2
        "id": 58373,
        "nome": "Bruno Lima",
        "email": "bruno@example.com",
        "senha": "123456",
        "esim": "ESIM-01002",
        "pacote": 202,
        "paises_ativos": [],
        "contratacao_inicio": "2026-11-05T09:00:00-03:00",
        "contratacao_fim": "2026-12-05T09:00:00-03:00",
        "status": "ativo",
    },
    {   # posição 3
        "id": 58374,
        "nome": "Carla Mendes",
        "email": "carla@example.com",
        "senha": "123456",
        "esim": "ESIM-01003",
        "pacote": 301,
        "paises_ativos": [],
        "contratacao_inicio": "2026-11-01T08:00:00-03:00",
        "contratacao_fim": "2026-12-01T08:00:00-03:00",
        "status": "ativo",
    },
    {   # posição 4 — Basic: exatamente 3 países da região do plano
        "id": 58375,
        "nome": "Diego Santos",
        "email": "diego@example.com",
        "senha": "123456",
        "esim": "ESIM-01004",
        "pacote": 201,
        "paises_ativos": ["BR", "CL", "MX"],
        "contratacao_inicio": "2026-11-12T14:00:00-03:00",
        "contratacao_fim": "2026-11-27T14:00:00-03:00",
        "status": "ativo",
    },
    {   # posição 5 — plano expirado (o cliente continua ativo)
        "id": 58376,
        "nome": "Elisa Costa",
        "email": "elisa@example.com",
        "senha": "123456",
        "esim": "ESIM-01005",
        "pacote": 202,
        "paises_ativos": [],
        "contratacao_inicio": "2026-10-01T10:00:00-03:00",
        "contratacao_fim": "2026-10-31T10:00:00-03:00",
        "status": "ativo",
    },
    {   # posição 6 — ainda sem plano contratado
        "id": 58377,
        "nome": "Fábio Rocha",
        "email": "fabio@example.com",
        "senha": "123456",
        "esim": "ESIM-01006",
        "pacote": None,
        "paises_ativos": [],
        "contratacao_inicio": None,
        "contratacao_fim": None,
        "status": "ativo",
    },
    {   # posição 7 — inativo: pacote, países e datas são preservados
        "id": 58378,
        "nome": "Gabriela Nunes",
        "email": "gabriela@example.com",
        "senha": "123456",
        "esim": "ESIM-01007",
        "pacote": 102,
        "paises_ativos": [],
        "contratacao_inicio": "2026-11-08T11:00:00-03:00",
        "contratacao_fim": "2026-12-08T11:00:00-03:00",
        "status": "inativo",
    },
    {   # posição 8
        "id": 58379,
        "nome": "Hugo Alves",
        "email": "hugo@example.com",
        "senha": "123456",
        "esim": "ESIM-01008",
        "pacote": None,
        "paises_ativos": [],
        "contratacao_inicio": None,
        "contratacao_fim": None,
        "status": "inativo",
    },
]


# =============================================================================
# FUNÇÕES SIMULADAS (mesma interface que o backend real deverá oferecer)
# =============================================================================

def normalizar_email(email):
    """Remove espaços das pontas e converte para minúsculas."""
    return str(email or "").strip().lower()


def _instrumentacao(arvore, chave, posicao):
    """
    Formato combinado para a instrumentação de uma busca na Árvore B.

    Aqui só "posicao" é conhecida. As métricas da árvore ficam None,
    porque a busca simulada não percorre nenhum nó.
    """
    return {
        "arvore": arvore,              # "id" ou "email"
        "chave": chave,
        "encontrado": posicao is not None,
        "posicao": posicao,
        "comparacoes": None,
        "nos_visitados": None,
        "altura": None,
        "divisoes": None,
        "simulado": True,
    }


def _posicao_por_id(cliente_id):
    for posicao, registro in enumerate(CLIENTES_DEMONSTRACAO):
        if registro is not None and registro["id"] == cliente_id:
            return posicao
    return None


def _posicao_por_email(email):
    for posicao, registro in enumerate(CLIENTES_DEMONSTRACAO):
        if registro is not None and registro["email"] == email:
            return posicao
    return None


def buscar_cliente_por_id(cliente_id):
    """
    Simula: Árvore B de ID -> posição -> registro.

    Devolve (cliente, instrumentacao). cliente é None se não existir.
    """
    try:
        cliente_id = int(str(cliente_id).strip())
    except (TypeError, ValueError):
        return None, _instrumentacao("id", cliente_id, None)

    posicao = _posicao_por_id(cliente_id)
    cliente = CLIENTES_DEMONSTRACAO[posicao] if posicao is not None else None

    return cliente, _instrumentacao("id", cliente_id, posicao)


def buscar_cliente_por_email(email):
    """
    Simula: Árvore B de e-mail -> posição -> registro.

    O e-mail é normalizado antes da busca.
    Devolve (cliente, instrumentacao).
    """
    email = normalizar_email(email)
    posicao = _posicao_por_email(email)
    cliente = CLIENTES_DEMONSTRACAO[posicao] if posicao is not None else None

    return cliente, _instrumentacao("email", email, posicao)


def listar_clientes(busca="", pacote="", status="ativo"):
    """
    Simula o percurso em ordem da Árvore B de ID (clientes ordenados por ID)
    e aplica os filtros da tela administrativa.

    busca:  número -> Árvore B de ID; texto com "@" -> Árvore B de e-mail;
            outro texto -> parte do nome (filtro sobre o percurso).
    pacote: código do pacote, "sem" (sem plano) ou "" (todos).
    status: "ativo" (padrão), "inativo" ou "todos".
    """
    busca = str(busca or "").strip()

    if busca.isdigit():
        cliente, _ = buscar_cliente_por_id(busca)
        clientes = [cliente] if cliente else []
    elif "@" in busca:
        cliente, _ = buscar_cliente_por_email(busca)
        clientes = [cliente] if cliente else []
    else:
        clientes = sorted(
            (registro for registro in CLIENTES_DEMONSTRACAO if registro is not None),
            key=lambda registro: registro["id"],
        )
        if busca:
            clientes = [c for c in clientes if busca.lower() in c["nome"].lower()]

    if status in STATUS_VALIDOS:
        clientes = [c for c in clientes if c["status"] == status]

    if pacote == "sem":
        clientes = [c for c in clientes if c["pacote"] is None]
    elif pacote:
        clientes = [c for c in clientes if str(c["pacote"]) == str(pacote)]

    return clientes


def total_clientes():
    """Quantidade de registros válidos (exclui posições removidas)."""
    return sum(1 for registro in CLIENTES_DEMONSTRACAO if registro is not None)


def _validar_dados(nome, email, esim, status, ignorar_id=None):
    """Validações comuns ao cadastro e à edição. Lança ValueError."""
    if not nome or not email or not esim:
        raise ValueError("Preencha todos os campos obrigatórios.")

    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("Informe um e-mail válido.")

    outro, _ = buscar_cliente_por_email(email)
    if outro is not None and outro["id"] != ignorar_id:
        raise ValueError("Já existe um cliente com esse e-mail.")

    for registro in CLIENTES_DEMONSTRACAO:
        if registro is not None and registro["esim"] == esim and registro["id"] != ignorar_id:
            raise ValueError("Já existe um cliente com esse eSIM.")

    if status not in STATUS_VALIDOS:
        raise ValueError("Selecione um status válido.")


def cadastrar_cliente(dados):
    """
    Simula: acrescenta o registro no FINAL da lista (nova posição) e
    "insere" a chave nas duas Árvores B.

    O cliente nasce sem plano (decisão P1): o pacote é associado
    somente pela contratação.

    dados: id, nome, email, esim, status (texto do formulário).
    Devolve o cliente criado. Lança ValueError em caso de dado inválido.
    """
    id_texto = str(dados.get("id", "")).strip()

    if not id_texto.isdigit() or int(id_texto) <= 0:
        raise ValueError("Informe um ID numérico válido.")

    cliente_id = int(id_texto)
    if _posicao_por_id(cliente_id) is not None:
        raise ValueError("Já existe um cliente com esse ID.")

    nome = str(dados.get("nome", "")).strip()
    email = normalizar_email(dados.get("email"))
    esim = str(dados.get("esim", "")).strip()
    status = str(dados.get("status", "ativo")).strip() or "ativo"

    _validar_dados(nome, email, esim, status)

    cliente = {
        "id": cliente_id,
        "nome": nome,
        "email": email,
        "senha": "123456",
        "esim": esim,
        "pacote": None,
        "paises_ativos": [],
        "contratacao_inicio": None,
        "contratacao_fim": None,
        "status": status,
    }

    CLIENTES_DEMONSTRACAO.append(cliente)
    return cliente


def editar_cliente(cliente_id, dados):
    """
    Simula: localiza pela Árvore B de ID e altera o registro NO MESMO
    LUGAR (a posição não muda). Se o e-mail mudar, o backend real deverá
    remover a chave antiga da Árvore B de e-mail e inserir a nova.

    Campos editáveis: nome, e-mail, eSIM e status. O ID é imutável e o
    pacote só muda pela contratação.
    Devolve o cliente alterado. Lança ValueError.
    """
    cliente, _ = buscar_cliente_por_id(cliente_id)
    if cliente is None:
        raise ValueError("Cliente não encontrado.")

    nome = str(dados.get("nome", "")).strip()
    email = normalizar_email(dados.get("email"))
    esim = str(dados.get("esim", "")).strip()
    status = str(dados.get("status", "")).strip()

    _validar_dados(nome, email, esim, status, ignorar_id=cliente["id"])

    cliente["nome"] = nome
    cliente["email"] = email
    cliente["esim"] = esim
    cliente["status"] = status

    return cliente


def inativar_cliente(cliente_id):
    """
    Exclusão lógica: muda SOMENTE o status para inativo. O registro continua
    na mesma posição do arquivo e nas duas Árvores B; pacote, países e datas
    são preservados.
    """
    cliente, _ = buscar_cliente_por_id(cliente_id)

    if cliente is None:
        raise ValueError("Cliente não encontrado.")
    if cliente["status"] == "inativo":
        raise ValueError("O cliente já está inativo.")

    cliente["status"] = "inativo"
    return cliente


def reativar_cliente(cliente_id):
    """Muda SOMENTE o status para ativo, preservando os demais campos."""
    cliente, _ = buscar_cliente_por_id(cliente_id)

    if cliente is None:
        raise ValueError("Cliente não encontrado.")
    if cliente["status"] == "ativo":
        raise ValueError("O cliente já está ativo.")

    cliente["status"] = "ativo"
    return cliente


def excluir_cliente_fisicamente(cliente_id, confirmacao, ciencia):
    """
    Exclusão física restrita (Zona de risco):
    - somente cliente inativo;
    - confirmação reforçada: digitar o ID do cliente (ou EXCLUIR)
      e marcar a ciência da irreversibilidade.

    Simula: a posição passa a None (nenhuma outra posição se desloca) e as
    chaves sairiam das duas Árvores B. O ID não é reutilizado.
    """
    cliente, instrumentacao = buscar_cliente_por_id(cliente_id)

    if cliente is None:
        raise ValueError("Cliente não encontrado.")

    if cliente["status"] != "inativo":
        raise ValueError(
            "Somente clientes inativos podem ser excluídos permanentemente. "
            "Inative o cliente antes."
        )

    if str(confirmacao or "").strip() not in (str(cliente["id"]), "EXCLUIR"):
        raise ValueError("Confirmação inválida: digite o ID do cliente ou EXCLUIR.")

    if not ciencia:
        raise ValueError("Marque a ciência de que a exclusão é irreversível.")

    CLIENTES_DEMONSTRACAO[instrumentacao["posicao"]] = None


def proximo_id():
    """
    Próximo ID livre = maior ID cadastrado + 1.

    Na Árvore B real, o maior ID é a chave mais à direita: basta descer
    sempre pelo último filho até a folha. Aqui a busca é simulada.
    """
    ids = [registro["id"] for registro in CLIENTES_DEMONSTRACAO if registro is not None]
    return max(ids, default=0) + 1


def criar_conta(dados):
    """
    Cadastro feito pelo próprio cliente (área pública).

    O cliente informa nome e e-mail. ID e eSIM são gerados automaticamente,
    a senha é a demonstrativa e o cliente nasce ativo e sem plano.
    Devolve o cliente criado. Lança ValueError.
    """
    cliente_id = proximo_id()

    return cadastrar_cliente({
        "id": str(cliente_id),
        "nome": dados.get("nome", ""),
        "email": dados.get("email", ""),
        "esim": f"ESIM-{cliente_id}",
        "status": "ativo",
    })


def contratar_plano(cliente_id, pacote_codigo, paises_ativos, inicio, fim):
    """
    Grava a contratação no registro do cliente (mesma posição do arquivo).
    Nenhuma chave das Árvores B muda. As validações ficam em regras_planos
    e na rota, antes desta chamada.
    """
    cliente, _ = buscar_cliente_por_id(cliente_id)

    if cliente is None:
        raise ValueError("Cliente não encontrado.")
    if cliente["status"] != "ativo":
        raise ValueError("Seu cadastro está inativo. Procure a administração da DGB SIM.")

    cliente["pacote"] = int(pacote_codigo)
    cliente["paises_ativos"] = list(paises_ativos)
    cliente["contratacao_inicio"] = inicio
    cliente["contratacao_fim"] = fim

    return cliente


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
