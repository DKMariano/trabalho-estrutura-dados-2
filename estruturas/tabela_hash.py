class TabelaHash:
    def __init__(self):
        self.paises = {}

    # normaliza o código
    def inserir(self, codigo, nome, regiao, operadora, tecnologia):
        codigo = codigo.strip().upper()

        # validação de duas letras
        if len(codigo) != 2 or not codigo.isalpha():
          raise ValueError("O código do país deve possuir exatamente 2 letras.")

        #impede que escreva um código já existente
        if codigo in self.paises:
            raise ValueError("Já existe um país cadastrado com esse código")

        self.paises[codigo] = {
            "nome": nome,
            "regiao": regiao,
            "operadora": operadora,
            "tecnologia": tecnologia
        }

    # buscar um país pelo código.
    def buscar(self, codigo):
        # normaliza o código e usa .get() para consultar diretamente o dicionário
        codigo = codigo.strip().upper()

        return self.paises.get(codigo)

    # .items() fornece os pares código e dados do país. list() reúne esses pares em uma lista
    def listar(self):
        # .items() fornece os pares código e dados do país. list() reúne esses pares em uma lista
        return list(self.paises.items())

    # alterar os dados de um país existente, mantendo seu código.
    def  alterar(self, codigo, nome, regiao, operadora, tecnologia):
        codigo = codigo.strip().upper()

        #verificação impede que uma alteração cadastre acidentalmente um país inexistente.
        if codigo not in self.paises:
            raise ValueError("País não encontrado.")

        self.paises[codigo] = {
            "nome": nome,
            "regiao": regiao,
            "operadora":operadora,
            "tecnologia": tecnologia
        }

    # remover um país
    def remover(self, codigo):
        codigo = codigo.strip().upper()
        
        #verificação permite informar quando o país não existe.
        if codigo not in self.paises:
            raise ValueError("País não encontrado.")

        del self.paises[codigo]

    
