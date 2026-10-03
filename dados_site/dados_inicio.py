"""
ATENÇÃO!

Dados estáticos utilizados somente para montar o conteúdo da página
inicial do MVP.

Este arquivo contém os dados do carrossel, benefícios, etapas,
depoimentos e planos apresentados na página inicial.

Confirmar com a professora se este arquivo poderá ser mantido na entrega
final ou se deverá ser substituído.
"""


# =============================================================================
# CARROSSEL PRINCIPAL
# =============================================================================

# Conteúdo exibido nos slides do carrossel da página inicial.
ITENS_CARROSSEL = [
    {
        "classe": "hero-santorini",
        "titulo": "Internet que vai mais longe.",
        "texto": (
            "Conecte-se durante suas viagens internacionais "
            "com praticidade, liberdade e economia."
        ),
        "botao": "Consultar cobertura",
    },
    {
        "classe": "hero-paris",
        "titulo": "Sua viagem continua conectada.",
        "texto": (
            "Tenha acesso à internet durante sua viagem "
            "de forma simples e prática."
        ),
        "botao": None,
    },
    {
        "classe": "hero-nova-york",
        "titulo": "Conecte-se ao seu próximo destino.",
        "texto": (
            "Consulte a cobertura disponível e prepare-se "
            "para viajar conectado."
        ),
        "botao": "Ver cobertura",
    },
]


# =============================================================================
# BENEFÍCIOS
# =============================================================================

# Benefícios apresentados na seção de destaques da página inicial.
BENEFICIOS = [
    {
        "icone": "🌐",
        "titulo": "Cobertura global",
        "texto": (
            "Verifique a disponibilidade de "
            "internet no seu destino."
        ),
    },
    {
        "icone": "📶",
        "titulo": "Planos flexíveis",
        "texto": (
            "Escolha o plano ideal para o seu "
            "tipo de viagem."
        ),
    },
    {
        "icone": "📱",
        "titulo": "Conexão sem complicação",
        "texto": (
            "Tecnologia eSIM para você viajar "
            "com mais liberdade."
        ),
    },
]


# =============================================================================
# COMO FUNCIONA
# =============================================================================

# Etapas apresentadas ao usuário para demonstrar o fluxo geral do serviço.
PASSOS = [
    {
        "numero": 1,
        "titulo": "Escolha o destino",
        "texto": (
            "Informe o país que deseja visitar e "
            "consulte a cobertura disponível."
        ),
    },
    {
        "numero": 2,
        "titulo": "Consulte os planos",
        "texto": (
            "Veja os pacotes disponíveis para "
            "o seu destino."
        ),
    },
    {
        "numero": 3,
        "titulo": "Contrate seu plano",
        "texto": (
            "Selecione um plano e faça a ativação "
            "de forma simples e rápida."
        ),
    },
]


# =============================================================================
# DEPOIMENTOS
# =============================================================================

# Informações utilizadas na construção dos cards de depoimentos.
DEPOIMENTOS = [
    {
        "estrelas": "★★★★★",
        "texto": (
            "“Consultar a cobertura foi simples e rápido. "
            "Encontrei as informações que precisava "
            "sem complicação.”"
        ),
        "foto": "img/depoimentos/antonio-atta.gif",
        "alt": "Foto de Antônio Carlos Fontes Atta",
        "nome": "Antônio Carlos Fontes Atta",
    },
    {
        "estrelas": "★★★★★",
        "texto": (
            "“A experiência com o DGB SIM foi muito prática. "
            "Consegui verificar meu destino e me preparar "
            "para a viagem com facilidade.”"
        ),
        "foto": "img/depoimentos/vagner-fonseca.jpeg",
        "alt": "Foto de Vagner de Souza Fonseca",
        "nome": "Vagner de Souza Fonseca",
    },
    {
        "estrelas": "★★★★★",
        "texto": (
            "“O serviço DGB SIM é nota dez! "
            "Aprovado com louvor!”"
        ),
        "foto": "img/depoimentos/ines-restovic.jpg",
        "alt": "Foto de Inês Valderrama Restovic",
        "nome": "Inês Valderrama Restovic",
    },
]


# =============================================================================
# PLANOS
# =============================================================================

# Dados utilizados tanto nos cards quanto nos modais de detalhes dos planos.
# O campo "id" identifica o modal correspondente a cada plano no template.
PLANOS = [
    {
        "id": "EuropaBasic",
        "nome": "Europa Basic",
        "dados": "5 GB",
        "validade": "15 dias",
        "cobertura": "Europa",
        "imagem": "img/planos/Europa-Basic.jpg",
        "alt": "Destino europeu representando o plano Europa Basic",
    },
    {
        "id": "EuropaPlus",
        "nome": "Europa Plus",
        "dados": "10 GB",
        "validade": "30 dias",
        "cobertura": "Europa",
        "imagem": "img/planos/EuropaPlus.jpg",
        "alt": "Paris representando o plano Europa Plus",
    },
    {
        "id": "AmericaBasic",
        "nome": "América Basic",
        "dados": "5 GB",
        "validade": "15 dias",
        "cobertura": "América",
        "imagem": "img/planos/AmericaBasic.jpg",
        "alt": "Nova York representando o plano América Basic",
    },
    {
        "id": "AmericaPlus",
        "nome": "América Plus",
        "dados": "15 GB",
        "validade": "30 dias",
        "cobertura": "América",
        "imagem": "img/planos/AmericaPlus.jpg",
        "alt": "Viagem internacional representando o plano América Plus",
    },
    {
        "id": "Global",
        "nome": "Global",
        "dados": "20 GB",
        "validade": "30 dias",
        "cobertura": "Global",
        "imagem": "img/planos/global.jpg",
        "alt": "Mapa de conexões internacionais representando o plano Global",
    },
]