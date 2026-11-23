"""
Testes de integração pelo Flask (app.test_client()) — Guia B10 e Bloco 5.

O backend de clientes é apontado para cópias temporárias dos JSON antes de
cada teste. Nenhuma rota que grava países ou o histórico (Etapa 1 e Etapa 3)
é chamada com POST. Os JSON reais são conferidos por hash no final.
"""

import json
import unittest

from app import app
from servicos import clientes as backend
from testes import apoio

HASHES_ANTES = None

# Rotas GET da linha de base da auditoria (Fase 02)
ROTAS_GET = [
    "/", "/paises", "/planos", "/login", "/criar-conta", "/adquirir/101",
    "/admin", "/admin/paises", "/admin/paises/IT", "/admin/paises/IT/editar",
    "/admin/paises/cadastrar", "/admin/tabela-hash",
    "/admin/clientes", "/admin/clientes?status=todos", "/admin/clientes?busca=1001",
    "/admin/clientes?busca=beatriz.barbosa1002@example.com", "/admin/clientes?busca=Barbosa",
    "/admin/clientes?status=inativo&pacote=sem&pagina=3&por_pagina=20",
    "/admin/clientes/cadastrar", "/admin/clientes/1001", "/admin/clientes/1001/editar",
    "/admin/clientes/2", "/admin/arvore-b", "/admin/arvore-b?chave=1001",
    "/admin/arvore-b?indice=email&chave=ines@ed2.com", "/admin/consulta",
    "/admin/consulta?cliente=1001&destino=IT", "/admin/consulta?cliente=ines@ed2.com&destino=JP",
    "/admin/rede", "/admin/grafo", "/cliente/1001", "/cliente/1001/minha-conta",
    "/cliente/1001/contratar", "/cliente/1001/contratar?destino=Itália",
    "/cliente/1001/minha-conectividade", "/cliente/2",
]


def setUpModule():
    global HASHES_ANTES
    HASHES_ANTES = apoio.hashes_reais()
    app.config["TESTING"] = True


def tearDownModule():
    backend.inicializar()
    assert apoio.hashes_reais() == HASHES_ANTES, "Um JSON real foi alterado pelos testes!"


class BaseIntegracao(unittest.TestCase):

    def setUp(self):
        self.pasta, self.arq_clientes, self.arq_controle = apoio.copiar_para_temporario()
        self.assertTrue(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))
        self.cliente = app.test_client()

    def tearDown(self):
        backend.inicializar()
        apoio.apagar(self.pasta)

    def html(self, resposta):
        return resposta.get_data(as_text=True)

    def lista_gravada(self):
        return json.loads(self.arq_clientes.read_text(encoding="utf-8"))


class TesteRotas(BaseIntegracao):

    def test_todas_as_rotas_get(self):
        for rota in ROTAS_GET:
            with self.subTest(rota=rota):
                self.assertEqual(self.cliente.get(rota).status_code, 200)

    def test_cliente_inexistente_e_inativo(self):
        resposta = self.cliente.get("/admin/clientes/999999")
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.headers["Location"].endswith("/admin/clientes"))

        resposta = self.cliente.get("/cliente/1")    # cliente 1 é inativo
        self.assertIn("Seu cadastro está inativo", self.html(resposta))


class TesteLoginEBuscas(BaseIntegracao):

    def test_login_com_cliente_do_json(self):
        resposta = self.cliente.post("/login", data={
            "tipo_acesso": "cliente", "usuario": "beatriz.barbosa1002@example.com", "senha": "123456"})
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.headers["Location"].endswith("/cliente/2"))

    def test_login_de_inativo_e_senha_errada(self):
        resposta = self.cliente.post("/login", data={
            "tipo_acesso": "cliente", "usuario": "nicolas.cardoso1001@example.com", "senha": "123456"})
        self.assertIn("Seu cadastro está inativo", self.html(resposta))

        resposta = self.cliente.post("/login", data={
            "tipo_acesso": "cliente", "usuario": "ines@ed2.com", "senha": "errada"})
        self.assertIn("E-mail ou senha incorretos.", self.html(resposta))

    def test_pagina_arvore_b_com_metricas_reais(self):
        html = self.html(self.cliente.get("/admin/arvore-b?chave=1001"))
        self.assertIn("posição 1000", html)
        self.assertIn("Ines", html)
        self.assertIn("número de níveis", html)
        self.assertIn("grau mínimo 3", html)

        metricas = backend.instrumentacao_arvore_b("id")
        self.assertFalse(metricas["simulado"])
        self.assertEqual(metricas["acumulado"]["total_buscas"], 1)
        self.assertGreater(metricas["ultima_busca"]["comparacoes"], 0)
        self.assertEqual(backend.instrumentacao_arvore_b("email")["acumulado"]["total_buscas"], 0)

        html = self.html(self.cliente.get("/admin/arvore-b?indice=email&chave=INES@ed2.com"))
        self.assertIn("posição 1000", html)
        self.assertEqual(backend.instrumentacao_arvore_b("email")["acumulado"]["total_buscas"], 1)

    def test_dashboard_com_resumo_real(self):
        html = self.html(self.cliente.get("/admin"))
        self.assertIn("Clientes indexados", html)
        self.assertIn("1.001", html)
        self.assertNotIn("a Árvore B ainda não foi", html,
                         "Pendência N5: texto fixo obsoleto em templates/admin/dashboard.html")

    def test_consulta_integrada_cliente_x_pais(self):
        html = self.html(self.cliente.get("/admin/consulta"))   # padrão: 1001 x IT
        self.assertIn('value="1001"', html)
        self.assertIn("Ines", html)
        self.assertIn("Itália", html)
        self.assertIn("Árvore B de ID", html)
        self.assertIn("buscar(1001)", html)
        self.assertNotIn("A busca de clientes é simulada", html,
                         "Pendência P7: texto fixo obsoleto em templates/admin/consulta.html")

        html = self.html(self.cliente.get("/admin/consulta?cliente=beatriz.barbosa1002@example.com&destino=BR"))
        self.assertIn("Árvore B de e-mail", html)


class TesteOperacoesCadastrais(BaseIntegracao):

    def test_cadastro_administrativo_com_pacote_basic(self):
        resposta = self.cliente.post("/admin/clientes/cadastrar", data={
            "nome": "Cliente Integração", "email": "integracao@example.com",
            "esim": "ESIM-INT", "status": "ativo", "pacote": "101",
            "paises": ["IT", "PT", "ES"],
        })
        self.assertEqual(resposta.status_code, 302)

        novo = self.lista_gravada()[1001]
        self.assertEqual(novo["id"], 1002)
        self.assertEqual(novo["pacote"], 101)
        self.assertEqual(novo["paises_ativos"], ["IT", "PT", "ES"])
        self.assertEqual(backend.buscar_cliente_por_email("integracao@example.com")[1]["posicao"], 1001)

    def test_cadastro_basic_com_pais_fora_da_regiao_nao_grava(self):
        antes = self.arq_clientes.read_bytes()
        resposta = self.cliente.post("/admin/clientes/cadastrar", data={
            "nome": "X", "email": "x@example.com", "esim": "E", "status": "ativo",
            "pacote": "101", "paises": ["IT", "PT", "BR"],
        }, follow_redirects=True)
        self.assertIn("não pertence à região", self.html(resposta))
        self.assertEqual(self.arq_clientes.read_bytes(), antes)

    def test_criar_conta_publica(self):
        resposta = self.cliente.post("/criar-conta", data={"nome": "Pública", "email": "pub@example.com"})
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("criado=1002", resposta.headers["Location"])
        self.assertEqual(self.lista_gravada()[1001]["esim"], "ESIM-1002")

    def test_editar_inativar_e_excluir(self):
        resposta = self.cliente.post("/admin/clientes/2/editar", data={
            "nome": "Nome Editado", "esim": "ESIM-ED", "status": "ativo"})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.lista_gravada()[1]["nome"], "Nome Editado")
        self.assertEqual(self.lista_gravada()[1]["email"], "beatriz.barbosa1002@example.com")

        # Cliente ativo não pode ser excluído
        resposta = self.cliente.post("/admin/clientes/2/excluir",
                                     data={"confirmacao": "2", "ciencia": "sim"}, follow_redirects=True)
        self.assertIn("Somente clientes inativos", self.html(resposta))

        self.cliente.post("/admin/clientes/2/inativar")
        self.assertEqual(self.lista_gravada()[1]["status"], "inativo")

        resposta = self.cliente.post("/admin/clientes/2/excluir",
                                     data={"confirmacao": "EXCLUIR", "ciencia": "sim", "voltar": "lista"},
                                     follow_redirects=True)
        self.assertIn("Cliente 2 excluído permanentemente.", self.html(resposta))
        self.assertIsNone(self.lista_gravada()[1])
        self.assertEqual(self.cliente.get("/admin/clientes/2").status_code, 302)
        self.assertEqual(backend.instrumentacao_arvore_b("id")["estado"]["ultima_operacao"], "reconstrucao")

    def test_contratacao_pela_area_do_cliente(self):
        resposta = self.cliente.post("/cliente/2/contratar", data={"plano": "102", "confirmado": "sim"})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.lista_gravada()[1]["pacote"], 102)


class TesteIndisponivel(BaseIntegracao):

    def setUp(self):
        super().setUp()
        lista = self.lista_gravada()
        lista[1]["email"] = lista[0]["email"]       # e-mail repetido no arquivo
        self.arq_clientes.write_text(json.dumps(lista), encoding="utf-8")
        self.assertFalse(apoio.inicializar(backend, self.arq_clientes, self.arq_controle))

    def test_clientes_bloqueados_e_etapa_1_disponivel(self):
        resposta = self.cliente.get("/admin/clientes")
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.headers["Location"].endswith("/admin"))

        html = self.html(self.cliente.get("/admin/clientes", follow_redirects=True))
        self.assertIn("Os dados de clientes estão indisponíveis", html)
        self.assertIn("As funcionalidades de países continuam disponíveis", html)

        for rota in ("/", "/paises", "/planos", "/admin/paises", "/admin/paises/IT",
                     "/admin/tabela-hash", "/admin", "/admin/arvore-b"):
            with self.subTest(rota=rota):
                self.assertEqual(self.cliente.get(rota).status_code, 200)


if __name__ == "__main__":
    unittest.main()
