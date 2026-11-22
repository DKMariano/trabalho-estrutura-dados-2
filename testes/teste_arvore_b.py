"""Testes unitários da Árvore B usada como índice no DGB SIM."""

import random
import unittest

from estruturas.arvore_b import ArvoreB


class TesteArvoreB(unittest.TestCase):
    """Verifica o contrato acadêmico da Árvore B com grau mínimo 3."""

    def test_arvore_vazia(self):
        arvore = ArvoreB(3, "id")
        posicao, _ = arvore.buscar(1001)

        self.assertIsNone(posicao)
        self.assertEqual(0, arvore.altura())
        self.assertEqual([], arvore.validar())

    def test_cinco_chaves_sem_divisao_e_sexta_com_divisao(self):
        arvore = ArvoreB(3, "id")

        # Com t = 3, um nó comporta no máximo cinco chaves.
        for chave in range(1, 6):
            arvore.inserir(chave, chave - 1)

        self.assertEqual(1, arvore.contar_nos())
        self.assertEqual(0, arvore.metricas()["estado"]["divisoes"])

        # A sexta chave força a divisão da raiz e cria o segundo nível.
        arvore.inserir(6, 5)

        self.assertEqual(1, arvore.metricas()["estado"]["divisoes"])
        self.assertEqual(2, arvore.altura())
        self.assertEqual([], arvore.validar())

    def test_1001_ids_crescentes(self):
        arvore = ArvoreB(3, "id")
        pares = [(chave, chave - 1) for chave in range(1, 1002)]

        # A carga crescente força divisões em um padrão previsível e permite
        # verificar se o balanceamento continua válido no caso sequencial.
        # A ordem aleatória exercita divisões em ramos diferentes da árvore.
        # Chaves textuais comprovam que o mesmo contrato atende ao índice de
        # e-mail sem misturar tipos dentro de uma única árvore.
        arvore.carregar(pares)

        self._verificar_carga(arvore, pares)

    def test_1001_ids_aleatorios(self):
        arvore = ArvoreB(3, "id")
        pares = [(chave, chave - 1) for chave in range(1, 1002)]
        # Semente fixa mantém o teste reproduzível sem limitar a árvore
        # ao caso favorável de inserção já ordenada.
        random.Random(2026).shuffle(pares)

        arvore.carregar(pares)

        self._verificar_carga(arvore, pares)

    def test_1001_emails(self):
        arvore = ArvoreB(3, "email")
        pares = [
            (f"cliente{numero:04d}@example.com", numero)
            for numero in range(1, 1002)
        ]

        arvore.carregar(pares)

        self._verificar_carga(arvore, pares)

    def test_busca_existente_e_inexistente(self):
        arvore = ArvoreB(3, "id")
        arvore.carregar([(10, 0), (20, 1), (30, 2)])

        # A posição retornada é o índice do registro persistido, não o próprio
        # cadastro completo do cliente.
        self.assertEqual(1, arvore.buscar(20)[0])
        self.assertIsNone(arvore.buscar(99)[0])

    def test_duplicidade_nao_altera_a_arvore(self):
        arvore = ArvoreB(3, "id")
        arvore.carregar([(10, 0), (20, 1), (30, 2)])
        metricas_antes = arvore.metricas()

        # A duplicidade deve ser recusada antes de qualquer divisão ou
        # alteração da quantidade de chaves.
        with self.assertRaises(ValueError):
            arvore.inserir(20, 99)

        metricas_depois = arvore.metricas()
        self.assertEqual(
            metricas_antes["estado"]["total_chaves"],
            metricas_depois["estado"]["total_chaves"]
        )
        self.assertEqual(
            metricas_antes["estado"]["divisoes"],
            metricas_depois["estado"]["divisoes"]
        )

    def test_tres_buscas_e_contem_sem_medir(self):
        arvore = ArvoreB(3, "id")
        arvore.carregar([(10, 0), (20, 1), (30, 2)])

        arvore.buscar(10)
        arvore.buscar(20)
        arvore.buscar(99)

        self.assertEqual(3, arvore.metricas()["acumulado"]["total_buscas"])
        # contem é usado em verificações internas e não deve contaminar as
        # métricas acadêmicas reservadas às buscas demonstradas.
        self.assertTrue(arvore.contem(20))
        self.assertEqual(3, arvore.metricas()["acumulado"]["total_buscas"])

    def test_bool_e_tipo_incompativel_sao_rejeitados(self):
        arvore = ArvoreB(3, "id")

        with self.assertRaises(ValueError):
            arvore.inserir(True, 0)

        arvore.inserir(1, 0)

        with self.assertRaises(ValueError):
            arvore.inserir("email@example.com", 1)

    def test_carregar_vazio_e_rejeitar_arvore_nao_vazia(self):
        arvore_vazia = ArvoreB(3, "id")
        arvore_vazia.carregar([])
        self.assertEqual(0, arvore_vazia.total_chaves())

        arvore = ArvoreB(3, "id")
        arvore.inserir(1, 0)

        with self.assertRaises(ValueError):
            arvore.carregar([(2, 1)])

    def test_metricas_iniciais(self):
        metricas = ArvoreB(3, "id").metricas()

        self.assertEqual(3, metricas["grau"])
        self.assertEqual(0, metricas["acumulado"]["total_buscas"])
        self.assertEqual(0, metricas["estado"]["altura"])
        self.assertEqual(0, metricas["estado"]["divisoes"])
        self.assertIsNone(metricas["estado"]["ultima_operacao"])

    def _verificar_carga(self, arvore, pares):
        """Confere invariantes, percurso e altura de uma carga grande."""
        # A ordem de inserção pode variar, mas o percurso da Árvore B precisa
        # devolver as chaves em ordem crescente e associadas às posições certas.
        percurso_esperado = sorted(pares)

        self.assertEqual([], arvore.validar())
        self.assertEqual(percurso_esperado, arvore.percorrer_em_ordem())
        self.assertGreaterEqual(arvore.altura(), 4)
        self.assertLessEqual(arvore.altura(), 6)


if __name__ == "__main__":
    unittest.main()