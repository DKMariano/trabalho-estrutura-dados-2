"""
DGB SIM

Professora: Inês Valderrama Restovic
Disciplina: Estrutura de Dados 2
Equipe: Bruno Barreto, Dimitrius Khouri e Guilherme Lopes
"""

from flask import Flask, render_template, request, redirect, url_for

#ATENÇÃO!!!! CONFIRMAR SE PODEMOS MANTER ESSA IMPORTAÇÃO
from  dados_site.dados_inicio import (BENEFICIOS, DEPOIMENTOS, ITENS_CARROSSEL, PASSOS, PLANOS)

#ATENÇÃO!!!! CONFIRMAR SEP ODEMOS MANTER ESSA IMPORTAÇÃO
from dados_site.dados_usuario import USUARIOS

# Carrega os países do arquivo JSON na TabelaHash.
from arquivos.persistencia_paises import carregar_paises

app = Flask(__name__)

# Carrega os registros persistidos na estrutura em memória.
tabela_paises = carregar_paises()

# Referência temporária para preservar as rotas ainda não adaptadas.
PAISES = tabela_paises.paises



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
    
    if request.method == "POST":
        # Obtém o código, remove espaços e converte para maiúsculas.
        codigo_selecionado = request.form.get("destino", "").strip().upper()     
        
        # Busca o país na TabelaHash; retorna None se não encontrar.   
        resultado = tabela_paises.buscar(codigo_selecionado)

    # Envia os países, o resultado e a seleção ao template.
    return render_template(
        "paises.html",
        paises=tabela_paises.paises,
        resultado=resultado,
        codigo_selecionado=codigo_selecionado
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    mensagem = None

    # ATENÇÃO!!!! CONFIRMAR SE PODEMOS MANTER ESSE TRECHO
    if request.method == "POST":
        tipo_acesso = request.form.get("tipo_acesso")
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        if tipo_acesso == "cliente":
            mensagem = (
                "O acesso de clientes não está disponível na Etapa 1 do projeto."
            )

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


# Exibe a página inicial da área administrativa.
@app.route("/admin")
def admin():

    # Pendente: integrar esta operação à classe TabelaHash.
    total_paises = len(PAISES)
    total_coberturas = len(PAISES)

    return render_template("admin/dashboard.html", paises=PAISES, total_paises=total_paises, total_coberturas=total_coberturas)


@app.route("/admin/paises")
def admin_paises():
    # Pendente: integrar esta operação à classe TabelaHash.

    busca = request.args.get("busca", "").strip().lower()
    regiao = request.args.get("regiao", "").strip()

    pagina = request.args.get("pagina", 1, type=int)

    por_pagina = 5

    paises_filtrados = list(PAISES.items())

    # =====================================
    # BUSCA POR NOME OU CÓDIGO
    # =====================================

    if busca:
        paises_filtrados = [
            (codigo, pais)
            for codigo, pais in paises_filtrados
            if busca in codigo.lower()
            or busca in pais["nome"].lower()
        ]

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
        for pais in PAISES.values()
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
        total_paises=len(PAISES),
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
    regioes = [
        "África",
        "América",
        "Ásia",
        "Europa",
        "Oceania"
    ]

    tecnologias = [
        "2G",
        "3G",
        "4G",
        "5G"
    ]

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
        if not nome or not codigo or not regiao or not operadora or not tecnologia:
            mensagem = "Preencha todos os campos obrigatórios."

        # O código utilizado como chave deve possuir duas letras.
        elif len(codigo) != 2 or not codigo.isalpha():
            mensagem = "O código do país deve possuir exatamente 2 letras."

        # Impede que uma chave já existente seja sobrescrita.
        elif codigo in PAISES:
            mensagem = "Já existe um país cadastrado com esse código."

        else:
            PAISES[codigo] = {
                "nome": nome,
                "regiao": regiao,
                "operadora": operadora,
                "tecnologia": tecnologia
            }

            return redirect(url_for("admin_paises"))

    return render_template(
        "admin/cadastrar_pais.html",
        regioes=regioes,
        tecnologias=tecnologias,
        dados_formulario=dados_formulario,
        mensagem=mensagem,
        pagina_ativa="paises"
    )


@app.route("/admin/paises/<codigo>")
def admin_visualizar_pais(codigo):
    # Pendente: integrar esta operação à classe TabelaHash.

    codigo = codigo.upper()

    pais = PAISES.get(codigo)

    if pais is None:
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
    codigo = codigo.upper()

    pais = PAISES.get(codigo)

    if pais is None:
        return redirect(url_for("admin_paises"))

    if request.method == "POST":

        pais["nome"] = request.form.get("nome", "").strip()
        pais["regiao"] = request.form.get("regiao", "").strip()
        pais["operadora"] = request.form.get("operadora", "").strip()
        pais["tecnologia"] = request.form.get("tecnologia", "").strip()

        return redirect(url_for("admin_paises"))

    return render_template(
        "admin/editar_pais.html",
        codigo=codigo,
        pais=pais
    )

@app.route(
    "/admin/paises/<codigo>/excluir",
    methods=["POST"]
)
def admin_excluir_pais(codigo):
    """
    Remove um país do dicionário utilizado pelo MVP.
    """

    codigo = codigo.upper()

    if codigo in PAISES:
        del PAISES[codigo]

    return redirect(url_for("admin_paises"))
