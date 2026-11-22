"""Testes da persistência em arquivos temporários da Etapa 2."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arquivos.persistencia_clientes import (
    carregar_clientes,
    carregar_controle_ids,
    salvar_clientes,
    salvar_controle_ids,
    validar_controle_ids
)


class TestePersistenciaClientes(unittest.TestCase):
    """Testa leitura, gravação segura e detecção de inconsistências."""

    def test_salvar_e_carregar_clientes_preserva_none(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "clientes.json"
            clientes = [{"id": 1001}, None, {"id": 1003}]

            # O caminho temporário garante que os JSON reais do projeto
            # não sejam alterados durante os testes automatizados.
            salvar_clientes(clientes, caminho)

            # Além do conteúdo, o teste confirma que o marcador None continua
            # na posição 1 e que não restou arquivo temporário.
            self.assertEqual(clientes, carregar_clientes(caminho))
            self.assertFalse((Path(pasta) / "clientes.json.tmp").exists())

    def test_carregar_clientes_rejeita_conteudo_que_nao_e_lista(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "clientes.json"
            caminho.write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "clientes.json não contém uma lista."
            ):
                carregar_clientes(caminho)

    def test_salvar_e_carregar_controle(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "controle_ids.json"
            controle = {
                "proximo_id": 1004,
                "ids_utilizados": [1001, 1002, 1003]
            }

            salvar_controle_ids(controle, caminho)

            self.assertEqual(controle, carregar_controle_ids(caminho))
            self.assertFalse((Path(pasta) / "controle_ids.json.tmp").exists())

    def test_carregar_controle_rejeita_quatro_formatos_invalidos(self):
        # Cada caso representa uma quebra distinta do contrato:
        # objeto incorreto, campo ausente, contador textual e histórico textual.
        controles_invalidos = [
            [],
            {"proximo_id": 1002},
            {"proximo_id": "1002", "ids_utilizados": [1001]},
            {"proximo_id": 1002, "ids_utilizados": "1001"}
        ]

        for numero, controle in enumerate(controles_invalidos):
            with self.subTest(controle=controle):
                with tempfile.TemporaryDirectory() as pasta:
                    caminho = Path(pasta) / f"controle_{numero}.json"
                    caminho.write_text(
                        json.dumps(controle),
                        encoding="utf-8"
                    )

                    with self.assertRaisesRegex(
                        ValueError,
                        "controle_ids.json com formato inválido."
                    ):
                        carregar_controle_ids(caminho)

    def test_validar_controle_correto(self):
        clientes = [{"id": 1001}, None, {"id": 1003}]
        controle = {
            "proximo_id": 1004,
            "ids_utilizados": [1001, 1002, 1003]
        }

        self.assertEqual([], validar_controle_ids(clientes, controle))

    def test_validar_detecta_os_tres_tipos_de_problema(self):
        clientes = [{"id": 1001}, {"id": 1002}]
        controle = {
            "proximo_id": 1001,
            "ids_utilizados": [1001, 1001]
        }

        # A função deve relatar todos os problemas na mesma execução, sem
        # interromper na primeira inconsistência encontrada.
        problemas = validar_controle_ids(clientes, controle)

        self.assertIn(
            "ID 1002 do cliente não está em ids_utilizados.",
            problemas
        )
        self.assertIn(
            "ID 1001 repetido em ids_utilizados.",
            problemas
        )
        self.assertIn(
            "proximo_id (1001) deve ser maior que o maior ID usado (1001).",
            problemas
        )

    def test_falha_em_replace_preserva_original_e_remove_temporario(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "clientes.json"
            original = [{"id": 1001}]
            caminho.write_text(
                json.dumps(original, ensure_ascii=False),
                encoding="utf-8"
            )

            # Simula falha exatamente na substituição final. Isso comprova
            # que o arquivo original permanece válido e o .tmp é removido.
            with patch(
                "arquivos.persistencia_clientes.os.replace",
                side_effect=OSError("falha simulada")
            ):
                with self.assertRaises(OSError):
                    salvar_clientes([{"id": 1002}], caminho)

            # Como os.replace falhou, a versão anterior continua legível.
            self.assertEqual(original, carregar_clientes(caminho))
            self.assertFalse((Path(pasta) / "clientes.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()