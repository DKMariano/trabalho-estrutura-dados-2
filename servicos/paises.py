"""
DGB SIM — Serviço de países.

Regra do país digitado livremente pelo cliente ou pelo admin: aceita o
código (IT) ou o nome, com ou sem acento (Itália, italia).

As funções recebem a Tabela Hash de países como parâmetro, para o
serviço não depender do app.py.
"""

import unicodedata


def _sem_acento(texto):
    """'Itália' -> 'italia' (para comparar o que o cliente digitou)."""
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower()


def resolver_pais(texto, tabela_paises):
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


def nome_do_pais(codigo, tabela_paises):
    """Nome para exibir no campo; se o código não existir, mostra o texto digitado."""
    for cod, pais in tabela_paises.listar():
        if cod == codigo:
            return pais["nome"]
    return codigo


def paises_agrupados_por_regiao(tabela_paises):
    """Países atendidos por região, lidos da Tabela Hash (para escolher o Basic)."""
    grupos = {}
    for codigo, pais in sorted(tabela_paises.listar(), key=lambda item: item[1]["nome"]):
        grupos.setdefault(pais["regiao"], []).append((codigo, pais["nome"]))
    return grupos