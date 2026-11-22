"""
Testes de arquivos/persistencia_clientes.py — Guia de Implementação, seção A9.
Tudo acontece numa pasta temporária; os JSON reais não são tocados.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from arquivos import persistencia_clientes as persistencia
from testes import apoio

HASHES_ANTES = None


def setUpModule():
    global HASHES_ANTES
    HASHES_ANTES = apoio.hashes_reais()


def tearDownModule():
    assert apoio.hashes_reais() == HASHES_ANTES, "Um JSON real foi alterado pelos testes!"


class TestePersistenciaClientes(unittest.TestCase):

    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="dgb_persistencia_"))
        self.clientes = self.pasta / "clientes.json"
        self.controle = self.pasta / "controle_ids.json"

    def tearDown(self):
        apoio.apagar(self.pasta)

    def test_caminhos_padrao(self):
        self.assertEqual(persistencia.CAMINHO_CLIENTES.name, "clientes.json")
        self.assertEqual(persistencia.CAMINHO_CONTROLE.name, "controle_ids.json")
        self.assertEqual(persistencia.CAMINHO_CLIENTES.parent.name, "arquivos")

    def test_salvar_e_carregar_lista_com_none(self):
        lista = [{"id": 1, "nome": "Ana", "email": "ana@x.com"}, None, {"id": 3, "nome": "Çé", "email": "c@x.com"}]
        persistencia.salvar_clientes(lista, self.clientes)

        self.assertEqual(persistencia.carregar_clientes(self.clientes), lista)
        self.assertEqual(list(self.pasta.glob("*.tmp")), [])
        texto = self.clientes.read_text(encoding="utf-8")
        self.assertIn("null", texto)
        self.assertIn("Çé", texto)            # ensure_ascii=False
        self.assertIn('\n    {', texto)        # indent=4

    def test_clientes_que_nao_sao_lista(self):
        self.clientes.write_text('{"1001": {}}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "clientes.json não contém uma lista."):
            persistencia.carregar_clientes(self.clientes)

    def test_salvar_e_carregar_controle(self):
        controle = {"proximo_id": 4, "ids_utilizados": [1, 2, 3]}
        persistencia.salvar_controle_ids(controle, self.controle)

        self.assertEqual(persistencia.carregar_controle_ids(self.controle), controle)
        self.assertEqual(list(self.pasta.glob("*.tmp")), [])
        self.assertIn('\n  "proximo_id"', self.controle.read_text(encoding="utf-8"))  # indent=2

    def test_controle_com_formato_invalido(self):
        invalidos = (
            [],
            {"proximo_id": "5", "ids_utilizados": []},
            {"proximo_id": 5},
            {"proximo_id": 5, "ids_utilizados": [1, "2"]},
            {"proximo_id": True, "ids_utilizados": []},
        )
        for conteudo in invalidos:
            self.controle.write_text(json.dumps(conteudo), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "controle_ids.json com formato inválido."):
                persistencia.carregar_controle_ids(self.controle)

    def test_validar_controle_ids_sem_problemas(self):
        clientes = [{"id": 1}, None, {"id": 3}]
        controle = {"proximo_id": 4, "ids_utilizados": [1, 2, 3]}   # 2 = cliente excluído
        self.assertEqual(persistencia.validar_controle_ids(clientes, controle), [])

    def test_validar_controle_ids_encontra_os_tres_problemas(self):
        clientes = [{"id": 1}, {"id": 2}, {"id": 9}]
        controle = {"proximo_id": 2, "ids_utilizados": [1, 2, 2]}
        problemas = persistencia.validar_controle_ids(clientes, controle)

        self.assertEqual(len(problemas), 3)
        # Textos da Decisão 11 (cada frase cita o ID ou o valor envolvido)
        self.assertIn("ID 2 repetido em ids_utilizados.", problemas)
        self.assertIn("ID 9 do cliente não está em ids_utilizados.", problemas)
        self.assertIn("proximo_id (2) deve ser maior que o maior ID usado (2).", problemas)
        # Nada é corrigido
        self.assertEqual(controle, {"proximo_id": 2, "ids_utilizados": [1, 2, 2]})

    def test_falha_de_gravacao_preserva_o_original(self):
        persistencia.salvar_clientes([{"id": 1}], self.clientes)
        original = self.clientes.read_bytes()

        with mock.patch.object(persistencia.os, "replace", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                persistencia.salvar_clientes([{"id": 1}, {"id": 2}], self.clientes)

        self.assertEqual(self.clientes.read_bytes(), original)

    def test_le_os_arquivos_reais_sem_alterar(self):
        clientes = persistencia.carregar_clientes()
        controle = persistencia.carregar_controle_ids()
        self.assertIsInstance(clientes, list)
        self.assertGreater(len(clientes), 0)
        self.assertEqual(persistencia.validar_controle_ids(clientes, controle), [])


if __name__ == "__main__":
    unittest.main()
