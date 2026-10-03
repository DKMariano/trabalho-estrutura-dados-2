# DGB SIM

Sistema Web desenvolvido como trabalho prático da disciplina de **Estruturas de Dados II**, utilizando **Python, Flask, HTML, CSS, Bootstrap e Jinja**.

O projeto simula uma plataforma de uma empresa fictícia de **eSIM para internet móvel internacional**, permitindo consultar a cobertura disponível em diferentes países e, progressivamente, aplicar estruturas de dados estudadas na disciplina.

---

## Sobre o projeto

O **DGB SIM** tem como objetivo aplicar, de forma prática, os conteúdos estudados em Estruturas de Dados II por meio de uma aplicação Web.

O desenvolvimento do sistema é dividido em etapas. Cada etapa introduz uma nova estrutura de dados e amplia as funcionalidades da aplicação:

- **Etapa 01:** Tabela Hash para gerenciamento dos países com cobertura;
- **Etapa 02:** Árvore B para gerenciamento de clientes e eSIMs;
- **Etapa 03:** Grafos para representação da rede internacional e cálculo de rotas.

As estruturas de dados são o foco principal do projeto. O Flask é utilizado como interface Web para permitir a interação com essas estruturas.

---

## Tecnologias utilizadas

- Python
- Flask
- HTML5
- CSS3
- Bootstrap
- Jinja
- JavaScript
- JSON

---

## Etapa atual — Tabela Hash

Na primeira etapa, o sistema trabalha com os países que possuem cobertura de eSIM.

Cada país possui informações como:

- código;
- nome;
- região;
- operadora;
- tecnologia disponível.

O **código do país** será utilizado como chave para armazenamento e consulta na Tabela Hash.

### Funcionalidades da etapa

O sistema possui interface para:

- consultar cobertura por código do país;
- listar países cadastrados;
- cadastrar um novo país;
- visualizar os dados de um país;
- editar um país;
- excluir um país;
- buscar países por nome ou código;
- filtrar países por região;
- visualizar informações relacionadas ao funcionamento da Tabela Hash.

---

## Estado atual do desenvolvimento

O projeto encontra-se em desenvolvimento.

Neste momento, o MVP utiliza **dicionários Python temporariamente** para armazenar os países e permitir o desenvolvimento e a validação das telas e dos fluxos da aplicação.

Essa implementação será substituída pela **Tabela Hash desenvolvida pela equipe**, conforme os requisitos da disciplina.

A arquitetura foi organizada de forma que essa substituição possa ser realizada preservando, sempre que possível, as rotas e as interfaces já desenvolvidas.

Também será implementada a persistência dos dados dos países em arquivo **JSON**.

---

## Perfis de acesso

O sistema considera dois tipos de utilização:

### Usuário

O usuário comum poderá acessar funcionalidades de consulta, como:

- página inicial;
- consulta de cobertura por país.

### Administrador

O administrador possui acesso às funcionalidades de gerenciamento, incluindo:

- dashboard administrativo;
- listagem de países;
- cadastro de países;
- visualização de país;
- edição de país;
- exclusão de país;
- painel relacionado à Tabela Hash.

A implementação de controle de acesso é mantida simples, pois o foco acadêmico do projeto está nas estruturas de dados.

---

## Estrutura atual do projeto

```text
dgb_sim/
│
├── app.py
│
├── dados_site/
│   ├── __init__.py
│   ├── dados_inicio.py
│   ├── dados_paises.py
│   └── dados_usuario.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── main.js
│   │
│   └── img/
│
├── templates/
│   ├── base.html
│   ├── inicio.html
│   ├── login.html
│   ├── paises.html
│   │
│   └── admin/
│       ├── base_admin.html
│       ├── dashboard.html
│       ├── paises.html
│       ├── cadastrar_pais.html
│       ├── editar_pais.html
│       ├── visualizar_pais.html
│       └── tabela_hash.html
│
└── README.md
```

A estrutura poderá sofrer alterações durante a implementação das estruturas de dados previstas nas próximas etapas.

---

## Estrutura planejada

Com a evolução do projeto, as estruturas de dados serão separadas da camada Web.

A organização prevista inclui:

```text
dgb_sim/
│
├── app.py
│
├── estruturas/
│   ├── tabela_hash.py
│   ├── arvore_b.py
│   └── grafo.py
│
├── arquivos/
│   ├── usuarios.json
│   ├── paises.json
│   ├── clientes.json
│   ├── pacotes.json
│   ├── rede.json
│   └── historico_consultas.json
│
├── templates/
│
└── static/
```

Essa separação permitirá que o Flask funcione principalmente como interface, enquanto as operações principais serão executadas pelas estruturas de dados desenvolvidas pela equipe.

---

## Evolução do projeto

### Etapa 01 — Tabela Hash

Responsável pelo armazenamento e gerenciamento dos países com cobertura.

Operações principais:

```text
Código do país
      ↓
Tabela Hash
      ↓
Dados de cobertura
```

### Etapa 02 — Árvore B

A segunda etapa adicionará o gerenciamento de clientes e eSIMs utilizando uma **Árvore B**.

Fluxo previsto:

```text
Cliente
   ↓
Árvore B
   ↓
Destino
   ↓
Tabela Hash
   ↓
Cobertura
```

### Etapa 03 — Grafos

Na etapa final, a rede internacional será representada por meio de **grafos**, permitindo analisar conexões entre localidades e calcular rotas.

O sistema deverá utilizar algoritmos estudados na disciplina, incluindo:

- BFS;
- DFS;
- Dijkstra.

Fluxo geral previsto:

```text
Cliente
   ↓
Árvore B
   ↓
Destino
   ↓
Tabela Hash
   ↓
Pacote / conexão
   ↓
Grafo
   ↓
Dijkstra
   ↓
Rota
```

---

## Diferencial do projeto

Como diferencial, o projeto prevê a implementação de **roteamento utilizando diferentes critérios**, permitindo comparar rotas da rede internacional de acordo com pesos distintos.

Entre os critérios planejados estão:

- menor latência;
- menor custo operacional simulado.

Também está previsto o registro de um **histórico de consultas**, permitindo acompanhar as operações realizadas no sistema.

O diferencial será integrado progressivamente conforme o desenvolvimento das etapas do projeto.

---

## Como executar o projeto

### 1. Clone o repositório

```bash
git clone URL_DO_REPOSITORIO
```

### 2. Entre na pasta do projeto

```bash
cd dgb_sim
```

### 3. Instale o Flask

```bash
pip install flask
```

### 4. Execute a aplicação

```bash
python app.py
```

### 5. Acesse pelo navegador

Utilize o endereço exibido pelo Flask no terminal, normalmente:

```text
http://127.0.0.1:5000
```

---

## Observação acadêmica

Este projeto foi desenvolvido para fins acadêmicos na disciplina de **Estruturas de Dados II**.

A aplicação Web tem como principal objetivo fornecer uma interface para demonstrar o funcionamento das estruturas de dados implementadas ao longo do trabalho.

Por esse motivo, algumas soluções relacionadas à autenticação, persistência e arquitetura Web são propositalmente mantidas simples, priorizando a compreensão e a aplicação das estruturas de dados estudadas.

---

## Status do projeto

🚧 **Em desenvolvimento**

### Etapa 01

- [x] Interface Web inicial
- [x] Página de consulta de cobertura
- [x] Listagem de países
- [x] Cadastro de país
- [x] Visualização de país
- [x] Edição de país
- [x] Exclusão de país
- [x] Busca por país
- [x] Filtro por região
- [x] Interface de visualização da Tabela Hash
- [ ] Implementação da Tabela Hash
- [ ] Integração das operações com a Tabela Hash
- [ ] Persistência dos países em JSON
- [ ] Instrumentação utilizando dados reais da Tabela Hash
- [ ] Testes e validação final da Etapa 01

### Próximas etapas

- [ ] Implementação da Árvore B
- [ ] Gerenciamento de clientes e eSIMs
- [ ] Implementação do grafo
- [ ] BFS e DFS
- [ ] Roteamento com Dijkstra
- [ ] Integração das estruturas
- [ ] Implementação completa do diferencial
- [ ] Documentação final

---

## Equipe

Projeto desenvolvido por estudantes da disciplina de **Estruturas de Dados II**.

**Instituição:** Universidade do Estado da Bahia — UNEB  
**Curso:** Bacharelado em Sistemas de Informação

---

## Licença

Projeto desenvolvido exclusivamente para fins acadêmicos.