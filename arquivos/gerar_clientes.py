"""
DGB SIM — Gerador da carga inicial de clientes (Etapa 2).

Gera, de uma só vez:
    arquivos/controle_ids.json  -> contador e histórico de IDs (DUV-006/010)
    arquivos/clientes.json      -> lista de clientes (posição = localização na Árvore B)
    arquivos/historico.json     -> lista vazia (somente com --forcar; DC-12)

Uso (executado manualmente, a partir da raiz do projeto):
    python arquivos/gerar_clientes.py            # recusa se os arquivos já existirem
    python arquivos/gerar_clientes.py --forcar   # recarga completa (exige autorização da equipe)

Regras (DC-05 e DC-12):
- Clientes 1 a 1000 fictícios:
    nome   "Cliente Fictício NNNN"
    e-mail "cliente{1000+id}@example.com"
    eSIM   "ESIM-0{1000+id}"
    senha  "123456" (fixa; DC-14)
    inativo    quando id % 11 == 1
    sem plano  quando id % 5 == 1
  Plano, países do Basic e datas são sorteados com semente fixa:
  rodar duas vezes gera exatamente os mesmos arquivos.
- Cliente 1001 (Ines): registro de demonstração, idêntico ao da carga original.

Segurança (DUV-007, DUV-011, DC-02):
- Sem --forcar, nada é gravado se algum arquivo de destino já existir
  (historico.json só bloqueia se tiver registros).
- Os dados são gerados e validados em memória ANTES de qualquer gravação.
- Ordem de gravação: controle_ids.json -> clientes.json -> historico.json.
  Cada arquivo é gravado em um temporário e depois substitui o original.
- Não há recuperação automática: se uma gravação falhar, o erro é exibido
  e o script termina.

Este script não importa o app.py nem a Árvore B: lê apenas pacotes.json
e paises.json.
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PASTA = Path(__file__).resolve().parent

CAMINHO_CLIENTES = PASTA / "clientes.json"
CAMINHO_CONTROLE = PASTA / "controle_ids.json"
CAMINHO_HISTORICO = PASTA / "historico.json"
CAMINHO_PACOTES = PASTA / "pacotes.json"
CAMINHO_PAISES = PASTA / "paises.json"

SEMENTE = 2026                 # semente fixa: resultado reproduzível
QUANTIDADE_FICTICIOS = 1000    # clientes 1 a 1000 (o 1001 é a Ines)
SENHA_DEMONSTRATIVA = "123456"

FUSO = timezone(timedelta(hours=-3))
# Data-base fixa: as datas não dependem do dia em que o script roda.
DATA_BASE = datetime(2026, 11, 16, 12, 0, 0, tzinfo=FUSO)
DIAS_RECENTES = 7              # contratações recentes: até 6 dias antes da data-base
DIAS_ANTIGA = 41               # contratação antiga (2026-10-06): plano já expirado
CHANCE_EXPIRADO = 1 / 9        # aproximadamente a proporção da carga original

# Registro de demonstração, idêntico ao da carga original.
CLIENTE_INES = {
    "id": 1001,
    "nome": "Ines",
    "email": "ines@ed2.com",
    "senha": "123456",
    "esim": "ESIM-10001",
    "pacote": 102,
    "paises_ativos": [],
    "contratacao_inicio": "2026-11-10T10:00:00-03:00",
    "contratacao_fim": "2026-12-10T10:00:00-03:00",
    "status": "ativo",
}


# =============================================================================
# LEITURA DOS CATÁLOGOS
# =============================================================================

def carregar_json(caminho):
    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def paises_por_regiao(paises):
    """{regiao: [códigos em ordem alfabética]} a partir de paises.json."""
    grupos = {}
    for codigo, pais in sorted(paises.items()):
        grupos.setdefault(pais["regiao"], []).append(codigo)
    return grupos


# =============================================================================
# GERAÇÃO
# =============================================================================

def gerar_cliente(cliente_id, sorteio, pacotes, grupos):
    """Monta um cliente fictício seguindo as regras da carga."""
    numero = 1000 + cliente_id

    cliente = {
        "id": cliente_id,
        "nome": f"Cliente Fictício {cliente_id:04d}",
        "email": f"cliente{numero}@example.com",
        "senha": SENHA_DEMONSTRATIVA,
        "esim": f"ESIM-{numero:05d}",
        "pacote": None,
        "paises_ativos": [],
        "contratacao_inicio": None,
        "contratacao_fim": None,
        "status": "inativo" if cliente_id % 11 == 1 else "ativo",
    }

    if cliente_id % 5 == 1:
        return cliente   # sem plano

    codigo = sorteio.choice(sorted(pacotes))
    pacote = pacotes[codigo]

    if pacote["categoria"] == "Basic":
        cliente["paises_ativos"] = sorted(sorteio.sample(grupos[pacote["regiao"]], 3))

    if sorteio.random() < CHANCE_EXPIRADO:
        inicio = DATA_BASE - timedelta(days=DIAS_ANTIGA)
    else:
        inicio = DATA_BASE - timedelta(days=sorteio.randrange(DIAS_RECENTES))

    fim = inicio + timedelta(days=pacote["validade_dias"])

    cliente["pacote"] = int(codigo)
    cliente["contratacao_inicio"] = inicio.isoformat()
    cliente["contratacao_fim"] = fim.isoformat()
    return cliente


def gerar_carga(pacotes, paises):
    """Devolve (clientes, controle) gerados em memória."""
    sorteio = random.Random(SEMENTE)
    grupos = paises_por_regiao(paises)

    clientes = [
        gerar_cliente(cliente_id, sorteio, pacotes, grupos)
        for cliente_id in range(1, QUANTIDADE_FICTICIOS + 1)
    ]
    clientes.append(dict(CLIENTE_INES))

    ids = [cliente["id"] for cliente in clientes]
    controle = {"proximo_id": max(ids) + 1, "ids_utilizados": ids}

    return clientes, controle


# =============================================================================
# VALIDAÇÃO (antes de gravar)
# =============================================================================

def validar_carga(clientes, controle, pacotes, paises):
    """Confere a carga gerada. Devolve a lista de erros (vazia = válida)."""
    erros = []
    ids, emails = set(), set()

    for posicao, cliente in enumerate(clientes):
        rotulo = f"posição {posicao} (id {cliente.get('id')})"

        if not isinstance(cliente["id"], int) or cliente["id"] <= 0:
            erros.append(f"{rotulo}: ID inválido")
        if cliente["id"] in ids:
            erros.append(f"{rotulo}: ID duplicado")
        ids.add(cliente["id"])

        email = cliente["email"]
        if email != email.strip().lower() or "@" not in email:
            erros.append(f"{rotulo}: e-mail não normalizado ou inválido")
        if email in emails:
            erros.append(f"{rotulo}: e-mail duplicado")
        emails.add(email)

        if not cliente["nome"] or not cliente["esim"]:
            erros.append(f"{rotulo}: nome ou eSIM vazio")
        if cliente["status"] not in ("ativo", "inativo"):
            erros.append(f"{rotulo}: status inválido")

        codigo = cliente["pacote"]
        if codigo is None:
            if cliente["paises_ativos"] or cliente["contratacao_inicio"] or cliente["contratacao_fim"]:
                erros.append(f"{rotulo}: sem plano, mas com países ou datas")
            continue

        pacote = pacotes.get(str(codigo))
        if pacote is None:
            erros.append(f"{rotulo}: pacote {codigo} inexistente")
            continue

        escolhidos = cliente["paises_ativos"]
        if pacote["categoria"] == "Basic":
            if len(escolhidos) != 3 or len(set(escolhidos)) != 3:
                erros.append(f"{rotulo}: Basic sem exatamente 3 países")
            elif any(paises.get(c, {}).get("regiao") != pacote["regiao"] for c in escolhidos):
                erros.append(f"{rotulo}: país fora da região do plano")
        elif escolhidos:
            erros.append(f"{rotulo}: Plus/Global não guarda países")

        inicio = datetime.fromisoformat(cliente["contratacao_inicio"])
        fim = datetime.fromisoformat(cliente["contratacao_fim"])
        if fim - inicio != timedelta(days=pacote["validade_dias"]):
            erros.append(f"{rotulo}: fim diferente de início + validade")

    historico_ids = controle["ids_utilizados"]
    if len(historico_ids) != len(set(historico_ids)):
        erros.append("controle: IDs repetidos no histórico")
    if set(historico_ids) != ids:
        erros.append("controle: histórico diferente dos IDs dos clientes")
    if controle["proximo_id"] <= max(historico_ids):
        erros.append("controle: proximo_id não é maior que todos os IDs usados")

    return erros


# =============================================================================
# GRAVAÇÃO (arquivo temporário + substituição; DUV-004)
# =============================================================================

def gravar_json(caminho, dados, indent):
    temporario = caminho.with_name(caminho.name + ".tmp")
    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=indent)
        arquivo.flush()
        os.fsync(arquivo.fileno())
    os.replace(temporario, caminho)


def historico_tem_registros():
    if not CAMINHO_HISTORICO.exists():
        return False
    try:
        return bool(carregar_json(CAMINHO_HISTORICO))
    except (OSError, json.JSONDecodeError):
        return True   # na dúvida, trata como ocupado


def arquivos_bloqueados():
    """Arquivos de destino que impedem a geração sem --forcar."""
    bloqueados = [c.name for c in (CAMINHO_CONTROLE, CAMINHO_CLIENTES) if c.exists()]
    if historico_tem_registros():
        bloqueados.append(CAMINHO_HISTORICO.name)
    return bloqueados


# =============================================================================
# EXECUÇÃO
# =============================================================================

def main(argumentos):
    forcar = "--forcar" in argumentos

    if not forcar:
        bloqueados = arquivos_bloqueados()
        if bloqueados:
            print("Nada foi gravado. Já existem: " + ", ".join(bloqueados) + ".")
            print("A recarga substitui todos os clientes e reinicia o controle de IDs.")
            print("Use --forcar somente com autorização da equipe (DUV-007).")
            return 1

    pacotes = carregar_json(CAMINHO_PACOTES)
    paises = carregar_json(CAMINHO_PAISES)

    clientes, controle = gerar_carga(pacotes, paises)

    erros = validar_carga(clientes, controle, pacotes, paises)
    if erros:
        print("Carga inválida; nada foi gravado:")
        for erro in erros:
            print("  -", erro)
        return 1

    try:
        gravar_json(CAMINHO_CONTROLE, controle, indent=2)     # 1º: controle (DC-02)
        gravar_json(CAMINHO_CLIENTES, clientes, indent=4)     # 2º: clientes
        if forcar:
            gravar_json(CAMINHO_HISTORICO, [], indent=4)      # 3º: histórico vazio
    except OSError as erro:
        print(f"Falha de gravação: {erro}")
        print("Confira os arquivos manualmente; não há recuperação automática (DUV-011).")
        return 1

    inativos = sum(1 for c in clientes if c["status"] == "inativo")
    sem_plano = sum(1 for c in clientes if c["pacote"] is None)
    print(f"Clientes gerados: {len(clientes)} ({inativos} inativos, {sem_plano} sem plano).")
    print(f"Próximo ID: {controle['proximo_id']}.")
    if forcar:
        print("Histórico de consultas esvaziado.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
