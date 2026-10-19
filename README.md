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
- Bootstrap (arquivos locais em `static/bootstrap/`)
- Jinja
- JSON

---

## Etapa atual — Tabela Hash

Na primeira etapa, o sistema trabalha com os países que possuem cobertura de eSIM.

Cada país possui as seguintes informações:

- código;
- nome;
- região;
- operadora;
- tecnologia disponível.

O **código do país** é utilizado como chave para armazenamento e consulta na Tabela Hash.

### Funcionalidades da etapa

O sistema possui interface para:

- consultar cobertura por código do país;
- listar países cadastrados (ordenados por nome);
- cadastrar um novo país;
- visualizar os dados de um país;
- editar um país;
- excluir um país, com confirmação em modal;
- buscar países por nome ou código;
- filtrar países por região;
- paginar a listagem administrativa (5 países por página);
- acompanhar, no dashboard, os contadores e tempos das operações da Tabela Hash.

As operações que alteram dados (cadastro, edição e exclusão) usam `POST` e terminam em redirecionamento (padrão Post/Redirect/Get).

---

## Estado atual do desenvolvimento

A Tabela Hash da Etapa 01 (`estruturas/tabela_hash.py`) foi implementada como um **dicionário de dicionários**, conforme a orientação da professora:

- **chave:** código do país com 2 letras (ex.: `BR`), normalizado para maiúsculas;
- **valor:** dicionário com `nome`, `regiao`, `operadora` e `tecnologia`.

Operações disponíveis: `inserir`, `buscar`, `alterar`, `remover`, `listar` e `tam`.

Todas as rotas passam pelos métodos da classe `TabelaHash`. A lógica da estrutura fica separada das rotas Flask, e a leitura e gravação do JSON ficam em `arquivos/persistencia_paises.py`.

### Validações

As validações ficam na `TabelaHash`, e as telas de cadastro e edição exibem as mensagens de erro:

- código com exatamente 2 letras ASCII e sem repetição;
- nome e operadora obrigatórios;
- região: África, América, Ásia, Europa ou Oceania;
- tecnologia: 2G, 3G, 4G ou 5G.

As listas de regiões e tecnologias vêm da própria classe, então os formulários e a estrutura usam sempre as mesmas opções.

### Persistência

Os países ficam em `arquivos/paises.json` e são carregados na `TabelaHash` quando o servidor inicia. Cadastro, edição e exclusão gravam o arquivo imediatamente.

O arquivo precisa existir e conter um JSON válido: se ele estiver ausente, o servidor não inicia.

### Tratamento de erros e avisos

- consulta de cobertura com código inexistente exibe um aviso;
- visualizar, editar ou excluir um país inexistente volta à listagem com mensagem de erro;
- cadastro, edição e exclusão bem-sucedidos exibem mensagem de confirmação.

### Instrumentação

A `TabelaHash` registra o próprio uso por meio do decorador `_medir`, aplicado a `inserir`, `buscar`, `alterar`, `remover` e `listar`. Para cada operação são guardados:

- número de chamadas;
- sucessos e falhas (falha: inserção, alteração ou remoção recusada pelas validações, ou busca sem resultado);
- tempo médio e tempo máximo, medidos com `time.perf_counter_ns()`;
- as 8 operações mais recentes, com código, resultado e duração.

Os dados aparecem no card **Instrumentação da Tabela Hash** do dashboard (`/admin`) e podem ser lidos por `tabela_paises.metricas()`.

Observações:

- a carga inicial do `paises.json` não é contada como uso;
- os contadores ficam em memória e voltam a zero quando o servidor é reiniciado;
- como a estrutura é um dicionário de dicionários, não há índices, buckets nem colisões a exibir: as métricas descrevem o uso da estrutura, não seu funcionamento interno;
- os tempos incluem o custo da própria medição, e as buscas feitas pelas rotas de visualização e edição também são contadas.

### Pendências da Etapa 01

- **Descrição inicial do diferencial:** exigida na entrega, ainda não registrada neste repositório. O diferencial precisa ser aprovado pela professora (ver seção "Diferencial do projeto").

---

## Perfis de acesso

O sistema considera dois tipos de utilização:

### Usuário

O usuário comum acessa funcionalidades de consulta, como:

- página inicial;
- consulta de cobertura por país.

O acesso de clientes pela tela de login ainda não está disponível nesta etapa.

### Administrador

O administrador possui acesso às funcionalidades de gerenciamento, incluindo:

- dashboard administrativo;
- listagem de países;
- cadastro de países;
- visualização de país;
- edição de país;
- exclusão de país.

### Limitações conhecidas

- O login valida usuário e senha, mas não cria sessão: as rotas `/admin` não são protegidas e podem ser acessadas diretamente pela URL, e o botão "Sair" apenas leva de volta ao login.
- As credenciais de teste ficam em `dados_site/dados_usuario.py`, em texto simples.
- A `secret_key` do Flask está fixa no código. Fora do contexto acadêmico, ela seria lida de uma variável de ambiente.
- O conteúdo da página inicial (carrossel, benefícios, planos e depoimentos) vem de dados estáticos em `dados_site/dados_inicio.py`.
- A busca administrativa diferencia acentos: pesquisar "mexico" não encontra "México".

Essas soluções são simplificadas de propósito, pois o foco acadêmico do projeto está nas estruturas de dados.

---

## Estrutura atual do projeto

```text
trabalho-estrutura-dados-2/
│
├── app.py
├── README.md
├── LICENSE
├── .gitignore
│
├── estruturas/
│   ├── __init__.py
│   └── tabela_hash.py
│
├── arquivos/
│   ├── __init__.py
│   ├── persistencia_paises.py
│   └── paises.json
│
├── dados_site/
│   ├── __init__.py
│   ├── dados_inicio.py
│   └── dados_usuario.py
│
├── documentos/
│   ├── TrabalhoPratico-2026.2.pdf
│   ├── Diario_Alteracoes.txt
│   └── comandos.txt
│
├── static/
│   ├── bootstrap/        (css, icons e js do Bootstrap)
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── img/              (admin, carousel, cobertura, depoimentos,
│                          login, logo e planos)
│
└── templates/
    ├── base.html
    ├── inicio.html
    ├── login.html
    ├── paises.html
    │
    └── admin/
        ├── base_admin.html
        ├── dashboard.html
        ├── paises.html
        ├── cadastrar_pais.html
        ├── editar_pais.html
        └── visualizar_pais.html
```

A estrutura poderá sofrer alterações durante a implementação das estruturas de dados previstas nas próximas etapas.

---

## Estrutura planejada

Com a evolução do projeto, as demais estruturas de dados também ficarão separadas da camada Web. Ainda serão adicionados:

```text
estruturas/
├── arvore_b.py
└── grafo.py

arquivos/
├── usuarios.json
├── clientes.json
├── pacotes.json
├── rede.json
└── historico_consultas.json
```

Essa separação permite que o Flask funcione principalmente como interface, enquanto as operações principais são executadas pelas estruturas de dados desenvolvidas pela equipe.

---

## Evolução do projeto

### Etapa 01 — Tabela Hash

Responsável pelo armazenamento e gerenciamento dos países com cobertura.

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

O trabalho exige que cada equipe proponha pelo menos um diferencial funcional ou algorítmico, submetido à aprovação da professora.

A proposta atual é o **roteamento utilizando diferentes critérios**, permitindo comparar rotas da rede internacional de acordo com pesos distintos.

Entre os critérios planejados estão:

- menor latência;
- menor custo operacional simulado.

Também está previsto o registro de um **histórico de consultas**, permitindo acompanhar as operações realizadas no sistema.

> **Situação:** proposta ainda não aprovada formalmente pela professora. A descrição inicial e a forma de integração ao projeto devem ser registradas para a entrega da Etapa 01.

---

## Como executar o projeto

Testado com Python 3.12 e Flask 3.1.

### 1. Clone o repositório

```bash
git clone https://github.com/DKMariano/trabalho-estrutura-dados-2.git
```

### 2. Entre na pasta do projeto

```bash
cd trabalho-estrutura-dados-2
```

### 3. Instale o Flask

```bash
pip install flask
```

### 4. Execute a aplicação

```bash
python -m flask --app app run --debug
```

Executar `python app.py` não inicia o servidor, pois o arquivo não define o ponto de entrada `if __name__ == "__main__"`.

### 5. Acesse pelo navegador

Utilize o endereço exibido pelo Flask no terminal, normalmente:

```text
http://127.0.0.1:5000
```

### Acesso administrativo

Use a opção de administrador na tela `/login`. As credenciais de teste estão em `dados_site/dados_usuario.py`.

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
- [x] Implementação da Tabela Hash (dicionário de dicionários)
- [x] Integração das operações com a Tabela Hash
- [x] Persistência dos países em JSON
- [x] Validações e mensagens de erro nos formulários
- [x] Testes das rotas e das validações
- [x] Instrumentação básica da estrutura (contadores e tempos no dashboard)
- [ ] Descrição inicial do diferencial

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

**Integrantes:** Bruno Barreto, Dimitrius Khouri e Guilherme Lopes
**Professora:** Inês Valderrama Restovic

**Instituição:** Universidade do Estado da Bahia — UNEB  
**Curso:** Bacharelado em Sistemas de Informação

---

## Licença

Distribuído sob a licença MIT. Veja o arquivo `LICENSE`.

Projeto desenvolvido para fins acadêmicos.