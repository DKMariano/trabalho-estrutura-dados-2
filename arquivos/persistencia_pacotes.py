#permite trabalhar com arquivos JSON
import json

#permite localizar o arquivo independentemente da pasta em que o terminal foi aberto.
from pathlib import Path

#faz a constante CAMINHO_PACOTES apontar para arquivos/pacotes.json
CAMINHO_PACOTES = Path(__file__).resolve().parent / "pacotes.json"





def carregar_pacotes():
    """
    Carrega os pacotes cadastrados no arquivo JSON.
    """

    #lê o arquivo 
    with CAMINHO_PACOTES.open("r", encoding="utf-8") as arquivo:
        pacotes = json.load(arquivo)

        return pacotes
