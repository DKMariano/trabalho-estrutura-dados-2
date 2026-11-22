"""
Etapa 2 — Árvore B

Passo 1: nós, inicialização e busca.

A árvore armazena pares (chave, posicao), sem armazenar
os registros completos dos clientes.
"""

import time

class NoArvoreB:
    """Representa um nó da Árvore B."""

    def __init__(self, folha=True):
        self.chaves = []
        self.posicoes = []
        self.filhos = []
        self.folha = folha

class ArvoreB:
    """Árvore B com grau mínimo configurável."""


    def __init__(self, grau_minimo=3, nome=""):
        if type(grau_minimo) is not int or grau_minimo < 2:
            raise ValueError("O grau mínimo deve ser um inteiro maior ou igual a 2.")

        self.grau_minimo = grau_minimo
        self.nome = nome
        # Como a árvore começa vazia, sua raiz é uma folha.
        self.raiz = NoArvoreB(folha=True)

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

        # Estado da árvore
        self._divisoes = 0
        self._ultima_operacao = None
        self._tempo_execucao_us = 0.0


    def _validar_chave(self, chave):
        """
        Valida o tipo e o conteúdo de uma chave.

        Aceita IDs inteiros positivos ou strings preenchidas
        e normalizadas. Rejeita booleanos e outros tipos.

        Lança ValueError quando a chave é inválida.
        """
        if type(chave) is int:
            if chave <= 0:
                raise ValueError("O ID deve ser maior que zero.")

        elif type(chave) is str:
            if not chave or chave != chave.strip().lower():
                raise ValueError("A chave textual deve estar preenchida e normalizada.")

        else:
            raise ValueError("A chave deve ser um inteiro ou uma string.")



    def _procurar(self, chave):
        """
        Procura uma chave sem modificar as métricas.

        Retorna:
            (posicao, comparacoes, nos_visitados)

        Uma chave não encontrada retorna posição None.
        Uma chave de tipo incompatível retorna
        (None, 0, 0), sem contabilizar a busca.
        """
        no = self.raiz
        comparacoes = 0
        nos_visitados = 0

        # A raiz sem chaves representa a árvore vazia.
        if not no.chaves:
            return None, 0, 0

        # Verifica a compatibilidade antes de percorrer nós.
        if type(chave) is not type(no.chaves[0]):
            return None, 0, 0

        while no is not None:
            nos_visitados += 1
            indice = 0

            # Examina as chaves em ordem crescente.
            while indice < len(no.chaves):
                comparacoes += 1
                chave_atual = no.chaves[indice]

                if chave == chave_atual:
                    return (
                        no.posicoes[indice],
                        comparacoes,
                        nos_visitados
                    )

                if chave < chave_atual:
                    break

                indice += 1

            # Não encontrou a chave em uma folha.
            if no.folha:
                return None, comparacoes, nos_visitados

            # Continua pelo filho correspondente.
            no = no.filhos[indice]

        return None, comparacoes, nos_visitados



    def buscar(self, chave):
        """
        Busca uma chave e registra sua instrumentação.

        Retorna:
            (posicao_ou_None, dados_busca)

        Entradas inválidas ou incompatíveis retornam
        None e métricas zeradas, sem contabilizar busca.
        """
        dados_zerados = {
            "comparacoes": 0,
            "nos_visitados": 0,
            "tempo_us": 0.0
        }

        # Buscar nunca deve lançar erro por chave inválida.
        try:
            self._validar_chave(chave)
        except ValueError:
            return None, dados_zerados

        # Tipos incompatíveis não geram uma busca.
        if self.raiz.chaves:
            if type(chave) is not type(self.raiz.chaves[0]):
                return None, dados_zerados

        inicio_ns = time.perf_counter_ns()

        posicao, comparacoes, nos_visitados = self._procurar(chave)

        fim_ns = time.perf_counter_ns()
        tempo_us = round((fim_ns - inicio_ns) / 1000, 2)

        dados_busca = {
            "comparacoes": comparacoes,
            "nos_visitados": nos_visitados,
            "tempo_us": tempo_us
        }

        # Somente buscas válidas atualizam a instrumentação.
        self._ultima_busca = dados_busca.copy()
        self._total_buscas += 1
        self._comparacoes_totais += comparacoes
        self._nos_visitados_totais += nos_visitados

        return posicao, dados_busca

    def contem(self, chave):
        """
        Verifica se uma chave existe na árvore.

        Retorna False para chaves inválidas ou
        incompatíveis, sem alterar métricas de busca.
        """
        try:
            self._validar_chave(chave)
        except ValueError:
            return False

        posicao, _, _ = self._procurar(chave)
        return posicao is not None

    def _estado_atual(self):
        """
        Calcula o estado atual da árvore.

        Método auxiliar para a instrumentação.
        """
        # Se a árvore estiver vazia, retorna  0, 0, 0
        if not self.raiz.chaves:
             return 0, 0, 0
        
        total_chaves = 0
        total_nos = 0
        altura = 0
        # utiliza uma pilha para percorrer os nós
        pilha = [(self.raiz, 1)]
        
        while pilha:
            # Cada elemento da pilha contém um nó e seu nível.
            # remove um elemento da pilha
            no, nivel = pilha.pop()

            # Contabiliza o nó visitado e suas chaves.
            total_nos += 1
            total_chaves += len(no.chaves)
            # Atualiza a altura com o maior nível encontrado.
            altura = max(altura, nivel)

            # acrescenta seus filhos para processamento.
            if not no.folha:
                for filho in no.filhos:
                    pilha.append((filho, nivel + 1))
        # Retorna somente após percorrer todos os nós.
        return altura, total_chaves, total_nos

    def metricas(self):
        """Retorna as métricas no contrato do DGB SIM."""
        altura, total_chaves, total_nos = self._estado_atual()

        #organiza os dados em um dicionário com quatro partes principais
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

    def _dividir_filho(self, pai, indice):
        """
        Divide um filho cheio do nó pai.

        A chave mediana e sua posição são promovidas
        ao pai. As demais chaves são distribuídas
        entre o filho original e um novo nó.
        """

        t = self.grau_minimo

        # Seleciona o filho cheio
        filho = pai.filhos[indice]

        # Cria um novo nó do mesmo tipo do filho.
        novo = NoArvoreB(folha=filho.folha)

        # A mediana está na posição t - 1.
        chave_mediana = filho.chaves[t - 1]
        posicao_mediana = filho.posicoes[t - 1]

        # O novo nó recebe as chaves à direita da mediana
        novo.chaves = filho.chaves[t:]
        novo.posicoes = filho.posicoes[t:]

        # O filho original mantém as chaves à esquerda.
        filho.chaves = filho.chaves[:t - 1]
        filho.posicoes = filho.posicoes[:t - 1]

        # Se o filho for interno, divide também seus filhos
        if not filho.folha:
            novo.filhos = filho.filhos[t:]
            filho.filhos = filho.filhos[:t]

        # Insere o novo nó à direita do filho original.
        pai.filhos.insert(indice + 1, novo)

        # Promove a mediana e sua posição para o pai
        pai.chaves.insert(indice, chave_mediana)
        pai.posicoes.insert(indice, posicao_mediana)

        # Registra uma divisão estrutural
        self._divisoes += 1

    def _inserir_nao_cheio(self, no, chave, posicao):
        """
        Insere uma chave em uma subárvore cuja raiz
        não está cheia.

        Antes de descer para um filho cheio, divide-o.
        """

        indice = len(no.chaves) - 1

        # Caso 1: o nó é uma filha
        if no.folha:

            # Procura a posição de inserção.
            while indice >= 0 and chave < no.chaves[indice]:
                indice -= 1

            #Insere a chave mantendo a ordenação
            no.chaves.insert(indice + 1, chave)
            no.posicoes.insert(indice + 1, posicao)
            return

        # Caso 2: o nó é interno.
        # Identifica o filho pelo qual devemos continuar.
        while indice >= 0 and chave < no.chaves[indice]:
            indice -= 1

        indice += 1

        if len(no.filhos[indice].chaves) == (2 * self.grau_minimo - 1):
            self._dividir_filho(no, indice)

            # Após a divisão, a mediana está no pai.
            # Decide entre o filho esquerdo e o direito.
            if chave > no.chaves[indice]:
                indice += 1

        # Continua a inserção no filho apropriado.
        self._inserir_nao_cheio(no.filhos[indice], chave, posicao)

    def inserir(self, chave, posicao):
        """
        Insere o par (chave, posicao) na Árvore B.

        Rejeita chaves duplicadas, posições inválidas
        e tipos de chave incompatíveis.
        """

        # Valida a chave utilizando o método existente
        self._validar_chave(chave)

        # A posição corresponde ao índice na lista JSON.
        if type(posicao) is not int or posicao < 0:
            raise ValueError("A posição deve ser um inteiro maior ou igual a zero.")


        # Impede misturar IDs e e-mails na mesma árvore.
        if self.raiz.chaves:
            tipo_existente = type(self.raiz.chaves[0])

            if type(chave) is not tipo_existente:
                raise ValueError("A chave possui tipo incompatível com as chaves armazenadas na árvore.")

        # Verifica duplicidade sem alterar métricas de busca.
        if self.contem(chave):
            raise ValueError(f"A chave {chave!r} já existe na Árvore B")

        inicio_ns = time.perf_counter_ns()

        limite = 2 * self.grau_minimo - 1

        # Caso especial: a raiz está cheia
        if len(self.raiz.chaves) == limite:
            raiz_antiga = self.raiz

            #Cria uma nova raiz interna,
            nova_raiz = NoArvoreB(folha=False)
            nova_raiz.filhos.append(raiz_antiga)

            # Divide a raiz antiga, promovendo a mediana.
            self._dividir_filho(nova_raiz, 0)

            # A nova raiz passa a representar a árvore.
            self.raiz = nova_raiz

        # Insere na raiz, que agora não está cheia.
        self._inserir_nao_cheio(self.raiz, chave, posicao)

        # Registra a operação concluída.
        fim_ns = time.perf_counter_ns()

        self._ultima_operacao = "insercao"
        self._tempo_execucao_us = round( (fim_ns - inicio_ns) / 1000, 2)

    def percorrer_em_ordem(self):
        """
        Retorna todos os pares (chave, posicao) em ordem
        crescente de chave.

        Percorre recursivamente os nós da Árvore B,
        incluindo as chaves dos nós internos.

        Não modifica a árvore nem suas métricas.
        """

        # Lista vazia que receberá os resultados
        pares_ordenados = []

        def percorrer_no(no):
            """Percorre um nó e seus filhos em ordem."""

            # Função auxiliar recursiva que chama a si mesma para visitar os filhos
            for indice, chave in enumerate(no.chaves):

                # Em nós internos, visita primeiro o filho à esquerda da chave atual.
                if not no.folha:
                    percorrer_no(no.filhos[indice])

                # Registra a chave junto de sua posição.
                pares_ordenados.append((chave, no.posicoes[indice]))

            # Um nó interno com N chaves possui N + 1
            # filhos. Falta visitar o último filho
            if not no.folha:
                percorrer_no(no.filhos[len(no.chaves)])

        # Uma árvore vazia não possui pares.
        if not self.raiz.chaves:
            return pares_ordenados

        percorrer_no(self.raiz)

        return pares_ordenados

    def altura(self):

        """
        Calcula a altura atual da Árvore B.

        A altura corresponde à quantidade de níveis existentes
        entre a raiz e uma folha, incluindo ambos.

        Retorna:
            int: altura da árvore.
                 0 se estiver vazia;
                 1 se possuir apenas a raiz;
                 2 ou mais se possuir outros níveis.

        Não modifica a estrutura nem as métricas da árvore.
        """

        # A raiz epresenta o primeiro nível.
        no_atual = self.raiz

        # Uma árvore sem raiz possui altura zero.
        if no_atual is None:
            return 0

        # Se a raiz não possui chaves, a árvore está vazia.
        # Nesse caso, sua altura também é zero.
        if len(no_atual.chaves) == 0:
            return 0

        # Inicialmente, contamos a raiz com nível 1.
        altura = 1

        # Em uma Árvore B válida, todas as folhas estão a mesma profundidade.
        #
        # Por isso, basta seguir o primeiro filho de cada nó interno até alcançar uma folha.
        while not no_atual.folha:
            no_atual = no_atual.filhos[0]

            #Cada descida representa um novo nível
            altura += 1

        # Ao alcançar uma folha, a quantidade de níveis percorridos corresponde à altura da árvore.
        return altura

    def total_chaves(self):
        """
        Conta a quantidade total de chaves armazenadas na Árvore B.

        Percorre recursivamente os nós da árvore e soma
        a quantidade de chaves existente em cada um deles.

        Retorna:
            int: quantidade total de chaves da árvore.
                 Retorna 0 quando a árvore está vazia.

        Não modifica a estrutura nem as métricas da árvore.
        """
        def contar(no):
            """
            Conta as chaves de um nó e de seus descendentes.

            Parâmetros:
                no: nó da Árvore B que será analisado.

            Retorna:
                int: total de chaves do nó e de sua subárvore.
            """

            # Caso base: se não existe nó, não existem chaves para contabilizar.
            if no is None:
                return 0

            # Começamos contando as chaves do nó atual.
            total = len(no.chaves)

            # Se o nó for interno, contabiliza  as chaves dos seus descendentes.
            if not no.folha:
                # Percorre todos os filhos do nó atual.
                for filho in no.filhos:

                    # A chamada recursiva retorna a quantidade de chaves armazenadas na subárvore do filho.
                    # Somamos esse valor ao total acumulado.
                    total += contar(filho)

            # Retorna o total de chaves deste nó juntamente com as de seus descendentes.
            return total

        # Inicia a contagem a partir da raiz.
        # Se a árvore estiver vazia, o resultado será zero.
        return contar(self.raiz)

    def contar_nos(self):
        """
        Conta a quantidade total de nós existentes na Árvore B.

        Percorre recursivamente a estrutura, contabilizando
        a raiz, os nós internos e as folhas.

        Retorna:
            int: quantidade total de nós da árvore.
                 Retorna 0 quando a árvore está vazia.

        Não modifica a estrutura nem as métricas da árvore.
        """

        def contar(no):
            """
            Conta o nó atual e todos os seus descendentes.

            Parâmetros:
                no: nó da Árvore B que será analisado.

            Retorna:
                int: quantidade de nós da subárvore.
            """

            # Caso base: não existe nó para contabilizar.
            if no is None:
                return 0

            #Cada nó existente contribui com uma unidade
            total = 1

            # Se o nó não for uma folha, precisamos contar também os nós presentes em seus descendentes.
            if not no.folha:

                # Percorre todos os filhos do nó atual.
                for filho in no.filhos:

                    # Soma a quantidade de nós da subárvore de cada filho ao total acumulado.
                    total += contar(filho)

            # Retorna a quantidade de nós desta subárvore.
            return total

        # Uma raiz sem chaves representa a árvore vazia.
        if self.raiz is None or len(self.raiz.chaves) == 0:
            return 0

        # Inicia a contagem a partir da raiz.
        return contar(self.raiz)

    def carregar(self, pares):

        """
        Carrega uma coleção de pares (chave, posicao) na Árvore B.

        A carga somente é permitida quando a árvore está vazia.
        Cada par é inserido utilizando o método inserir(),
        preservando as validações e divisões da estrutura.

        Parâmetros:
            pares: coleção iterável de pares (chave, posicao).

        Lança:
            ValueError: se a árvore não estiver vazia ou
                        se uma inserção for inválida.

        A carga não é atômica: caso ocorra um erro durante
        a inserção, os pares anteriores permanecem na árvore.

        Ao concluir, registra a operação "reconstrucao"
        e o tempo total de execução em microssegundos.
        """

        # A carga somente pode ocorrer em uma árvore vazia.
        # Isso evita misturar os dados existentes com uma nova coleção de chaves e posições.
        if self.raiz is not None and self.raiz.chaves:
            raise ValueError("A carga somente é permitida em uma Árvore B vazia.")

        # Inicia a medição do tempo total da carga
        inicio_ns = time.perf_counter_ns()

        # Percorre todos os pares fornecidos
        for chave, posicao in pares:

            # Reutiliza a inserção já implementada
            # Ela valida as entradas, rejeita duplicatas e divide os nós quando necessário
            self.inserir(chave, posicao)

        # Registra o instante em que a carga terminou
        fim_ns = time.perf_counter_ns()

        # Converte nanossegundos em que a carga terminou.
        tempo_total_us = round((fim_ns - inicio_ns) / 1000, 2)

        # Sobrescreve o registro da última inserção, indicando que a operação completa foi uma carga.
        self._ultima_operacao = "reconstrucao"

        # Armazena o tempo total, não apenas o tempo d aúltima inserção realizada
        self._tempo_execucao_us = tempo_total_us


    def validar(self):
        """
        Verifica os invariantes estruturais da Árvore B.

        São verificadas:
        - A quantidade mínima e máxima de chaves por nó;
        - A correspondência entre chaves e posições;
        - A validade dos tipos e valores armazenados;
        - A ordenação crescente e a ausência de duplicatas;
        - A compatibilidade dos tipos entre todos os nós;
        - Os limites definidos pelos nós ancestrais;
        - A quantidade correta de filhos;
        - A profundidade uniforme das folhas;
        - A ausência de ciclos e nós compartilhados.

        Retorna:
            list[str]: mensagens das inconsistências encontradas.
            Retorna [] quando nenhuma inconsistência é encontrada.

        O método não modifica a árvore nem suas métricas.
        Continua a análise dos demais nós sempre que for seguro.
        """

        # Armazena as mensagens de erro encontradas.
        # A validação não termina na primeira inconsistência.
        erros = []

        # Grau mínimo da Árvore B.
        # Com t = 3, cada nó admite no máximo 5 chaves.
        t = self.grau_minimo
        limite_maximo = 2 * t - 1

        # Guarda as profundidades em que encontramos folhas.
        # Todas as folhas devem estar no mesmo nível.
        profundidades_folhas = set()

        # Guarda os identificadores dos nós visitados.
        # Isso permite detectar ciclos e filhos compartilhados.
        nos_visitados = set()

        # Registra o tipo das primeiras chaves válidas.
        # Todos os nós devem utilizar o mesmo tipo de chave.
        tipo_chave_arvore = None

        def visitar(no, minimo, maximo, profundidade, eh_raiz=False):
            """
            Verifica um nó e visita recursivamente seus filhos.

            Parâmetros:
                no: nó que será analisado.
                minimo: limite inferior permitido para suas chaves.
                maximo: limite superior permitido para suas chaves.
                profundidade: nível atual, começando em 1.
                eh_raiz: indica se o nó analisado é a raiz.

            Os limites são herdados dos nós ancestrais.
            Isso garante que cada chave pertença à subárvore
            correta, não apenas que esteja ordenada no seu nó.
            """
            nonlocal tipo_chave_arvore

            # 1. VERIFICAÇÃO DA EXISTÊNCIA E DO TIPO DO NÓ

            # Antes de acessar seus atributos, verificamos se o objeto realmente representa um nó da Árvore B.
            if not isinstance(no, NoArvoreB):
                erros.append(
                    f"Nó inválido na profundidade {profundidade}."
                )
                return

            # id(no) identifica a instância do nó em memória.
            identificador = id(no)

            # Se o mesmo objeto aparecer novamente, pode existir um ciclo ou dois pais apontando para o mesmo filho.
            # Não visita novamente para evitar recursão infinita.
            if identificador in nos_visitados:
                erros.append(
                    f"Nó repetido no nível {profundidade}: "
                    "possível ciclo ou filho compartilhado."
                )
                return

            # Marca o nó como visitado antes de analisar seus filhos.
            nos_visitados.add(identificador)

            # 2. VERIFICAÇÃO DOS ATRIBUTOS DO NÓ

            # Obtém as listas e o indicador de folha.
            # Um atributo ausente ou inacessível representa uma inconsistência estrutural.
            try:
                chaves = no.chaves
                posicoes = no.posicoes
                filhos = no.filhos
                folha = no.folha

            except Exception as erro:
                erros.append(
                    f"Atributos inválidos no nível {profundidade}: "
                    f"{type(erro).__name__}: {erro}"
                )
                return

            # A implementação exige listas para armazenar chaves, posições e referências aos filhos.
            # Se alguma dessas listas estiver corrompida, não é seguro continuar percorrendo esse nó.
            if not all(
                isinstance(valor, list)
                for valor in (chaves, posicoes, filhos)
            ):
                erros.append(
                    f"Estrutura de listas inválida "
                    f"no nível {profundidade}."
                )
                return

            # O indicador folha deve ser exatamente booleano.
            # Não aceita números ou strings como substitutos.
            if type(folha) is not bool:
                erros.append(
                    f"Indicador de folha inválido "
                    f"no nível {profundidade}."
                )

            # Quantidade de chaves armazenadas no nó atual.
            quantidade = len(chaves)

            # 3. VERIFICAÇÃO DA QUANTIDADE DE CHAVES

            if eh_raiz:
                # A raiz é uma exceção à ocupação mínima.
                # Ela pode possuir menos de t - 1 chaves.
                # Uma árvore vazia possui uma raiz folha com zero chaves e nenhum filho.
                if quantidade > limite_maximo:
                    erros.append(
                        f"Raiz possui {quantidade} chaves; "
                        f"máximo permitido: {limite_maximo}."
                    )

                # Uma raiz vazia não pode ser um nó interno nem possuir descendentes.
                if quantidade == 0 and (
                    folha is not True or len(filhos) != 0
                ):
                    erros.append(
                        "Raiz vazia deve ser uma folha sem filhos."
                    )

            else:
                # Todos os demais nós precisam possuir entrem t - 1 e 2t - 1 chaves.
                # Para t = 3: mínimo = 2 e  máximo = 5
                if not t - 1 <= quantidade <= limite_maximo:
                    erros.append(
                        f"Nó no nível {profundidade} possui "
                        f"{quantidade} chaves; permitido: "
                        f"{t - 1} a {limite_maximo}."
                    )

            # 4. CORRESPONDÊNCIA ENTRE CHAVES E POSIÇÕES

            # Cada chave possui uma posição correspondente.
            if len(posicoes) != quantidade:
                erros.append(
                    f"Nó no nível {profundidade}: "
                    "quantidade de posições diferente "
                    "da quantidade de chaves."
                )

            # 5. VALIDAÇÃO DAS POSIÇÕES

            # Uma posição deve ser um inteiro não negativo.
            # Usamos type() para rejeitar True e False, que são subclasses de int em Python.
            for indice, posicao in enumerate(posicoes):
                if type(posicao) is not int or posicao < 0:
                    erros.append(
                        f"Posição inválida no nível {profundidade}, "
                        f"índice {indice}: {posicao!r}."
                    )

            # 6. VALIDAÇÃO E ORDENAÇÃO DAS CHAVES

            for indice, chave in enumerate(chaves):

                # Reutiliza o contrato de validação de chaves já implementado na classe ArvoreB.
                try:
                    self._validar_chave(chave)
                    chave_valida = True

                except (ValueError, TypeError):
                    chave_valida = False
                    erros.append(
                        f"Chave inválida no nível {profundidade}: "
                        f"{chave!r}."
                    )

                # Todas as chaves da árvore precisam possuir o mesmo tipo, inclusive em nós diferentes.
                if chave_valida:
                    if tipo_chave_arvore is None:
                        tipo_chave_arvore = type(chave)

                    elif type(chave) is not tipo_chave_arvore:
                        erros.append(
                            f"Tipo de chave incompatível "
                            f"no nível {profundidade}: "
                            f"{chave!r}."
                        )

                # A partir da segunda chave, verificamos a ordenação em relação à chave anterior.
                if indice > 0:
                    anterior = chaves[indice - 1]

                    # Tipos diferentes não podem ser ordenados de forma consistente nesta Árvore B.
                    if type(anterior) is not type(chave):
                        erros.append(
                            f"Tipos de chave incompatíveis "
                            f"no nível {profundidade}."
                        )

                    elif type(chave) in (int, str):
                        # A ordem precisa ser estritamente crescente, impedindo duplicatas.
                        if not anterior < chave:
                            erros.append(
                                f"Chaves fora de ordem ou repetidas "
                                f"no nível {profundidade}."
                            )

            # 7. VERIFICAÇÃO DOS LIMITES DA SUBÁRVORE

            # Além da ordenação dentro do nó, cada chave deve respeitar os limites dos ancestrais.

            for chave in chaves:

                # Verifica o limite inferior, quando existir.
                if minimo is not None:

                    if type(chave) is not type(minimo):
                        erros.append(
                            f"Tipo incompatível com o limite "
                            f"inferior no nível {profundidade}."
                        )

                    elif type(chave) in (int, str):
                        if not minimo < chave:
                            erros.append(
                                f"Chave {chave!r} viola o limite "
                                f"inferior no nível {profundidade}."
                            )

                # Verifica o limite superior, quando existir.
                if maximo is not None:

                    if type(chave) is not type(maximo):
                        erros.append(
                            f"Tipo incompatível com o limite "
                            f"superior no nível {profundidade}."
                        )

                    elif type(chave) in (int, str):
                        if not chave < maximo:
                            erros.append(
                                f"Chave {chave!r} viola o limite "
                                f"superior no nível {profundidade}."
                            )

            # 8. VERIFICAÇÃO DOS FILHOS E DAS FOLHAS

            if folha is True:
                # Uma folha não possui descendentes.
                # Registramos sua profundidade para verificar
                # se todas as folhas estão no mesmo nível.
                profundidades_folhas.add(profundidade)

                if filhos:
                    erros.append(
                        f"Nó folha no nível {profundidade} "
                        "possui filhos."
                    )

                # Mesmo com uma referência indevida a filhos, não os percorremos como descendentes de folha.
                return

            # Um nó interno com N chaves deve possuir N + 1 filhos, pois suas chaves definem N + 1 intervalos.
            if folha is False:
                if len(filhos) != quantidade + 1:
                    erros.append(
                        f"Nó interno no nível {profundidade} "
                        f"possui {len(filhos)} filhos; "
                        f"esperado: {quantidade + 1}."
                    )

            # Se folha não é booleano, não sabemos se o nó é folha ou interno. Mesmo assim, podemos tentar examinar os filhos existentes com segurança.

            # 9. PERCURSO RECURSIVO DOS FILHOS

            for indice, filho in enumerate(filhos):

                # Se houver filhos excedentes, registramos a inconsistência. Não inventamos limites para um intervalo que não deveria existir.
                if indice > quantidade:
                    erros.append(
                        f"Filho excedente no nível {profundidade}."
                    )
                    limite_inferior = None
                    limite_superior = None

                else:
                    # O primeiro filho herda o limite inferior  recebido do nó ancestral.
                    # Os demais recebem como limite inferior  a chave imediatamente anterior.
                    limite_inferior = (
                        minimo if indice == 0
                        else chaves[indice - 1]
                    )

                    # O último filho herda o limite superior  recebido do nó ancestral.
                    #  Os demais recebem como limite superior a chave do índice correspondente.
                    limite_superior = (
                        maximo if indice == quantidade
                        else chaves[indice]
                    )

                # Uma falha inesperada em um filho não deve impedir a análise dos seus irmãos.
                try:
                    visitar(
                        filho,
                        limite_inferior,
                        limite_superior,
                        profundidade + 1
                    )

                except Exception as erro:
                    erros.append(
                        f"Falha ao validar filho {indice} "
                        f"no nível {profundidade}: "
                        f"{type(erro).__name__}: {erro}"
                    )

        # 10. INÍCIO DA VALIDAÇÃO PELA RAIZ

        try:
            # A raiz está no nível 1 e não possui limites mínimo ou máximo definidos por ancestrais.
            visitar(
                self.raiz,
                minimo=None,
                maximo=None,
                profundidade=1,
                eh_raiz=True
            )

        except Exception as erro:
            # Proteção final para uma falha inesperada na raiz.
            # Registramos o erro em vez de propagá-lo.
            erros.append(
                "Falha durante a validação estrutural: "
                f"{type(erro).__name__}: {erro}"
            )

        # ------------------------------------------------------
        # 11. VERIFICAÇÃO DA PROFUNDIDADE DAS FOLHAS
        # ------------------------------------------------------

        # Um set contém apenas valores distintos.
        # Se todas as folhas estiverem no nível 3: {3, 3, 3} será armazenado como {3}.
        # Se houver folhas nos níveis 2 e 3: o conjunto será {2, 3}, indicando erro.
        if len(profundidades_folhas) > 1:
            erros.append(
                "As folhas estão em profundidades diferentes."
            )

        # Uma lista vazia significa que nenhuma inconsistência foi encontrada nas verificações realizadas.
        # A validação nunca corrige automaticamente os nós.
        return erros