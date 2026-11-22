"""
DGB SIM — Etapa 02
Backend de clientes: duas Árvores B (ID e e-mail) + persistência em JSON.

Organização:
- arquivos/clientes.json é uma lista. O índice de cada registro é a
  "posição no arquivo" que as Árvores B guardam (chave -> posição).
- Uma posição com None é um cliente excluído fisicamente: as demais
  posições não se deslocam e o ID nunca é reutilizado
  (arquivos/controle_ids.json guarda proximo_id e ids_utilizados).
- A Árvore B de ID usa chave inteira; a de e-mail usa o e-mail
  normalizado (strip().lower()). As árvores não guardam os dados do
  cliente, apenas a posição.
- Buscas por ID ou e-mail sempre passam pela Árvore B; a lista nunca é
  percorrida.

Ordem das alterações (cadastrar, editar, inativar, reativar, excluir,
contratar): validar, preparar uma cópia, gravar no arquivo e só depois
atualizar a memória e as árvores. As funções que devolvem um cliente
devolvem uma cópia.

Situações de bloqueio (sem rollback, nova tentativa ou restauração):
- Indisponível: os dados não puderam ser carregados ou reconstruídos.
  Todas as funções de clientes lançam ErroIndices, exceto
  normalizar_email, resumo_arvore_b e instrumentacao_arvore_b. As
  funcionalidades de países (Etapa 1) continuam funcionando, porque o
  import nunca lança exceção.
- Falha de gravação: um OSError ao gravar bloqueia novas alterações até
  a aplicação ser reiniciada (ou inicializar() ser chamada); as
  consultas continuam funcionando.

Pacote no cadastro e na edição: cadastrar_cliente() e editar_cliente()
só gravam um pacote quando os dados trazem "pacote" e "paises_ativos"
(lista vazia para Plus e Global). Caso contrário, o pacote é ignorado
aqui e o app.py faz a associação depois, com contratar_plano().
"""

import threading
from datetime import datetime

from arquivos import persistencia_clientes as persistencia
from arquivos.persistencia_clientes import CAMINHO_CLIENTES, CAMINHO_CONTROLE
from arquivos.persistencia_pacotes import carregar_pacotes
from arquivos.persistencia_paises import carregar_paises
from dados_site.regras_planos import calcular_fim, validar_paises_basic
from estruturas.arvore_b import ArvoreB

STATUS_VALIDOS = ("ativo", "inativo")
GRAU_MINIMO = 3
SENHA_PADRAO = "123456"
MAX_PROBLEMAS_NA_MENSAGEM = 10

# Mensagens exatas (consumidas pelo app.py e pelos testes).
MSG_FALHA_GRAVACAO = (
    "Não foi possível gravar os dados de clientes. As alterações de clientes "
    "estão bloqueadas até a aplicação ser reiniciada."
)
MSG_NAO_ENCONTRADO = "Cliente não encontrado."
MSG_CAMPOS_VAZIOS = "Preencha todos os campos obrigatórios."
MSG_EMAIL_INVALIDO = "Informe um e-mail válido."
MSG_EMAIL_DUPLICADO = "Já existe um cliente com esse e-mail."
MSG_STATUS_INVALIDO = "Selecione um status válido."
MSG_EMAIL_IMUTAVEL = "O e-mail não pode ser alterado."
MSG_JA_INATIVO = "O cliente já está inativo."
MSG_JA_ATIVO = "O cliente já está ativo."
MSG_EXCLUIR_ATIVO = (
    "Somente clientes inativos podem ser excluídos permanentemente. "
    "Inative o cliente antes."
)
MSG_CONFIRMACAO = "Confirmação inválida: digite o ID do cliente ou EXCLUIR."
MSG_CIENCIA = "Marque a ciência de que a exclusão é irreversível."
MSG_CONTRATAR_INATIVO = "Seu cadastro está inativo. Procure a administração da DGB SIM."
MSG_PLANO_INVALIDO = "Selecione um plano válido."
MSG_PACOTE_STATUS = "Para associar um pacote, o status do cliente deve ser Ativo."


class ErroIndices(RuntimeError):
    """Dados de clientes indisponíveis (arquivos ou índices inconsistentes)."""


# =============================================================================
# ESTADO EM MEMÓRIA
# =============================================================================

_clientes = []                                   # list[dict | None]
_controle_ids = {"proximo_id": 1, "ids_utilizados": []}
_arvore_id = ArvoreB(GRAU_MINIMO, "id")          # chave int
_arvore_email = ArvoreB(GRAU_MINIMO, "email")    # chave str normalizada
_caminho_clientes = CAMINHO_CLIENTES
_caminho_controle = CAMINHO_CONTROLE
_erro_indisponivel = None                        # str | None
_erro_gravacao = None                            # str | None

# O Flask atende em várias threads: as alterações são serializadas para que
# dois cadastros simultâneos não recebam o mesmo ID.
_TRAVA = threading.RLock()


# =============================================================================
# CONSTRUÇÃO DOS ÍNDICES E INICIALIZAÇÃO
# =============================================================================

def construir_indices(clientes):
    """
    Constrói do zero as duas Árvores B a partir da lista de clientes.

    Pula posições None (excluídos), valida id e e-mail de cada registro,
    confere duplicidades, carrega as árvores, roda validar() e compara o
    percurso em ordem com os pares esperados.

    Devolve (arvore_id, arvore_email). Lança ValueError com os problemas
    encontrados (a mensagem mostra os primeiros e a quantidade restante).
    """
    problemas = []
    pares_id, pares_email = [], []
    posicao_do_id, posicao_do_email = {}, {}

    for posicao, registro in enumerate(clientes):
        if registro is None:
            continue

        if not isinstance(registro, dict):
            problemas.append(f"posição {posicao}: registro inválido")
            continue

        cid = registro.get("id")
        if type(cid) is not int or cid <= 0:
            problemas.append(f"posição {posicao}: id inválido ({cid!r})")
        elif cid in posicao_do_id:
            problemas.append(
                f"id {cid} duplicado (posições {posicao_do_id[cid]} e {posicao})"
            )
        else:
            posicao_do_id[cid] = posicao
            pares_id.append((cid, posicao))

        email = registro.get("email")
        if (not isinstance(email, str) or email != email.strip().lower()
                or "@" not in email):
            problemas.append(f"posição {posicao}: e-mail inválido ou não normalizado ({email!r})")
        elif email in posicao_do_email:
            problemas.append(
                f"e-mail {email} duplicado (posições {posicao_do_email[email]} e {posicao})"
            )
        else:
            posicao_do_email[email] = posicao
            pares_email.append((email, posicao))

    arvore_id = ArvoreB(GRAU_MINIMO, "id")
    arvore_email = ArvoreB(GRAU_MINIMO, "email")

    if not problemas:
        try:
            arvore_id.carregar(pares_id)
            arvore_email.carregar(pares_email)

            for rotulo, arvore, pares in (
                ("ID", arvore_id, pares_id),
                ("e-mail", arvore_email, pares_email),
            ):
                for inconsistencia in arvore.validar():
                    problemas.append(f"Árvore B de {rotulo}: {inconsistencia}")
                if arvore.percorrer_em_ordem() != sorted(pares):
                    problemas.append(
                        f"Árvore B de {rotulo}: percurso em ordem diferente dos registros"
                    )
        except Exception as erro:  # a árvore recusou algum dado
            problemas.append(f"falha ao construir as Árvores B: {erro}")

    if problemas:
        mostrados = problemas[:MAX_PROBLEMAS_NA_MENSAGEM]
        texto = "; ".join(mostrados)
        if len(problemas) > len(mostrados):
            texto += f"; e mais {len(problemas) - len(mostrados)} problema(s)"
        raise ValueError(texto)

    return arvore_id, arvore_email


def _motivo(erro):
    """Texto curto (sem ponto final) para a mensagem de indisponibilidade."""
    if isinstance(erro, FileNotFoundError):
        texto = f"arquivo não encontrado ({erro.filename})"
    elif isinstance(erro, OSError):
        texto = f"falha ao ler {erro.filename}: {erro.strerror}" if erro.filename else str(erro)
    elif isinstance(erro, ValueError) and type(erro).__name__ == "JSONDecodeError":
        texto = f"JSON inválido ({erro})"
    else:
        texto = str(erro)
    return texto.strip().rstrip(".").strip() or type(erro).__name__


def inicializar(caminho_clientes=None, caminho_controle=None):
    """
    Carrega clientes.json e controle_ids.json, reconstrói as duas Árvores B
    e confere o controle de IDs.

    Com caminhos, todas as gravações seguintes usam esses caminhos; sem
    caminhos, volta aos padrão. NUNCA lança exceção: qualquer falha liga o
    aviso "indisponível" para o Flask subir e a Etapa 1 continuar funcionando.
    """
    global _clientes, _controle_ids, _arvore_id, _arvore_email
    global _caminho_clientes, _caminho_controle, _erro_indisponivel, _erro_gravacao

    with _TRAVA:
        _caminho_clientes = caminho_clientes if caminho_clientes is not None else CAMINHO_CLIENTES
        _caminho_controle = caminho_controle if caminho_controle is not None else CAMINHO_CONTROLE

        try:
            clientes = persistencia.carregar_clientes(_caminho_clientes)
            controle = persistencia.carregar_controle_ids(_caminho_controle)
            arvore_id, arvore_email = construir_indices(clientes)

            inconsistencias = persistencia.validar_controle_ids(clientes, controle)
            if inconsistencias:
                raise ValueError("controle de IDs inconsistente: " + "; ".join(inconsistencias))
        except Exception as erro:
            _clientes = []
            _controle_ids = {"proximo_id": 1, "ids_utilizados": []}
            _arvore_id = ArvoreB(GRAU_MINIMO, "id")
            _arvore_email = ArvoreB(GRAU_MINIMO, "email")
            _erro_indisponivel = _motivo(erro)
            _erro_gravacao = None
            return

        _clientes = clientes
        _controle_ids = controle
        _arvore_id = arvore_id
        _arvore_email = arvore_email
        _erro_indisponivel = None
        _erro_gravacao = None


# =============================================================================
# BLOQUEIOS E AUXILIARES
# =============================================================================

def _mensagem_indisponivel():
    return (
        f"Os dados de clientes estão indisponíveis: {_erro_indisponivel}. "
        "As funcionalidades de países continuam disponíveis."
    )


def _exigir_disponivel():
    """Toda função de clientes (exceto as isentas) começa por aqui."""
    if _erro_indisponivel is not None:
        raise ErroIndices(_mensagem_indisponivel())


def _exigir_alteracao():
    """Toda função que ALTERA dados começa por aqui."""
    _exigir_disponivel()
    if _erro_gravacao is not None:
        raise ValueError(MSG_FALHA_GRAVACAO)


def _falha_de_gravacao():
    """Liga o bloqueio de gravação e devolve o erro a ser lançado."""
    global _erro_gravacao
    _erro_gravacao = MSG_FALHA_GRAVACAO
    return ValueError(MSG_FALHA_GRAVACAO)


def _gravar_clientes(lista):
    try:
        persistencia.salvar_clientes(lista, _caminho_clientes)
    except OSError as erro:
        raise _falha_de_gravacao() from erro


def _gravar_controle(controle):
    try:
        persistencia.salvar_controle_ids(controle, _caminho_controle)
    except OSError as erro:
        raise _falha_de_gravacao() from erro


def normalizar_email(email):
    """Remove espaços das pontas e converte para minúsculas."""
    return str(email or "").strip().lower()


def _texto(valor):
    return "" if valor is None else str(valor).strip()


def _converter_id(valor):
    """int > 0 ou None (não consulta a árvore com ID inválido)."""
    if isinstance(valor, int) and not isinstance(valor, bool):
        cid = valor
    else:
        texto = _texto(valor)
        if not (texto.isascii() and texto.isdigit()):
            return None
        cid = int(texto)
    return cid if cid > 0 else None


def _copia(registro):
    """Cópia defensiva: nunca expõe o dicionário interno de _clientes."""
    copia = dict(registro)
    copia["paises_ativos"] = list(registro.get("paises_ativos") or [])
    return copia


def _email_valido(email):
    if email.count("@") != 1 or any(caractere.isspace() for caractere in email):
        return False
    usuario, dominio = email.split("@")
    return bool(usuario) and bool(dominio)


def _localizar(cliente_id):
    """Busca na Árvore B de ID. Devolve (cid, posicao, registro) ou lança ValueError."""
    cid = _converter_id(cliente_id)
    if cid is None:
        raise ValueError(MSG_NAO_ENCONTRADO)

    posicao, _ = _arvore_id.buscar(cid)
    if posicao is None or posicao >= len(_clientes) or _clientes[posicao] is None:
        raise ValueError(MSG_NAO_ENCONTRADO)

    return cid, posicao, _clientes[posicao]


def _substituir(posicao, novo_registro):
    """GRAVA a lista com o registro trocado e SÓ ENTÃO atualiza a memória."""
    global _clientes
    nova_lista = list(_clientes)
    nova_lista[posicao] = novo_registro
    _gravar_clientes(nova_lista)
    _clientes = nova_lista
    return _copia(novo_registro)


def _lista_de_paises(valor):
    if valor is None:
        return []
    if isinstance(valor, str):
        return [valor]
    return list(valor)


def _texto_de_data(valor):
    return valor.isoformat() if isinstance(valor, datetime) else valor


# =============================================================================
# REGRAS DE PLANO (Tabela Hash da Etapa 1 + catálogo pacotes.json)
# =============================================================================

def _validar_plano(pacote_codigo, paises):
    """
    Devolve (codigo_int, pacote, paises_normalizados). Lança ValueError.

    Basic: exatamente 3 países distintos da região do plano, consultados um a
    um na Tabela Hash. Plus e Global não guardam países.
    """
    try:
        pacotes = carregar_pacotes()
    except (OSError, ValueError) as erro:
        raise ValueError("Não foi possível consultar o catálogo de pacotes.") from erro

    chave = _texto(pacote_codigo)
    pacote = pacotes.get(chave)
    if pacote is None:
        raise ValueError(MSG_PLANO_INVALIDO)

    if pacote.get("categoria") == "Basic":
        try:
            tabela = carregar_paises()
        except (OSError, ValueError, KeyError) as erro:
            raise ValueError("Não foi possível consultar o catálogo de países.") from erro
        normalizados = validar_paises_basic(pacote, _lista_de_paises(paises), tabela)
    else:
        normalizados = []

    return int(chave), pacote, normalizados


def _plano_dos_dados(dados, status):
    """
    Plano enviado junto do cadastro/edição (ver docstring do módulo).
    Devolve None ou um dicionário com os quatro campos de contratação.
    """
    codigo = _texto(dados.get("pacote"))
    if not codigo or "paises_ativos" not in dados:
        return None

    if status != "ativo":
        raise ValueError(MSG_PACOTE_STATUS)

    codigo_int, pacote, paises = _validar_plano(codigo, dados["paises_ativos"])

    inicio = _texto_de_data(dados.get("contratacao_inicio"))
    fim = _texto_de_data(dados.get("contratacao_fim"))
    if not inicio or not fim:
        agora = datetime.now().astimezone().replace(microsecond=0)
        inicio, fim = agora.isoformat(), calcular_fim(agora, pacote).isoformat()

    return {
        "pacote": codigo_int,
        "paises_ativos": paises,
        "contratacao_inicio": inicio,
        "contratacao_fim": fim,
    }


# =============================================================================
# INSTRUMENTAÇÃO
# =============================================================================

NOMES_ARVORES = {
    "id": {
        "arvore": "id",
        "nome": "Árvore B de ID",
        "chave": "ID do cliente (inteiro)",
        "icone": "bi-123",
    },
    "email": {
        "arvore": "email",
        "nome": "Árvore B de e-mail",
        "chave": "e-mail normalizado (minúsculas, sem espaços)",
        "icone": "bi-envelope",
    },
}


def _instrumentacao_busca(arvore, nome, chave, posicao, metricas_busca):
    """Formato combinado para a instrumentação de UMA busca."""
    return {
        "arvore": nome,
        "chave": chave,
        "encontrado": posicao is not None,
        "posicao": posicao,
        "comparacoes": metricas_busca["comparacoes"],
        "nos_visitados": metricas_busca["nos_visitados"],
        "altura": arvore.altura(),
        "divisoes": arvore.metricas()["estado"]["divisoes"],
        "simulado": False,
    }


_SEM_BUSCA = {"comparacoes": 0, "nos_visitados": 0}


# =============================================================================
# CONSULTAS
# =============================================================================

def buscar_cliente_por_id(cliente_id):
    """
    Árvore B de ID -> posição -> registro.
    Devolve (cópia do cliente ou None, instrumentacao).
    """
    _exigir_disponivel()

    cid = _converter_id(cliente_id)
    if cid is None:
        # ID inválido: a árvore nem é consultada e as métricas não mudam.
        return None, _instrumentacao_busca(_arvore_id, "id", cliente_id, None, _SEM_BUSCA)

    posicao, metricas_busca = _arvore_id.buscar(cid)
    cliente = _copia(_clientes[posicao]) if posicao is not None else None

    return cliente, _instrumentacao_busca(_arvore_id, "id", cid, posicao, metricas_busca)


def buscar_cliente_por_email(email):
    """
    Árvore B de e-mail -> posição -> registro (o e-mail é normalizado antes).
    Devolve (cópia do cliente ou None, instrumentacao).
    """
    _exigir_disponivel()

    email_norm = normalizar_email(email)
    if not email_norm:
        return None, _instrumentacao_busca(_arvore_email, "email", email_norm, None, _SEM_BUSCA)

    posicao, metricas_busca = _arvore_email.buscar(email_norm)
    cliente = _copia(_clientes[posicao]) if posicao is not None else None

    return cliente, _instrumentacao_busca(_arvore_email, "email", email_norm, posicao, metricas_busca)


def listar_clientes(busca="", pacote="", status="ativo"):
    """
    Lista para a tela administrativa.

    busca:  só dígitos -> Árvore B de ID; com "@" -> Árvore B de e-mail;
            outro texto -> parte do nome, sobre o percurso em ordem da
            Árvore B de ID (já ordenado por ID).
    pacote: código do pacote, "sem" (sem plano) ou "" (todos).
    status: "ativo" (padrão), "inativo" ou "todos".
    """
    _exigir_disponivel()

    busca = _texto(busca)

    if busca.isdigit():
        cliente, _ = buscar_cliente_por_id(busca)
        clientes = [cliente] if cliente else []
    elif "@" in busca:
        cliente, _ = buscar_cliente_por_email(busca)
        clientes = [cliente] if cliente else []
    else:
        clientes = [_copia(_clientes[posicao]) for _, posicao in _arvore_id.percorrer_em_ordem()]
        if busca:
            clientes = [c for c in clientes if busca.lower() in str(c["nome"]).lower()]

    if status in STATUS_VALIDOS:
        clientes = [c for c in clientes if c["status"] == status]

    if pacote == "sem":
        clientes = [c for c in clientes if c["pacote"] is None]
    elif pacote:
        clientes = [c for c in clientes if str(c["pacote"]) == str(pacote)]

    return clientes


def total_clientes():
    """Quantidade de clientes indexados (exclui posições removidas)."""
    _exigir_disponivel()
    return _arvore_id.total_chaves()


def proximo_id():
    """Próximo ID livre, vindo do controle de IDs (nunca reutiliza ID excluído)."""
    _exigir_disponivel()
    return _controle_ids["proximo_id"]


# =============================================================================
# ALTERAÇÕES
# =============================================================================

def _validar_campos(nome, email, esim, status):
    if not nome or not email or not esim:
        raise ValueError(MSG_CAMPOS_VAZIOS)
    if not _email_valido(email):
        raise ValueError(MSG_EMAIL_INVALIDO)
    if status not in STATUS_VALIDOS:
        raise ValueError(MSG_STATUS_INVALIDO)


def cadastrar_cliente(dados):
    """
    Cadastro administrativo. Lê nome, email, esim e status (padrão "ativo");
    qualquer "id" enviado é ignorado: o ID vem do controle de IDs.

    Ordem de gravação: 1) controle_ids.json, 2) clientes.json (novo registro
    no FIM), 3) memória e as duas Árvores B. O eSIM não precisa ser único.
    Um pacote só é trocado nas condições descritas na docstring do módulo; 
    nesse caso, a vigência é reiniciada.
    Devolve a cópia do cliente criado. Lança ValueError.
    """
    global _clientes, _controle_ids, _erro_indisponivel

    with _TRAVA:
        _exigir_alteracao()

        nome = _texto(dados.get("nome"))
        email = normalizar_email(dados.get("email"))
        esim = _texto(dados.get("esim"))
        status = _texto(dados.get("status")) or "ativo"

        _validar_campos(nome, email, esim, status)
        if _arvore_email.contem(email):
            raise ValueError(MSG_EMAIL_DUPLICADO)

        plano = _plano_dos_dados(dados, status)

        novo_id = _controle_ids["proximo_id"]
        posicao = len(_clientes)
        cliente = {
            "id": novo_id,
            "nome": nome,
            "email": email,
            "senha": SENHA_PADRAO,
            "esim": esim,
            "pacote": None,
            "paises_ativos": [],
            "contratacao_inicio": None,
            "contratacao_fim": None,
            "status": status,
        }
        if plano:
            cliente.update(plano)

        novo_controle = {
            "proximo_id": novo_id + 1,
            "ids_utilizados": list(_controle_ids["ids_utilizados"]) + [novo_id],
        }

        # 1) controle de IDs primeiro: se algo falhar depois, o ID já foi consumido.
        _gravar_controle(novo_controle)
        _controle_ids = novo_controle

        # 2) arquivo de clientes, com o novo registro no final.
        nova_lista = list(_clientes) + [cliente]
        _gravar_clientes(nova_lista)

        # 3) memória e índices.
        _clientes = nova_lista
        try:
            _arvore_id.inserir(novo_id, posicao)
            _arvore_email.inserir(email, posicao)
        except ValueError as erro:
            _erro_indisponivel = f"índices inconsistentes após o cadastro ({erro})"
            raise ErroIndices(_mensagem_indisponivel()) from erro

        return _copia(cliente)


def criar_conta(dados):
    """
    Cadastro feito pelo próprio cliente (área pública): informa nome e e-mail;
    o eSIM é gerado (ESIM-<id>) e o cliente nasce ativo e sem plano.
    """
    with _TRAVA:
        _exigir_disponivel()

        return cadastrar_cliente({
            "nome": dados.get("nome", ""),
            "email": dados.get("email", ""),
            "esim": f"ESIM-{proximo_id()}",
            "status": "ativo",
        })


def editar_cliente(cliente_id, dados):
    """
    Altera nome, eSIM e status NA MESMA POSIÇÃO. ID, e-mail, senha e posição
    não mudam, então as Árvores B não são tocadas. O e-mail (chave de índice)
    é imutável: enviar um e-mail diferente do atual lança ValueError.

    Um pacote só é trocado nas condições descritas no docstring do módulo
    (DC-08/DC-14): a vigência é reiniciada.
    """
    with _TRAVA:
        _exigir_alteracao()

        _, posicao, atual = _localizar(cliente_id)

        email_enviado = normalizar_email(dados.get("email"))
        if email_enviado and email_enviado != atual["email"]:
            raise ValueError(MSG_EMAIL_IMUTAVEL)

        nome = _texto(dados.get("nome"))
        esim = _texto(dados.get("esim"))
        status = _texto(dados.get("status"))

        if not nome or not esim:
            raise ValueError(MSG_CAMPOS_VAZIOS)
        if status not in STATUS_VALIDOS:
            raise ValueError(MSG_STATUS_INVALIDO)

        plano = _plano_dos_dados(dados, status)

        novo = _copia(atual)
        novo.update({"nome": nome, "esim": esim, "status": status})
        if plano:
            novo.update(plano)

        return _substituir(posicao, novo)


def _mudar_status(cliente_id, novo_status, mensagem_repetido):
    with _TRAVA:
        _exigir_alteracao()

        _, posicao, atual = _localizar(cliente_id)
        if atual["status"] == novo_status:
            raise ValueError(mensagem_repetido)

        novo = _copia(atual)
        novo["status"] = novo_status
        return _substituir(posicao, novo)


def inativar_cliente(cliente_id):
    """Exclusão lógica: muda SOMENTE o status. Continua nas duas Árvores B."""
    return _mudar_status(cliente_id, "inativo", MSG_JA_INATIVO)


def reativar_cliente(cliente_id):
    """Muda SOMENTE o status para ativo, preservando todo o resto."""
    return _mudar_status(cliente_id, "ativo", MSG_JA_ATIVO)


def excluir_cliente_fisicamente(cliente_id, confirmacao, ciencia):
    """
    Exclusão física (zona de risco): só cliente inativo, com confirmação
    (ID ou EXCLUIR) e ciência da irreversibilidade.

    A posição vira None no clientes.json (nenhuma outra se desloca) e o ID
    continua em ids_utilizados. As duas Árvores B são reconstruídas do zero;
    se a reconstrução falhar, os dados ficam indisponíveis.
    """
    global _clientes, _arvore_id, _arvore_email, _erro_indisponivel

    with _TRAVA:
        _exigir_alteracao()

        cid, posicao, atual = _localizar(cliente_id)

        if atual["status"] != "inativo":
            raise ValueError(MSG_EXCLUIR_ATIVO)

        resposta = _texto(confirmacao)
        if resposta != str(cid) and resposta.upper() != "EXCLUIR":
            raise ValueError(MSG_CONFIRMACAO)

        if not ciencia:
            raise ValueError(MSG_CIENCIA)

        nova_lista = list(_clientes)
        nova_lista[posicao] = None
        _gravar_clientes(nova_lista)
        _clientes = nova_lista

        try:
            _arvore_id, _arvore_email = construir_indices(nova_lista)
        except Exception as erro:
            _arvore_id = ArvoreB(GRAU_MINIMO, "id")
            _arvore_email = ArvoreB(GRAU_MINIMO, "email")
            _erro_indisponivel = _motivo(erro)


def contratar_plano(cliente_id, pacote_codigo, paises_ativos, inicio, fim):
    """
    Grava a contratação no registro (mesma posição; nenhuma chave de Árvore B
    muda). Exige cliente ativo e plano válido: no Basic, 3 países distintos da
    região do plano, consultados na Tabela Hash; Plus e Global guardam [].
    """
    with _TRAVA:
        _exigir_alteracao()

        _, posicao, atual = _localizar(cliente_id)
        if atual["status"] != "ativo":
            raise ValueError(MSG_CONTRATAR_INATIVO)

        codigo, _, paises = _validar_plano(pacote_codigo, paises_ativos)

        novo = _copia(atual)
        novo.update({
            "pacote": codigo,
            "paises_ativos": paises,
            "contratacao_inicio": _texto_de_data(inicio),
            "contratacao_fim": _texto_de_data(fim),
        })
        return _substituir(posicao, novo)


# =============================================================================
# ÁRVORE B — RESUMO E INSTRUMENTAÇÃO (nunca lançam erro)
# =============================================================================

def _resumo_zerado(erro):
    return {
        "grau": GRAU_MINIMO,
        "clientes": 0,
        "altura": 0,
        "nos": 0,
        "media_nos_visitados": 0.0,
        "divisoes": 0,
        "disponivel": False,
        "erro": erro,
    }


def resumo_arvore_b():
    """Números da Árvore B de ID para o painel (dashboard)."""
    if _erro_indisponivel is not None:
        return _resumo_zerado(_mensagem_indisponivel())

    try:
        metricas = _arvore_id.metricas()
        acumulado, estado = metricas["acumulado"], metricas["estado"]
        buscas = acumulado["total_buscas"]
        media = round(acumulado["nos_visitados_totais"] / buscas, 1) if buscas > 0 else 0.0

        return {
            "grau": GRAU_MINIMO,
            "clientes": _arvore_id.total_chaves(),
            "altura": _arvore_id.altura(),
            "nos": _arvore_id.contar_nos(),
            "media_nos_visitados": media,
            "divisoes": estado["divisoes"],
            "disponivel": True,
        }
    except Exception as erro:
        return _resumo_zerado(f"Não foi possível ler as métricas da Árvore B: {erro}")


def _instrumentacao_zerada(arvore, erro=None):
    dados = {
        **NOMES_ARVORES[arvore],
        "grau": GRAU_MINIMO,
        "ultima_busca": {"comparacoes": 0, "nos_visitados": 0, "tempo_us": 0.0},
        "acumulado": {"comparacoes_totais": 0, "total_buscas": 0},
        "estado": {
            "altura": 0,
            "divisoes": 0,
            "total_chaves": 0,
            "ultima_operacao": None,
            "tempo_execucao_us": 0.0,
        },
        "simulado": False,
    }
    if erro is not None:
        dados["erro"] = erro
    return dados


def instrumentacao_arvore_b(arvore):
    """
    Instrumentação de UMA árvore: "email" -> Árvore B de e-mail; qualquer
    outro valor -> Árvore B de ID.
    """
    nome = "email" if arvore == "email" else "id"

    if _erro_indisponivel is not None:
        return _instrumentacao_zerada(nome, _mensagem_indisponivel())

    try:
        objeto = _arvore_email if nome == "email" else _arvore_id
        metricas = objeto.metricas()
        estado = metricas["estado"]

        return {
            **NOMES_ARVORES[nome],
            "grau": GRAU_MINIMO,
            "ultima_busca": dict(metricas["ultima_busca"]),
            "acumulado": {
                "comparacoes_totais": metricas["acumulado"]["comparacoes_totais"],
                "total_buscas": metricas["acumulado"]["total_buscas"],
            },
            "estado": {
                "altura": estado["altura"],
                "divisoes": estado["divisoes"],
                "total_chaves": estado["total_chaves"],
                "ultima_operacao": estado["ultima_operacao"],
                "tempo_execucao_us": estado["tempo_execucao_us"],
            },
            "simulado": False,
        }
    except Exception as erro:
        return _instrumentacao_zerada(
            nome, f"Não foi possível ler as métricas da Árvore B: {erro}"
        )


# Carga automática: nunca deixa exceção escapar (o Flask precisa subir).
inicializar()
