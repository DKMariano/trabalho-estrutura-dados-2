"""
Testes do backend de clientes (dados_site/dados_etapa02.py) — Guia B10.

Cada teste copia clientes.json e controle_ids.json para uma pasta temporária
e chama inicializar(caminho_clientes, caminho_controle). No final, volta a
chamar inicializar() sem argumentos. Os JSON reais nunca são alterados.
"""

import json
import unittest
from unittest import mock

from dados_site import dados_etapa02 as backend
from dados_site.dados_etapa02 import ErroIndices
from testes import apoio

HASHES_ANTES = None


def setUpModule():
    global HASHES_ANTES
    HASHES_ANTES = apoio.hashes_reais()


def tearDownModule():
    backend.inicializar()
    assert apoio.hashes_reais() == HASHES_ANTES, "Um JSON real foi alterado pelos testes!"


class BaseClientes(unittest.TestCase):

    def setUp(self):
        self.pasta, self.arq_clientes, self.arq_controle = apoio.copiar_para_temporario()
        self.assertTrue(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))

    def tearDown(self):
        backend.inicializar()
        apoio.apagar(self.pasta)

    def ler(self, caminho):
        return json.loads(caminho.read_text(encoding="utf-8"))


class TesteCargaEBusca(BaseClientes):

    def test_carga_das_duas_arvores(self):
        self.assertEqual(backend.total_clientes(), 1001)
        self.assertEqual(backend._arvore_id.total_chaves(), 1001)
        self.assertEqual(backend._arvore_email.total_chaves(), 1001)
        self.assertEqual(backend._arvore_id.validar(), [])
        self.assertEqual(backend._arvore_email.validar(), [])
        self.assertEqual(backend.proximo_id(), 1002)

    def test_busca_por_id_e_por_email(self):
        por_id, inst_id = backend.buscar_cliente_por_id(1001)
        por_email, inst_email = backend.buscar_cliente_por_email(" INES@ed2.com ")

        self.assertEqual(por_id, por_email)
        self.assertEqual(por_id["nome"], "Ines")
        for inst, arvore in ((inst_id, "id"), (inst_email, "email")):
            self.assertEqual(inst["arvore"], arvore)
            self.assertTrue(inst["encontrado"])
            self.assertEqual(inst["posicao"], 1000)
            self.assertFalse(inst["simulado"])
            self.assertGreater(inst["comparacoes"], 0)
            self.assertGreater(inst["nos_visitados"], 0)
            self.assertGreater(inst["altura"], 0)
            self.assertGreater(inst["divisoes"], 0)
        self.assertEqual(inst_email["chave"], "ines@ed2.com")

    def test_busca_inexistente_e_id_invalido(self):
        cliente, inst = backend.buscar_cliente_por_id(999999)
        self.assertIsNone(cliente)
        self.assertFalse(inst["encontrado"])
        self.assertGreater(inst["nos_visitados"], 0)

        buscas_antes = backend.instrumentacao_arvore_b("id")["acumulado"]["total_buscas"]
        cliente, inst = backend.buscar_cliente_por_id("abc")
        self.assertIsNone(cliente)
        self.assertEqual((inst["posicao"], inst["comparacoes"], inst["nos_visitados"]), (None, 0, 0))
        self.assertEqual(backend.instrumentacao_arvore_b("id")["acumulado"]["total_buscas"], buscas_antes)

    def test_devolve_copias(self):
        cliente, _ = backend.buscar_cliente_por_id(1001)
        cliente["nome"] = "Alterado fora do backend"
        self.assertEqual(backend.buscar_cliente_por_id(1001)[0]["nome"], "Ines")

    def test_listagem_pelo_percurso_e_filtros(self):
        todos = backend.listar_clientes(status="todos")
        self.assertEqual(len(todos), 1001)
        self.assertEqual([c["id"] for c in todos], sorted(c["id"] for c in todos))

        self.assertEqual(len(backend.listar_clientes()), 910)                 # ativos (padrão)
        self.assertEqual(len(backend.listar_clientes(status="inativo")), 91)
        self.assertEqual(len(backend.listar_clientes(pacote="sem", status="todos")), 200)
        self.assertEqual([c["id"] for c in backend.listar_clientes(busca="1001")], [1001])
        self.assertEqual([c["id"] for c in backend.listar_clientes(busca="ines@ed2.com")], [1001])
        self.assertEqual([c["id"] for c in backend.listar_clientes(busca="Beatriz Barbosa")], [2])

    def test_listagem_usa_a_arvore(self):
        with mock.patch.object(backend._arvore_id, "percorrer_em_ordem", return_value=[(2, 1)]) as percurso:
            self.assertEqual([c["id"] for c in backend.listar_clientes(status="todos")], [2])
            percurso.assert_called_once()


class TesteCadastro(BaseClientes):

    def test_cadastrar_recebe_id_do_contador(self):
        cliente = backend.cadastrar_cliente({
            "id": "77777",   # ignorado (DC-01)
            "nome": "Nova Cliente", "email": "  Nova@Example.com ", "esim": "ESIM-X",
        })
        self.assertEqual(cliente["id"], 1002)
        self.assertEqual(cliente["email"], "nova@example.com")
        self.assertEqual(cliente["senha"], "123456")
        self.assertEqual(cliente["status"], "ativo")
        self.assertIsNone(cliente["pacote"])

        # Nas duas árvores, na posição = tamanho anterior da lista
        self.assertEqual(backend.buscar_cliente_por_id(1002)[1]["posicao"], 1001)
        self.assertEqual(backend.buscar_cliente_por_email("nova@example.com")[1]["posicao"], 1001)
        self.assertEqual(backend._arvore_id.metricas()["estado"]["ultima_operacao"], "insercao")

        # Gravado e controle avançado
        self.assertEqual(self.ler(self.arq_clientes)[1001]["id"], 1002)
        controle = self.ler(self.arq_controle)
        self.assertEqual(controle["proximo_id"], 1003)
        self.assertIn(1002, controle["ids_utilizados"])

    def test_email_repetido_nao_grava(self):
        antes = (self.arq_clientes.read_bytes(), self.arq_controle.read_bytes())
        with self.assertRaisesRegex(ValueError, "Já existe um cliente com esse e-mail."):
            backend.cadastrar_cliente({"nome": "X", "email": "INES@ed2.com", "esim": "E"})
        self.assertEqual((self.arq_clientes.read_bytes(), self.arq_controle.read_bytes()), antes)
        self.assertEqual(backend.proximo_id(), 1002)

    def test_validacoes(self):
        casos = (
            ({"nome": "", "email": "a@b.com", "esim": "E"}, "Preencha todos"),
            ({"nome": "A", "email": "sem-arroba", "esim": "E"}, "e-mail válido"),
            ({"nome": "A", "email": "a b@c.com", "esim": "E"}, "e-mail válido"),
            ({"nome": "A", "email": "a@b.com", "esim": ""}, "Preencha todos"),
            ({"nome": "A", "email": "a@b.com", "esim": "E", "status": "x"}, "status válido"),
        )
        for dados, mensagem in casos:
            with self.assertRaisesRegex(ValueError, mensagem):
                backend.cadastrar_cliente(dados)

    def test_esim_repetido_e_permitido(self):
        cliente = backend.cadastrar_cliente({"nome": "A", "email": "a@b.com", "esim": "ESIM-10001"})
        self.assertEqual(cliente["esim"], "ESIM-10001")   # DC-03 / DC-11

    def test_criar_conta(self):
        cliente = backend.criar_conta({"nome": "Pública", "email": "publica@x.com"})
        self.assertEqual(cliente["id"], 1002)
        self.assertEqual(cliente["esim"], "ESIM-1002")
        self.assertEqual(cliente["status"], "ativo")
        self.assertIsNone(cliente["pacote"])


class TesteEdicaoEStatus(BaseClientes):

    def test_editar_nome_esim_status(self):
        cliente = backend.editar_cliente(2, {
            "nome": "Novo Nome", "esim": "ESIM-NOVO", "status": "inativo",
            "email": "beatriz.barbosa1002@example.com",
        })
        self.assertEqual((cliente["nome"], cliente["esim"], cliente["status"]),
                         ("Novo Nome", "ESIM-NOVO", "inativo"))
        self.assertEqual(self.ler(self.arq_clientes)[1]["nome"], "Novo Nome")
        self.assertEqual(backend.buscar_cliente_por_id(2)[1]["posicao"], 1)

    def test_editar_email_e_rejeitado(self):
        with self.assertRaisesRegex(ValueError, "O e-mail não pode ser alterado."):
            backend.editar_cliente(2, {"nome": "A", "esim": "E", "status": "ativo",
                                       "email": "outro@example.com"})

    def test_editar_nao_muda_arvores_nem_senha(self):
        divisoes = backend._arvore_id.metricas()["estado"]["divisoes"]
        backend.editar_cliente(2, {"nome": "A", "esim": "E", "status": "ativo", "senha": "x"})
        self.assertEqual(backend._arvore_id.metricas()["estado"]["divisoes"], divisoes)
        self.assertEqual(backend.buscar_cliente_por_id(2)[0]["senha"], "123456")

    def test_inativar_e_reativar(self):
        antes, _ = backend.buscar_cliente_por_id(2)
        backend.inativar_cliente(2)
        depois, inst = backend.buscar_cliente_por_id(2)

        self.assertEqual(depois["status"], "inativo")
        self.assertEqual({k: v for k, v in depois.items() if k != "status"},
                         {k: v for k, v in antes.items() if k != "status"})
        self.assertTrue(inst["encontrado"])                       # continua nas árvores
        self.assertTrue(backend.buscar_cliente_por_email(antes["email"])[1]["encontrado"])

        with self.assertRaisesRegex(ValueError, "já está inativo"):
            backend.inativar_cliente(2)

        backend.reativar_cliente(2)
        self.assertEqual(backend.buscar_cliente_por_id(2)[0]["status"], "ativo")
        with self.assertRaisesRegex(ValueError, "já está ativo"):
            backend.reativar_cliente(2)

    def test_contratar_plano(self):
        cliente = backend.contratar_plano(2, "101", ["ES", "IT", "PT"],
                                          "2026-11-20T10:00:00-03:00", "2026-12-05T10:00:00-03:00")
        self.assertEqual(cliente["pacote"], 101)
        self.assertEqual(self.ler(self.arq_clientes)[1]["paises_ativos"], ["ES", "IT", "PT"])

        with self.assertRaisesRegex(ValueError, "cadastro está inativo"):
            backend.contratar_plano(1, "102", [], "a", "b")       # cliente 1 é inativo

    def test_cliente_inexistente(self):
        for funcao in (backend.inativar_cliente, backend.reativar_cliente):
            with self.assertRaisesRegex(ValueError, "Cliente não encontrado."):
                funcao(999999)


class TesteExclusaoFisica(BaseClientes):

    def test_cliente_ativo_nao_pode_ser_excluido(self):
        with self.assertRaisesRegex(ValueError, "Somente clientes inativos"):
            backend.excluir_cliente_fisicamente(2, "2", True)

    def test_confirmacao_e_ciencia(self):
        with self.assertRaisesRegex(ValueError, "Confirmação inválida"):
            backend.excluir_cliente_fisicamente(1, "errado", True)
        with self.assertRaisesRegex(ValueError, "Marque a ciência"):
            backend.excluir_cliente_fisicamente(1, "EXCLUIR", False)

    def test_exclusao_reconstroi_e_nao_reutiliza_id(self):
        backend.buscar_cliente_por_id(500)   # gera métricas na instância atual
        arvore_antiga = backend._arvore_id

        self.assertIsNone(backend.excluir_cliente_fisicamente(1, "1", True))

        # Registro vira null na mesma posição; nenhuma outra se desloca
        lista = self.ler(self.arq_clientes)
        self.assertIsNone(lista[0])
        self.assertEqual(len(lista), 1001)
        self.assertEqual(lista[1]["id"], 2)

        # Índices reconstruídos: novas instâncias, métricas zeradas
        self.assertIsNot(backend._arvore_id, arvore_antiga)
        metricas = backend.instrumentacao_arvore_b("id")
        self.assertEqual(metricas["acumulado"]["total_buscas"], 0)
        self.assertEqual(metricas["estado"]["ultima_operacao"], "reconstrucao")
        self.assertEqual(metricas["estado"]["total_chaves"], 1000)
        self.assertEqual(backend.total_clientes(), 1000)
        self.assertEqual(backend._arvore_id.validar(), [])

        self.assertIsNone(backend.buscar_cliente_por_id(1)[0])
        self.assertIsNone(backend.buscar_cliente_por_email("nicolas.cardoso1001@example.com")[0])
        self.assertEqual(backend.buscar_cliente_por_id(2)[1]["posicao"], 1)

        # O ID continua no histórico e o próximo cadastro não o reutiliza
        self.assertIn(1, self.ler(self.arq_controle)["ids_utilizados"])
        novo = backend.cadastrar_cliente({"nome": "N", "email": "n@x.com", "esim": "E"})
        self.assertEqual(novo["id"], 1002)

        # Reiniciar a partir dos arquivos dá o mesmo estado
        self.assertTrue(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        self.assertEqual(backend.total_clientes(), 1001)
        self.assertIsNone(backend.buscar_cliente_por_id(1)[0])
        self.assertEqual(backend.buscar_cliente_por_id(1002)[1]["posicao"], 1001)


class TesteFalhas(BaseClientes):

    def test_reinicializar_reproduz_o_gravado(self):
        backend.cadastrar_cliente({"nome": "N", "email": "n@x.com", "esim": "E"})
        backend.inativar_cliente(3)
        lista_memoria = backend.listar_clientes(status="todos")

        self.assertTrue(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        self.assertEqual(backend.listar_clientes(status="todos"), lista_memoria)
        self.assertEqual(backend.proximo_id(), 1003)

    def test_email_repetido_no_arquivo_deixa_indisponivel(self):
        lista = self.ler(self.arq_clientes)
        lista[1]["email"] = lista[0]["email"]
        self.arq_clientes.write_text(json.dumps(lista), encoding="utf-8")

        self.assertFalse(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        with self.assertRaises(ErroIndices) as contexto:
            backend.buscar_cliente_por_id(1001)
        self.assertIn("duplicado", str(contexto.exception))
        self.assertIn("funcionalidades de países continuam disponíveis", str(contexto.exception))

        for funcao in (backend.listar_clientes, backend.total_clientes, backend.proximo_id):
            with self.assertRaises(ErroIndices):
                funcao()

        resumo = backend.resumo_arvore_b()
        self.assertFalse(resumo["disponivel"])
        self.assertEqual(resumo["clientes"], 0)
        self.assertIn("erro", resumo)
        self.assertIn("erro", backend.instrumentacao_arvore_b("email"))
        self.assertEqual(backend.normalizar_email(" A@B "), "a@b")

    def test_controle_inconsistente_deixa_indisponivel(self):
        self.arq_controle.write_text(json.dumps({"proximo_id": 10, "ids_utilizados": [1, 2]}),
                                     encoding="utf-8")
        self.assertFalse(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        with self.assertRaisesRegex(ErroIndices, "controle de IDs inconsistente"):
            backend.cadastrar_cliente({"nome": "A", "email": "a@b.com", "esim": "E"})
        # Nada foi corrigido nem reinicializado
        self.assertEqual(self.ler(self.arq_controle), {"proximo_id": 10, "ids_utilizados": [1, 2]})

    def test_arquivo_ausente_ou_invalido(self):
        self.arq_clientes.write_text("{}", encoding="utf-8")
        self.assertFalse(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        self.assertFalse(backend.resumo_arvore_b()["disponivel"])

        self.arq_clientes.unlink()
        self.assertFalse(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))

    def test_null_legitimo_e_registro_invalido(self):
        lista = self.ler(self.arq_clientes)
        lista[5] = None
        controle_ok = self.ler(self.arq_controle)
        self.arq_clientes.write_text(json.dumps(lista), encoding="utf-8")
        self.assertTrue(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        self.assertEqual(backend.total_clientes(), 1000)

        lista[5] = "registro estranho"
        self.arq_clientes.write_text(json.dumps(lista), encoding="utf-8")
        self.assertFalse(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        self.assertEqual(self.ler(self.arq_controle), controle_ok)

    def test_falha_na_gravacao_dos_clientes_bloqueia_escritas(self):
        # O controle é gravado; a lista de clientes falha (DC-02 + Guia B6).
        with mock.patch.object(backend.persistencia, "salvar_clientes", side_effect=OSError("disco cheio")):
            with self.assertRaisesRegex(ValueError, "Não foi possível gravar"):
                backend.cadastrar_cliente({"nome": "A", "email": "a@b.com", "esim": "E"})

        controle = self.ler(self.arq_controle)
        self.assertEqual(controle["proximo_id"], 1003)               # ID 1002 consumido
        self.assertEqual(len(self.ler(self.arq_clientes)), 1001)      # lista inalterada
        self.assertFalse(backend.buscar_cliente_por_email("a@b.com")[1]["encontrado"])

        # Escritas bloqueadas; consultas continuam
        with self.assertRaisesRegex(ValueError, "bloqueadas até a aplicação ser reiniciada"):
            backend.inativar_cliente(2)
        self.assertEqual(backend.buscar_cliente_por_id(2)[0]["status"], "ativo")

        # Ao reiniciar, o ID 1002 nunca é reutilizado
        self.assertTrue(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        novo = backend.cadastrar_cliente({"nome": "A", "email": "a@b.com", "esim": "E"})
        self.assertEqual(novo["id"], 1003)

    def test_falha_na_gravacao_do_controle_nao_altera_nada(self):
        with mock.patch.object(backend.persistencia, "salvar_controle_ids", side_effect=OSError("sem permissão")):
            with self.assertRaises(ValueError):
                backend.cadastrar_cliente({"nome": "A", "email": "a@b.com", "esim": "E"})
        self.assertEqual(backend.proximo_id(), 1002)
        self.assertEqual(backend.total_clientes(), 1001)


class TesteInstrumentacao(BaseClientes):

    def test_metricas_separadas_por_arvore(self):
        backend.buscar_cliente_por_id(10)
        backend.buscar_cliente_por_id(20)
        backend.buscar_cliente_por_email("ines@ed2.com")

        por_id = backend.instrumentacao_arvore_b("id")
        por_email = backend.instrumentacao_arvore_b("email")
        self.assertEqual(por_id["acumulado"]["total_buscas"], 2)
        self.assertEqual(por_email["acumulado"]["total_buscas"], 1)
        self.assertEqual(por_id["nome"], "Árvore B de ID")
        self.assertEqual(por_email["icone"], "bi-envelope")
        self.assertEqual(por_id["grau"], 3)
        self.assertFalse(por_id["simulado"])
        self.assertEqual(backend.instrumentacao_arvore_b("qualquer")["arvore"], "id")

        self.assertEqual(set(por_id), {"arvore", "nome", "chave", "icone", "grau",
                                       "ultima_busca", "acumulado", "estado", "simulado"})
        self.assertEqual(set(por_id["estado"]), {"altura", "divisoes", "total_chaves",
                                                 "ultima_operacao", "tempo_execucao_us"})

    def test_resumo_do_dashboard(self):
        resumo = backend.resumo_arvore_b()
        self.assertEqual(resumo["media_nos_visitados"], 0.0)

        _, a = backend.buscar_cliente_por_id(1)
        _, b = backend.buscar_cliente_por_id(1001)
        resumo = backend.resumo_arvore_b()
        self.assertEqual(resumo["clientes"], 1001)
        self.assertEqual(resumo["altura"], backend._arvore_id.altura())
        self.assertEqual(resumo["nos"], backend._arvore_id.contar_nos())
        self.assertEqual(resumo["media_nos_visitados"],
                         round((a["nos_visitados"] + b["nos_visitados"]) / 2, 1))
        self.assertTrue(resumo["disponivel"])


if __name__ == "__main__":
    unittest.main()
