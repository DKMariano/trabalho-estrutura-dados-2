import time
from collections import deque
from datetime import datetime
from functools import wraps


def _medir(operacao, falha_se_none=False, registrar_evento=True):
    """Decorador que instrumenta um método da TabelaHash.

    A cada chamada, registra quantas vezes a operação foi usada, se terminou
    com sucesso ou falha e quanto tempo levou (em nanossegundos).

    Falha significa que o método lançou ValueError (inserir, alterar e
    remover) ou que não encontrou o país (buscar devolve None).
    """

    def decorador(metodo):
        @wraps(metodo)
        def interno(self, *args, **kwargs):
            inicio = time.perf_counter_ns()
            sucesso = False

            try:
                resultado = metodo(self, *args, **kwargs)
                sucesso = not (falha_se_none and resultado is None)
                return resultado

            finally:
                # O finally roda também quando o método lança ValueError.
                duracao = time.perf_counter_ns() - inicio
                codigo = None

                if registrar_evento and args:
                    codigo = str(args[0]).strip().upper()

                self._registrar(operacao, sucesso, duracao, codigo)

        return interno

    return decorador


class TabelaHash:
    REGIOES = ["África", "América", "Ásia", "Europa", "Oceania"]
    TECNOLOGIAS = ["2G", "3G", "4G", "5G"]

    # Operações instrumentadas, na ordem em que aparecem no dashboard.
    OPERACOES = ["inserir", "buscar", "alterar", "remover", "listar"]

    # Quantidade de operações recentes guardadas para exibição.
    MAX_EVENTOS = 8

    def __init__(self):
        self.paises = {}
        self.zerar_metricas()

    # ------------------------------------------------------------------
    # Operações da estrutura
    # ------------------------------------------------------------------

    # normaliza o código
    @_medir("inserir")
    def inserir(self, codigo, nome, regiao, operadora, tecnologia):
        codigo:str = codigo.strip().upper()

        # validação de duas letras
        if len(codigo) != 2 or not (codigo.isalpha() and codigo.isascii()):
          raise ValueError("O código do país deve possuir exatamente 2 letras.")

        #impede que escreva um código já existente
        if codigo in self.paises:
            raise ValueError("Já existe um país cadastrado com esse código")

        self._validar_dados(nome, regiao, operadora, tecnologia)

        self.paises[codigo] = {
            "nome": nome,
            "regiao": regiao,
            "operadora": operadora,
            "tecnologia": tecnologia
        }

    # buscar um país pelo código.
    @_medir("buscar", falha_se_none=True)
    def buscar(self, codigo):
        # normaliza o código e usa .get() para consultar diretamente o dicionário
        codigo = codigo.strip().upper()

        return self.paises.get(codigo)

    # .items() fornece os pares código e dados do país. list() reúne esses pares em uma lista
    @_medir("listar", registrar_evento=False)
    def listar(self):
        return list(self.paises.items())

    # alterar os dados de um país existente, mantendo seu código.
    @_medir("alterar")
    def alterar(self, codigo, nome, regiao, operadora, tecnologia):
        codigo = codigo.strip().upper()

        #verificação impede que uma alteração cadastre acidentalmente um país inexistente.
        if codigo not in self.paises:
            raise ValueError("País não encontrado.")

        self._validar_dados(nome, regiao, operadora, tecnologia)

        self.paises[codigo] = {
            "nome": nome,
            "regiao": regiao,
            "operadora": operadora,
            "tecnologia": tecnologia
        }

    # remover um país
    @_medir("remover")
    def remover(self, codigo):
        codigo = codigo.strip().upper()

        #verificação permite informar quando o país não existe.
        if codigo not in self.paises:
            raise ValueError("País não encontrado.")

        del self.paises[codigo]

    def tam(self):
        return len(self.paises.keys())

    def _validar_dados(self, nome, regiao, operadora, tecnologia):
        if not nome.strip() or not operadora.strip():
            raise ValueError("Preencha todos os campos obrigatórios.")
        if regiao not in self.REGIOES:
            raise ValueError("Região inválida.")
        if tecnologia not in self.TECNOLOGIAS:
            raise ValueError("Tecnologia inválida.")

    # ------------------------------------------------------------------
    # Instrumentação
    # ------------------------------------------------------------------

    def zerar_metricas(self):
        """Zera os contadores, os tempos e o histórico de operações."""
        self._metricas = {
            operacao: {
                "chamadas": 0,
                "sucessos": 0,
                "falhas": 0,
                "tempo_total_ns": 0,
                "tempo_max_ns": 0
            }
            for operacao in self.OPERACOES
        }
        self._eventos = deque(maxlen=self.MAX_EVENTOS)

    def _registrar(self, operacao, sucesso, duracao_ns, codigo=None):
        """Atualiza os contadores de uma operação (chamado pelo decorador)."""
        metrica = self._metricas[operacao]

        metrica["chamadas"] += 1
        metrica["sucessos" if sucesso else "falhas"] += 1
        metrica["tempo_total_ns"] += duracao_ns
        metrica["tempo_max_ns"] = max(metrica["tempo_max_ns"], duracao_ns)

        # Operações com código entram no histórico recente (a mais nova primeiro).
        if codigo is not None:
            if operacao == "buscar":
                resultado = "Encontrado" if sucesso else "Não encontrado"
            else:
                resultado = "Sucesso" if sucesso else "Recusada"

            self._eventos.appendleft({
                "hora": datetime.now().strftime("%H:%M:%S"),
                "operacao": operacao,
                "codigo": codigo,
                "resultado": resultado,
                "sucesso": sucesso,
                "duracao_us": duracao_ns / 1000
            })

    def metricas(self):
        """Devolve um resumo das métricas para exibição (não altera os contadores)."""
        operacoes = []
        total_chamadas = 0

        for operacao in self.OPERACOES:
            metrica = self._metricas[operacao]
            chamadas = metrica["chamadas"]
            total_chamadas += chamadas

            media_us = metrica["tempo_total_ns"] / chamadas / 1000 if chamadas else 0

            operacoes.append({
                "operacao": operacao,
                "chamadas": chamadas,
                "sucessos": metrica["sucessos"],
                "falhas": metrica["falhas"],
                "tempo_medio_us": media_us,
                "tempo_max_us": metrica["tempo_max_ns"] / 1000
            })

        return {
            "operacoes": operacoes,
            "total_chamadas": total_chamadas,
            "eventos": list(self._eventos)
        }