from TiposToken import TiposToken

class TabelaSimbolos:
    def __init__(self):
        self.simbolos = {}
        self.carregar_palavras_reservadas()

    def carregar_palavras_reservadas(self):
        # Carrega as palavras reservadas iniciais da linguagem
        self.simbolos = {
            "if": TiposToken.IF, "else": TiposToken.ELSE, "while": TiposToken.WHILE,
            "return": TiposToken.RETURN, "int": TiposToken.INT, "float": TiposToken.FLOAT,
            "char": TiposToken.CHAR, "double": TiposToken.DOUBLE, "define": TiposToken.DEFINE,
            "void": TiposToken.VOID, "break": TiposToken.BREAK, "continue": TiposToken.CONTINUE,
            "switch": TiposToken.SWITCH, "case": TiposToken.CASE, "default": TiposToken.DEFAULT,
            "struct": TiposToken.STRUCT, "typedef": TiposToken.TYPEDEF, "do": TiposToken.DO,
            "const": TiposToken.CONST, "true": TiposToken.TRUE, "false": TiposToken.FALSE,
            "bool": TiposToken.BOOL, "readln": TiposToken.READLN, "print": TiposToken.PRINT,
            "class": TiposToken.CLASS, "static": TiposToken.STATIC, "string": TiposToken.STRING,
            "main": TiposToken.MAIN, "include": TiposToken.INCLUDE, "using": TiposToken.USING,
            "vector": TiposToken.VECTOR
        }

    def inserir(self, lexema: str, tipo_token: TiposToken):
        # Insere um novo símbolo na tabela
        self.simbolos[lexema] = tipo_token

    def buscar(self, lexema: str) -> TiposToken:
        # Busca uma string na tabela. Se não for encontrada, classifica como ID.
        return self.simbolos.get(lexema, TiposToken.ID)

    def existe(self, lexema: str) -> bool:
        # Verifica se o lexema já existe na tabela
        return lexema in self.simbolos

    def remover(self, lexema: str) -> bool:
        # Remove um símbolo da tabela
        if lexema in self.simbolos:
            del self.simbolos[lexema]
            return True
        return False

    def quantidade(self) -> int:
        # Retorna o total de elementos na tabela
        return len(self.simbolos)