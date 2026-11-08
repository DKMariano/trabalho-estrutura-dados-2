"""
DGB SIM

Professora: Inês Valderrama Restovic
Disciplina: Estrutura de Dados 2
Equipe: Bruno Barreto, Dimitrius Khouri e Guilherme Lopes
"""

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
from dados_site.servico_conectividade import consultar_conectividade

#ATENÇÃO!!!! APAGAR ESSE IMPORT QUANDO CRIAR A ARVORE B
from dados_site.dados_etapa02 import CLIENTES_DEMONSTRACAO, resumo_arvore_b

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

    # Envia os países, o resultado e a seleção ao template.
    return render_template(
        "paises.html",
        paises=sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]),
        resultado=resultado,
        codigo_selecionado=codigo_selecionado,
        nao_encontrado=nao_encontrado   
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

@app.route("/login", methods=["GET", "POST"])
def login():

    mensagem = None

    if request.method == "POST":

        tipo_acesso = request.form.get("tipo_acesso")
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        if tipo_acesso == "cliente":

            cliente_encontrado = None

            # Localiza o cliente pelo e-mail.
            for cliente in CLIENTES_DEMONSTRACAO.values():

                if cliente["email"].lower() == usuario.lower():
                    cliente_encontrado = cliente
                    break

            # Verifica a senha.
            if (
                cliente_encontrado
                and cliente_encontrado["senha"] == senha
            ):
                return redirect(
                    url_for(
                        "cliente_dashboard",
                        cliente_id=cliente_encontrado["id"]
                    )
                )

            mensagem = "E-mail ou senha incorretos."

        else:

            dados_usuario = USUARIOS.get(usuario)

            if (
                dados_usuario
                and dados_usuario["senha"] == senha
                and dados_usuario["tipo_acesso"] == tipo_acesso
            ):
                return redirect(url_for("admin"))

            else:
                mensagem = "Usuário ou senha incorretos."

    return render_template(
        "login.html",
        mensagem=mensagem
    )

@app.route("/cliente/<int:cliente_id>")
def cliente_dashboard(cliente_id):

    cliente = CLIENTES_DEMONSTRACAO.get(str(cliente_id))

    if cliente is None:
        return redirect(url_for("login"))

    # Busca o pacote do cliente no catálogo (pacotes.json)
    pacotes = carregar_pacotes()
    pacote = pacotes.get(str(cliente["pacote"]))

    return render_template(
        "cliente/dashboard.html",
        cliente=cliente,
        pacote=pacote,
        pagina_ativa="dashboard"
    )

# =====================================
# MINHA CONTA
# =====================================
@app.route("/cliente/<int:cliente_id>/minha-conta")
def cliente_conta(cliente_id):

    cliente = CLIENTES_DEMONSTRACAO.get(str(cliente_id))

    if cliente is None:
        return redirect(url_for("login"))

    pacotes = carregar_pacotes()
    pacote = pacotes.get(str(cliente["pacote"]))

    return render_template(
        "cliente/minha_conta.html",
        cliente=cliente,
        pacote=pacote,
        pagina_ativa="conta"
    )


# =====================================
# MINHA CONECTIVIDADE CLIENTE
# =====================================

@app.route(
    "/cliente/<int:cliente_id>/minha-conectividade",
    methods=["GET", "POST"]
)
def minha_conectividade(cliente_id):
    """
    Consulta de conectividade da área do cliente.

    Etapa 1: Tabela Hash de países.
    Etapa 2: clientes demonstrativos.
    Etapa 3: roteamento demonstrativo.
    """

    cliente = CLIENTES_DEMONSTRACAO.get(str(cliente_id))

    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("login"))

    resposta = None
    resultado = None
    mensagem = None

    formulario = {
        "cliente_id": str(cliente_id),
        "origem": "BR",
        "destino": "IT",
        "criterio": "menor_latencia"
    }

    paises_disponiveis = sorted(
        tabela_paises.listar(),
        key=lambda item: item[1]["nome"]
    )

    if request.method == "POST":
        formulario["origem"] = (
            request.form.get("origem", "").strip().upper()
        )
        formulario["destino"] = (
            request.form.get("destino", "").strip().upper()
        )
        formulario["criterio"] = (
            request.form.get("criterio", "").strip()
        )

        pacotes = carregar_pacotes()

        resposta = consultar_conectividade(
            cliente_id=formulario["cliente_id"],
            origem=formulario["origem"],
            destino=formulario["destino"],
            criterio=formulario["criterio"],
            tabela_paises=tabela_paises,
            pacotes=pacotes
        )

        mensagem = resposta["mensagem"]

        if resposta["sucesso"]:
            resultado = resposta["dados"]
            registrar_consulta(cliente_id, resultado)

    return render_template(
        "cliente/minha_conectividade.html",
        cliente=cliente,
        paises=paises_disponiveis,
        formulario=formulario,
        resposta=resposta,
        resultado=resultado,
        mensagem=mensagem,
        pagina_ativa="conectividade"
    )

# =====================================
# HISTÓRICO DO CLIENTE
# =====================================

@app.route("/cliente/<int:cliente_id>/historico")
def cliente_historico(cliente_id):

    cliente = CLIENTES_DEMONSTRACAO.get(str(cliente_id))

    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("login"))

    registros = [
        registro
        for registro in carregar_historico()
        if registro["cliente_id"] == cliente_id
    ]

    registros.reverse()

    por_pagina = 5
    total = len(registros)

    total_paginas = max(
        1, (total + por_pagina - 1) // por_pagina
    )

    pagina = request.args.get("pagina", 1, type=int)
    pagina = max(1, min(pagina, total_paginas))

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    return render_template(
        "cliente/historico.html",
        cliente=cliente,
        registros=registros[inicio:fim],
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        inicio=inicio + 1 if total else 0,
        fim=min(fim, total),
        pagina_ativa="historico"
    )


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

@app.route("/admin/paises")
def admin_paises():
    # Pendente: integrar esta operação à classe TabelaHash.
    # Feito
    
    busca = request.args.get("busca", "").strip().lower()
    regiao = request.args.get("regiao", "").strip()

    pagina = request.args.get("pagina", 1, type=int)

    por_pagina = 5

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
        por_pagina=por_pagina
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
        tecnologias=tabela_paises.TECNOLOGIAS,
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
        tecnologias=tabela_paises.TECNOLOGIAS,
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

    # Dados demonstrativos temporários.
    clientes = list(CLIENTES_DEMONSTRACAO.values())

    # Catálogo existente de pacotes.
    pacotes = carregar_pacotes()

    nomes_pacotes = {
        str(codigo): dados["nome"]
        for codigo, dados in pacotes.items()
    }

    # Busca por ID (completo) ou por parte do nome.
    busca = request.args.get("busca", "").strip().lower()

    total_clientes = len(clientes)

    if busca:
        clientes = [
            cliente
            for cliente in clientes
            if busca == str(cliente["id"])
            or busca in cliente["nome"].lower()
        ]

    # Filtros por status e por pacote.
    status = request.args.get("status", "").strip()
    pacote_filtro = request.args.get("pacote", "").strip()

    if status:
        clientes = [
            cliente
            for cliente in clientes
            if cliente["status"] == status
        ]

    if pacote_filtro:
        clientes = [
            cliente
            for cliente in clientes
            if str(cliente["pacote"]) == pacote_filtro
        ]

    total_filtrado = len(clientes)

    # Paginação: cinco registros por página.
    por_pagina = 5

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
        busca_id=busca,
        total_clientes=total_clientes,
        total_filtrado=total_filtrado,
        pagina=pagina,
        total_paginas=total_paginas,
        paginas_visiveis=paginas_visiveis,
        inicio=inicio,
        fim=fim
    )
# =====================================
# ARVORE B CLIENTES
# =====================================

@app.route("/admin/arvore-b")
def admin_arvore_b():
    return render_template(
        "admin/arvore_b.html",
        arvore=resumo_arvore_b()
    )

# =====================================
# CADASTRO DE CLIENTES
# =====================================

@app.route("/admin/clientes/cadastrar", methods=["GET", "POST"])
def admin_cadastrar_cliente():

    pacotes = carregar_pacotes()
    formulario = {}

    if request.method == "POST":

        formulario = request.form.to_dict()

        id_texto = formulario.get("id", "").strip()
        nome = formulario.get("nome", "").strip()
        email = formulario.get("email", "").strip()
        esim = formulario.get("esim", "").strip()
        pacote_texto = formulario.get("pacote", "").strip()
        status = formulario.get("status", "ativo").strip()

        # Validação do identificador.
        if not id_texto.isdigit() or int(id_texto) <= 0:
            flash("Informe um ID numérico válido.", "danger")

        elif id_texto in CLIENTES_DEMONSTRACAO:
            flash("Já existe um cliente com esse ID.", "danger")

        elif not nome or not email or not esim:
            flash("Preencha todos os campos obrigatórios.", "danger")

        elif pacote_texto not in pacotes:
            flash("Selecione um pacote válido.", "danger")

        elif status not in ("ativo", "inativo"):
            flash("Selecione um status válido.", "danger")

        else:
            id_cliente = int(id_texto)
            codigo_pacote = int(pacote_texto)

            CLIENTES_DEMONSTRACAO[str(id_cliente)] = {
                "id": id_cliente,
                "nome": nome,
                "email": email,
                "senha": "123456",
                "esim": esim,
                "pacote": codigo_pacote,
                "status": status
            }

            flash(
                "Cliente cadastrado com sucesso!",
                "success"
            )

            return redirect(url_for("admin_clientes"))

    return render_template(
        "admin/cadastrar_cliente.html",
        pacotes=pacotes,
        formulario=formulario
    )


# =====================================
# VISUALIZAR CLIENTE
# =====================================

@app.route("/admin/clientes/<int:cliente_id>")
def admin_visualizar_cliente(cliente_id):

    # Busca o cliente no dicionário demonstrativo.
    cliente = CLIENTES_DEMONSTRACAO.get(str(cliente_id))

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

    cliente = CLIENTES_DEMONSTRACAO.get(str(cliente_id))

    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("admin_clientes"))

    pacotes = carregar_pacotes()

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        esim = request.form.get("esim", "").strip()
        pacote_texto = request.form.get("pacote", "").strip()
        status = request.form.get("status", "").strip()

        if not nome or not email or not esim:
            flash("Preencha todos os campos obrigatórios.", "danger")

        elif pacote_texto not in pacotes:
            flash("Selecione um pacote válido.", "danger")

        elif status not in ("ativo", "inativo"):
            flash("Selecione um status válido.", "danger")

        else:
            cliente["nome"] = nome
            cliente["email"] = email
            cliente["esim"] = esim
            cliente["pacote"] = int(pacote_texto)
            cliente["status"] = status

            flash("Cliente atualizado com sucesso!", "success")

            return redirect(
                url_for(
                    "admin_visualizar_cliente",
                    cliente_id=cliente_id
                )
            )

    return render_template(
        "admin/editar_cliente.html",
        cliente=cliente,
        pacotes=pacotes,
        pagina_ativa="clientes"
    )

# =====================================
# EXCLUIR CLIENTE
# =====================================

@app.route(
    "/admin/clientes/<int:cliente_id>/excluir",
    methods=["POST"]
)
def admin_excluir_cliente(cliente_id):

    # Converte o ID para a chave do dicionário.
    chave = str(cliente_id)

    # Verifica se o cliente existe.
    cliente = CLIENTES_DEMONSTRACAO.get(chave)

    if cliente is None:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("admin_clientes"))

    # Remove o cliente do dicionário demonstrativo.
    del CLIENTES_DEMONSTRACAO[chave]

    flash(
        "Cliente removido com sucesso!",
        "success"
    )

    return redirect(url_for("admin_clientes"))


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
