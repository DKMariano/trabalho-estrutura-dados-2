"""
DGB SIM

Professora: Inês Valderrama Restovic
Disciplina: Estrutura de Dados 2
Equipe: Bruno Barreto, Dimitrius Khouri e Guilherme Lopes
"""

from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash

from  dados_site.dados_inicio import (BENEFICIOS, DEPOIMENTOS, ITENS_CARROSSEL, PASSOS, PLANOS, APRESENTACAO_PLANOS)

from dados_site.dados_usuario import USUARIOS

# Carrega os países do arquivo JSON na TabelaHash.
from arquivos.persistencia_paises import carregar_paises
from arquivos.persistencia_paises import salvar_paises

#ATENÇÃO!!!!  CONFIRMAR COM A PROFESSORA SE OS ARQUIVOS JSON  DOS PACPOTES DEVEM SER CARREGADOS na TabelaHash.
from arquivos.persistencia_pacotes import carregar_pacotes
from arquivos.persistencia_historico import (carregar_historico, registrar_consulta)

#ATENÇÃO!!!!  CONFIRMAR COM A PROFESSORA SE DEVEMOS MANTER OS ARQUIVOS ASSIM
from dados_site.servico_conectividade import consultar_cobertura_cliente, rota_demonstrativa
from dados_site.regras_planos import (
    planos_compativeis, plano_vigente, calcular_fim, validar_paises_basic,
    sugestoes_upgrade
)

#ATENÇÃO!!!! TROCAR ESTE IMPORT PELO MÓDULO REAL QUANDO A ÁRVORE B ESTIVER PRONTA.
# As funções abaixo são SIMULADAS e têm a mesma interface do backend definitivo.
from dados_site.dados_etapa02 import (
    buscar_cliente_por_id,
    buscar_cliente_por_email,
    listar_clientes,
    total_clientes,
    cadastrar_cliente,
    editar_cliente,
    inativar_cliente,
    reativar_cliente,
    excluir_cliente_fisicamente,
    criar_conta,
    contratar_plano,
    resumo_arvore_b,
)

#ATENÇÃO!!!! APAGAR ESSE IMPORT QUANDO CRIAR O GRAFO
from dados_site.dados_etapa03 import (
    resumo_grafo,
    rede_demonstracao,
    execucao_demonstrativa,
    ALGORITMOS_REDE,
    INSTRUMENTACAO_REDE_DEMONSTRACAO,
    EVENTOS_REDE_DEMONSTRACAO,
)



app = Flask(__name__)
app.secret_key = "dgb-sim-chave-de-desenvolvimento"

# Carrega os registros persistidos na estrutura em memória.
tabela_paises = carregar_paises()

# Tecnologias oferecidas nos formulários de país (decisão D5). A Tabela Hash
# aceita 2G a 5G e não pode ser alterada; a restrição fica só na tela.
TECNOLOGIAS_OFERECIDAS = ["4G", "5G"]


@app.template_filter("data_br")
def data_br(valor):
    """Mostra uma data ISO (2026-11-27T14:00:00-03:00) como 27/11/2026."""
    if not valor:
        return "—"
    return f"{valor[8:10]}/{valor[5:7]}/{valor[0:4]}"

# Referência temporária para preservar as rotas ainda não adaptadas.
# PAISES = tabela_paises.paises



@app.route("/")
def inicio():
    return render_template(
        "inicio.html",  
        itens_carrossel=ITENS_CARROSSEL, 
        beneficios=BENEFICIOS, 
        passos=PASSOS, 
        depoimentos=DEPOIMENTOS, 
        planos=PLANOS
    )

# Define a URL /paises e permite dois tipos de requisição:
# GET: acessar a página de consulta.
# POST: enviar o formulário com o destino selecionado.
@app.route("/paises", methods=["GET", "POST"])
def paises():
    """Exibe o formulário e consulta a cobertura por código na TabelaHash."""    

    # Começa sem resultado, pois o usuário pode apenas abrir a página.
    resultado = None
    codigo_selecionado = None
    nao_encontrado = False

    if request.method == "POST":
        # Obtém o código, remove espaços e converte para maiúsculas.
        codigo_selecionado = request.form.get("destino", "").strip().upper()     
        
        # Busca o país na TabelaHash; retorna None se não encontrar.   
        resultado = tabela_paises.buscar(codigo_selecionado)

        nao_encontrado = resultado is None

    # Planos que podem cobrir o destino encontrado na Tabela Hash.
    compativeis = planos_compativeis(resultado, carregar_pacotes()) if resultado else []

    # Envia os países, o resultado e a seleção ao template.
    return render_template(
        "paises.html",
        paises=sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]),
        resultado=resultado,
        codigo_selecionado=codigo_selecionado,
        nao_encontrado=nao_encontrado,
        planos_compativeis=compativeis
    )


@app.route("/planos")
def planos():
    pacotes = carregar_pacotes()

    return render_template(
        "planos.html",
        pacotes=pacotes,
        planos=PLANOS,
        apresentacao=APRESENTACAO_PLANOS,
    )

MENSAGEM_INATIVO = "Seu cadastro está inativo. Procure a administração da DGB SIM."


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Tela de acesso com duas abas.

    - Cliente: o e-mail é buscado na Árvore B de e-mail; a senha demonstrativa
      e o status são conferidos; o cliente vai para /cliente/<id>.
      Não existe sessão: daí em diante o cliente é identificado pela URL.
    - Administrador: confere admin/admin (dados_usuario.py) e leva ao painel.
      É apenas demonstrativo: as rotas /admin não são protegidas.
    """
    usuario = ""
    mensagem = None

    if request.method == "POST":

        tipo_acesso = request.form.get("tipo_acesso")
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        if tipo_acesso == "cliente":

            cliente, mensagem = autenticar_cliente(usuario, senha)

            if cliente:
                return redirect(url_for("cliente_dashboard", cliente_id=cliente["id"]))

        else:

            dados_usuario = USUARIOS.get(usuario)

            if (
                dados_usuario
                and dados_usuario["senha"] == senha
                and dados_usuario["tipo_acesso"] == tipo_acesso
            ):
                return redirect(url_for("admin"))

            mensagem = "Usuário ou senha incorretos."

    return render_template(
        "login.html",
        mensagem=mensagem,
        usuario=usuario
    )


def autenticar_cliente(email, senha):
    """
    Localiza o cliente pela Árvore B de e-mail (simulada por enquanto),
    confere a senha demonstrativa e o status.
    Devolve (cliente, None) ou (None, mensagem de erro).
    """
    cliente, _ = buscar_cliente_por_email(email)

    if cliente is None or cliente["senha"] != senha:
        return None, "E-mail ou senha incorretos."

    if cliente["status"] != "ativo":
        return None, MENSAGEM_INATIVO

    return cliente, None


def processar_contratacao(cliente, plano, paises_marcados, confirmado, pacotes):
    """
    Regras comuns à compra pública (/adquirir) e à área do cliente:
    - Basic: exatamente 3 países da região do plano (validados na Tabela Hash);
    - Plus e Global: sem países;
    - Basic, ou troca de um plano ainda vigente, exige confirmação.
    Grava a contratação e devolve (pacote, fim). Lança ValueError.
    """
    pacote = pacotes.get(plano)

    if pacote is None:
        raise ValueError("Selecione um plano válido.")

    if pacote["categoria"] == "Basic":
        paises = validar_paises_basic(pacote, paises_marcados, tabela_paises)
    else:
        paises = []   # Plus e Global não guardam países

    if (pacote["categoria"] == "Basic" or plano_vigente(cliente)) and not confirmado:
        raise ValueError("Confirme a contratação para continuar.")

    inicio = datetime.now().astimezone().replace(microsecond=0)
    fim = calcular_fim(inicio, pacote)

    contratar_plano(cliente["id"], plano, paises, inicio.isoformat(), fim.isoformat())
    return pacote, fim


def paises_agrupados_por_regiao():
    """Países atendidos por região, lidos da Tabela Hash (para escolher o Basic)."""
    grupos = {}
    for codigo, pais in sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]):
        grupos.setdefault(pais["regiao"], []).append((codigo, pais["nome"]))
    return grupos


@app.route("/adquirir/<plano>", methods=["GET", "POST"])
def adquirir(plano):
    """
    Compra pública de um plano (vem do botão "Adquirir" em Cobertura ou Planos).

    Lado esquerdo: e-mail e senha. Lado direito: o plano e, no Basic,
    a escolha dos 3 países. Com cadastro ativo, o plano é gravado e o
    cliente vai para o painel. Sem cadastro: link para Criar conta, que
    volta para esta mesma tela.
    """
    pacotes = carregar_pacotes()
    pacote = pacotes.get(plano)

    if pacote is None:
        flash("Plano não encontrado.", "danger")
        return redirect(url_for("planos"))

    destino = request.values.get("destino", "").strip().upper()
    paises_marcados = [destino] if destino else []
    usuario = ""
    mensagem = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        paises_marcados = request.form.getlist("paises")

        cliente, mensagem = autenticar_cliente(usuario, request.form.get("senha", ""))

        if cliente:
            try:
                pacote, fim = processar_contratacao(
                    cliente, plano, paises_marcados,
                    request.form.get("confirmado") == "sim", pacotes
                )
                flash(f"Plano {pacote['nome']} contratado com sucesso. "
                      f"Vigência até {fim.strftime('%d/%m/%Y')}.", "success")
                return redirect(url_for("cliente_dashboard", cliente_id=cliente["id"]))
            except ValueError as erro:
                mensagem = str(erro)

    # Plano anterior e próximo, na ordem do catálogo (setas do painel direito).
    codigos = list(pacotes)
    posicao_plano = codigos.index(plano)
    plano_anterior = codigos[posicao_plano - 1] if posicao_plano > 0 else None
    plano_proximo = codigos[posicao_plano + 1] if posicao_plano < len(codigos) - 1 else None

    # Imagem do plano (mesma da página Planos); o Global usa a imagem geral.
    imagem_plano = next(
        (item["imagem"] for item in PLANOS if item["nome"] == pacote["nome"]),
        "img/login/login-aviao.png"
    )

    return render_template(
        "adquirir.html",
        plano=plano,
        pacote=pacote,
        imagem_plano=imagem_plano,
        plano_anterior=plano_anterior,
        plano_proximo=plano_proximo,
        posicao_plano=posicao_plano,
        nomes_planos={codigo: dados["nome"] for codigo, dados in pacotes.items()},
        destino=destino,
        usuario=usuario,
        mensagem=mensagem,
        paises_por_regiao=paises_agrupados_por_regiao(),
        paises_marcados=paises_marcados
    )


@app.route("/criar-conta", methods=["GET", "POST"])
def criar_conta_cliente():
    """
    Cadastro feito pelo próprio cliente. ID e eSIM são gerados; o cliente
    nasce ativo e sem plano. Depois do POST, a página volta com ?criado=<id>
    (Post/Redirect/Get) e mostra o modal de sucesso.
    """
    plano = request.values.get("plano", "").strip()
    destino = request.values.get("destino", "").strip().upper()
    formulario = {}

    if request.method == "POST":
        formulario = request.form.to_dict()

        try:
            # Simula: gravação no fim do arquivo e inserção nas duas Árvores B.
            cliente = criar_conta(formulario)
            return redirect(url_for("criar_conta_cliente", criado=cliente["id"],
                                    plano=plano or None, destino=destino or None))
        except ValueError as erro:
            flash(str(erro), "danger")

    criado, _ = buscar_cliente_por_id(request.args.get("criado", ""))

    return render_template(
        "criar_conta.html",
        formulario=formulario,
        criado=criado,
        plano=plano,
        destino=destino,
        pacote_escolhido=carregar_pacotes().get(plano)
    )


def cliente_liberado(cliente_id):
    """
    Usado no início de toda página /cliente/<id>/...

    Busca o cliente pela Árvore B de ID. Sem sessão, quem digitar a URL de
    um cliente inativo também é barrado aqui (não só no login).
    Devolve (cliente, None) ou (None, resposta_de_bloqueio).
    """
    cliente, _ = buscar_cliente_por_id(cliente_id)

    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return None, redirect(url_for("login"))

    if cliente["status"] != "ativo":
        return None, render_template("cliente/bloqueado.html", mensagem=MENSAGEM_INATIVO)

    return cliente, None


@app.route("/cliente/<int:cliente_id>")
def cliente_dashboard(cliente_id):

    cliente, bloqueio = cliente_liberado(cliente_id)
    if bloqueio:
        return bloqueio

    # Busca o pacote do cliente no catálogo (pacotes.json)
    pacotes = carregar_pacotes()
    pacote = pacotes.get(str(cliente["pacote"]))

    return render_template(
        "cliente/dashboard.html",
        cliente=cliente,
        pacote=pacote,
        plano_vigente=plano_vigente(cliente),
        pagina_ativa="dashboard"
    )

# =====================================
# MINHA CONTA
# =====================================
@app.route("/cliente/<int:cliente_id>/minha-conta")
def cliente_conta(cliente_id):

    cliente, bloqueio = cliente_liberado(cliente_id)
    if bloqueio:
        return bloqueio

    pacotes = carregar_pacotes()
    pacote = pacotes.get(str(cliente["pacote"]))

    return render_template(
        "cliente/minha_conta.html",
        cliente=cliente,
        pacote=pacote,
        plano_vigente=plano_vigente(cliente),
        pagina_ativa="conta"
    )


# =====================================
# CONTRATAÇÃO DE PLANO
# =====================================

# =====================================
# PAÍS DIGITADO PELO CLIENTE
# =====================================

def _sem_acento(texto):
    """'Itália' -> 'italia' (para comparar o que o cliente digitou)."""
    import unicodedata
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower()


def resolver_pais(texto):
    """
    Aceita o código (IT) ou o nome (Itália, italia) digitado livremente.
    Devolve o código do país na Tabela Hash; se não achar, devolve o
    texto em maiúsculas, e a consulta informa que o país não foi encontrado.
    """
    texto = (texto or "").strip()
    if not texto:
        return ""

    digitado = _sem_acento(texto)
    for codigo, pais in tabela_paises.listar():
        if digitado == codigo.lower() or digitado == _sem_acento(pais["nome"]):
            return codigo

    return texto.upper()


def nome_do_pais(codigo):
    """Nome para exibir no campo; se o código não existir, mostra o texto digitado."""
    for cod, pais in tabela_paises.listar():
        if cod == codigo:
            return pais["nome"]
    return codigo


@app.route("/cliente/<int:cliente_id>/contratar", methods=["GET", "POST"])
def cliente_contratar(cliente_id):
    """
    Área do cliente: consulta do destino com sugestões de upgrade (topo)
    e contratação do plano (formulário abaixo).

    Consulta (GET ?origem=&destino=): Árvore B (cliente) -> Tabela Hash
    (destino) -> regra do plano atual. A origem é guardada para a Etapa 3
    e não influencia a cobertura.
    """
    cliente, bloqueio = cliente_liberado(cliente_id)
    if bloqueio:
        return bloqueio

    pacotes = carregar_pacotes()

    plano = request.values.get("plano", "").strip()
    # Origem e destino são digitados livremente (nome ou código do país)
    origem = resolver_pais(request.args.get("origem", ""))
    destino = resolver_pais(request.args.get("destino", ""))
    paises_marcados = [destino] if destino else []

    # ---------- contratação ----------
    if request.method == "POST":
        paises_marcados = request.form.getlist("paises")

        try:
            pacote, fim = processar_contratacao(
                cliente, plano, paises_marcados,
                request.form.get("confirmado") == "sim", pacotes
            )
            flash(f"Plano {pacote['nome']} contratado com sucesso. "
                  f"Vigência até {fim.strftime('%d/%m/%Y')}.", "success")
            return redirect(url_for("cliente_dashboard", cliente_id=cliente_id))
        except ValueError as erro:
            flash(str(erro), "danger")

    # ---------- consulta do destino + sugestões ----------
    consulta = None

    if destino:
        resposta = consultar_cobertura_cliente(cliente_id, destino, tabela_paises, pacotes)
        consulta = {"resposta": resposta, "mensagem": resposta["mensagem"], "sugestoes": []}
        pais = resposta["destino"]

        if pais:
            nome_pais = pais["nome"]

            if resposta["situacao"] == "sem_plano":
                consulta["mensagem"] = f"Você não tem plano contratado. Estes planos cobrem {nome_pais}:"
                consulta["sugestoes"] = resposta["planos_compativeis"]

            elif resposta["situacao"] == "expirado":
                consulta["mensagem"] = f"Seu plano expirou. Estes planos cobrem {nome_pais}:"
                consulta["sugestoes"] = resposta["planos_compativeis"]

            elif resposta["pacote"]:
                consulta["sugestoes"] = sugestoes_upgrade(resposta["pacote"], pais, pacotes)
                cobre = "cobre" if resposta["coberto"] else "não cobre"

                if consulta["sugestoes"]:
                    consulta["mensagem"] = f"Seu plano {cobre} {nome_pais}, mas que tal um upgrade?"
                else:
                    consulta["mensagem"] = f"Seu plano {cobre} {nome_pais}."

    return render_template(
        "cliente/contratacao.html",
        cliente=cliente,
        pacotes=pacotes,
        plano=plano,
        origem=origem,
        destino=destino,
        origem_digitada=nome_do_pais(origem),
        destino_digitado=nome_do_pais(destino),
        consulta=consulta,
        paises=sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]),
        paises_por_regiao=paises_agrupados_por_regiao(),
        paises_marcados=paises_marcados,
        plano_vigente=plano_vigente(cliente),
        pacote_atual=pacotes.get(str(cliente["pacote"])),
        pacote_escolhido=pacotes.get(plano),   # só aparece depois de "Adquirir este plano"
        pagina_ativa="contratar"
    )


# =====================================
# MINHA CONECTIVIDADE CLIENTE
# =====================================

OPCOES_POR_PAGINA = [5, 10, 20, 50]


def historico_do_cliente(cliente_id, pagina, por_pagina=5):
    """
    Consultas do cliente, da mais recente para a mais antiga.
    O cliente escolhe quantas linhas ver por página (5, 10, 20 ou 50).
    """
    if por_pagina not in OPCOES_POR_PAGINA:
        por_pagina = OPCOES_POR_PAGINA[0]

    registros = [
        registro
        for registro in carregar_historico()
        if registro["cliente_id"] == cliente_id
    ]

    registros.reverse()

    total = len(registros)

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    pagina = max(1, min(pagina, total_paginas))

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    return {
        "registros": registros[inicio:fim],
        "total": total,
        "pagina": pagina,
        "total_paginas": total_paginas,
        "inicio": inicio + 1 if total else 0,
        "fim": min(fim, total),
        "por_pagina": por_pagina,
        "opcoes_por_pagina": OPCOES_POR_PAGINA
    }


@app.route(
    "/cliente/<int:cliente_id>/minha-conectividade",
    methods=["GET", "POST"]
)
def minha_conectividade(cliente_id):
    """
    Consulta de conectividade da área do cliente.

    Etapa 2: cliente (Árvore B, pela URL) × destino (Tabela Hash).
    Etapa 3: rota demonstrativa e histórico (diferencial), ainda simulados.
    """

    cliente, bloqueio = cliente_liberado(cliente_id)
    if bloqueio:
        return bloqueio

    resposta = None   # Etapa 2: decisão de cobertura
    rota = None       # Etapa 3: rota simulada (só existe para BR -> IT)

    formulario = {
        "origem": "BR",
        "destino": "IT",
        "criterio": "menor_latencia"
    }

    paises_disponiveis = sorted(
        tabela_paises.listar(),
        key=lambda item: item[1]["nome"]
    )

    if request.method == "POST":
        formulario["origem"] = request.form.get("origem", "").strip().upper()
        formulario["destino"] = request.form.get("destino", "").strip().upper()
        formulario["criterio"] = request.form.get("criterio", "").strip()

        # Etapa 2: o cliente vem da URL; o destino, do formulário.
        resposta = consultar_cobertura_cliente(
            cliente_id,
            formulario["destino"],
            tabela_paises,
            carregar_pacotes()
        )

        # Etapa 3: só tenta a rota quando há cobertura.
        if resposta["coberto"]:
            rota = rota_demonstrativa(
                formulario["origem"],
                formulario["destino"],
                formulario["criterio"]
            )

            if rota:
                pais_origem = tabela_paises.buscar(formulario["origem"])
                registrar_consulta(cliente_id, {
                    "origem": {
                        "codigo": formulario["origem"],
                        "nome": pais_origem["nome"] if pais_origem else formulario["origem"]
                    },
                    "cobertura": {
                        "codigo": formulario["destino"],
                        "pais": resposta["destino"]["nome"]
                    },
                    "rota": rota
                })

    return render_template(
        "cliente/minha_conectividade.html",
        cliente=cliente,
        paises=paises_disponiveis,
        formulario=formulario,
        resposta=resposta,
        rota=rota,
        pagina_ativa="conectividade",
        **historico_do_cliente(
            cliente_id,
            request.args.get("pagina", 1, type=int),
            request.args.get("por_pagina", 5, type=int)
        )
    )

# =====================================
# HISTÓRICO DO CLIENTE
# =====================================

@app.route("/cliente/<int:cliente_id>/historico")
def cliente_historico(cliente_id):
    """O histórico agora é exibido na página Minha conectividade."""

    return redirect(url_for(
        "minha_conectividade",
        cliente_id=cliente_id,
        pagina=request.args.get("pagina", 1, type=int),
        _anchor="historico"
    ))


# =====================================
# DASHBOARD ADMINISTRATIVO
# =====================================

@app.route("/admin")
def admin():
    return render_template(
        "admin/dashboard.html",
        total_paises=tabela_paises.tam(),
        arvore=resumo_arvore_b(),
        metricas=tabela_paises.metricas(),
        grafo=resumo_grafo()
    )

# =====================================
# LISTAGEM DE PAÍSES
# =====================================

OPCOES_POR_PAGINA_ADMIN = [5, 10, 20]


def ler_por_pagina():
    """Quantidade de linhas por página escolhida na tabela (5, 10 ou 20)."""
    por_pagina = request.args.get("por_pagina", 5, type=int)
    return por_pagina if por_pagina in OPCOES_POR_PAGINA_ADMIN else 5


@app.route("/admin/paises")
def admin_paises():
    # Pendente: integrar esta operação à classe TabelaHash.
    # Feito
    
    busca = request.args.get("busca", "").strip().lower()
    regiao = request.args.get("regiao", "").strip()

    pagina = request.args.get("pagina", 1, type=int)

    por_pagina = ler_por_pagina()

    # paises_filtrados = list(PAISES.items())
    paises_filtrados = sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"])

    # =====================================
    # BUSCA POR NOME OU CÓDIGO
    # =====================================

    if busca:
        # 1) Descobre quais códigos (chaves) correspondem ao que foi digitado,
        #    seja pelo código ou por parte do nome.
        codigos = [
            codigo
            for codigo, pais in paises_filtrados
            if busca in codigo.lower()
            or busca in pais["nome"].lower()
        ]

        if codigos:
            # 2) Cada país é recuperado pela chave na Tabela Hash.
            paises_filtrados = [
                (codigo, tabela_paises.buscar(codigo))
                for codigo in codigos
            ]
        else:
            # 3) Nada correspondeu: a consulta à Tabela Hash também falha
            #    e fica registrada como "Não encontrado".
            tabela_paises.buscar(busca)
            paises_filtrados = []

    # =====================================
    # FILTRO POR REGIÃO
    # =====================================

    if regiao:
        paises_filtrados = [
            (codigo, pais)
            for codigo, pais in paises_filtrados
            if pais["regiao"] == regiao
        ]

    # =====================================
    # REGIÕES DISPONÍVEIS
    # =====================================

    regioes = sorted({
        pais["regiao"]
        for _, pais in tabela_paises.listar()
    })

    # =====================================
    # PAGINAÇÃO
    # =====================================

    total_filtrados = len(paises_filtrados)

    total_paginas = max(
        1,
        (total_filtrados + por_pagina - 1) // por_pagina
    )

    if pagina < 1:
        pagina = 1

    if pagina > total_paginas:
        pagina = total_paginas

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    paises_pagina = paises_filtrados[inicio:fim]

    return render_template(
        "admin/paises.html",
        paises=paises_pagina,
        total_paises=tabela_paises.tam(),
        total_filtrados=total_filtrados,
        regioes=regioes,
        busca=busca,
        regiao_selecionada=regiao,
        pagina=pagina,
        total_paginas=total_paginas,
        por_pagina=por_pagina,
        opcoes_por_pagina=OPCOES_POR_PAGINA_ADMIN
    )

@app.route("/admin/paises/cadastrar", methods=["GET", "POST"])
def admin_cadastrar_pais():
    # Pendente: integrar esta operação à classe TabelaHash.
    #Feito

    # regioes = [
    #     "África",
    #     "América",
    #     "Ásia",
    #     "Europa",
    #     "Oceania"
    # ]

    # tecnologias = [
    #     "2G",
    #     "3G",
    #     "4G",
    #     "5G"
    # ]

    mensagem = None
    dados_formulario = {}

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        codigo = request.form.get("codigo", "").strip().upper()
        regiao = request.form.get("regiao", "").strip()
        operadora = request.form.get("operadora", "").strip()
        tecnologia = request.form.get("tecnologia", "").strip()

        dados_formulario = {
            "nome": nome,
            "codigo": codigo,
            "regiao": regiao,
            "operadora": operadora,
            "tecnologia": tecnologia
        }

        # Validação dos campos obrigatórios.
        # if not nome or not codigo or not regiao or not operadora or not tecnologia:
        #     mensagem = "Preencha todos os campos obrigatórios."

        # # O código utilizado como chave deve possuir duas letras.
        # elif len(codigo) != 2 or not codigo.isalpha():
        #     mensagem = "O código do país deve possuir exatamente 2 letras."

        # # Impede que uma chave já existente seja sobrescrita.
        # #elif codigo in PAISES:
        # elif tabela_paises.buscar(codigo) is not None:
        #     mensagem = "Já existe um país cadastrado com esse código."

        # else:
            # PAISES[codigo] = {
            #     "nome": nome,
            #     "regiao": regiao,
            #     "operadora": operadora,
            #     "tecnologia": tecnologia
            # }

        try:
            tabela_paises.inserir(codigo, nome, regiao, operadora, tecnologia)
            salvar_paises(tabela_paises)
            flash("Cadastro realizado com sucesso!", "sucesso")

            return redirect(url_for("admin_paises"))
        except ValueError as erro:
            mensagem = str(erro)

    return render_template(
        "admin/cadastrar_pais.html",
        regioes=tabela_paises.REGIOES,
        tecnologias=TECNOLOGIAS_OFERECIDAS,
        dados_formulario=dados_formulario,
        mensagem=mensagem,
        pagina_ativa="paises"
    )


@app.route("/admin/paises/<codigo>")
def admin_visualizar_pais(codigo):
    # Pendente: integrar esta operação à classe TabelaHash.
    # Feito

    codigo = codigo.upper()

    pais = tabela_paises.buscar(codigo)

    if pais is None:
        flash("País não encontrado.", "erro")
        return redirect(url_for("admin_paises"))

    return render_template(
        "admin/visualizar_pais.html",
        codigo=codigo,
        pais=pais
    )

@app.route(
    "/admin/paises/<codigo>/editar",
    methods=["GET", "POST"]
)
def admin_editar_pais(codigo):
    # Pendente: integrar esta operação à classe TabelaHash. 
    # Feito

    codigo = codigo.upper()

    pais = tabela_paises.buscar(codigo)

    if pais is None:
        flash("País não encontrado.", "erro")
        return redirect(url_for("admin_paises"))

    mensagem = None
    dados = pais

    if request.method == "POST":

        # pais["nome"] = request.form.get("nome", "").strip()
        # pais["regiao"] = request.form.get("regiao", "").strip()
        # pais["operadora"] = request.form.get("operadora", "").strip()
        # pais["tecnologia"] = request.form.get("tecnologia", "").strip()

        nome = request.form.get("nome", "").strip()
        regiao = request.form.get("regiao", "").strip()
        operadora = request.form.get("operadora", "").strip()
        tecnologia = request.form.get("tecnologia", "").strip()

        try:
            tabela_paises.alterar(codigo, nome, regiao, operadora, tecnologia)
            salvar_paises(tabela_paises)
            flash("Alteração realizada com sucesso!", "sucesso")
            return redirect(url_for("admin_paises"))
        except ValueError as erro:
            mensagem = str(erro)
            dados = {"nome": nome, "regiao": regiao,
                "operadora": operadora, "tecnologia": tecnologia}

    return render_template(
        "admin/editar_pais.html",
        codigo=codigo,
        pais=pais,
        dados=dados,
        regioes=tabela_paises.REGIOES,
        tecnologias=TECNOLOGIAS_OFERECIDAS,
        mensagem=mensagem
    )

@app.route(
    "/admin/paises/<codigo>/excluir",
    methods=["POST"]
)
def admin_excluir_pais(codigo):
    """Remove um país da TabelaHash e persiste a alteração no JSON."""

    codigo = codigo.upper()

    # if codigo in PAISES:
    #     del PAISES[codigo]
    try:
        tabela_paises.remover(codigo)
        salvar_paises(tabela_paises)
        flash("País excluido com sucesso!", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")

    return redirect(url_for("admin_paises"))

# =====================================
# TABELA HASH
# =====================================
@app.route("/admin/tabela-hash")
def admin_tabela_hash():
    return render_template(
        "admin/tabela_hash.html",
        total_paises=tabela_paises.tam(),
        metricas=tabela_paises.metricas()
    )

# =====================================
# GERENCIAMENTO DE CLIENTES
# =====================================

@app.route("/admin/clientes", methods=["GET"])
def admin_clientes():

    # Catálogo existente de pacotes.
    pacotes = carregar_pacotes()

    nomes_pacotes = {
        str(codigo): dados["nome"]
        for codigo, dados in pacotes.items()
    }

    # Busca: número -> Árvore B de ID; "@" -> Árvore B de e-mail; texto -> nome.
    # Status: a lista abre em "ativo"; "inativo" e "todos" mostram os demais.
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "ativo").strip() or "ativo"
    pacote_filtro = request.args.get("pacote", "").strip()

    # Percurso em ordem da Árvore B de ID (simulado por enquanto) + filtros.
    clientes = listar_clientes(busca=busca, pacote=pacote_filtro, status=status)

    total_clientes_cadastrados = total_clientes()
    total_filtrado = len(clientes)

    # Paginação: 5, 10 ou 20 registros por página (escolha do admin).
    por_pagina = ler_por_pagina()

    try:
        pagina = int(request.args.get("pagina", 1))
    except (TypeError, ValueError):
        pagina = 1

    total_paginas = max(
        1,
        (total_filtrado + por_pagina - 1) // por_pagina
    )

    pagina = max(1, min(pagina, total_paginas))

    indice_inicial = (pagina - 1) * por_pagina
    indice_final = indice_inicial + por_pagina

    clientes_pagina = clientes[
        indice_inicial:indice_final
    ]

    inicio = indice_inicial + 1 if total_filtrado else 0
    fim = min(indice_final, total_filtrado)

    # Paginação compacta, mesmo com muitos clientes.
    numeros = sorted({
        1,
        total_paginas,
        *range(
            max(1, pagina - 1),
            min(total_paginas, pagina + 1) + 1
        )
    })

    paginas_visiveis = []

    for numero in numeros:
        if paginas_visiveis:
            anterior = paginas_visiveis[-1]

            if numero - anterior > 1:
                paginas_visiveis.append(None)

        paginas_visiveis.append(numero)

    return render_template(
        "admin/clientes.html",
        clientes=clientes_pagina,
        nomes_pacotes=nomes_pacotes,
        pacotes=pacotes,
        status_selecionado=status,
        pacote_selecionado=pacote_filtro,
        busca=busca,
        total_clientes=total_clientes_cadastrados,
        total_filtrado=total_filtrado,
        pagina=pagina,
        total_paginas=total_paginas,
        paginas_visiveis=paginas_visiveis,
        inicio=inicio,
        fim=fim,
        por_pagina=por_pagina,
        opcoes_por_pagina=OPCOES_POR_PAGINA_ADMIN
    )
# =====================================
# ARVORE B CLIENTES
# =====================================

@app.route("/admin/arvore-b")
def admin_arvore_b():
    """
    Página da Árvore B. A busca usa o índice de ID ou o de e-mail
    (com "@") e mostra a posição devolvida e o registro lido nessa posição.
    """
    chave = request.args.get("chave", "").strip()
    busca = None

    if chave:
        if "@" in chave:
            cliente, instrumentacao = buscar_cliente_por_email(chave)
        else:
            cliente, instrumentacao = buscar_cliente_por_id(chave)

        busca = {
            "instrumentacao": instrumentacao,
            "registro": (
                {campo: valor for campo, valor in cliente.items() if campo != "senha"}
                if cliente else None
            )
        }

    return render_template(
        "admin/arvore_b.html",
        arvore=resumo_arvore_b(),
        chave=chave,
        busca=busca
    )

# =====================================
# CADASTRO DE CLIENTES
# =====================================

@app.route("/admin/clientes/cadastrar", methods=["GET", "POST"])
def admin_cadastrar_cliente():

    formulario = {}

    if request.method == "POST":

        formulario = request.form.to_dict()

        try:
            # Simula: grava no fim do arquivo e insere ID e e-mail nas Árvores B.
            # O cliente nasce sem plano; o pacote é associado na contratação.
            cadastrar_cliente(formulario)
            flash("Cliente cadastrado com sucesso!", "success")
            return redirect(url_for("admin_clientes"))
        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "admin/cadastrar_cliente.html",
        formulario=formulario
    )


# =====================================
# VISUALIZAR CLIENTE
# =====================================

@app.route("/admin/clientes/<int:cliente_id>")
def admin_visualizar_cliente(cliente_id):

    # Busca o cliente (Árvore B de ID; simulada por enquanto).
    cliente, _ = buscar_cliente_por_id(cliente_id)

    # Verifica se o cliente existe.
    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("admin_clientes"))

    # Carrega o catálogo de pacotes.
    pacotes = carregar_pacotes()

    # Recupera o pacote associado.
    pacote = pacotes.get(str(cliente["pacote"]))

    # Renderiza a tela.
    return render_template(
        "admin/visualizar_cliente.html",
        cliente=cliente,
        pacote=pacote,
        plano_vigente=plano_vigente(cliente),
        pagina_ativa="clientes"
    )

# =====================================
# EDITAR CLIENTE
# =====================================

@app.route(
    "/admin/clientes/<int:cliente_id>/editar",
    methods=["GET", "POST"]
)
def admin_editar_cliente(cliente_id):

    cliente, _ = buscar_cliente_por_id(cliente_id)

    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("admin_clientes"))

    if request.method == "POST":

        try:
            # Simula: altera o registro na mesma posição do arquivo.
            editar_cliente(cliente_id, request.form)
            flash("Cliente atualizado com sucesso!", "success")
            return redirect(
                url_for(
                    "admin_visualizar_cliente",
                    cliente_id=cliente_id
                )
            )
        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "admin/editar_cliente.html",
        cliente=cliente,
        pagina_ativa="clientes"
    )

# =====================================
# INATIVAR / REATIVAR CLIENTE (exclusão lógica)
# =====================================

def _voltar(cliente_id):
    """Volta para a página de origem (lista com filtros ou detalhes do cliente)."""
    origem = request.referrer or ""
    if origem.startswith(request.host_url):
        return redirect(origem)
    return redirect(url_for("admin_visualizar_cliente", cliente_id=cliente_id))


@app.route("/admin/clientes/<int:cliente_id>/inativar", methods=["POST"])
def admin_inativar_cliente(cliente_id):
    """Exclusão lógica: só o status muda; registro e índices são preservados."""
    try:
        inativar_cliente(cliente_id)
        flash(
            "Cliente inativado. Acesso, contratação e consulta de conectividade "
            "foram bloqueados; os dados foram preservados.",
            "success"
        )
    except ValueError as erro:
        flash(str(erro), "danger")

    return _voltar(cliente_id)


@app.route("/admin/clientes/<int:cliente_id>/reativar", methods=["POST"])
def admin_reativar_cliente(cliente_id):
    try:
        reativar_cliente(cliente_id)
        flash("Cliente reativado. O acesso foi liberado.", "success")
    except ValueError as erro:
        flash(str(erro), "danger")

    return _voltar(cliente_id)


# =====================================
# EXCLUIR CLIENTE (exclusão física restrita — Zona de risco)
# =====================================

@app.route(
    "/admin/clientes/<int:cliente_id>/excluir",
    methods=["POST"]
)
def admin_excluir_cliente(cliente_id):
    try:
        # Simula: a posição do registro fica vazia e as chaves saem das Árvores B.
        excluir_cliente_fisicamente(
            cliente_id,
            request.form.get("confirmacao", ""),
            request.form.get("ciencia") == "sim"
        )
    except ValueError as erro:
        flash(str(erro), "danger")
        if request.form.get("voltar") == "lista":
            return redirect(url_for("admin_clientes", status="todos"))
        return redirect(url_for("admin_visualizar_cliente", cliente_id=cliente_id))

    flash(f"Cliente {cliente_id} excluído permanentemente.", "success")
    return redirect(url_for("admin_clientes", status="inativo"))


# =====================================
# CONSULTA INTEGRADA (Árvore B + Tabela Hash + Grafo)
# =====================================

@app.route("/admin/consulta")
def admin_consulta():
    """
    Consulta integrada do PDF: Árvore B (cliente) -> Tabela Hash (destino).
    A rota (Etapa 3) é apenas demonstrativa e não interfere no resultado.
    """
    formulario = {
        "cliente": request.args.get("cliente", "58372").strip(),
        "destino": request.args.get("destino", "IT").strip().upper(),
        "origem": request.args.get("origem", "BR").strip().upper()
    }

    resposta = consultar_cobertura_cliente(
        formulario["cliente"],
        formulario["destino"],
        tabela_paises,
        carregar_pacotes()
    )

    rota = None
    if resposta["coberto"]:
        rota = rota_demonstrativa(formulario["origem"], formulario["destino"], "menor_latencia")

    return render_template(
        "admin/consulta.html",
        paises=sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]),
        formulario=formulario,
        resposta=resposta,
        rota=rota
    )


# =====================================
# REDE INTERNACIONAL
# =====================================

@app.route("/admin/rede")
def admin_rede():
    formulario = {
        "algoritmo": request.args.get("algoritmo", "dfs"),
        "origem": request.args.get("origem", "BR"),
        "destino": request.args.get("destino", "IT"),
        "criterio": request.args.get("criterio", "menor_latencia")
    }

    return render_template(
        "admin/rede.html",
        rede=rede_demonstracao(),
        grafo=resumo_grafo(),
        algoritmos=ALGORITMOS_REDE,
        instrumentacao=INSTRUMENTACAO_REDE_DEMONSTRACAO,
        formulario=formulario,
        execucao=execucao_demonstrativa(
            formulario["algoritmo"],
            formulario["origem"],
            formulario["destino"],
            formulario["criterio"]
        )
    )

@app.route("/admin/grafo")
def admin_grafo():
    return render_template(
        "admin/grafo.html",
        rede=rede_demonstracao(),
        grafo=resumo_grafo(),
        instrumentacao=INSTRUMENTACAO_REDE_DEMONSTRACAO,
        eventos=EVENTOS_REDE_DEMONSTRACAO
    )
