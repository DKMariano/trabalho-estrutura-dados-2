"""
Etapa 2 — Persistência de clientes

Responsável somente pela leitura e gravação dos arquivos JSON.
Este módulo não conhece Flask, regras de negócio ou Árvores B.
"""

import json
import os
from pathlib import Path


# Caminhos padrão dos arquivos utilizados pelo backend de clientes.
# O uso de __file__ evita depender da pasta em que o comando Python foi executado.
_PASTA_ARQUIVOS = Path(__file__).resolve().parent
CAMINHO_CLIENTES = _PASTA_ARQUIVOS / "clientes.json"
CAMINHO_CONTROLE = _PASTA_ARQUIVOS / "controle_ids.json"


def carregar_clientes(caminho=CAMINHO_CLIENTES):
    """
    Carrega a lista persistida de clientes.

    Os valores null do JSON são convertidos em None pelo módulo json
    e permanecem nas mesmas posições da lista.
    """
    # Path aceita tanto strings quanto objetos Path, facilitando o uso dos caminhos reais e também de pastas temporárias nos testes.
    # O módulo json converte automaticamente null em None. Nenhuma posição é removida durante a leitura, preservando os índices das Árvores B.
    with Path(caminho).open("r", encoding="utf-8") as arquivo:
        clientes = json.load(arquivo)

    # O backend depende de posições estáveis. Por isso, o arquivo deve representar uma lista, e não um dicionário indexado por ID.
    if type(clientes) is not list:
        raise ValueError("clientes.json não contém uma lista.")

    # A lista é devolvida como foi persistida. 
    # Regras de cliente e construção dos índices pertencem a dados_site/dados_etapa02.py.
    return clientes


def salvar_clientes(clientes, caminho=CAMINHO_CLIENTES):
    """
    Grava a lista de clientes com indentação de quatro espaços.

    A função apenas persiste os dados recebidos. As validações dos
    clientes pertencem ao backend de clientes.
    """
    # A função não valida regras de cliente. A responsabilidade aqui é somente persistir exatamente o estado preparado pelo backend.
    _gravar_json(
        dados=clientes,
        caminho=caminho,
        indentacao=4
    )


def carregar_controle_ids(caminho=CAMINHO_CONTROLE):
    """
    Carrega o contador sequencial e o histórico de IDs utilizados.

    Lança ValueError quando o JSON não segue o formato definido para
    proximo_id e ids_utilizados.
    """
    # O controle é separado de clientes.json porque também registra IDs de clientes já excluídos, impedindo que identificadores sejam reutilizados.
    with Path(caminho).open("r", encoding="utf-8") as arquivo:
        controle = json.load(arquivo)

    # A validação estrutural impede que o backend receba um contador sem histórico ou com tipos incompatíveis com os IDs dos clientes.
    if not _formato_controle_valido(controle):
        raise ValueError("controle_ids.json com formato inválido.")

    return controle


def salvar_controle_ids(controle, caminho=CAMINHO_CONTROLE):
    """
    Grava o controle de IDs com indentação de dois espaços.

    A função apenas persiste os dados recebidos. A validação de
    coerência é feita separadamente por validar_controle_ids.
    """
    # A coerência com clientes.json é verificada separadamente. 
    # Assim, salvar_controle_ids permanece uma operação simples de persistência.
    _gravar_json(
        dados=controle,
        caminho=caminho,
        indentacao=2
    )


def validar_controle_ids(clientes, controle):
    """
    Detecta problemas de coerência no controle de IDs.

    Retorna uma lista de mensagens. A função nunca corrige os dados.
    Registros None são ignorados, e IDs no histórico sem cliente são
    aceitos porque podem pertencer a clientes excluídos.
    """
    problemas = []

    # A inicialização chama esta função depois das funções de carga.
    # Mesmo assim, tratar formatos inválidos evita correções silenciosas.
    if type(clientes) is not list:
        return ["clientes.json não contém uma lista."]

    if not _formato_controle_valido(controle):
        return ["controle_ids.json com formato inválido."]

    ids_utilizados = controle["ids_utilizados"]
    proximo_id = controle["proximo_id"]

    # A validação só reúne mensagens. Nenhum contador, histórico ou registro é alterado, pois correção automática está fora do contrato da Etapa 2.

    # Dois conjuntos permitem detectar repetição em uma única passagem, sem modificar a ordem ou o conteúdo da lista persistida.
    ids_repetidos = set()
    ids_encontrados = set()

    for cliente_id in ids_utilizados:
        if cliente_id in ids_encontrados:
            ids_repetidos.add(cliente_id)
        else:
            ids_encontrados.add(cliente_id)

    # Uma mensagem é produzida para cada ID repetido, conforme o contrato da auditoria de integração.
    for cliente_id in sorted(ids_repetidos):
        problemas.append(
            f"ID {cliente_id} repetido em ids_utilizados."
        )

    for cliente in clientes:
        # None representa uma exclusão física. 
        # A posição continua ocupada logicamente para não deslocar registros apontados pelas Árvores B.
        if cliente is None:
            continue

        cliente_id = cliente.get("id")

        if cliente_id not in ids_encontrados:
            problemas.append(
                f"ID {cliente_id} do cliente não está em ids_utilizados."
            )

    maior_id_usado = max(ids_utilizados, default=0)

    if proximo_id <= maior_id_usado:
        problemas.append(
            f"proximo_id ({proximo_id}) deve ser maior que o maior "
            f"ID usado ({maior_id_usado})."
        )

    return problemas


def _formato_controle_valido(controle):
    """
    Confere o formato estrutural do controle de IDs.

    O formato só é válido se:
    - o conteúdo for um dicionário com exatamente as chaves proximo_id
      e ids_utilizados (chaves extras são recusadas);
    - proximo_id for um inteiro (não bool) maior que 0;
    - ids_utilizados for uma lista de inteiros (não bool) maiores que 0.
    """
    # type(...) é usado intencionalmente para rejeitar subclasses inesperadas e, no caso dos inteiros, impedir que bool seja aceito como ID.
    if type(controle) is not dict:
        return False

    if set(controle) != {"proximo_id", "ids_utilizados"}:
        return False

    proximo_id = controle["proximo_id"]
    ids_utilizados = controle["ids_utilizados"]

    if type(proximo_id) is not int or proximo_id <= 0:
        return False

    if type(ids_utilizados) is not list:
        return False

    for cliente_id in ids_utilizados:
        if type(cliente_id) is not int or cliente_id <= 0:
            return False

    return True


def _gravar_json(dados, caminho, indentacao):
    """
    Grava em arquivo temporário e substitui o arquivo original.

    O temporário fica na mesma pasta do destino. Depois da escrita,
    flush e fsync garantem o envio ao disco antes de os.replace.
    Em caso de erro (OSError ou dado que não pode ser convertido em JSON),
    o temporário é removido quando possível e o erro original é relançado,
    sem nova tentativa ou restauração (Decisão 8).
    """
    caminho = Path(caminho)

    # A pasta é criada apenas quando necessário. Nos testes, isso facilita usar diretórios temporários sem preparar previamente toda a estrutura.
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")

    try:
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(
                dados,
                arquivo,
                indent=indentacao,
                ensure_ascii=False
            )
            # A quebra final mantém os JSON legíveis em editores e no Git.
            arquivo.write("\n")

            # flush transfere o buffer do Python ao sistema operacional; 
            # fsync solicita que o conteúdo seja efetivamente sincronizado em disco.
            arquivo.flush()
            os.fsync(arquivo.fileno())

        # A substituição ocorre somente depois que o conteúdo completo foi escrito e sincronizado. O arquivo original não fica parcial.
        os.replace(temporario, caminho)

    except Exception:
        # Qualquer falha (disco, permissão ou dado não serializável) remove somente o temporário criado nesta tentativa. 
        # O arquivo original não é modificado, pois os.replace não chegou a ocorrer.
        try:
            temporario.unlink(missing_ok=True)
        except OSError:
            pass

        raise