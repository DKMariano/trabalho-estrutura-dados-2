"""
DGB SIM — Rotas da área do cliente (/cliente/<id>/...).
Não existe sessão: o cliente é identificado pelo ID na URL.

Rotas (5):
    /cliente/<id>                       painel do cliente         Árvore B (ID) + Tabela Hash
    /cliente/<id>/minha-conta           dados da conta            Árvore B (ID)
    /cliente/<id>/contratar             consulta e contratação    Árvore B + Tabela Hash
    /cliente/<id>/minha-conectividade   cobertura e histórico     Árvore B + Tabela Hash
    /cliente/<id>/historico             redireciona para a Minha conectividade
"""

from flask import render_template, request, redirect, url_for, flash

from app import app, tabela_paises, paginar

from arquivos.persistencia_pacotes import carregar_pacotes
from arquivos.persistencia_historico import (carregar_historico, registrar_consulta)

from servicos.paises import resolver_pais, nome_do_pais, paises_agrupados_por_regiao
from servicos.conectividade import consultar_cobertura_cliente, rota_demonstrativa
from servicos.planos import plano_vigente, sugestoes_upgrade
from servicos.clientes import  buscar_cliente_por_id, MENSAGEM_INATIVO, processar_contratacao

# =====================================
# ACESSO À ÁREA DO CLIENTE
# =====================================
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

# =====================================
# PAINEL DO CLIENTE
# =====================================
@app.route("/cliente/<int:cliente_id>")
def cliente_dashboard(cliente_id):

    cliente, bloqueio = cliente_liberado(cliente_id)
    if bloqueio:
        return bloqueio

    # Busca o pacote do cliente no catálogo (pacotes.json)
    pacotes = carregar_pacotes()
    pacote = pacotes.get(str(cliente["pacote"]))

    # Texto da cobertura do plano (card Meu plano)
    cobertura = None
    if pacote:
        if pacote["categoria"] == "Basic":
            cobertura = ", ".join(nome_do_pais(codigo, tabela_paises) for codigo in cliente["paises_ativos"])
        elif pacote["categoria"] == "Plus":
            total = len(paises_agrupados_por_regiao(tabela_paises).get(pacote["regiao"], []))
            cobertura = f"Os {total} países da {pacote['regiao']}"
        else:
            cobertura = f"Os {len(tabela_paises.listar())} países atendidos"

    # Resumo do histórico (card Minha conectividade): total e consulta mais recente
    historico = historico_do_cliente(cliente_id, 1)
    ultima_consulta = historico["registros"][0] if historico["registros"] else None

    return render_template(
        "cliente/dashboard.html",
        cliente=cliente,
        pacote=pacote,
        cobertura=cobertura,
        plano_vigente=plano_vigente(cliente),
        total_consultas=historico["total"],
        ultima_consulta=ultima_consulta,
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
# CONTRATAR PLANO
# =====================================
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
    origem = resolver_pais(request.args.get("origem", ""), tabela_paises)
    destino = resolver_pais(request.args.get("destino", ""), tabela_paises)
    paises_marcados = [destino] if destino else []

    # ---------- contratação ----------
    if request.method == "POST":
        paises_marcados = request.form.getlist("paises")

        try:
            pacote, fim = processar_contratacao(
                cliente, plano, paises_marcados,
                request.form.get("confirmado") == "sim", pacotes, tabela_paises
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
        origem_digitada=nome_do_pais(origem, tabela_paises),
        destino_digitado=nome_do_pais(destino, tabela_paises),
        consulta=consulta,
        paises=sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]),
        paises_por_regiao=paises_agrupados_por_regiao(tabela_paises),
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

    paginacao = paginar(registros, pagina, por_pagina)

    return {
        "registros": paginacao["itens"],
        "total": paginacao["total"],
        "pagina": paginacao["pagina"],
        "total_paginas": paginacao["total_paginas"],
        "inicio": paginacao["inicio"],
        "fim": paginacao["fim"],
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
        # Origem e destino aceitam o nome ou o código do país (ex.: Itália ou IT)
        formulario["origem"] = resolver_pais(request.form.get("origem", ""), tabela_paises)
        formulario["destino"] = resolver_pais(request.form.get("destino", ""), tabela_paises)
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
        origem_digitada=nome_do_pais(formulario["origem"], tabela_paises),
        destino_digitado=nome_do_pais(formulario["destino"], tabela_paises),
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
