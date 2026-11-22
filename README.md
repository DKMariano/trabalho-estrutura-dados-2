# DGB SIM

**Etapa 01 — Tabela Hash e Aplicação Web** (entrega prevista: 20/10/2026)  
**Etapa 02 — Árvore B e clientes** (entrega prevista: 24/11/2026) — Árvores B de ID e de e-mail integradas ao Flask, com testes de integração.

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

O `dict` fornece o mecanismo nativo de hashing e gerencia as colisões internamente. A equipe implementa a classe, suas operações, validações e instrumentação; não há função hash ou tratamento manual de colisões. A busca pública consulta diretamente a chave; a busca administrativa por trecho de nome ou código percorre a listagem.

As rotas de gerenciamento e consulta de países utilizam os métodos da classe `TabelaHash`. A lógica da estrutura fica separada das rotas Flask, e a leitura e gravação do JSON ficam em `arquivos/persistencia_paises.py`.

### Validações

As validações ficam na `TabelaHash`, e as telas de cadastro e edição exibem as mensagens de erro:

- código com exatamente 2 letras ASCII e sem repetição (a validação não consulta uma base oficial de códigos ISO);
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

O decorador `_medir` instrumenta `inserir`, `buscar`, `alterar`, `remover` e `listar`, utilizando `time.perf_counter_ns()`. São registrados chamadas, sucessos, falhas, tempo acumulado e tempo máximo. O resumo calcula o tempo médio e converte os tempos para microssegundos.

O dashboard (`/admin`) apresenta os contadores e os tempos médio e máximo por operação. Também mostra até oito eventos recentes com hora, operação, código e resultado. A duração individual é armazenada no evento, mas não aparece nessa tabela.

- Busca sem resultado conta como falha; exceções nos métodos também são registradas como falhas.
- `listar()` entra nos contadores, mas não nos eventos recentes.
- A carga inicial do JSON é excluída dos contadores.
- As métricas ficam em memória e são reiniciadas com o servidor.
- São contadas chamadas de métodos, não cliques: abrir páginas pode gerar listagens e buscas auxiliares. Abrir o dashboard também conta uma listagem.
- Os tempos abrangem o método e suas validações, com o custo do mecanismo de medição; não incluem salvamento do JSON, renderização ou toda a requisição Web.
- Não são expostos buckets, índices ou colisões internos do `dict`.
- O histórico recente de operações da estrutura é distinto do histórico de roteamentos proposto como diferencial.

Os tempos observados não substituem a análise de complexidade. O acesso por chave tem custo médio esperado constante em relação à quantidade de países, considerando campos de tamanho limitado. Listar todos os registros e gravar o JSON completo dependem do volume de dados; ordenar a listagem acrescenta custo de ordenação.

### Situação da entrega

O código contém o CRUD de países integrado à estrutura, a persistência e a instrumentação. A descrição inicial do diferencial e sua integração planejada constam neste README. Árvore B, Grafos e roteamento permanecem como desenvolvimento futuro.

A aprovação formal do diferencial deve ser confirmada com a professora. A documentação não substitui a validação da aplicação em execução.

---

## Perfis de acesso

O sistema considera dois tipos de utilização:

### Usuário

O usuário comum acessa funcionalidades de consulta, como:

- página inicial;
- consulta de cobertura por país;
- aquisição de planos (tela pública "Adquirir") e criação de conta.

O cliente entra pela aba "Cliente" da tela de login (e-mail e senha demonstrativa `123456`). Não há sessão: depois do login, o cliente é identificado pelo ID na URL (`/cliente/<id>`). Cliente inativo é bloqueado no login e também ao abrir essas URLs diretamente.

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
- Falhas de leitura ou escrita do JSON não têm tratamento específico. Uma falha de gravação pode deixar o estado em memória diferente do arquivo, pois a alteração ocorre antes do salvamento.
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

A segunda etapa adiciona o gerenciamento de clientes e eSIMs utilizando uma **Árvore B**.

Fluxo:

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

### Etapa 02 — Implementação (Árvore B e clientes)

A Etapa 2 está integrada de ponta a ponta: as telas administrativas e a área do cliente leem e gravam clientes por meio de **duas Árvores B reais**, e a página `/admin/arvore-b` mostra a instrumentação medida nessas árvores (comparações, nós visitados, altura, divisões e tempos), sem valores simulados.

#### Estrutura de Dados — Árvore B

**Convenção adotada: grau mínimo `t = 3`** (convenção do livro do Cormen):

| Propriedade | Valor com `t = 3` |
|---|---|
| Máximo de chaves por nó (`2t − 1`) | 5 |
| Máximo de filhos por nó (`2t`) | 6 |
| Mínimo de chaves em nó não-raiz (`t − 1`) | 2 |
| Chaves na raiz | de 1 a 5 |
| Folhas | todas na mesma profundidade |

Em bibliografias que definem a árvore pela **ordem** (máximo de filhos), essa mesma árvore é a de **ordem 6**.

**Índices duplos.** Há duas Árvores B independentes:

- **Árvore B de ID:** chave inteira (`id` do cliente);
- **Árvore B de e-mail:** chave normalizada (`strip().lower()`: minúsculas e sem espaços nas pontas).

Cada nó guarda exclusivamente pares **`(chave, posicao)`**, em que `posicao` é o índice do cliente na **lista** de `arquivos/clientes.json`. Os dados completos do cliente nunca ficam dentro dos nós: a árvore localiza a posição e o registro é lido no arquivo, nessa posição. Buscas por ID ou e-mail sempre descem a árvore; nunca percorrem a lista.

Módulos: `estruturas/arvore_b.py` (a estrutura), `arquivos/persistencia_clientes.py` (leitura e gravação dos JSON) e `dados_site/dados_etapa02.py` (regras de negócio, índices e instrumentação usados pelo `app.py`).

<!-- INSERIR PARÁGRAFO DO INTEGRANTE 1 SOBRE BUSCA/INSERÇÃO/DIVISÃO -->

#### Decisões de arquitetura e regras de negócio

- **Exclusão física:** a posição do cliente em `clientes.json` vira `null`, preservando as demais posições (nenhuma se desloca). Em seguida, os **dois índices são reconstruídos por inteiro** a partir da lista. Não há remoção interna de nós (fusão/empréstimo). Só clientes **inativos** podem ser excluídos, com confirmação (ID ou `EXCLUIR`) e ciência de que a ação é irreversível. A inativação é o fluxo normal e preserva registro e índices.
- **Geração de IDs:** contador sequencial persistente em `arquivos/controle_ids.json` (`proximo_id` e `ids_utilizados`). O histórico de IDs já atribuídos impede a **reutilização**, mesmo após exclusão física.
- **E-mail imutável:** depois do cadastro, o e-mail não pode ser alterado, porque é a chave da Árvore B de e-mail. No formulário de edição ele aparece como campo somente leitura (`readonly`, não `disabled`) e, mesmo que outro valor seja enviado, o servidor mantém o e-mail cadastrado.
- **eSIM editável:** o identificador do eSIM pode ser alterado e **não tem verificação de unicidade** nesta etapa.
- **Sem sessão ou autenticação:** a área administrativa é demonstrativa (as rotas `/admin` não são protegidas) e o cliente é identificado pela URL `/cliente/<id>`. O acesso de cliente inativo é barrado no login e também ao digitar a URL.
- **Ordem das gravações:** validar, preparar a cópia, gravar em arquivo e só então atualizar a memória e as árvores.
- **Dados indisponíveis:** se `clientes.json` ou `controle_ids.json` estiverem ausentes, ilegíveis ou inconsistentes (por exemplo, e-mail duplicado), os índices não são montados. Qualquer rota de clientes lança `ErroIndices`, tratada em `app.py`: o usuário volta ao painel `/admin` com um aviso. As funcionalidades da Etapa 1 (países e Tabela Hash) continuam funcionando.
- **Planos:** os códigos e franquias diferem **de propósito** da tabela ilustrativa do enunciado: 101/102 Europa, 201/202 América, 301 IlimitadoSIM (30 GB) e 401/402 Ásia. O Basic cobre exatamente 3 países da sua região, escolhidos na contratação.
- **Consulta integrada:** Árvore B (cliente) → pacote do cliente → Tabela Hash (destino) → cobertura. O cliente padrão da tela é o `1001`.
- **Países:** o campo `regiao` aparece na interface como "Continente"; os formulários oferecem as tecnologias 4G e 5G.

O registro completo das decisões está em `documentos/DGB_SIM_Decisoes_Etapa2.docx`.

#### Carga inicial de clientes

`arquivos/gerar_clientes.py` gera a carga de demonstração (1.000 clientes fictícios mais o cliente 1001, com semente fixa, então o resultado é reproduzível). Ele recusa sobrescrever arquivos existentes sem `--forcar`:

```bash
python arquivos/gerar_clientes.py
```

Alguns acessos úteis para demonstração: o cliente `cliente1002@example.com` (senha `123456`) é ativo e vai para `/cliente/2`; clientes cujo ID deixa resto 1 na divisão por 11 são gerados **inativos**.

#### Testes

Execute a partir da raiz do projeto:

```bash
python -m unittest discover -s testes -t ..
```

- `testes/teste_clientes.py`: backend de clientes (`dados_etapa02.py`);
- `testes/teste_integracao.py`: rotas Flask com `app.test_client()` (login, bloqueio de inativo, página da Árvore B, tratamento de `ErroIndices` e rotas da Etapa 1).

Os testes trabalham em **cópias temporárias** de `clientes.json` e `controle_ids.json`; os arquivos reais não são alterados (os módulos conferem isso ao final).

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

## Diferencial proposto — roteamento multicritério com histórico

**Situação na Etapa 01:** proposta documentada para aprovação e implementação futura na etapa de Grafos. Não é uma funcionalidade operacional desta versão.

### Problema e objetivo

A rota de menor latência já faz parte do escopo comum do trabalho. O diferencial acrescentará a escolha por **menor custo operacional simulado** e um histórico persistente dos roteamentos realizados.

### Funcionamento planejado

Cada conexão do Grafo terá dois atributos não negativos: latência simulada em milissegundos e custo operacional simulado, em unidade a ser definida pela equipe.

O usuário informará origem, destino e critério. Dijkstra utilizará o peso correspondente ao critério escolhido e calculará **uma rota por consulta**. O resultado apresentará a sequência de países, o critério utilizado, a latência total e o custo total desse caminho.

Exibir os dois totais não significa otimização simultânea nem cálculo automático de duas alternativas. Neste projeto, “multicritério” significa disponibilizar diferentes critérios para escolha do usuário.

### Integração planejada

1. Localizar o cliente pelo ID na Árvore B.
2. Verificar o país de destino na Tabela Hash e identificar o pacote associado ao cliente.
3. Localizar origem e destino no Grafo.
4. Aplicar Dijkstra ao atributo escolhido: latência ou custo.
5. Apresentar a rota e os dois totais do caminho encontrado.
6. Persistir a consulta no histórico JSON para visualização posterior.

O histórico deverá guardar origem, destino, critério, rota, latência total e custo operacional total.

### Condições de cálculo

A implementação deverá rejeitar pesos negativos ou ausentes antes do cálculo e informar localidades indisponíveis ou inexistência de caminho. Latências e custos serão identificados como simulados.

O detalhamento segue o material de proposta fornecido pela equipe. As estruturas, rotas e persistência desse diferencial ainda não estão implementadas no código analisado.

---

## Como executar o projeto

Ambiente informado pela equipe: Python 3.12 e Flask 3.1. O projeto não possui arquivo de dependências com versões fixadas.

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

Use a opção de administrador na tela `/login` (`admin` / `admin`). As credenciais de teste estão em `dados_site/dados_usuario.py`. O login de administrador é apenas demonstrativo: as rotas `/admin` não são protegidas.

---

## Observação acadêmica

Este projeto foi desenvolvido para fins acadêmicos na disciplina de **Estruturas de Dados II**.

A aplicação Web tem como principal objetivo fornecer uma interface para demonstrar o funcionamento das estruturas de dados implementadas ao longo do trabalho.

Por esse motivo, algumas soluções relacionadas à autenticação, persistência e arquitetura Web são propositalmente mantidas simples, priorizando a compreensão e a aplicação das estruturas de dados estudadas.

---

## Status do projeto

🚧 **Em desenvolvimento**

### Etapa 01 — Implementada, pendente de validação final

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
- [x] Confirmar, no ambiente de apresentação, rotas, validações e persistência após reinício
- [x] Instrumentação básica da estrutura (contadores e tempos no dashboard)
- [x] Descrição inicial do diferencial e integração planejada
- [ ] Confirmar aprovação formal do diferencial com a professora

### Próximas etapas

- [x] Telas da Etapa 2 (clientes, contratação, consulta integrada, Árvore B)
- [x] Implementação da Árvore B (ID e e-mail, chave → posição)
- [x] `arquivos/clientes.json` com cerca de 1.000 clientes gerados automaticamente
- [x] Integração das Árvores B ao Flask e testes de integração
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
