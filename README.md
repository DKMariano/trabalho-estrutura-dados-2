# DGB SIM

**Etapa 01 — Tabela Hash e Aplicação Web** (entrega prevista: 20/10/2026)  
**Etapa 02 — Árvore B e clientes** (entrega prevista: 24/11/2026) — implementada: duas Árvores B (ID e e-mail), persistência em JSON, operações cadastrais e instrumentação real.

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

## Etapa 01 — Tabela Hash

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
- paginar a listagem administrativa (5, 10 ou 20 países por página, à escolha do administrador);
- acompanhar, no dashboard, os contadores e tempos das operações da Tabela Hash.

As operações que alteram dados (cadastro, edição e exclusão) usam `POST` e terminam em redirecionamento (padrão Post/Redirect/Get).

---

## Etapa 01 — Estado do desenvolvimento

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

O código contém o CRUD de países integrado à estrutura, a persistência e a instrumentação. A descrição inicial do diferencial e sua integração planejada constam neste README. A Árvore B foi implementada na Etapa 02 (seção seguinte); Grafos e roteamento permanecem como desenvolvimento futuro.

O diferencial foi aprovado pela professora e será entregue na Etapa 03. A documentação não substitui a validação da aplicação em execução.

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
- exclusão de país;
- gerenciamento de clientes (cadastro, edição, inativação, reativação, exclusão física e associação de pacotes);
- páginas de instrumentação da Tabela Hash e da Árvore B e consulta integrada.

### Limitações conhecidas

- O login valida usuário e senha, mas não cria sessão: as rotas `/admin` e `/cliente/<id>` não são protegidas e podem ser acessadas diretamente pela URL, e o botão "Sair" apenas leva de volta ao login (veja "Acesso de demonstração e rotas").
- As credenciais de teste ficam em `dados_site/dados_usuario.py`, em texto simples.
- A `secret_key` do Flask está fixa no código. Fora do contexto acadêmico, ela seria lida de uma variável de ambiente.
- O conteúdo da página inicial (carrossel, benefícios, planos e depoimentos) vem de dados estáticos em `dados_site/dados_inicio.py`.
- Países (Etapa 01): falhas de leitura ou escrita do `paises.json` não têm tratamento específico. Uma falha de gravação pode deixar o estado em memória diferente do arquivo, pois a alteração ocorre antes do salvamento. (Os clientes da Etapa 02 seguem regras próprias; veja a seção da Etapa 02.)
- A busca administrativa diferencia acentos: pesquisar "mexico" não encontra "México".

Essas soluções são simplificadas de propósito, pois o foco acadêmico do projeto está nas estruturas de dados.

---

## Etapa 02 — Árvore B e gerenciamento de clientes

A Etapa 02 administra **1.001 clientes** (`arquivos/clientes.json`) com **duas Árvores B independentes**, integradas à Tabela Hash da Etapa 01.

### Árvore B (`estruturas/arvore_b.py`)

**Grau mínimo t = 3** (convenção de Cormen et al.):

| Regra | Valor com t = 3 |
| --- | --- |
| Máximo de chaves por nó | 2t − 1 = 5 |
| Máximo de filhos por nó | 2t = 6 |
| Mínimo de chaves (nós que não são raiz) | t − 1 = 2 |
| Raiz não vazia | 1 a 5 chaves |
| Folhas | todas na mesma profundidade |

**Convenção de "ordem":** livros que chamam de *ordem* o número máximo de filhos (Knuth) descreveriam esta mesma árvore como uma **Árvore B de ordem 6**. Usamos "grau mínimo" para evitar a ambiguidade.

Classes e operações:

- `NoArvoreB`: `chaves` (em ordem), `posicoes` (`posicoes[i]` é a posição de `chaves[i]` no arquivo), `filhos` e `folha`.
- `ArvoreB(grau_minimo=3, nome)`:
  - `buscar(chave)` → `(posição ou None, {comparacoes, nos_visitados, tempo_us})`. Busca **linear** dentro de cada nó: cada chave examinada conta uma comparação; cada nó em que a busca entra conta um nó visitado.
  - `contem(chave)`: mesma procura, **sem** alterar as métricas (usada para verificar duplicatas).
  - `inserir(chave, posicao)`: inserção com **divisão preventiva**. Ao descer, todo nó cheio é dividido antes de a busca entrar nele; a chave do meio sobe para o pai. Se a raiz está cheia, cria-se uma nova raiz (é a única forma de a altura crescer). Rejeita duplicatas, posições inválidas e tipos de chave misturados (`ValueError`).
  - `carregar(pares)`: carga em lote numa árvore vazia (registrada como "reconstrução").
  - `percorrer_em_ordem()`, `validar()` (confere todos os invariantes e devolve a lista de problemas), `altura()` (em níveis: só a raiz = 1), `total_chaves()`, `contar_nos()` e `metricas()`.

Exemplo de divisão (t = 3): o nó cheio `[10, 20, 30, 40, 50]` recebe 60 → 30 sobe para o pai, o nó vira `[10, 20]` e `[40, 50]`, e 60 entra em `[40, 50, 60]`. As posições acompanham as chaves.

**Remoção de chaves não é implementada** (decisão da equipe): a exclusão física reconstrói os índices.

### Estrutura dos índices

As árvores funcionam **somente como índice** (orientação da professora): guardam **chave → posição** do registro na lista de `clientes.json`. O cadastro completo nunca fica dentro da árvore.

| Índice | Chave | Valor |
| --- | --- | --- |
| Árvore B de ID | ID do cliente (inteiro positivo, imutável) | posição na lista |
| Árvore B de e-mail | e-mail normalizado (sem espaços nas pontas, minúsculas; imutável) | posição na lista |

Exemplo: o cliente 1001 (Ines) está na posição 1000. A árvore de ID guarda `1001 → 1000`; a de e-mail guarda `"ines@ed2.com" → 1000`.

Clientes ativos e inativos estão nas duas árvores. **Toda busca de cliente passa pela Árvore B**: o registro só é lido na posição que a árvore devolve. A listagem administrativa usa o **percurso em ordem** da árvore de ID; a busca por número usa a árvore de ID, por texto com "@" a árvore de e-mail, e qualquer outro texto filtra o percurso pelo nome.

Fluxo de uma busca:

```text
ID ou e-mail ──► Árvore B ──► posição ──► clientes.json[posição] ──► cliente
```

Com a carga atual, as duas árvores têm formas diferentes porque recebem as chaves em ordens diferentes:

| Árvore | Ordem de inserção | Altura | Nós | Divisões | Busca da Ines |
| --- | --- | --- | --- | --- | --- |
| ID | crescente (1, 2, …, 1001) | 6 | 498 | 492 | `1001`: 6 nós visitados, 17 comparações |
| E-mail | fora de ordem alfabética | 5 | 315 | 310 | `ines@ed2.com`: 5 nós visitados, 9 comparações |

A inserção em ordem crescente deixa a maioria dos nós com o mínimo de 2 chaves, o que leva a árvore de ID à maior altura possível para 1.001 chaves com t = 3 (a menor seria 4). Na árvore de e-mail, as chaves chegam embaralhadas, os nós ficam mais cheios e a árvore fica mais baixa.

### Backend de clientes (`dados_site/dados_etapa02.py`)

É a interface pública usada pelo `app.py` e pelo `servico_conectividade.py`. As assinaturas foram preservadas; o funcionamento interno passou de dados simulados para as Árvores B e os arquivos JSON.

- **Inicialização:** ao importar o módulo, `inicializar()` lê os dois JSON, ignora posições `null` (clientes excluídos), confere ID e e-mail de cada registro, procura duplicatas, constrói as duas árvores, confere os invariantes e se cada chave aponta para a posição correta, e valida o controle de IDs. Os índices só ficam disponíveis depois de todas as verificações.
- **Cadastro** (administrativo e "Criar conta"): o ID vem do contador persistente; o registro entra no **final** da lista (posição = tamanho anterior) e as chaves são inseridas nas duas árvores. O administrador pode associar um pacote no cadastro e na edição (o Basic exige 3 países da região, validados na Tabela Hash).
- **Edição:** nome, eSIM, status e pacote. **ID e e-mail são imutáveis** (chaves das árvores) e a senha demonstrativa é fixa (`123456`); o registro é alterado na mesma posição, e as árvores não mudam.
- **Inativação e reativação:** exclusão lógica; muda só o status. O cliente continua nas duas árvores, e pacote, países e datas são preservados.
- **Exclusão física:** só para cliente **inativo**, com confirmação reforçada (digitar o ID ou `EXCLUIR` e marcar a ciência da irreversibilidade). A posição vira `null` (nenhuma outra se desloca) e **as duas árvores são reconstruídas** a partir dos registros restantes. O ID permanece no histórico e nunca é reutilizado.
- **eSIM:** editável, sem verificação de unicidade (regra de negócio fora do escopo desta etapa).

### Controle de IDs (`arquivos/controle_ids.json`)

```json
{ "proximo_id": 1002, "ids_utilizados": [1, 2, "...", 1001] }
```

- Contador sequencial persistente + histórico dos IDs já atribuídos: **um ID nunca é reutilizado**, nem após a exclusão física.
- Regras de coerência verificadas ao iniciar: todo ID de cliente está em `ids_utilizados`; não há IDs repetidos; `proximo_id` é maior que todos os IDs usados. Um ID no histórico sem cliente é normal (cliente excluído).

### Persistência (`arquivos/persistencia_clientes.py`)

- Cada gravação escreve um arquivo temporário **na mesma pasta** (`.tmp`), força a ida ao disco (`flush` + `fsync`) e substitui o original com `os.replace`. Se a gravação for interrompida, o arquivo original continua inteiro.
- Em qualquer falha durante a gravação (erro de disco ou dado que não pode ser convertido em JSON), o `.tmp` é apagado e o erro original é relançado.
- Em operações que alteram os dois arquivos (cadastro), grava-se **primeiro o controle de IDs** e depois os clientes. Se a segunda gravação falhar, o ID fica sem uso e nunca será reutilizado.
- Cada alteração segue a ordem: **validar → preparar a nova lista → gravar → só então alterar a memória**.
- **Não há atomicidade entre arquivos diferentes**, nem rollback, nova tentativa ou recuperação automática.

### Tratamento de falhas

| Situação | Comportamento |
| --- | --- |
| Inconsistência ao iniciar (JSON inválido, ID ou e-mail repetido, controle de IDs incoerente) ou falha ao reconstruir os índices | Índices **indisponíveis**: as operações de clientes lançam `ErroIndices`; o `app.py` mostra a mensagem e volta ao painel `/admin`. **Nenhum dado é corrigido ou reinicializado.** As funcionalidades de países (Etapa 01) continuam disponíveis. |
| Erro ao gravar um arquivo (`OSError`) | Estado **falha de gravação**: a operação informa o erro e, daí em diante, as alterações de clientes ficam bloqueadas até a aplicação ser reiniciada (o reinício revalida tudo). As consultas continuam. |

### Instrumentação (métricas reais, por árvore)

A página **Árvore B** (`/admin/arvore-b`) mostra, em painéis separados para a árvore de ID e a de e-mail, somente valores medidos:

| Grupo | Métricas |
| --- | --- |
| Última busca | comparações (chaves examinadas), nós visitados, tempo (µs) |
| Acumuladas | comparações totais, total de buscas |
| Estado da árvore | altura (número de níveis), divisões, total de chaves, última operação (inserção ou reconstrução) e seu tempo (µs) |

- O tempo é medido com `time.perf_counter_ns()` e exibido em microssegundos.
- Só `buscar()` conta como busca; `contem()`, inserção, carga, percurso e validação não alteram as métricas de busca.
- **Toda reconstrução** (inicialização ou exclusão física) cria uma nova instância e **zera todas as métricas**, inclusive as acumuladas. As divisões contadas são as da construção da instância atual mais as inserções posteriores.
- O painel `/admin` mostra o resumo da árvore de ID: clientes indexados (total de chaves), altura, quantidade de nós e média de nós visitados por busca.
- A consulta integrada mostra a estrutura usada (árvore de ID ou de e-mail) e a posição devolvida; a busca conta nas métricas da árvore exibidas na página Árvore B.
- Cada visita a uma página de cliente faz uma busca real e, portanto, atualiza a "última busca".

### Integração Árvore B × Tabela Hash

A consulta integrada (`/admin/consulta`, padrão: cliente **1001** e destino **IT**) e a área do cliente executam:

```text
1. ÁRVORE B   buscar(1001)  → posição 1000 → Ines, eSIM, pacote 102
2. TABELA HASH buscar("IT") → Itália, cobertura disponível, 5G
3. Regra do plano do cliente → coberto ou não, com sugestões de planos
```

### Carga de clientes e gerador

`arquivos/clientes.json` contém 1.001 clientes: os clientes 1 a 1.000 são fictícios, com nome e sobrenome de pessoa sem repetição (ex.: "Beatriz Barbosa") e e-mail `nome.sobrenome{1000+id}@example.com`, sem acentos (ex.: `beatriz.barbosa1002@example.com` é o cliente 2). São inativos quando `id % 11 == 1` e ficam sem plano quando `id % 5 == 1`. O cliente 1001 (Ines, `ines@ed2.com`) é o registro de demonstração. Resultado: 910 ativos e 91 inativos; 200 sem plano e 801 com plano.

O gerador `arquivos/gerar_clientes.py` é executado **manualmente** e nunca roda junto com a aplicação:

```bash
python arquivos/gerar_clientes.py            # recusa se os arquivos já existirem
python arquivos/gerar_clientes.py --forcar   # recarga completa: exige autorização da equipe
```

Com sementes e data-base fixas (uma semente para planos e datas, outra para os nomes), o resultado é reproduzível. Ele valida a carga antes de gravar, grava o controle antes dos clientes (via arquivo temporário) e, com `--forcar`, esvazia o `historico.json`. A carga atual **não** deve ser substituída sem autorização da equipe.

### Testes automatizados

A pasta `testes/` tem 71 testes (`unittest`), executados a partir da raiz do projeto:

```bash
python -m unittest discover -s testes -t .
```

| Arquivo | O que verifica |
| --- | --- |
| `teste_arvore_b.py` | árvore vazia e `carregar([])`; 5 chaves sem divisão e 6ª com divisão (chaves **e posições** conferidas); 1.001 chaves crescentes, aleatórias e de e-mail com invariantes válidos e altura entre 4 e 6; busca de todas as chaves; chaves inválidas; duplicatas; métricas; `validar()` detectando árvore corrompida |
| `teste_persistencia_clientes.py` | gravação segura (`.tmp` apagado em qualquer falha), listas com `null`, formato do arquivo gravado, formatos inválidos, coerência do controle de IDs |
| `teste_clientes.py` | carga, buscas, listagem pelo percurso, cadastro, edição, inativação, exclusão com reconstrução, não reutilização de IDs, falhas de gravação e dados inconsistentes |
| `teste_integracao.py` | rotas Flask, login com cliente do JSON, página da Árvore B, consulta integrada, operações cadastrais pelas telas, bloqueio com índices indisponíveis e Etapa 01 funcionando |

Os testes trabalham com **cópias temporárias** dos JSON e conferem, por hash, que os arquivos reais não foram alterados.

### Roteiro de demonstração

1. **Busca:** `/admin/arvore-b`, buscar o ID `1001` (posição 1000, 6 nós visitados) e depois, na árvore de e-mail, `ines@ed2.com` (posição 1000, 5 nós visitados); comparar os painéis das duas árvores e explicar por que a de e-mail é mais baixa.
2. **Inserção com divisão:** anotar as divisões da árvore de ID, cadastrar um cliente em `/admin/clientes/cadastrar` e voltar à página: total de chaves +1, última operação "Inserção". Como as chaves chegam em ordem crescente, a nova chave entra na folha mais à direita; a divisão acontece quando essa folha já está cheia, e o contador sobe.
3. **Inativação:** inativar o cliente na lista; ele continua encontrado pela busca nas duas árvores.
4. **Exclusão física:** na "Zona de risco" do cliente inativo, digitar o ID ou `EXCLUIR` e marcar a ciência.
5. **Reconstrução:** a página da Árvore B mostra a última operação "Reconstrução", métricas zeradas e uma chave a menos; a busca do ID excluído não encontra nada.
6. **Integração:** `/admin/consulta` com o cliente 1001 e destino IT.
7. **Área do cliente:** login com `beatriz.barbosa1002@example.com` / `123456`, que abre `/cliente/2`.
8. **Testes:** executar a suíte automatizada.

### Diferenças em relação ao enunciado (decisões da equipe)

- **Planos:** mantidos os códigos do enunciado (101/102 Europa, 201/202 América, 301), com 301 renomeado para **IlimitadoSIM** e Ásia como 401/402. Franquias definidas pela equipe: Europa Plus com **15 GB** (o enunciado indica 10 GB) e IlimitadoSIM com **30 GB** (o enunciado indica "Global, 20 GB").
- **Índice adicional por e-mail**, usado no login do cliente e na busca administrativa.
- **Inativação e exclusão física** acrescentadas ao CRUD exigido.

### Situação do diferencial na Etapa 02

O enunciado pede, para a Etapa 02, a "primeira implementação funcional do diferencial, quando aplicável". O diferencial (roteamento multicritério com histórico) **já foi confirmado pela professora** e, como depende do grafo, **será entregue na Etapa 03**. Por isso, não há implementação do diferencial nesta etapa.

### Limitações e decisões relevantes

- Sem remoção interna de chaves na Árvore B: a exclusão física reconstrói os dois índices (custo proporcional ao número de clientes).
- Sem atomicidade entre `controle_ids.json` e `clientes.json`; sem rollback ou recuperação automática.
- O cadastro com pacote grava duas vezes (cliente e depois o pacote). Se a segunda gravação falhar, o cliente fica cadastrado sem pacote e a tela informa o erro.
- Com os índices indisponíveis, as páginas que dependem de clientes (inclusive login e área do cliente) redirecionam ao painel administrativo com a mensagem de erro.
- Gravações simultâneas não são sincronizadas (uso acadêmico com um operador).
- `paises.json` (Etapa 01) e `historico.json` (Etapa 03) continuam sendo gravados diretamente, sem arquivo temporário.
- A área administrativa e a área do cliente continuam demonstrativas, sem sessão nem controle de acesso.


---

## Estrutura atual do projeto

```text
trabalho-estrutura-dados-2/
│
├── app.py                        rotas Flask (interface)
├── README.md
├── LICENSE
├── .gitignore
│
├── estruturas/
│   ├── tabela_hash.py            Etapa 01 (inalterada)
│   └── arvore_b.py               Etapa 02: Árvore B (t = 3)
│
├── arquivos/
│   ├── persistencia_paises.py
│   ├── persistencia_pacotes.py
│   ├── persistencia_historico.py
│   ├── persistencia_clientes.py  Etapa 02: leitura e gravação segura
│   ├── gerar_clientes.py         Etapa 02: gerador manual da carga
│   ├── paises.json
│   ├── pacotes.json
│   ├── clientes.json             1.001 clientes (lista; posição = índice)
│   ├── controle_ids.json         contador e histórico de IDs
│   └── historico.json            consultas demonstrativas (Etapa 03)
│
├── dados_site/
│   ├── dados_etapa02.py          backend de clientes (Árvores B + JSON)
│   ├── servico_conectividade.py  consulta integrada Árvore B × Tabela Hash
│   ├── regras_planos.py          vigência, cobertura e regra do Basic
│   ├── dados_etapa03.py          dados demonstrativos da Etapa 03
│   ├── dados_inicio.py
│   └── dados_usuario.py
│
├── testes/                       71 testes (unittest)
│   ├── apoio.py
│   ├── teste_arvore_b.py
│   ├── teste_persistencia_clientes.py
│   ├── teste_clientes.py
│   └── teste_integracao.py
│
├── documentos/                   enunciado, diferencial e slides da Etapa 01
├── static/                       bootstrap/, css/, js/, img/
└── templates/                    páginas públicas, admin/ e cliente/
```

A estrutura poderá sofrer alterações durante a implementação das estruturas de dados previstas nas próximas etapas.

---

## Estrutura planejada

Com a evolução do projeto, as demais estruturas de dados também ficarão separadas da camada Web. Ainda serão adicionados:

```text
estruturas/
└── grafo.py

arquivos/
└── rede.json
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

Gerenciamento de clientes e eSIMs com duas **Árvores B** (ID e e-mail), implementado (detalhes na seção "Etapa 02").

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

**Situação:** diferencial confirmado pela professora, com entrega na Etapa 03 (Grafos). Não é uma funcionalidade operacional desta versão.

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

Ao iniciar, o backend carrega `arquivos/clientes.json` e `arquivos/controle_ids.json` e constrói as duas Árvores B. Não é necessário executar o gerador de clientes: a carga já está no projeto.

### Testes

```bash
python -m unittest discover -s testes -t .
```

Executar `python app.py` não inicia o servidor, pois o arquivo não define o ponto de entrada `if __name__ == "__main__"`.

### 5. Acesse pelo navegador

Utilize o endereço exibido pelo Flask no terminal, normalmente:

```text
http://127.0.0.1:5000
```

---

## Acesso de demonstração e rotas

### Credenciais de teste

O login é feito na tela `/login`, escolhendo a aba correspondente ao perfil:

| Perfil | Login | Senha | Destino após o login |
| --- | --- | --- | --- |
| Administrador | `admin` | `admin` | `/admin` |
| Cliente Ines (ID 1001) | `ines@ed2.com` | `123456` | `/cliente/1001` |
| Demais clientes fictícios | `nome.sobrenome{1000+id}@example.com` (ex.: `beatriz.barbosa1002@example.com` → ID 2) | `123456` | `/cliente/<id>` |

As credenciais do administrador estão em `dados_site/dados_usuario.py`; as dos clientes vêm de `arquivos/clientes.json` (senha demonstrativa fixa `123456`). Clientes inativos são recusados no login.

### Não há proteção de rotas

> ⚠️ **O sistema não tem sessão, autenticação nem controle de acesso.** O login apenas confere usuário e senha e redireciona para a página do perfil; nada é guardado entre uma requisição e outra.

Consequências:

- **todas as rotas de administrador e de cliente podem ser acessadas diretamente pela URL**, sem passar pelo login;
- a área do cliente é identificada só pelo ID na URL: trocar o número em `/cliente/<id>` abre a área de outro cliente;
- o botão "Sair" apenas volta para a tela de login.

As únicas restrições existentes são regras de negócio, não de segurança: nas rotas `/cliente/<id>`, um cliente **inativo** vê a página "Acesso bloqueado" e um ID inexistente volta para o login; se os índices de clientes estiverem indisponíveis, as páginas que dependem de clientes redirecionam para `/admin` com o aviso.

Essa simplificação é proposital: o foco do trabalho são as estruturas de dados, e a aplicação Web serve apenas para demonstrá-las.

### Lista de rotas

**Páginas públicas**

| Rota | Métodos | Função |
| --- | --- | --- |
| `/` | GET | Página inicial |
| `/paises` | GET, POST | Consulta de cobertura por país (Tabela Hash) |
| `/planos` | GET | Planos disponíveis |
| `/login` | GET, POST | Login de administrador e de cliente |
| `/adquirir/<plano>` | GET, POST | Aquisição de um plano |
| `/criar-conta` | GET, POST | Criação de conta de cliente (novo ID nas duas Árvores B) |

**Área do cliente** (`<cliente_id>` = ID do cliente, ex.: `1001`)

| Rota | Métodos | Função |
| --- | --- | --- |
| `/cliente/<cliente_id>` | GET | Painel do cliente |
| `/cliente/<cliente_id>/minha-conta` | GET | Dados da conta |
| `/cliente/<cliente_id>/contratar` | GET, POST | Contratação de plano |
| `/cliente/<cliente_id>/minha-conectividade` | GET, POST | Consulta de conectividade (Árvore B × Tabela Hash; rota e histórico demonstrativos da Etapa 03) |
| `/cliente/<cliente_id>/historico` | GET | Redireciona para o histórico em "Minha conectividade" |

**Administração — painel e países (Etapa 01)**

| Rota | Métodos | Função |
| --- | --- | --- |
| `/admin` | GET | Dashboard (métricas da Tabela Hash e resumo da Árvore B) |
| `/admin/paises` | GET | Listagem de países |
| `/admin/paises/cadastrar` | GET, POST | Cadastro de país |
| `/admin/paises/<codigo>` | GET | Visualização de país |
| `/admin/paises/<codigo>/editar` | GET, POST | Edição de país |
| `/admin/paises/<codigo>/excluir` | POST | Exclusão de país |
| `/admin/tabela-hash` | GET | Instrumentação da Tabela Hash |

**Administração — clientes e Árvore B (Etapa 02)**

| Rota | Métodos | Função |
| --- | --- | --- |
| `/admin/clientes` | GET | Listagem de clientes (percurso em ordem da Árvore B de ID, com filtros) |
| `/admin/clientes/cadastrar` | GET, POST | Cadastro de cliente |
| `/admin/clientes/<cliente_id>` | GET | Visualização do cliente |
| `/admin/clientes/<cliente_id>/editar` | GET, POST | Edição do cliente (e-mail somente leitura) |
| `/admin/clientes/<cliente_id>/inativar` | POST | Inativação (exclusão lógica) |
| `/admin/clientes/<cliente_id>/reativar` | POST | Reativação |
| `/admin/clientes/<cliente_id>/excluir` | POST | Exclusão física (somente cliente inativo, com confirmação) |
| `/admin/arvore-b` | GET | Busca e instrumentação das Árvores B (`?indice=id` ou `?indice=email`, `&chave=`) |
| `/admin/consulta` | GET | Consulta integrada: cliente (Árvore B) × destino (Tabela Hash) |

**Administração — rede (Etapa 03, demonstrativa)**

| Rota | Métodos | Função |
| --- | --- | --- |
| `/admin/rede` | GET | Rede internacional e execução demonstrativa de algoritmos |
| `/admin/grafo` | GET | Visualização demonstrativa do grafo |

Exemplos para abrir direto no navegador: `/admin/arvore-b?chave=1001`, `/admin/arvore-b?indice=email&chave=ines@ed2.com`, `/admin/consulta?cliente=1001&destino=IT` e `/cliente/1001`.

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
- [x] Confirmar aprovação formal do diferencial com a professora

### Etapa 02 — Implementada

- [x] Telas da Etapa 2 (clientes, contratação, consulta integrada, Árvore B)
- [x] Árvore B com t = 3 (busca, inserção com divisão, validação de invariantes)
- [x] Duas Árvores B (ID e e-mail, chave → posição) usadas em todas as buscas
- [x] `arquivos/clientes.json` com 1.001 clientes gerados automaticamente
- [x] Persistência segura e controle de IDs sem reutilização
- [x] Cadastro, busca, listagem, edição, inativação, exclusão física com reconstrução
- [x] Integração cliente × país de destino (Árvore B × Tabela Hash)
- [x] Instrumentação real, separada por árvore
- [x] Testes automatizados (71)

### Próximas etapas

- [ ] Implementação do grafo
- [ ] BFS e DFS
- [ ] Roteamento com Dijkstra
- [ ] Integração das estruturas
- [ ] Implementação e entrega do diferencial (Etapa 03)
- [ ] Documentação final

---

## Equipe

**Integrantes:** Bruno Barreto, Dimitrius Khouri e Guilherme Lopes
**Professora:** Maria Inés Restovic

**Instituição:** Universidade do Estado da Bahia — UNEB  
**Curso:** Bacharelado em Sistemas de Informação

---

## Licença

Distribuído sob a licença MIT. Veja o arquivo `LICENSE`.

Projeto desenvolvido para fins acadêmicos.