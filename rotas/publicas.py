"""
DGB SIM — Rotas públicas: início, cobertura, planos, login,
compra de plano e criação de conta.

Rotas (6):
    /                    página inicial                dados fixos (dados_inicio.py)
    /paises              cobertura por país            Tabela Hash
    /planos              catálogo de planos            pacotes.json
    /login               login do cliente e do admin   Árvore B (e-mail)
    /adquirir/<plano>    compra pública de um plano    Árvore B (e-mail) + Tabela Hash
    /criar-conta         cadastro feito pelo cliente   Árvore B (ID e e-mail)
"""

from flask import render_template, request, redirect, url_for, flash

from app import app, tabela_paises

from dados_site.dados_inicio import (BENEFICIOS, DEPOIMENTOS, ITENS_CARROSSEL, PASSOS, PLANOS, APRESENTACAO_PLANOS)
from dados_site.credenciais_admin import USUARIOS

from arquivos.persistencia_pacotes import carregar_pacotes

from servicos.paises import paises_agrupados_por_regiao
from servicos.planos import planos_compativeis
from servicos.clientes import (
    buscar_cliente_por_id,
    criar_conta,
    autenticar_cliente,
    processar_contratacao
)


# =====================================
# PÁGINA INICIAL
# =====================================
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

# =====================================
# COBERTURA POR PAÍS (Tabela Hash)
# =====================================
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

    return render_template(
        "paises.html",
        paises=sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]),
        resultado=resultado,
        codigo_selecionado=codigo_selecionado,
        nao_encontrado=nao_encontrado,
        planos_compativeis=compativeis
    )

# =====================================
# PLANOS
# =====================================
@app.route("/planos")
def planos():
    pacotes = carregar_pacotes()

    return render_template(
        "planos.html",
        pacotes=pacotes,
        planos=PLANOS,
        apresentacao=APRESENTACAO_PLANOS,
    )

# =====================================
# LOGIN
# =====================================
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Tela de acesso com duas abas.

    - Cliente: o e-mail é buscado na Árvore B de e-mail; a senha demonstrativa
      e o status são conferidos; o cliente vai para /cliente/<id>.
      Não existe sessão: daí em diante o cliente é identificado pela URL.
    - Administrador: confere admin/admin (credenciais_admin.py) e leva ao painel.
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

# =====================================
# COMPRA DE PLANO
# =====================================
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
                    request.form.get("confirmado") == "sim", pacotes, tabela_paises
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
        paises_por_regiao=paises_agrupados_por_regiao(tabela_paises),
        paises_marcados=paises_marcados
    )


# =====================================
# CRIAR CONTA
# =====================================
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
            # Grava no fim do clientes.json e insere ID e e-mail nas duas Árvores B.
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
