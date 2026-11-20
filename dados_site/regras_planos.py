"""
DGB SIM — Regras de cobertura dos planos (versão inicial).

Funções puras: recebem os dados já recuperados pelas estruturas
(cliente pela Árvore B, país pela Tabela Hash, pacote pelo catálogo)
e decidem a cobertura. Não fazem buscas.

Regras (decisões da equipe):
- Basic: cobre somente os 3 países escolhidos na contratação (paises_ativos).
- Plus: cobre os países da região do plano.
- Global (plano 301, IlimitadoSIM): cobre todos os países atendidos.
- Plano com contratacao_fim já atingida está expirado (o cliente continua ativo).

Revisar com a tarefa B4 do backend (regras puras de cobertura).
"""

from datetime import datetime, timedelta


def plano_vigente(cliente, agora=None):
    """True se o cliente tem plano e a data de fim ainda não chegou."""
    if cliente.get("pacote") is None or not cliente.get("contratacao_fim"):
        return False

    agora = agora or datetime.now().astimezone()
    fim = datetime.fromisoformat(cliente["contratacao_fim"])

    return agora < fim


def cobertura_do_plano(pacote, cliente, codigo_destino, pais_destino):
    """True se o plano do cliente cobre o destino (já encontrado na Tabela Hash)."""
    categoria = pacote.get("categoria")

    if categoria == "Basic":
        return codigo_destino in cliente.get("paises_ativos", [])

    if categoria == "Plus":
        return pais_destino["regiao"] == pacote.get("regiao")

    if categoria == "Global":
        return True

    return False


def planos_compativeis(pais_destino, pacotes):
    """
    Planos que podem cobrir o destino.

    Basic aparece quando o destino é da região do plano: o país deverá ser
    um dos 3 escolhidos na contratação.
    Devolve uma lista de dicionários com o código incluído.
    """
    compativeis = []

    for codigo, pacote in pacotes.items():
        categoria = pacote.get("categoria")

        if categoria == "Global" or pacote.get("regiao") == pais_destino["regiao"]:
            compativeis.append({"codigo": codigo, **pacote})

    return compativeis


def calcular_fim(inicio, pacote):
    """Fim da vigência = início + validade do pacote (em dias)."""
    return inicio + timedelta(days=pacote["validade_dias"])


def validar_paises_basic(pacote, codigos, tabela_paises):
    """
    Regra do Basic: exatamente 3 países distintos, atendidos e da região do
    plano. Cada código é consultado pela chave na Tabela Hash.

    Devolve a lista de códigos normalizados. Lança ValueError.
    """
    codigos = [str(codigo).strip().upper() for codigo in codigos if str(codigo).strip()]

    if len(codigos) != 3 or len(set(codigos)) != 3:
        raise ValueError(f"O plano {pacote['nome']} exige exatamente 3 países diferentes.")

    for codigo in codigos:
        pais = tabela_paises.buscar(codigo)

        if pais is None:
            raise ValueError(f"O país {codigo} não está cadastrado como atendido.")

        if pais["regiao"] != pacote.get("regiao"):
            raise ValueError(
                f"{pais['nome']} não pertence à região {pacote.get('regiao')} do plano."
            )

    return codigos


def sugestoes_upgrade(pacote, pais_destino, pacotes):
    """
    Planos sugeridos na tela "Contratar plano" (decisão da equipe):

    - Basic -> Plus da região do destino + Global;
    - Plus  -> Global;
    - Global -> nenhum (já cobre todos os países atendidos).

    Devolve uma lista de dicionários com o código incluído.
    """
    categoria = pacote.get("categoria")
    sugestoes = []

    for codigo, outro in pacotes.items():
        if outro.get("categoria") == "Global" and categoria in ("Basic", "Plus"):
            sugestoes.append({"codigo": codigo, **outro})
        elif (categoria == "Basic" and outro.get("categoria") == "Plus"
              and outro.get("regiao") == pais_destino["regiao"]):
            sugestoes.append({"codigo": codigo, **outro})

    # Plus antes do Global, para a leitura ficar em ordem de abrangência.
    return sorted(sugestoes, key=lambda plano: plano["categoria"] == "Global")
