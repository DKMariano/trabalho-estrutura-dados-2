# Disponibiliza as funções do Python que leem e escrevem JSON.
import json

# importa Path, que permite representar caminhos de arquivos e pastas.
from pathlib import Path

#Importa a classe TabelaHash criada pela equipe
from estruturas.tabela_hash import TabelaHash

# o resultado aponta para dgb_sim/arquivos/paises.json
CAMINHO_PAISES = Path(__file__).resolve().parent / "paises.json"


def carregar_paises():
    """Carrega os países do JSON em uma nova TabelaHash."""

    # A abertura e a leitura do arquivo
    with CAMINHO_PAISES.open("r", encoding="utf-8") as arquivo:
        # O texto JSON é convertido em objetos Python.
        dados = json.load(arquivo)

        # Cria uma nova instância da classe TabelaHash
        tabela = TabelaHash()


        for codigo, pais in dados.items():
            tabela.inserir(
                codigo,
                pais["nome"],
                pais["regiao"],
                pais["operadora"],
                pais["tecnologia"]
            )

        # A devolução da tabela preenchida
        return tabela

# recebe a instância de TabelaHash no parâmetro tabela
def salvar_paises(tabela):
    """Salva os países da TabelaHash no arquivo JSON."""

    # abre o JSON com "w", substituindo o conteúdo anterior;
    with CAMINHO_PAISES.open("w", encoding="utf-8") as arquivo:
        # converte os dados Python para o formato JSON e escreve no arquivo aberto.
        json.dump(
            # O que salvar: o dicionário com todos os países armazenados na tabela
            tabela.paises,
            # Onde salvar: no arquivo paises.json, que foi aberto pelo with
            arquivo,
            # Como escrever os acentos: mantém palavras legíveis, como "América", em vez de usar códigos como "Am\u00e9rica"
            ensure_ascii=False,
            # Como organizar o texto: usa quatro espaços por nível, deixando o JSON organizado
            indent=4
        )
