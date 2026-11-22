"""
DGB SIM — Etapa 2 — Testes do backend de clientes (dados_site/dados_etapa02.py).

Execução, a partir da raiz do projeto:

    python -m unittest discover -s testes -t ..

Isolamento: cada teste trabalha em CÓPIAS de arquivos/clientes.json e
arquivos/controle_ids.json dentro de um diretório temporário. Os arquivos
reais nunca são alterados (setUpModule/tearDownModule conferem isso).
"""

import hashlib
import importlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from arquivos import persistencia_clientes
from dados_site import dados_etapa02 as de

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVOS_REAIS = [
    RAIZ / "arquivos" / "clientes.json",
    RAIZ / "arquivos" / "controle_ids.json",
    RAIZ / "arquivos" / "historico.json",
]

MSG_INDISPONIVEL = "Os dados de clientes estão indisponíveis: "
MSG_PAISES = "As funcionalidades de países continuam disponíveis."


def _hash(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest() if caminho.exists() else None


def _ler_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def _gravar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


_HASHES_ANTES = {}


def setUpModule():
    _HASHES_ANTES.update({caminho: _hash(caminho) for caminho in ARQUIVOS_REAIS})


def tearDownModule():
    for caminho, antes in _HASHES_ANTES.items():
        assert _hash(caminho) == antes, f"{caminho.name} (arquivo real) foi alterado pelos testes"


class BaseClientes(unittest.TestCase):
    """Prepara cópias temporárias dos arquivos e inicializa o módulo nelas."""

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.tmp_clientes = os.path.join(self.pasta.name, "clientes.json")
        self.tmp_controle = os.path.join(self.pasta.name, "controle_ids.json")
        shutil.copy(RAIZ / "arquivos" / "clientes.json", self.tmp_clientes)
        shutil.copy(RAIZ / "arquivos" / "controle_ids.json", self.tmp_controle)

        de.inicializar(self.tmp_clientes, self.tmp_controle)
        self.assertIsNone(de._erro_indisponivel, "a carga inicial deveria funcionar")

    def tearDown(self):
        de.inicializar()          # volta aos caminhos padrão
        self.pasta.cleanup()

    # --- auxiliares ---------------------------------------------------------
    def erro_de(self, excecao, funcao, *args, **kwargs):
        """Executa e devolve a mensagem da exceção esperada."""
        with self.assertRaises(excecao) as contexto:
            funcao(*args, **kwargs)
        return str(contexto.exception)

    def clientes_json(self):
        return _ler_json(self.tmp_clientes)

    def controle_json(self):
        return _ler_json(self.tmp_controle)

    def snapshot_arquivos(self):
        return (Path(self.tmp_clientes).read_bytes(), Path(self.tmp_controle).read_bytes())

    def primeiro_cliente(self, **filtros):
        """Primeiro cliente (por ID) que atende a todos os filtros campo=valor."""
        for cliente in de.listar_clientes(status="todos"):
            if all(cliente[campo] == valor for campo, valor in filtros.items()):
                return cliente
        self.fail(f"nenhum cliente com {filtros} na carga")

    def cadastrar_exemplo(self, email="novo@teste.com"):
        return de.cadastrar_cliente({"nome": "Novo Cliente", "email": email, "esim": "ESIM-NOVO"})


# =============================================================================
# CARGA E BUSCAS
# =============================================================================

class TestCargaEBuscas(BaseClientes):

    def test_carga_inicial_tem_1001_chaves_nas_duas_arvores(self):
        self.assertEqual(de._arvore_id.total_chaves(), 1001)
        self.assertEqual(de._arvore_email.total_chaves(), 1001)
        self.assertEqual(de.total_clientes(), 1001)
        self.assertEqual(de._arvore_id.validar(), [])
        self.assertEqual(de._arvore_email.validar(), [])
        self.assertEqual(de.proximo_id(), 1002)

    def test_busca_por_id_e_por_email_devolvem_o_mesmo_cliente(self):
        por_id, inst_id = de.buscar_cliente_por_id(1001)
        por_email, inst_email = de.buscar_cliente_por_email("INES@ed2.com ")

        self.assertIsNotNone(por_id)
        self.assertEqual(por_id, por_email)
        self.assertEqual(por_id["email"], "ines@ed2.com")
        self.assertIs(inst_id["simulado"], False)
        self.assertIs(inst_email["simulado"], False)
        self.assertTrue(inst_id["encontrado"] and inst_email["encontrado"])
        self.assertEqual(inst_id["posicao"], inst_email["posicao"])
        self.assertGreater(inst_id["nos_visitados"], 0)
        self.assertGreater(inst_email["comparacoes"], 0)

    def test_busca_de_cliente_inexistente(self):
        cliente, inst = de.buscar_cliente_por_id(999999)
        self.assertIsNone(cliente)
        self.assertFalse(inst["encontrado"])
        self.assertIsNone(inst["posicao"])

        cliente, inst = de.buscar_cliente_por_email("ninguem@nada.com")
        self.assertIsNone(cliente)
        self.assertFalse(inst["encontrado"])

    def test_id_invalido_nao_consulta_a_arvore(self):
        antes = de.instrumentacao_arvore_b("id")["acumulado"]["total_buscas"]

        for invalido in ("abc", "", "0", -5, "1001.0", None, True):
            cliente, inst = de.buscar_cliente_por_id(invalido)
            self.assertIsNone(cliente)
            self.assertEqual(inst["comparacoes"], 0)
            self.assertEqual(inst["nos_visitados"], 0)
            self.assertIs(inst["simulado"], False)

        cliente, inst = de.buscar_cliente_por_email("   ")
        self.assertIsNone(cliente)
        self.assertEqual(inst["comparacoes"], 0)

        depois = de.instrumentacao_arvore_b("id")["acumulado"]["total_buscas"]
        self.assertEqual(antes, depois)

    def test_listar_clientes_usa_busca_filtros_e_ordem_por_id(self):
        todos = de.listar_clientes(status="todos")
        self.assertEqual(len(todos), 1001)
        self.assertEqual([c["id"] for c in todos], sorted(c["id"] for c in todos))

        ativos = de.listar_clientes()
        inativos = de.listar_clientes(status="inativo")
        self.assertEqual(len(ativos) + len(inativos), 1001)
        self.assertTrue(all(c["status"] == "ativo" for c in ativos))

        self.assertEqual([c["id"] for c in de.listar_clientes(busca="1001", status="todos")], [1001])
        self.assertEqual(
            [c["id"] for c in de.listar_clientes(busca=" INES@ed2.com", status="todos")], [1001]
        )
        self.assertEqual(
            [c["id"] for c in de.listar_clientes(busca="ines", status="todos")], [1001]
        )

        sem_plano = de.listar_clientes(pacote="sem", status="todos")
        self.assertTrue(sem_plano and all(c["pacote"] is None for c in sem_plano))
        plus_europa = de.listar_clientes(pacote="102", status="todos")
        self.assertTrue(all(c["pacote"] == 102 for c in plus_europa))

    def test_clientes_devolvidos_sao_copias(self):
        cliente = next(c for c in de.listar_clientes(status="todos") if c["paises_ativos"])
        cliente["nome"] = "ALTERADO FORA"
        cliente["paises_ativos"].append("XX")

        de_novo, _ = de.buscar_cliente_por_id(cliente["id"])
        self.assertNotEqual(de_novo["nome"], "ALTERADO FORA")
        self.assertNotIn("XX", de_novo["paises_ativos"])

        for item in de.listar_clientes(status="todos"):
            item["nome"] = "OUTRA ALTERAÇÃO"
        self.assertNotEqual(de.buscar_cliente_por_id(cliente["id"])[0]["nome"], "OUTRA ALTERAÇÃO")


    def test_retorno_das_alteracoes_tambem_e_copia(self):
        criado = self.cadastrar_exemplo()
        criado["nome"] = "ALTERADO FORA"
        criado["paises_ativos"].append("XX")

        editado = de.editar_cliente(criado["id"], {"nome": "Nome Certo", "esim": "E", "status": "ativo"})
        editado["nome"] = "ALTERADO FORA 2"

        inativado = de.inativar_cliente(criado["id"])
        inativado["status"] = "ativo"

        contratado = de.contratar_plano(
            1001, "102", [], "2026-11-20T10:00:00-03:00", "2026-12-20T10:00:00-03:00"
        )
        contratado["paises_ativos"].append("XX")

        guardado, _ = de.buscar_cliente_por_id(criado["id"])
        self.assertEqual((guardado["nome"], guardado["status"]), ("Nome Certo", "inativo"))
        self.assertEqual(guardado["paises_ativos"], [])
        self.assertEqual(de.buscar_cliente_por_id(1001)[0]["paises_ativos"], [])


# =============================================================================
# CADASTRO
# =============================================================================

class TestCadastro(BaseClientes):

    def test_cadastro_recebe_1002_entra_nas_duas_arvores_e_grava_nos_json(self):
        cliente = de.cadastrar_cliente({
            "id": "1",                       # id enviado é ignorado
            "nome": "  Maria Nova ",
            "email": " Maria.Nova@Teste.COM ",
            "esim": "ESIM-777",
            "status": "ativo",
        })

        self.assertEqual(cliente["id"], 1002)
        self.assertEqual(cliente["email"], "maria.nova@teste.com")
        self.assertEqual(cliente["nome"], "Maria Nova")
        self.assertEqual(cliente["senha"], "123456")
        self.assertIsNone(cliente["pacote"])
        self.assertEqual(cliente["paises_ativos"], [])
        self.assertIsNone(cliente["contratacao_inicio"])
        self.assertIsNone(cliente["contratacao_fim"])

        # Árvores B
        self.assertTrue(de._arvore_id.contem(1002))
        self.assertTrue(de._arvore_email.contem("maria.nova@teste.com"))
        self.assertEqual(de._arvore_id.total_chaves(), 1002)
        self.assertEqual(de._arvore_email.total_chaves(), 1002)
        self.assertEqual(de.buscar_cliente_por_id(1002)[0]["esim"], "ESIM-777")
        self.assertEqual(de.buscar_cliente_por_email("MARIA.NOVA@teste.com")[0]["id"], 1002)

        # JSON: novo registro no FIM, posição = tamanho anterior
        gravados = self.clientes_json()
        self.assertEqual(len(gravados), 1002)
        self.assertEqual(gravados[1001]["id"], 1002)
        self.assertEqual(gravados[1001]["email"], "maria.nova@teste.com")
        posicao, _ = de._arvore_id.buscar(1002)
        self.assertEqual(posicao, 1001)

        controle = self.controle_json()
        self.assertEqual(controle["proximo_id"], 1003)
        self.assertIn(1002, controle["ids_utilizados"])
        self.assertEqual(de.proximo_id(), 1003)

    def test_cadastro_com_email_repetido_nao_grava_nada(self):
        antes = self.snapshot_arquivos()

        for repetido in ("ines@ed2.com", "  INES@ED2.COM "):
            mensagem = self.erro_de(ValueError, de.cadastrar_cliente, {
                "nome": "Outra Pessoa", "email": repetido, "esim": "ESIM-1",
            })
            self.assertEqual(mensagem, "Já existe um cliente com esse e-mail.")

        self.assertEqual(self.snapshot_arquivos(), antes)
        self.assertEqual(de.proximo_id(), 1002)
        self.assertEqual(de.total_clientes(), 1001)
        self.assertEqual(de._arvore_email.total_chaves(), 1001)

    def test_cadastro_invalido_nao_grava_e_usa_mensagens_exatas(self):
        antes = self.snapshot_arquivos()
        base = {"nome": "Fulano", "email": "fulano@teste.com", "esim": "ESIM-9"}

        casos = [
            ({**base, "nome": " "}, "Preencha todos os campos obrigatórios."),
            ({**base, "esim": ""}, "Preencha todos os campos obrigatórios."),
            ({**base, "email": ""}, "Preencha todos os campos obrigatórios."),
            ({**base, "email": "semarroba.com"}, "Informe um e-mail válido."),
            ({**base, "email": "@dominio.com"}, "Informe um e-mail válido."),
            ({**base, "email": "usuario@"}, "Informe um e-mail válido."),
            ({**base, "status": "suspenso"}, "Selecione um status válido."),
        ]
        for dados, esperado in casos:
            with self.subTest(dados=dados):
                self.assertEqual(self.erro_de(ValueError, de.cadastrar_cliente, dados), esperado)

        self.assertEqual(self.snapshot_arquivos(), antes)

    def test_esim_repetido_e_permitido(self):
        a = de.cadastrar_cliente({"nome": "A", "email": "a@teste.com", "esim": "ESIM-IGUAL"})
        b = de.cadastrar_cliente({"nome": "B", "email": "b@teste.com", "esim": "ESIM-IGUAL"})
        self.assertEqual((a["id"], b["id"]), (1002, 1003))

    def test_cadastro_com_status_inativo(self):
        cliente = de.cadastrar_cliente({
            "nome": "Inativo", "email": "inativo@teste.com", "esim": "ESIM-I", "status": "inativo",
        })
        self.assertEqual(cliente["status"], "inativo")

    def test_cadastro_com_pacote_valida_as_regras_do_plano(self):
        base = {"nome": "Com Plano", "email": "plano@teste.com", "esim": "ESIM-P",
                "status": "ativo", "pacote": "201"}

        # Basic exige exatamente 3 países distintos da região (Tabela Hash).
        antes = self.snapshot_arquivos()
        mensagem = self.erro_de(ValueError, de.cadastrar_cliente, {**base, "paises_ativos": ["BR", "CL"]})
        self.assertIn("exige exatamente 3 países", mensagem)
        mensagem = self.erro_de(ValueError, de.cadastrar_cliente, {**base, "paises_ativos": ["BR", "CL", "IT"]})
        self.assertIn("não pertence à região", mensagem)
        self.assertEqual(self.snapshot_arquivos(), antes)

        cliente = de.cadastrar_cliente({**base, "paises_ativos": ["br", "CL", "MX"]})
        self.assertEqual(cliente["pacote"], 201)
        self.assertEqual(cliente["paises_ativos"], ["BR", "CL", "MX"])
        self.assertTrue(cliente["contratacao_inicio"] and cliente["contratacao_fim"])
        self.assertEqual(self.clientes_json()[-1]["pacote"], 201)

    def test_cadastro_com_pacote_exige_status_ativo(self):
        mensagem = self.erro_de(ValueError, de.cadastrar_cliente, {
            "nome": "X", "email": "x@teste.com", "esim": "E", "status": "inativo",
            "pacote": "102", "paises_ativos": [],
        })
        self.assertEqual(mensagem, "Para associar um pacote, o status do cliente deve ser Ativo.")

    def test_pacote_sem_paises_ativos_e_ignorado_como_no_app_atual(self):
        """app.py associa o pacote depois, via contratar_plano()."""
        cliente = de.cadastrar_cliente({
            "nome": "Legado", "email": "legado@teste.com", "esim": "E", "pacote": "201", "paises": "BR",
        })
        self.assertIsNone(cliente["pacote"])
        self.assertEqual(cliente["paises_ativos"], [])

    def test_criar_conta_gera_esim_e_nasce_ativo_sem_plano(self):
        conta = de.criar_conta({"nome": "Nova Conta", "email": "conta@teste.com"})
        self.assertEqual(conta["id"], 1002)
        self.assertEqual(conta["esim"], "ESIM-1002")
        self.assertEqual(conta["status"], "ativo")
        self.assertIsNone(conta["pacote"])


# =============================================================================
# EDIÇÃO, INATIVAÇÃO E REATIVAÇÃO
# =============================================================================

class TestEdicao(BaseClientes):

    def test_edita_nome_esim_e_status_na_mesma_posicao(self):
        posicao_antes, _ = de._arvore_id.buscar(1001)
        original, _ = de.buscar_cliente_por_id(1001)

        editado = de.editar_cliente(1001, {
            "nome": "  Ines Editada ", "email": "ines@ed2.com", "esim": "ESIM-EDIT", "status": "inativo",
        })

        self.assertEqual(editado["nome"], "Ines Editada")
        self.assertEqual(editado["esim"], "ESIM-EDIT")
        self.assertEqual(editado["status"], "inativo")
        for campo in ("id", "email", "senha", "pacote", "paises_ativos",
                      "contratacao_inicio", "contratacao_fim"):
            self.assertEqual(editado[campo], original[campo], campo)

        self.assertEqual(de._arvore_id.buscar(1001)[0], posicao_antes)
        gravado = self.clientes_json()[posicao_antes]
        self.assertEqual((gravado["nome"], gravado["esim"], gravado["status"]),
                         ("Ines Editada", "ESIM-EDIT", "inativo"))
        self.assertEqual(de.buscar_cliente_por_email("ines@ed2.com")[0]["nome"], "Ines Editada")
        self.assertEqual(de.total_clientes(), 1001)

    def test_email_pode_ser_reenviado_igual_mas_nao_alterado(self):
        dados = {"nome": "Ines", "esim": "ESIM-10001", "status": "ativo"}

        # mesmo e-mail (com maiúsculas e espaços) ou ausente: aceito
        de.editar_cliente(1001, {**dados, "email": " INES@ed2.com "})
        de.editar_cliente(1001, dados)

        antes = self.snapshot_arquivos()
        mensagem = self.erro_de(ValueError, de.editar_cliente, 1001, {**dados, "email": "outro@ed2.com"})
        self.assertEqual(mensagem, "O e-mail não pode ser alterado.")
        self.assertEqual(self.snapshot_arquivos(), antes)
        self.assertIsNone(de.buscar_cliente_por_email("outro@ed2.com")[0])
        self.assertIsNotNone(de.buscar_cliente_por_email("ines@ed2.com")[0])

    def test_edicao_invalida(self):
        base = {"nome": "Ines", "email": "ines@ed2.com", "esim": "E", "status": "ativo"}
        antes = self.snapshot_arquivos()

        self.assertEqual(self.erro_de(ValueError, de.editar_cliente, 999999, base), "Cliente não encontrado.")
        self.assertEqual(self.erro_de(ValueError, de.editar_cliente, "abc", base), "Cliente não encontrado.")
        self.assertEqual(self.erro_de(ValueError, de.editar_cliente, 1001, {**base, "nome": ""}),
                         "Preencha todos os campos obrigatórios.")
        self.assertEqual(self.erro_de(ValueError, de.editar_cliente, 1001, {**base, "esim": " "}),
                         "Preencha todos os campos obrigatórios.")
        self.assertEqual(self.erro_de(ValueError, de.editar_cliente, 1001, {**base, "status": "x"}),
                         "Selecione um status válido.")
        self.assertEqual(self.snapshot_arquivos(), antes)

    def test_edicao_com_pacote_reinicia_a_vigencia(self):
        cliente = self.primeiro_cliente(status="ativo", pacote=None)
        editado = de.editar_cliente(cliente["id"], {
            "nome": cliente["nome"], "esim": cliente["esim"], "status": "ativo",
            "pacote": "201", "paises_ativos": ["BR", "CL", "MX"],
        })
        self.assertEqual(editado["pacote"], 201)
        self.assertEqual(editado["paises_ativos"], ["BR", "CL", "MX"])
        self.assertTrue(editado["contratacao_inicio"])

        mensagem = self.erro_de(ValueError, de.editar_cliente, cliente["id"], {
            "nome": cliente["nome"], "esim": cliente["esim"], "status": "ativo",
            "pacote": "201", "paises_ativos": ["BR"],
        })
        self.assertIn("exige exatamente 3 países", mensagem)
        self.assertEqual(de.buscar_cliente_por_id(cliente["id"])[0]["paises_ativos"], ["BR", "CL", "MX"])


class TestInativarEReativar(BaseClientes):

    def test_inativar_e_reativar_alteram_somente_o_status(self):
        # Cliente ativo com plano Basic (países preenchidos), para provar a preservação.
        original = next(
            c for c in de.listar_clientes(status="ativo") if c["pacote"] and c["paises_ativos"]
        )
        cid, email = original["id"], original["email"]
        posicao, _ = de._arvore_id.buscar(cid)

        inativo = de.inativar_cliente(cid)
        self.assertEqual(inativo["status"], "inativo")
        self.assertEqual({**inativo, "status": "ativo"}, original)
        self.assertEqual(self.clientes_json()[posicao]["status"], "inativo")
        self.assertEqual(self.clientes_json()[posicao]["paises_ativos"], original["paises_ativos"])
        self.assertTrue(de._arvore_id.contem(cid))
        self.assertTrue(de._arvore_email.contem(email))
        self.assertEqual(de._arvore_id.buscar(cid)[0], posicao)

        self.assertEqual(self.erro_de(ValueError, de.inativar_cliente, cid), "O cliente já está inativo.")

        ativo = de.reativar_cliente(cid)
        self.assertEqual(ativo, original)
        self.assertEqual(self.clientes_json()[posicao]["status"], "ativo")
        self.assertTrue(de._arvore_id.contem(cid) and de._arvore_email.contem(email))
        self.assertEqual(de.total_clientes(), 1001)

        self.assertEqual(self.erro_de(ValueError, de.reativar_cliente, cid), "O cliente já está ativo.")

    def test_inativar_cliente_inexistente(self):
        self.assertEqual(self.erro_de(ValueError, de.inativar_cliente, 424242), "Cliente não encontrado.")
        self.assertEqual(self.erro_de(ValueError, de.reativar_cliente, "x"), "Cliente não encontrado.")


# =============================================================================
# EXCLUSÃO FÍSICA
# =============================================================================

class TestExclusaoFisica(BaseClientes):

    def test_cliente_ativo_nao_pode_ser_excluido(self):
        antes = self.snapshot_arquivos()
        mensagem = self.erro_de(ValueError, de.excluir_cliente_fisicamente, 1001, "1001", True)
        self.assertEqual(
            mensagem,
            "Somente clientes inativos podem ser excluídos permanentemente. Inative o cliente antes.",
        )
        self.assertEqual(self.snapshot_arquivos(), antes)
        self.assertTrue(de._arvore_id.contem(1001))

    def test_confirmacao_e_ciencia_sao_obrigatorias(self):
        alvo = self.primeiro_cliente(status="inativo")["id"]
        antes = self.snapshot_arquivos()

        for confirmacao in ("", "abc", "999", None, "EXCLUIR!"):
            self.assertEqual(
                self.erro_de(ValueError, de.excluir_cliente_fisicamente, alvo, confirmacao, True),
                "Confirmação inválida: digite o ID do cliente ou EXCLUIR.",
            )
        for ciencia in (False, None, ""):
            self.assertEqual(
                self.erro_de(ValueError, de.excluir_cliente_fisicamente, alvo, str(alvo), ciencia),
                "Marque a ciência de que a exclusão é irreversível.",
            )
        self.assertEqual(
            self.erro_de(ValueError, de.excluir_cliente_fisicamente, 424242, "EXCLUIR", True),
            "Cliente não encontrado.",
        )
        self.assertEqual(self.snapshot_arquivos(), antes)

    def test_exclusao_vira_none_no_json_e_o_id_nao_e_reutilizado(self):
        # Exclui o MAIOR ID: com "maior + 1" o 1001 seria reaproveitado.
        email = de.buscar_cliente_por_id(1001)[0]["email"]
        posicao, _ = de._arvore_id.buscar(1001)
        de.inativar_cliente(1001)

        self.assertIsNone(de.excluir_cliente_fisicamente(1001, "1001", True))

        gravados = self.clientes_json()
        self.assertIsNone(gravados[posicao])
        self.assertEqual(len(gravados), 1001)                       # nada se desloca
        self.assertEqual(self.controle_json()["proximo_id"], 1002)
        self.assertIn(1001, self.controle_json()["ids_utilizados"])

        self.assertIsNone(de.buscar_cliente_por_id(1001)[0])
        self.assertIsNone(de.buscar_cliente_por_email(email)[0])
        self.assertEqual(de.total_clientes(), 1000)
        self.assertEqual(de._arvore_id.total_chaves(), 1000)
        self.assertEqual(de._arvore_email.total_chaves(), 1000)
        self.assertEqual(de._arvore_id.validar() + de._arvore_email.validar(), [])
        self.assertEqual(de._arvore_id.metricas()["acumulado"]["total_buscas"], 1)  # árvore reconstruída
        self.assertEqual(de._arvore_id.metricas()["estado"]["ultima_operacao"], "reconstrucao")

        # O próximo cadastro recebe 1002 (não 1001) e vai para o fim do arquivo.
        novo = self.cadastrar_exemplo()
        self.assertEqual(novo["id"], 1002)
        self.assertEqual(de._arvore_id.buscar(1002)[0], 1001)
        self.assertIsNone(self.clientes_json()[posicao])

    def test_confirmacao_aceita_excluir_em_qualquer_caixa(self):
        alvo = self.primeiro_cliente(status="inativo")["id"]
        de.excluir_cliente_fisicamente(alvo, " excluir ", True)
        self.assertIsNone(de.buscar_cliente_por_id(alvo)[0])
        self.assertEqual(de.total_clientes(), 1000)

    def test_falha_na_reconstrucao_deixa_os_dados_indisponiveis(self):
        alvo = self.primeiro_cliente(status="inativo")["id"]

        with mock.patch.object(de, "construir_indices", side_effect=ValueError("índice quebrado")):
            de.excluir_cliente_fisicamente(alvo, "EXCLUIR", True)

        self.assertEqual(de._erro_indisponivel, "índice quebrado")
        mensagem = self.erro_de(de.ErroIndices, de.total_clientes)
        self.assertEqual(mensagem, f"{MSG_INDISPONIVEL}índice quebrado. {MSG_PAISES}")
        self.assertIsNone(self.clientes_json()[alvo - 1])          # a exclusão já estava gravada


# =============================================================================
# CONTRATAÇÃO
# =============================================================================

class TestContratacao(BaseClientes):

    def test_contrata_basic_com_tres_paises_da_regiao(self):
        cliente = self.primeiro_cliente(status="ativo", pacote=None)
        posicao, _ = de._arvore_id.buscar(cliente["id"])

        atualizado = de.contratar_plano(
            cliente["id"], "201", ["BR", "cl", "MX"],
            "2026-11-20T10:00:00-03:00", "2026-12-05T10:00:00-03:00",
        )
        self.assertEqual(atualizado["pacote"], 201)
        self.assertEqual(atualizado["paises_ativos"], ["BR", "CL", "MX"])
        self.assertEqual(atualizado["contratacao_fim"], "2026-12-05T10:00:00-03:00")
        self.assertEqual(self.clientes_json()[posicao]["pacote"], 201)
        self.assertEqual(de._arvore_id.buscar(cliente["id"])[0], posicao)

    def test_basic_invalido_nao_grava(self):
        cliente = self.primeiro_cliente(status="ativo", pacote=None)
        antes = self.snapshot_arquivos()
        datas = ("2026-11-20T10:00:00-03:00", "2026-12-05T10:00:00-03:00")

        for paises in (["BR", "CL"], ["BR", "BR", "CL"], ["BR", "CL", "IT"], ["BR", "CL", "ZZ"], []):
            with self.subTest(paises=paises):
                with self.assertRaises(ValueError):
                    de.contratar_plano(cliente["id"], "201", paises, *datas)

        self.assertEqual(self.erro_de(ValueError, de.contratar_plano, cliente["id"], "999", [], *datas),
                         "Selecione um plano válido.")
        self.assertEqual(self.snapshot_arquivos(), antes)

    def test_plus_e_global_guardam_lista_vazia_de_paises(self):
        cliente = self.primeiro_cliente(status="ativo", pacote=None)
        datas = ("2026-11-20T10:00:00-03:00", "2026-12-20T10:00:00-03:00")

        plus = de.contratar_plano(cliente["id"], 102, [], *datas)
        self.assertEqual((plus["pacote"], plus["paises_ativos"]), (102, []))
        global_ = de.contratar_plano(cliente["id"], "301", ["BR"], *datas)
        self.assertEqual((global_["pacote"], global_["paises_ativos"]), (301, []))

    def test_cliente_inativo_nao_contrata(self):
        inativo = self.primeiro_cliente(status="inativo")
        mensagem = self.erro_de(ValueError, de.contratar_plano, inativo["id"], "102", [], "a", "b")
        self.assertEqual(mensagem, "Seu cadastro está inativo. Procure a administração da DGB SIM.")
        self.assertEqual(self.erro_de(ValueError, de.contratar_plano, 424242, "102", [], "a", "b"),
                         "Cliente não encontrado.")


# =============================================================================
# PERSISTÊNCIA E REINICIALIZAÇÃO
# =============================================================================

class TestReinicializacao(BaseClientes):

    def estado(self):
        return {
            "clientes": de.listar_clientes(status="todos"),
            "controle": json.loads(json.dumps(de._controle_ids)),
            "ids": de._arvore_id.percorrer_em_ordem(),
            "emails": de._arvore_email.percorrer_em_ordem(),
            "proximo_id": de.proximo_id(),
            "total": de.total_clientes(),
        }

    def test_inicializar_de_novo_mantem_tudo_igual_ao_gravado(self):
        self.cadastrar_exemplo("um@teste.com")
        self.cadastrar_exemplo("dois@teste.com")
        de.editar_cliente(1001, {"nome": "Ines 2", "esim": "ESIM-2", "status": "ativo"})
        inativo = self.primeiro_cliente(status="inativo")["id"]
        de.excluir_cliente_fisicamente(inativo, "EXCLUIR", True)
        ativo = self.primeiro_cliente(status="ativo")["id"]
        de.inativar_cliente(ativo)
        de.contratar_plano(1001, "201", ["BR", "CL", "MX"], "2026-11-20T10:00:00-03:00",
                           "2026-12-05T10:00:00-03:00")

        antes = self.estado()
        self.assertEqual((antes["total"], antes["proximo_id"]), (1002, 1004))

        de.inicializar(self.tmp_clientes, self.tmp_controle)

        self.assertIsNone(de._erro_indisponivel)
        self.assertIsNone(de._erro_gravacao)
        self.assertEqual(self.estado(), antes)
        self.assertEqual(self.controle_json(), antes["controle"])
        self.assertIsNone(self.clientes_json()[inativo - 1])
        self.assertIsNone(de.buscar_cliente_por_id(inativo)[0])

    def test_importar_sem_os_arquivos_nao_quebra(self):
        """O Flask precisa subir mesmo sem clientes.json (países continuam)."""
        vazio = tempfile.TemporaryDirectory()
        diretorio_atual = os.getcwd()
        try:
            os.chdir(vazio.name)
            importlib.reload(de)                      # reexecuta o import com a carga automática
            self.assertIsNotNone(de._erro_indisponivel)
            with self.assertRaises(de.ErroIndices):
                de.total_clientes()
            self.assertFalse(de.resumo_arvore_b()["disponivel"])
        finally:
            os.chdir(diretorio_atual)
            vazio.cleanup()
            importlib.reload(de)


# =============================================================================
# AVISOS DE ERRO (BLOQUEIOS)
# =============================================================================

class TestIndisponivel(BaseClientes):

    def preparar_arquivo_com_email_duplicado(self):
        clientes = self.clientes_json()
        clientes[5]["email"] = clientes[4]["email"]
        _gravar_json(self.tmp_clientes, clientes)
        de.inicializar(self.tmp_clientes, self.tmp_controle)      # não pode lançar

    def test_email_duplicado_no_arquivo_bloqueia_clientes_mas_nao_o_import(self):
        self.preparar_arquivo_com_email_duplicado()

        self.assertIsNotNone(de._erro_indisponivel)
        self.assertIn("duplicado", de._erro_indisponivel)

        consultas = [
            (de.buscar_cliente_por_id, (1001,)),
            (de.buscar_cliente_por_email, ("ines@ed2.com",)),
            (de.listar_clientes, ()),
            (de.total_clientes, ()),
            (de.proximo_id, ()),
        ]
        alteracoes = [
            (de.cadastrar_cliente, ({"nome": "A", "email": "a@a.com", "esim": "E"},)),
            (de.criar_conta, ({"nome": "A", "email": "a@a.com"},)),
            (de.editar_cliente, (1001, {})),
            (de.inativar_cliente, (1001,)),
            (de.reativar_cliente, (1001,)),
            (de.excluir_cliente_fisicamente, (1001, "EXCLUIR", True)),
            (de.contratar_plano, (1001, "102", [], "a", "b")),
        ]
        for funcao, args in consultas + alteracoes:
            with self.subTest(funcao=funcao.__name__):
                mensagem = self.erro_de(de.ErroIndices, funcao, *args)
                self.assertTrue(mensagem.startswith(MSG_INDISPONIVEL), mensagem)
                self.assertTrue(mensagem.endswith(f". {MSG_PAISES}"), mensagem)
                self.assertIn(de._erro_indisponivel, mensagem)

        self.assertEqual(de.normalizar_email("  A@B.com "), "a@b.com")      # continua funcionando

    def test_resumo_e_instrumentacao_funcionam_com_zeros_e_erro(self):
        self.preparar_arquivo_com_email_duplicado()

        resumo = de.resumo_arvore_b()
        self.assertIs(resumo["disponivel"], False)
        self.assertIn("erro", resumo)
        self.assertTrue(resumo["erro"].startswith(MSG_INDISPONIVEL))
        for campo in ("clientes", "altura", "nos", "divisoes"):
            self.assertEqual(resumo[campo], 0)
        self.assertEqual(resumo["media_nos_visitados"], 0.0)
        self.assertEqual(resumo["grau"], 3)

        for arvore, nome in (("id", "Árvore B de ID"), ("email", "Árvore B de e-mail"), ("qualquer", "Árvore B de ID")):
            instrumentacao = de.instrumentacao_arvore_b(arvore)
            self.assertIn("erro", instrumentacao)
            self.assertEqual(instrumentacao["nome"], nome)
            self.assertEqual(instrumentacao["ultima_busca"],
                             {"comparacoes": 0, "nos_visitados": 0, "tempo_us": 0.0})
            self.assertEqual(instrumentacao["acumulado"], {"comparacoes_totais": 0, "total_buscas": 0})
            self.assertEqual(instrumentacao["estado"]["total_chaves"], 0)
            self.assertIs(instrumentacao["simulado"], False)

    def test_arquivos_ausentes_ou_invalidos_tambem_viram_indisponivel(self):
        os.remove(self.tmp_controle)
        de.inicializar(self.tmp_clientes, self.tmp_controle)
        self.assertIn("não encontrado", de._erro_indisponivel)

        shutil.copy(RAIZ / "arquivos" / "controle_ids.json", self.tmp_controle)
        Path(self.tmp_clientes).write_text("{ isto não é json", encoding="utf-8")
        de.inicializar(self.tmp_clientes, self.tmp_controle)
        self.assertIn("JSON inválido", de._erro_indisponivel)

        _gravar_json(self.tmp_clientes, {"nao": "e lista"})
        de.inicializar(self.tmp_clientes, self.tmp_controle)
        self.assertIn("clientes.json não contém uma lista", de._erro_indisponivel)

    def test_controle_de_ids_inconsistente_deixa_indisponivel(self):
        _gravar_json(self.tmp_controle, {"proximo_id": 500, "ids_utilizados": list(range(1, 1002))})
        de.inicializar(self.tmp_clientes, self.tmp_controle)
        self.assertIsNotNone(de._erro_indisponivel)
        self.assertIn("controle", de._erro_indisponivel)

    def test_reiniciar_com_dados_corretos_restaura_o_servico(self):
        self.preparar_arquivo_com_email_duplicado()
        shutil.copy(RAIZ / "arquivos" / "clientes.json", self.tmp_clientes)
        de.inicializar(self.tmp_clientes, self.tmp_controle)

        self.assertIsNone(de._erro_indisponivel)
        self.assertEqual(de.total_clientes(), 1001)
        self.assertTrue(de.resumo_arvore_b()["disponivel"])


class TestFalhaDeGravacao(BaseClientes):

    MENSAGEM = ("Não foi possível gravar os dados de clientes. "
                "As alterações de clientes estão bloqueadas até a aplicação ser reiniciada.")

    def test_falha_ao_gravar_clientes_bloqueia_alteracoes_mas_nao_consultas(self):
        with mock.patch.object(persistencia_clientes, "salvar_clientes", side_effect=OSError("disco cheio")):
            self.assertEqual(self.erro_de(ValueError, de.inativar_cliente, 1001), self.MENSAGEM)

        # Nada mudou na memória, e o bloqueio continua mesmo sem o erro de disco.
        self.assertEqual(de.buscar_cliente_por_id(1001)[0]["status"], "ativo")
        self.assertEqual(self.clientes_json()[1000]["status"], "ativo")
        self.assertEqual(self.erro_de(ValueError, de.reativar_cliente, 1001), self.MENSAGEM)
        self.assertEqual(self.erro_de(ValueError, self.cadastrar_exemplo), self.MENSAGEM)
        self.assertEqual(self.erro_de(ValueError, de.editar_cliente, 1001, {}), self.MENSAGEM)
        self.assertEqual(self.erro_de(ValueError, de.excluir_cliente_fisicamente, 1001, "EXCLUIR", True),
                         self.MENSAGEM)
        self.assertEqual(self.erro_de(ValueError, de.contratar_plano, 1001, "102", [], "a", "b"), self.MENSAGEM)
        self.assertEqual(self.erro_de(ValueError, de.criar_conta, {"nome": "A", "email": "a@a.com"}),
                         self.MENSAGEM)

        # Consultas continuam.
        self.assertEqual(de.total_clientes(), 1001)
        self.assertIsNotNone(de.buscar_cliente_por_email("ines@ed2.com")[0])
        self.assertEqual(len(de.listar_clientes(status="todos")), 1001)
        self.assertEqual(de.proximo_id(), 1002)
        self.assertTrue(de.resumo_arvore_b()["disponivel"])
        self.assertNotIn("erro", de.instrumentacao_arvore_b("id"))

        # Só reiniciar libera.
        de.inicializar(self.tmp_clientes, self.tmp_controle)
        self.assertEqual(de.inativar_cliente(1001)["status"], "inativo")

    def test_falha_ao_gravar_o_controle_nao_toca_no_arquivo_de_clientes(self):
        antes = self.snapshot_arquivos()

        with mock.patch.object(persistencia_clientes, "salvar_controle_ids", side_effect=OSError("sem permissão")):
            self.assertEqual(self.erro_de(ValueError, self.cadastrar_exemplo), self.MENSAGEM)

        self.assertEqual(self.snapshot_arquivos(), antes)
        self.assertEqual(de.proximo_id(), 1002)
        self.assertEqual(de.total_clientes(), 1001)
        self.assertEqual(self.erro_de(ValueError, self.cadastrar_exemplo), self.MENSAGEM)

    def test_falha_ao_gravar_clientes_no_cadastro_nao_atualiza_as_arvores(self):
        with mock.patch.object(persistencia_clientes, "salvar_clientes", side_effect=OSError("disco cheio")):
            self.assertEqual(self.erro_de(ValueError, self.cadastrar_exemplo), self.MENSAGEM)

        # O controle já foi gravado primeiro (o ID 1002 fica consumido); o cliente não entrou.
        self.assertEqual(self.controle_json()["proximo_id"], 1003)
        self.assertEqual(de.proximo_id(), 1003)
        self.assertEqual(len(self.clientes_json()), 1001)
        self.assertEqual(de.total_clientes(), 1001)
        self.assertIsNone(de.buscar_cliente_por_id(1002)[0])
        self.assertFalse(de._arvore_email.contem("novo@teste.com"))


if __name__ == "__main__":
    unittest.main()
