from flask import Flask, redirect, url_for, flash

# Carrega os países do arquivo JSON na TabelaHash.
from arquivos.persistencia_paises import carregar_paises

# Erro dos índices de clientes (Árvores B), tratado para todas as rotas.
from servicos.clientes import ErroIndices

app = Flask(__name__)
app.secret_key = "dgb-sim-chave-de-desenvolvimento"

# Carrega os registros persistidos na estrutura em memória.
tabela_paises = carregar_paises()


@app.template_filter("data_br")
def data_br(valor):
    """Mostra uma data ISO (2026-11-27T14:00:00-03:00) como 27/11/2026."""
    if not valor:
        return "—"
    return f"{valor[8:10]}/{valor[5:7]}/{valor[0:4]}"

def paginar(itens, pagina, por_pagina):
    """
    Divide a lista em páginas e devolve a página pedida com os números
    usados nas telas. Página fora do intervalo é ajustada para a mais próxima.
    """
    total = len(itens)
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    pagina = max(1, min(pagina, total_paginas))

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    return {
        "itens": itens[inicio:fim],
        "total": total,
        "pagina": pagina,
        "total_paginas": total_paginas,
        "inicio": inicio + 1 if total else 0,
        "fim": min(fim, total),
    }


@app.errorhandler(ErroIndices)
def tratar_erro_indices(erro):
    flash(str(erro), "danger")
    return redirect(url_for("admin"))


# As rotas usam @app.route; por isso são importadas só aqui no fim,
# depois que app, tabela_paises e paginar já existem.
# (importação circular entre o app.py e as rotas).
from rotas import publicas, cliente, admin  # noqa: E402,F401