"""
Testes da Árvore B (estruturas/arvore_b.py) — Guia de Implementação, seção A9.

Executar a partir da raiz do projeto:
    python -m unittest discover -s testes -t .
"""

import random
import unittest

from estruturas.arvore_b import ArvoreB, NoArvoreB

TOTAL = 1001


class TesteArvoreVazia(unittest.TestCase):

    def test_arvore_vazia(self):
        arvore = ArvoreB(3, "id")
        posicao, dados = arvore.buscar(10)
        self.assertIsNone(posicao)
        self.assertEqual(dados["comparacoes"], 0)
        self.assertEqual(arvore.altura(), 0)
        self.assertEqual(arvore.total_chaves(), 0)
        self.assertEqual(arvore.contar_nos(), 0)
        self.assertEqual(arvore.percorrer_em_ordem(), [])
        self.assertEqual(arvore.validar(), [])

    def test_grau_invalido(self):
        for grau in (1, 0, -3, 2.5, "3", True):
            with self.assertRaises(ValueError):
                ArvoreB(grau)

    def test_no_padrao_e_folha(self):
        no = NoArvoreB()
        self.assertTrue(no.folha)
        self.assertEqual((no.chaves, no.posicoes, no.filhos), ([], [], []))

    def test_metricas_iniciais(self):
        self.assertEqual(ArvoreB(3, "id").metricas(), {
            "grau": 3,
            "ultima_busca": {"comparacoes": 0, "nos_visitados": 0, "tempo_us": 0.0},
            "acumulado": {"comparacoes_totais": 0, "total_buscas": 0, "nos_visitados_totais": 0},
            "estado": {"altura": 0, "divisoes": 0, "total_chaves": 0, "nos": 0,
                       "ultima_operacao": None, "tempo_execucao_us": 0.0},
        })


class TesteInsercaoEDivisao(unittest.TestCase):

    def test_cinco_chaves_sem_divisao_e_sexta_divide(self):
        arvore = ArvoreB(3, "id")
        for posicao, chave in enumerate([10, 20, 30, 40, 50]):
            arvore.inserir(chave, posicao)

        self.assertEqual(arvore.contar_nos(), 1)
        self.assertEqual(arvore.metricas()["estado"]["divisoes"], 0)
        self.assertEqual(arvore.altura(), 1)

        arvore.inserir(60, 5)   # raiz cheia -> divisão preventiva

        estado = arvore.metricas()["estado"]
        self.assertEqual(estado["divisoes"], 1)
        self.assertEqual(arvore.altura(), 2)
        self.assertEqual(estado["ultima_operacao"], "insercao")
        # Exemplo do Guia (A5): 30 sobe; [10, 20] e [40, 50, 60]
        self.assertEqual(arvore.raiz.chaves, [30])
        self.assertEqual(arvore.raiz.filhos[0].chaves, [10, 20])
        self.assertEqual(arvore.raiz.filhos[1].chaves, [40, 50, 60])
        # As posições acompanham as chaves
        self.assertEqual(arvore.raiz.posicoes, [2])
        self.assertEqual(arvore.raiz.filhos[1].posicoes, [3, 4, 5])
        self.assertEqual(arvore.validar(), [])

    def test_duplicata_rejeitada_sem_efeito(self):
        arvore = ArvoreB(3, "id")
        for chave in range(1, 31):
            arvore.inserir(chave, chave - 1)
        antes = arvore.metricas()["estado"]

        with self.assertRaises(ValueError):
            arvore.inserir(15, 99)

        depois = arvore.metricas()["estado"]
        self.assertEqual(antes["divisoes"], depois["divisoes"])
        self.assertEqual(antes["total_chaves"], depois["total_chaves"])
        self.assertEqual(arvore.buscar(15)[0], 14)

    def test_posicao_e_tipo_invalidos(self):
        arvore = ArvoreB(3, "id")
        arvore.inserir(1, 0)
        for chave, posicao in ((2, -1), (3, 1.5), (4, "7"), (5, True), (6, None)):
            with self.assertRaises(ValueError):
                arvore.inserir(chave, posicao)
        for chave in ("texto", 2.0, None, True, (1,)):
            with self.assertRaises(ValueError):
                arvore.inserir(chave, 1)
        self.assertEqual(arvore.total_chaves(), 1)

    def test_carregar_lista_vazia(self):
        # Decisão 7: lista vazia é aceita (todos os clientes excluídos)
        arvore = ArvoreB(3, "id")
        arvore.carregar([])
        estado = arvore.metricas()["estado"]
        self.assertEqual(arvore.total_chaves(), 0)
        self.assertEqual(arvore.altura(), 0)
        self.assertEqual(estado["ultima_operacao"], "reconstrucao")
        self.assertEqual(arvore.validar(), [])
        self.assertIsNone(arvore.buscar(1)[0])

    def test_carregar_so_com_arvore_vazia(self):
        arvore = ArvoreB(3, "id")
        arvore.carregar([(1, 0), (2, 1)])
        self.assertEqual(arvore.metricas()["estado"]["ultima_operacao"], "reconstrucao")
        with self.assertRaises(ValueError):
            arvore.carregar([(3, 2)])


class TesteMilChaves(unittest.TestCase):
    """1.001 chaves em ordem crescente, em ordem aleatória e com e-mails."""

    def _conferir(self, pares):
        arvore = ArvoreB(3, "teste")
        arvore.carregar(pares)

        self.assertEqual(arvore.validar(), [])
        self.assertEqual(arvore.total_chaves(), len(pares))
        self.assertEqual(arvore.percorrer_em_ordem(), sorted(pares))
        self.assertTrue(4 <= arvore.altura() <= 6, arvore.altura())
        self.assertGreater(arvore.metricas()["estado"]["divisoes"], 0)

        for chave, posicao in pares:
            self.assertEqual(arvore.buscar(chave)[0], posicao)

        return arvore

    def test_ids_em_ordem_crescente(self):
        self._conferir([(chave, chave - 1) for chave in range(1, TOTAL + 1)])

    def test_ids_em_ordem_aleatoria(self):
        chaves = list(range(1, TOTAL + 1))
        random.Random(42).shuffle(chaves)
        self._conferir([(chave, posicao) for posicao, chave in enumerate(chaves)])

    def test_emails(self):
        emails = [f"cliente{1000 + i}@example.com" for i in range(1, TOTAL)] + ["ines@ed2.com"]
        random.Random(7).shuffle(emails)
        arvore = self._conferir([(email, posicao) for posicao, email in enumerate(emails)])

        self.assertIsNone(arvore.buscar("ninguem@example.com")[0])
        with self.assertRaises(ValueError):
            arvore.inserir(5, 2000)   # tipo diferente das chaves existentes

    def test_insercao_uma_a_uma_mantem_invariantes(self):
        arvore = ArvoreB(3, "id")
        chaves = list(range(1, 301))
        random.Random(3).shuffle(chaves)
        for posicao, chave in enumerate(chaves):
            arvore.inserir(chave, posicao)
            if posicao % 25 == 0:
                self.assertEqual(arvore.validar(), [])
        self.assertEqual(arvore.validar(), [])


class TesteBuscaEMetricas(unittest.TestCase):

    def setUp(self):
        self.arvore = ArvoreB(3, "id")
        self.arvore.carregar([(chave, chave - 1) for chave in range(1, TOTAL + 1)])

    def test_busca_existente_e_inexistente(self):
        posicao, dados = self.arvore.buscar(1001)
        self.assertEqual(posicao, 1000)
        self.assertGreater(dados["comparacoes"], 0)
        self.assertEqual(dados["nos_visitados"], self.arvore.altura())  # chave em folha
        self.assertGreaterEqual(dados["tempo_us"], 0)

        # Chave válida ausente: a busca desce até uma folha
        posicao, dados = self.arvore.buscar(5000)
        self.assertIsNone(posicao)
        self.assertEqual(dados["nos_visitados"], self.arvore.altura())

        # IDs menores ou iguais a 0 são chaves inválidas na árvore de ID:
        # não encontram e não contam como busca (mesma regra da Decisão 3)
        buscas = self.arvore.metricas()["acumulado"]["total_buscas"]
        for invalida in (0, -1):
            posicao, dados = self.arvore.buscar(invalida)
            self.assertIsNone(posicao)
            self.assertEqual(dados["nos_visitados"], 0)
        self.assertEqual(self.arvore.metricas()["acumulado"]["total_buscas"], buscas)

        # Tipo incompatível: não encontra e não lança erro
        self.assertIsNone(self.arvore.buscar("1001")[0])

    def test_acumuladas_e_contem(self):
        comparacoes = 0
        nos = 0
        for chave in (1, 500, 999999):
            _, dados = self.arvore.buscar(chave)
            comparacoes += dados["comparacoes"]
            nos += dados["nos_visitados"]

        metricas = self.arvore.metricas()
        self.assertEqual(metricas["acumulado"]["total_buscas"], 3)
        self.assertEqual(metricas["acumulado"]["comparacoes_totais"], comparacoes)
        self.assertEqual(metricas["acumulado"]["nos_visitados_totais"], nos)

        self.assertTrue(self.arvore.contem(500))
        self.assertFalse(self.arvore.contem(999999))
        self.assertEqual(self.arvore.metricas()["acumulado"], metricas["acumulado"])
        self.assertEqual(self.arvore.metricas()["ultima_busca"], metricas["ultima_busca"])

    def test_comparacoes_seguem_busca_linear(self):
        # Busca na raiz: a contagem de comparações é a posição da chave + 1.
        raiz = self.arvore.raiz
        for indice, chave in enumerate(raiz.chaves):
            _, dados = self.arvore.buscar(chave)
            self.assertEqual(dados["comparacoes"], indice + 1)
            self.assertEqual(dados["nos_visitados"], 1)

    def test_estado(self):
        estado = self.arvore.metricas()["estado"]
        self.assertEqual(estado["total_chaves"], TOTAL)
        self.assertEqual(estado["altura"], self.arvore.altura())
        self.assertEqual(estado["nos"], self.arvore.contar_nos())
        self.assertEqual(estado["ultima_operacao"], "reconstrucao")
        self.assertGreater(estado["tempo_execucao_us"], 0)

    def test_validar_detecta_problemas(self):
        folha = self.arvore.raiz
        while not folha.folha:
            folha = folha.filhos[0]
        folha.chaves[0], folha.chaves[1] = folha.chaves[1], folha.chaves[0]
        self.assertTrue(self.arvore.validar())

    def test_validar_detecta_posicao_perdida(self):
        self.arvore.raiz.posicoes.pop()
        self.assertTrue(self.arvore.validar())


if __name__ == "__main__":
    unittest.main()
