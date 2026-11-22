"""
Funções de apoio aos testes (não é um arquivo de testes).

Os testes NUNCA alteram os JSON reais: trabalham com cópias numa pasta
temporária. As funções abaixo ajudam a copiar os arquivos e a conferir,
ao final, que os originais continuam idênticos (mesmo hash SHA-256).
"""

import hashlib
import shutil
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ARQUIVOS = RAIZ / "arquivos"
ARQUIVOS_REAIS = ("clientes.json", "controle_ids.json", "historico.json", "paises.json", "pacotes.json")


def hashes_reais():
    """SHA-256 dos JSON reais do projeto."""
    return {
        nome: hashlib.sha256((PASTA_ARQUIVOS / nome).read_bytes()).hexdigest()
        for nome in ARQUIVOS_REAIS
    }


def copiar_para_temporario():
    """Copia clientes.json e controle_ids.json para uma pasta temporária nova."""
    pasta = Path(tempfile.mkdtemp(prefix="dgb_teste_"))
    clientes = pasta / "clientes.json"
    controle = pasta / "controle_ids.json"
    shutil.copyfile(PASTA_ARQUIVOS / "clientes.json", clientes)
    shutil.copyfile(PASTA_ARQUIVOS / "controle_ids.json", controle)
    return pasta, clientes, controle


def apagar(pasta):
    shutil.rmtree(pasta, ignore_errors=True)


def inicializar(backend, caminho_clientes=None, caminho_controle=None):
    """
    Chama backend.inicializar() e informa se os dados ficaram disponíveis.

    O contrato do Guia (B3) não define valor de retorno para inicializar():
    a disponibilidade é lida no aviso "indisponível" do próprio backend.
    """
    backend.inicializar(caminho_clientes, caminho_controle)
    return backend._erro_indisponivel is None
