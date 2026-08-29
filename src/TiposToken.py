from enum import Enum, auto

class TiposToken(Enum):
    ID = auto(); NUM_INT = auto(); NUM_FLOAT = auto(); LITERAL = auto(); ASCII = auto()
    COMMA = auto(); OPEN_BRACKETS = auto(); CLOSE_BRACKETS = auto()
    OPEN_PARENTHESES = auto(); CLOSE_PARENTHESES = auto()
    OPEN_BRACES = auto(); CLOSE_BRACES = auto()
    PLUS = auto(); MINUS = auto(); DECREMENT = auto(); INCREMENT = auto()
    ADDRESS = auto(); NEG = auto(); ASSIGN = auto(); EQUALS = auto()
    LESS_THAN = auto(); LESS_THAN_EQUAL = auto()
    GREATER_THAN = auto(); GREATER_THAN_EQUAL = auto()
    DIFF = auto(); OR = auto(); AND = auto(); MULT = auto()
    DIV = auto(); MOD = auto(); SEMICOLON = auto()
    INT = auto(); FLOAT = auto(); CHAR = auto(); BOOL = auto()
    IF = auto(); ELSE = auto(); WHILE = auto(); READLN = auto()
    PRINT = auto(); BREAK = auto(); RETURN = auto()
    TRUE = auto(); FALSE = auto(); END_OF_FILE = auto(); UNKNOWN = auto()

# Mapeamento para a saída formatada de cada token
NOMES_TOKEN = {
    TiposToken.ID: "ID", TiposToken.NUM_INT: "NUMINT", TiposToken.NUM_FLOAT: "NUMFLOAT",
    TiposToken.LITERAL: "LITERAL", TiposToken.ASCII: "ASCII", TiposToken.COMMA: "COMMA",
    TiposToken.OPEN_BRACKETS: "OPEN_BRACKETS", TiposToken.CLOSE_BRACKETS: "CLOSE_BRACKETS",
    TiposToken.OPEN_PARENTHESES: "LPARENT", TiposToken.CLOSE_PARENTHESES: "RPARENT",
    TiposToken.OPEN_BRACES: "OPEN_BRACES", TiposToken.CLOSE_BRACES: "CLOSE_BRACES",
    TiposToken.PLUS: "PLUS", TiposToken.MINUS: "MINUS", TiposToken.DECREMENT: "DECREMENT",
    TiposToken.INCREMENT: "INCREMENT", TiposToken.ADDRESS: "ADDRESS", TiposToken.NEG: "NEG",
    TiposToken.ASSIGN: "ASSIGN", TiposToken.EQUALS: "EQUALS", TiposToken.LESS_THAN: "LESS_THAN",
    TiposToken.LESS_THAN_EQUAL: "LEQ", TiposToken.GREATER_THAN: "GREATER_THAN",
    TiposToken.GREATER_THAN_EQUAL: "GEQ", TiposToken.DIFF: "DIFF", TiposToken.OR: "OR",
    TiposToken.AND: "AND", TiposToken.MULT: "MULT", TiposToken.DIV: "DIV",
    TiposToken.MOD: "MOD", TiposToken.SEMICOLON: "SEMICOLON", TiposToken.INT: "INT",
    TiposToken.FLOAT: "FLOAT", TiposToken.CHAR: "CHAR", TiposToken.BOOL: "BOOL",
    TiposToken.IF: "IF", TiposToken.ELSE: "ELSE", TiposToken.WHILE: "WHILE",
    TiposToken.READLN: "READLN", TiposToken.PRINT: "PRINT", TiposToken.BREAK: "BREAK",
    TiposToken.RETURN: "RETURN", TiposToken.TRUE: "TRUE", TiposToken.FALSE: "FALSE",
    TiposToken.END_OF_FILE: "EOF", TiposToken.UNKNOWN: "UNKNOWN"
}

class Token:
    def __init__(self, tipo: TiposToken, lexema: str, linha: int, coluna: int):
        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha
        self.coluna = coluna

    def obter_tipo(self) -> TiposToken:
        return self.tipo

    def obter_lexema(self) -> str:
        return self.lexema

    def obter_linha(self) -> int:
        return self.linha

    def obter_coluna(self) -> int:
        return self.coluna

    def para_string(self) -> str:
        """
        Converte o token para o formato de saída exigido.
        Exemplos: "IF", "ID.x1", "NUMINT.32"
        """
        nome_tipo = NOMES_TOKEN.get(self.tipo, "UNKNOWN")
        
        # Se for ID, NUM_INT ou NUM_FLOAT, concatena com o lexema
        if self.tipo in (TiposToken.ID, TiposToken.NUM_INT, TiposToken.NUM_FLOAT):
            return f"{nome_tipo}.{self.lexema}"
        
        return nome_tipo