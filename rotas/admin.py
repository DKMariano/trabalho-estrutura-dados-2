"""
DGB SIM — Rotas do painel administrativo (/admin/...): países (Tabela
Hash), clientes (Árvores B), consulta integrada, rede e grafo.

Rotas (18):
    /admin                           painel                    Tabela Hash + Árvore B (métricas)
    /admin/paises                    listar países             Tabela Hash
    /admin/paises/cadastrar          cadastrar país            Tabela Hash
    /admin/paises/<codigo>           visualizar país           Tabela Hash
    /admin/paises/<codigo>/editar    editar país               Tabela Hash
    /admin/paises/<codigo>/excluir   excluir país              Tabela Hash
    /admin/tabela-hash               instrumentação            Tabela Hash
    /admin/clientes                  listar clientes           Árvore B (ID e e-mail)
    /admin/arvore-b                  busca e instrumentação    Árvore B (ID ou e-mail)
    /admin/clientes/cadastrar        cadastrar cliente         Árvore B + Tabela Hash (Basic)
    /admin/clientes/<id>             visualizar cliente        Árvore B (ID)
    /admin/clientes/<id>/editar      editar cliente            Árvore B + Tabela Hash (Basic)
    /admin/clientes/<id>/inativar    exclusão lógica           Árvore B (ID)
    /admin/clientes/<id>/reativar    reativar cliente          Árvore B (ID)
    /admin/clientes/<id>/excluir     exclusão física           reconstrói as Árvores B
    /admin/consulta                  consulta integrada        Árvore B + Tabela Hash
    /admin/rede                      rede (Etapa 3)            dados demonstrativos
    /admin/grafo                     grafo (Etapa 3)           dados demonstrativos
"""

from flask import render_template, request, redirect, url_for, flash

from app import app, tabela_paises, paginar

from arquivos.persistencia_paises import salvar_paises
from arquivos.persistencia_pacotes import carregar_pacotes

from servicos.paises import resolver_pais, nome_do_pais, paises_agrupados_por_regiao
from servicos.conectividade import consultar_cobertura_cliente, rota_demonstrativa
from servicos.planos import plano_vigente, pacote_escolhido_pelo_admin, paises_abrangidos
from servicos.clientes import (
    buscar_cliente_por_id,
    buscar_cliente_por_email,
    listar_clientes,
    total_clientes,
    cadastrar_cliente,
    editar_cliente,
    inativar_cliente,
    reativar_cliente,
    excluir_cliente_fisicamente,
    proximo_id,
    resumo_arvore_b,
    instrumentacao_arvore_b,
    associar_pacote
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

# Tecnologias oferecidas nos formulários de país.
# A Tabela Hash aceita 2G a 5G e não pode ser alterada; a restrição fica só na tela.
TECNOLOGIAS_OFERECIDAS = ["4G", "5G"]


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
# PAÍSES (Tabela Hash): listar, cadastrar, visualizar, editar e excluir
# =====================================

OPCOES_POR_PAGINA_ADMIN = [5, 10, 20]


def ler_por_pagina():
    """Quantidade de linhas por página escolhida na tabela (5, 10 ou 20)."""
    por_pagina = request.args.get("por_pagina", 5, type=int)
    return por_pagina if por_pagina in OPCOES_POR_PAGINA_ADMIN else 5


@app.route("/admin/paises")
def admin_paises():

    busca = request.args.get("busca", "").strip().lower()
    regiao = request.args.get("regiao", "").strip()

    pagina = request.args.get("pagina", 1, type=int)

    por_pagina = ler_por_pagina()

    paises_filtrados = sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"])

    # BUSCA POR NOME OU CÓDIGO

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

    # FILTRO POR REGIÃO

    if regiao:
        paises_filtrados = [
            (codigo, pais)
            for codigo, pais in paises_filtrados
            if pais["regiao"] == regiao
        ]

    # REGIÕES DISPONÍVEIS

    regioes = sorted({
        pais["regiao"]
        for _, pais in tabela_paises.listar()
    })

    # PAGINAÇÃO

    paginacao = paginar(paises_filtrados, pagina, por_pagina)

    return render_template(
        "admin/paises.html",
        paises=paginacao["itens"],
        total_paises=tabela_paises.tam(),
        total_filtrados=paginacao["total"],
        regioes=regioes,
        busca=busca,
        regiao_selecionada=regiao,
        pagina=paginacao["pagina"],
        total_paginas=paginacao["total_paginas"],
        por_pagina=por_pagina,
        opcoes_por_pagina=OPCOES_POR_PAGINA_ADMIN
    )

@app.route("/admin/paises/cadastrar", methods=["GET", "POST"])
def admin_cadastrar_pais():

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

    codigo = codigo.upper()

    pais = tabela_paises.buscar(codigo)

    if pais is None:
        flash("País não encontrado.", "erro")
        return redirect(url_for("admin_paises"))

    mensagem = None
    dados = pais

    if request.method == "POST":
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

    # Percurso em ordem da Árvore B de ID + filtros.
    clientes = listar_clientes(busca=busca, pacote=pacote_filtro, status=status)

    total_clientes_cadastrados = total_clientes()
    total_filtrado = len(clientes)

    # Paginação: 5, 10 ou 20 registros por página (escolha do admin).
    por_pagina = ler_por_pagina()

    try:
        pagina = int(request.args.get("pagina", 1))
    except (TypeError, ValueError):
        pagina = 1

    paginacao = paginar(clientes, pagina, por_pagina)
    pagina = paginacao["pagina"]
    total_paginas = paginacao["total_paginas"]

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
        clientes=paginacao["itens"],
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
        fim=paginacao["fim"],
        por_pagina=por_pagina,
        opcoes_por_pagina=OPCOES_POR_PAGINA_ADMIN
    )


# =====================================
# ÁRVORE B DE CLIENTES
# =====================================

@app.route("/admin/arvore-b")
def admin_arvore_b():
    """
    Página da Árvore B. O administrador escolhe o índice (?indice=id ou
    ?indice=email) e a página mostra somente a instrumentação dessa árvore.
    A busca (?chave=) devolve a posição e o registro lido nessa posição.
    """
    indice = request.args.get("indice", "id").strip()
    if indice not in ("id", "email"):
        indice = "id"

    chave = request.args.get("chave", "").strip()
    busca = None

    if chave:
        if indice == "email":
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
        indice=indice,
        chave=chave,
        busca=busca,
        metricas=instrumentacao_arvore_b(indice)
    )


# =====================================
# CADASTRO DE CLIENTES
# =====================================

@app.route("/admin/clientes/cadastrar", methods=["GET", "POST"])
def admin_cadastrar_cliente():

    pacotes = carregar_pacotes()
    formulario = {}
    paises_marcados = []

    if request.method == "POST":

        formulario = request.form.to_dict()
        paises_marcados = request.form.getlist("paises")

        try:
            escolha = pacote_escolhido_pelo_admin(request.form, pacotes, tabela_paises)

            # O ID vem do controle_ids.json (proximo_id); IDs excluídos nunca são reutilizados
            formulario["id"] = str(proximo_id())

            # Grava no fim do clientes.json e insere ID e e-mail nas Árvores B.
            cliente = cadastrar_cliente(formulario)

            # Pacote escolhido pelo admin: grava no registro (mesma posição).
            if escolha:
                associar_pacote(cliente["id"], escolha)

            flash(f"Cliente {cliente['id']} cadastrado com sucesso!", "success")
            return redirect(url_for("admin_clientes"))
        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "admin/cadastrar_cliente.html",
        formulario=formulario,
        pacotes=pacotes,
        paises_por_regiao=paises_agrupados_por_regiao(tabela_paises),
        paises_marcados=paises_marcados,
        proximo_id=proximo_id()
    )


# =====================================
# VISUALIZAR CLIENTE
# =====================================

@app.route("/admin/clientes/<int:cliente_id>")
def admin_visualizar_cliente(cliente_id):

    cliente, _ = buscar_cliente_por_id(cliente_id)

    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("admin_clientes"))

    pacotes = carregar_pacotes()

    pacote = pacotes.get(str(cliente["pacote"]))

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

    pacotes = carregar_pacotes()
    formulario = {}
    paises_marcados = list(cliente.get("paises_ativos", []))

    if request.method == "POST":

        formulario = request.form.to_dict()
        paises_marcados = request.form.getlist("paises")

        try:
            escolha = pacote_escolhido_pelo_admin(request.form, pacotes, tabela_paises)

            # O e-mail é chave da Árvore B de e-mail e não pode ser alterado: o formulário não envia o campo e o valor atual é mantido.
            dados = request.form.to_dict()
            dados["email"] = cliente["email"]

            # Altera o registro na mesma posição do clientes.json; as Árvores B não mudam.
            editar_cliente(cliente_id, dados)

            # Novo pacote escolhido: substitui o atual e reinicia a vigência.
            if escolha:
                associar_pacote(cliente_id, escolha)

            flash("Cliente atualizado com sucesso!", "success")
            return redirect(
                url_for(
                    "admin_visualizar_cliente",
                    cliente_id=cliente_id
                )
            )
        except ValueError as erro:
            flash(str(erro), "danger")

    pacote_atual = pacotes.get(str(cliente["pacote"]))

    return render_template(
        "admin/editar_cliente.html",
        cliente=cliente,
        formulario=formulario,
        pacotes=pacotes,
        pacote_atual=pacote_atual,
        pacote_escolhido=formulario.get("pacote", ""),
        paises_marcados=paises_marcados,
        paises_por_regiao=paises_agrupados_por_regiao(tabela_paises),
        paises_abrangidos=paises_abrangidos(cliente, pacote_atual, tabela_paises),
        plano_vigente=plano_vigente(cliente),
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
        # A posição vira null no clientes.json e as duas Árvores B são reconstruídas.
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
        "cliente": request.args.get("cliente", "1001").strip(),
        # Origem e destino aceitam o nome ou o código do país (ex.: Itália ou IT)
        "origem": resolver_pais(request.args.get("origem", "BR"), tabela_paises),
        "destino": resolver_pais(request.args.get("destino", "IT"), tabela_paises)
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
        origem_digitada=nome_do_pais(formulario["origem"], tabela_paises),
        destino_digitado=nome_do_pais(formulario["destino"], tabela_paises),
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


# =====================================
# GRAFO
# =====================================

@app.route("/admin/grafo")
def admin_grafo():
    return render_template(
        "admin/grafo.html",
        rede=rede_demonstracao(),
        grafo=resumo_grafo(),
        instrumentacao=INSTRUMENTACAO_REDE_DEMONSTRACAO,
        eventos=EVENTOS_REDE_DEMONSTRACAO
    )
