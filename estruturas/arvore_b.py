""" A Árvore B é usada como índice de chave para posição persistida no DGB SIM """

""" ========== IMPORTANDO MÓDULOS E/OU BIBLIOTECAS ========== """
# Importa o módulo usado para medir o tempo de execução das operações
import time
""" ========== =================================== ========== """

""" ======================== CLASSES ======================== """
""" Classe que representa um nó da Árvore B """
class NoArvoreB:
    # Método de inicialização para quando um objeto da classe é criado
    def __init__(self, folha = True): # "self" é o próprio objeto
        self.chaves = []
        self.posicoes = []
        self.filhos = []
        self.folha = folha

""" Classe que representa uma Árvore B com grau mínimo configurável """
class ArvoreB:
    # Método de inicialização para quando um objeto da classe é criado
    def __init__(self, grau_minimo = 3, nome = ""):
        # Verifica se grau mínimo da árvore foi devidamente informado
        if type(grau_minimo) is not int or grau_minimo < 2:
            raise ValueError("O grau mínimo deve ser um inteiro maior ou igual a 2")

        self.grau_minimo = grau_minimo
        self.nome = nome
        # Como Árvore B começa vazia aqui, a raiz é a folha
        self.raiz = NoArvoreB(folha = True)
        # Métricas da última busca
        self._ultima_busca = {
            "comparacoes": 0,
            "nos_visitados": 0,
            "tempo_us": 0.0
        }
        # Métricas acumuladas
        self._comparacoes_totais = 0
        self._total_buscas = 0
        self._nos_visitados_totais = 0
        # Estado da Árvore B
        self._divisoes = 0
        self._ultima_operacao = None
        self._tempo_execucao_us = 0.0

    # Método para validação da chave (inteiro ou string)
    def _validar_chave(self, chave):
        if type(chave) is int:
            if chave <= 0:
                raise ValueError("O ID deve ser maior que zero.")
        elif type(chave) is str:
            if not chave or chave != chave.strip().lower():
                raise ValueError("A chave textual deve estar preenchida e normalizada.")
        else:
            raise TypeError("A chave deve ser um inteiro ou uma string.")

    # Método para procurar uma chave sem modificar as métricas
    def _procurar(self, chave):
        """
        Retorna:
            (posicao, comparacoes, nos_visitados)

        Se a chave não existir, posicao será None.
        """

        # Inicia a busca pela raiz da árvore.
        no = self.raiz
        comparacoes = 0
        nos_visitados = 0

        # Enquanto existir um nó a examinar
        while no is not None:
            # Uma raiz vazia representa uma árvore vazia.
            if no is self.raiz and not no.chaves:
                return None, comparacoes, nos_visitados

            nos_visitados += 1
            indice = 0

            # Percorre as chaves do nó em ordem crescente.
            while indice < len(no.chaves):
                comparacoes += 1
                chave_atual = no.chaves[indice]

                # Tipos incompatíveis não correspondem à chave.
                if type(chave) is not type(chave_atual):
                    raise TypeError(
                        "A chave pesquisada possui tipo incompatível "
                        "com as chaves armazenadas na árvore."
                    )
                # Retorna a posição encontrada e as contagens da busca.
                if chave == chave_atual:
                    return (no.posicoes[indice], comparacoes, nos_visitados)

                # Se a chave procurada for menor que a chave examinada,
                if chave < chave_atual:
                    # Interrompe a busca dentro daquele nó, pois as chaves estão ordenadas
                    break

                indice += 1

            # Se o nó for uma folha e a chave não tiver sido encontrada, retorna None
            if no.folha:
                return None, comparacoes, nos_visitados

            # Caso seja um nó interno, continua pelo filho correspondente
            no = no.filhos[indice]

        # Retorna None e as contagens se a busca terminar sem encontrar a chave.
        return None, comparacoes, nos_visitados

    # Método para buscar uma chave e registrar a instrumentação
    def buscar(self, chave):
        """
        Retorna:
            (
                posicao_ou_None,
                {
                    "comparacoes": int,
                    "nos_visitados": int,
                    "tempo_us": float
                }
            )
        """

        self._validar_chave(chave)

        # Registra o instante inicial
        inicio_ns = time.perf_counter_ns()

        # Utiliza _procurar() para realizar a busca, mas acrescenta a instrumentação
        posicao, comparacoes, nos_visitados = self._procurar(chave)

        # Registra o instante final da busca.
        fim_ns = time.perf_counter_ns()

        # Calcula o tempo gasto
        # A divisão por 1000 converte nanossegundos em microssegundos.
        tempo_us = round((fim_ns - inicio_ns) / 1000, 2)    

        # Organiza as métricas da busca em um dicionário. 
        dados_busca = {
            "comparacoes": comparacoes,
            "nos_visitados": nos_visitados,
            "tempo_us": tempo_us
        }   

        # Armazena uma cópia das métricas da busca mais recente.
        self._ultima_busca = dados_busca.copy()

        # Atualiza as métricas da última busca e os contadores acumulados
        self._total_buscas += 1
        self._comparacoes_totais += comparacoes
        self._nos_visitados_totais += nos_visitados

        # Retorna a posição (ou None) e o dicionário de métricas.
        return posicao, dados_busca

    # Método para verificar existência de uma chave
    def contem(self, chave):
        """
        Não altera nenhuma métrica de busca.
        """

        self._validar_chave(chave)

        posicao, _, _ = self._procurar(chave)
        return posicao is not None

    # Método para calcular o estado atual da Árvore B
    def _estado_atual(self):
        """
        Método auxiliar para a instrumentação.
        """

        # Se a árvore estiver vazia, retorna  0, 0, 0
        if not self.raiz.chaves:
             return 0, 0, 0
        
        total_chaves = 0
        total_nos = 0
        altura = 0

        # Utiliza uma pilha para percorrer os nós
        pilha = [(self.raiz, 1)]
        
        while pilha:
            # Cada elemento da pilha contém um nó e seu nível.
            # Remove um elemento da pilha
            no, nivel = pilha.pop()

            # Contabiliza o nó visitado e suas chaves.
            total_nos += 1
            total_chaves += len(no.chaves)
            # Atualiza a altura com o maior nível encontrado.
            altura = max(altura, nivel)

            # Acrescenta seus filhos para processamento.
            if not no.folha:
                for filho in no.filhos:
                    pilha.append((filho, nivel + 1))

        # Retorna somente após percorrer todos os nós.
        return altura, total_chaves, total_nos

    # Método para retornar as métricas no contrato do DGB SIM
    def metricas(self):
        altura, total_chaves, total_nos = self._estado_atual()

        # Organiza os dados em um dicionário com quatro partes principais
        return {
            "grau": self.grau_minimo,
            "ultima_busca": self._ultima_busca.copy(),
            "acumulado": {
                "comparacoes_totais": self._comparacoes_totais,
                "total_buscas": self._total_buscas,
                "nos_visitados_totais": (
                    self._nos_visitados_totais
                )
            },
            "estado": {
                "altura": altura,
                "divisoes": self._divisoes,
                "total_chaves": total_chaves,
                "nos": total_nos,
                "ultima_operacao": self._ultima_operacao,
                "tempo_execucao_us": self._tempo_execucao_us
            }
        }

