"""
DGB SIM — Etapa 2 — Testes de integração Flask (app.py + dados_etapa02.py).

Execução, a partir da raiz do projeto:

    python -m unittest discover -s testes -t ..

Isolamento: cada teste trabalha em CÓPIAS de arquivos/clientes.json e
arquivos/controle_ids.json dentro de um diretório temporário
(dados_etapa02.inicializar(tmp_clientes, tmp_controle) no setUp e
dados_etapa02.inicializar() no tearDown). Os arquivos reais nunca são
alterados: setUpModule/tearDownModule conferem isso, inclusive para
arquivos/historico.json.
"""

import hashlib
import importlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import app as modulo_app
from dados_site import dados_etapa02

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVOS_REAIS = [
    RAIZ / "arquivos" / "clientes.json",
    RAIZ / "arquivos" / "controle_ids.json",
    RAIZ / "arquivos" / "historico.json",
]

MSG_INATIVO = "Seu cadastro está inativo. Procure a administração da DGB SIM."
MSG_INDISPONIVEL = "Os dados de clientes estão indisponíveis: "
MSG_PAISES = "As funcionalidades de países continuam disponíveis."


def _hash(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest() if caminho.exists() else None


_HASHES_ANTES = {}


def setUpModule():
    _HASHES_ANTES.update({caminho: _hash(caminho) for caminho in ARQUIVOS_REAIS})

    # teste_clientes.py recarrega dados_etapa02 (importlib.reload), o que cria uma
    # NOVA classe ErroIndices; um app importado antes disso ficaria com o
    # @app.errorhandler ligado à classe antiga. Recarregar o app equivale a uma
    # importação nova (como no servidor) e liga o tratador à classe atual.
    importlib.reload(modulo_app)


def tearDownModule():
    for caminho, antes in _HASHES_ANTES.items():
        assert _hash(caminho) == antes, f"{caminho.name} (arquivo real) foi alterado pelos testes"


class BaseIntegracao(unittest.TestCase):
    """Cópias temporárias dos arquivos + cliente de teste do Flask."""

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.tmp_clientes = os.path.join(self.pasta.name, "clientes.json")
        self.tmp_controle = os.path.join(self.pasta.name, "controle_ids.json")
        shutil.copy(RAIZ / "arquivos" / "clientes.json", self.tmp_clientes)
        shutil.copy(RAIZ / "arquivos" / "controle_ids.json", self.tmp_controle)

        dados_etapa02.inicializar(self.tmp_clientes, self.tmp_controle)

        modulo_app.app.config.update(TESTING=True)
        self.client = modulo_app.app.test_client()

    def tearDown(self):
        dados_etapa02.inicializar()   # volta aos caminhos reais (somente leitura)
        self.pasta.cleanup()

    # -- auxiliares -----------------------------------------------------------

    def ler_clientes(self):
        with open(self.tmp_clientes, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def gravar_clientes(self, clientes):
        with open(self.tmp_clientes, "w", encoding="utf-8") as arquivo:
            json.dump(clientes, arquivo, ensure_ascii=False, indent=2)

    def primeiro_inativo(self):
        return next(c for c in self.ler_clientes() if c and c["status"] == "inativo")

    @staticmethod
    def texto(resposta):
        return resposta.get_data(as_text=True)


class TestLoginCliente(BaseIntegracao):

    def test_cliente_ativo_e_redirecionado_para_o_painel(self):
        resposta = self.client.post("/login", data={
            "tipo_acesso": "cliente",
            "usuario": "cliente1002@example.com",
            "senha": "123456",
        })

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.headers["Location"].endswith("/cliente/2"))

        painel = self.client.get("/cliente/2")
        self.assertEqual(painel.status_code, 200)
        self.assertNotIn(MSG_INATIVO, self.texto(painel))

    def test_login_com_senha_errada_nao_libera(self):
        resposta = self.client.post("/login", data={
            "tipo_acesso": "cliente",
            "usuario": "cliente1002@example.com",
            "senha": "senha-errada",
        })

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("E-mail ou senha incorretos.", self.texto(resposta))


class TestClienteInativo(BaseIntegracao):

    def test_login_de_cliente_inativo_e_bloqueado(self):
        inativo = self.primeiro_inativo()

        resposta = self.client.post("/login", data={
            "tipo_acesso": "cliente",
            "usuario": inativo["email"],
            "senha": inativo["senha"],
        })

        self.assertEqual(resposta.status_code, 200)   # não redireciona
        self.assertIn(MSG_INATIVO, self.texto(resposta))

    def test_acesso_direto_pela_url_de_cliente_inativo_e_bloqueado(self):
        inativo = self.primeiro_inativo()

        resposta = self.client.get(f"/cliente/{inativo['id']}")

        self.assertEqual(resposta.status_code, 200)
        html = self.texto(resposta)
        self.assertIn(MSG_INATIVO, html)
        self.assertIn("Acesso bloqueado", html)


class TestPaginaArvoreB(BaseIntegracao):

    def test_busca_por_id_mostra_posicao_e_metricas_reais(self):
        resposta = self.client.get("/admin/arvore-b?chave=1001")

        self.assertEqual(resposta.status_code, 200)
        html = self.texto(resposta)
        self.assertIn("posição 1000", html)           # Ines é o último registro
        self.assertIn("ines@ed2.com", html)
        self.assertIn("encontrada", html)

        # As métricas vêm da árvore real, não de números fixos de demonstração.
        _, instrumentacao = dados_etapa02.buscar_cliente_por_id(1001)
        self.assertFalse(instrumentacao["simulado"])
        self.assertEqual(instrumentacao["posicao"], 1000)
        self.assertGreaterEqual(instrumentacao["comparacoes"], 1)
        self.assertGreaterEqual(instrumentacao["nos_visitados"], 1)

        metricas = dados_etapa02.instrumentacao_arvore_b("id")
        self.assertFalse(metricas["simulado"])
        self.assertEqual(metricas["estado"]["total_chaves"], len(self.ler_clientes()))

    def test_busca_por_email_mostra_a_mesma_posicao(self):
        resposta = self.client.get("/admin/arvore-b?indice=email&chave=ines@ed2.com")

        self.assertEqual(resposta.status_code, 200)
        html = self.texto(resposta)
        self.assertIn("posição 1000", html)
        self.assertIn("encontrada", html)

    def test_chave_inexistente_nao_le_registro(self):
        resposta = self.client.get("/admin/arvore-b?chave=999999")

        self.assertEqual(resposta.status_code, 200)
        html = self.texto(resposta)
        self.assertIn("não encontrada", html)
        self.assertNotIn("Registro lido no arquivo", html)

    def test_rotulo_da_altura_conta_niveis(self):
        html = self.texto(self.client.get("/admin/arvore-b"))

        self.assertIn("Altura atual da árvore (número de níveis)", html)
        self.assertNotIn("raiz no nível 0", html)


class TestEdicaoDeCliente(BaseIntegracao):

    def test_campo_de_email_e_somente_leitura_e_nao_desabilitado(self):
        html = self.texto(self.client.get("/admin/clientes/2/editar"))

        inicio = html.index('id="email"')
        tag = html[html.rfind("<input", 0, inicio):html.index(">", inicio)]
        self.assertIn("readonly", tag)
        self.assertNotIn("disabled", tag)   # disabled não seria enviado no POST

    def test_email_enviado_no_post_nao_altera_o_cadastro(self):
        antes = dados_etapa02.buscar_cliente_por_id(2)[0]

        resposta = self.client.post("/admin/clientes/2/editar", data={
            "nome": "Nome Alterado",
            "email": "outro@example.com",
            "esim": antes["esim"],
            "status": "ativo",
        })

        self.assertEqual(resposta.status_code, 302)
        depois = dados_etapa02.buscar_cliente_por_id(2)[0]
        self.assertEqual(depois["nome"], "Nome Alterado")
        self.assertEqual(depois["email"], antes["email"])
        self.assertIsNone(dados_etapa02.buscar_cliente_por_email("outro@example.com")[0])
        self.assertEqual(self.ler_clientes()[1]["email"], antes["email"])


class TestErroIndicesNaWeb(BaseIntegracao):

    def corromper_com_email_duplicado(self):
        clientes = self.ler_clientes()
        clientes[5]["email"] = clientes[4]["email"]
        self.gravar_clientes(clientes)
        dados_etapa02.inicializar(self.tmp_clientes, self.tmp_controle)

    def test_rota_de_clientes_redireciona_para_admin_com_aviso(self):
        self.corromper_com_email_duplicado()

        resposta = self.client.get("/admin/clientes")

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.headers["Location"].endswith("/admin"))

        pagina = self.client.get(resposta.headers["Location"])
        self.assertEqual(pagina.status_code, 200)
        html = self.texto(pagina)
        self.assertIn(MSG_INDISPONIVEL, html)
        self.assertIn("duplicado", html)
        self.assertIn(MSG_PAISES, html)

    def test_aviso_aparece_ao_seguir_o_redirecionamento(self):
        self.corromper_com_email_duplicado()

        resposta = self.client.get("/admin/clientes", follow_redirects=True)

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(MSG_INDISPONIVEL, self.texto(resposta))

    def test_login_de_cliente_tambem_cai_no_tratador(self):
        self.corromper_com_email_duplicado()

        resposta = self.client.post("/login", data={
            "tipo_acesso": "cliente",
            "usuario": "cliente1002@example.com",
            "senha": "123456",
        })

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.headers["Location"].endswith("/admin"))

    def test_json_ilegivel_tambem_aciona_o_tratador(self):
        with open(self.tmp_clientes, "w", encoding="utf-8") as arquivo:
            arquivo.write("{ isto nao e json")
        dados_etapa02.inicializar(self.tmp_clientes, self.tmp_controle)

        resposta = self.client.get("/admin/clientes", follow_redirects=True)

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(MSG_INDISPONIVEL, self.texto(resposta))

    def test_rotas_da_etapa_1_continuam_funcionando(self):
        self.corromper_com_email_duplicado()

        for rota in ("/paises", "/admin/paises", "/admin/tabela-hash"):
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(rota).status_code, 200)

        resposta = self.client.post("/paises", data={"destino": "IT"})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Itália", self.texto(resposta))


class TestRotasCorrigidas(BaseIntegracao):

    def test_admin_rede_responde_sem_erro_500(self):
        resposta = self.client.get("/admin/rede")

        self.assertEqual(resposta.status_code, 200)

    def test_consulta_integrada_usa_cliente_1001_por_padrao(self):
        resposta = self.client.get("/admin/consulta")

        self.assertEqual(resposta.status_code, 200)
        html = self.texto(resposta)
        self.assertIn('value="1001"', html)
        self.assertNotIn('value="58372"', html)


if __name__ == "__main__":
    unittest.main()
