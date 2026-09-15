from src.TiposToken import TiposToken
from src.models.Simbolo import CategoriaSimbolo, Simbolo

PALAVRAS_RESERVADAS = {
    "int": TiposToken.INT,
    "float": TiposToken.FLOAT,
    "char": TiposToken.CHAR,
    "bool": TiposToken.BOOL,
    "if": TiposToken.IF,
    "else": TiposToken.ELSE,
    "while": TiposToken.WHILE,
    "readln": TiposToken.READLN,
    "print": TiposToken.PRINT,
    "break": TiposToken.BREAK,
    "return": TiposToken.RETURN,
    "true": TiposToken.TRUE,
    "false": TiposToken.FALSE,
    "typedef": TiposToken.TYPEDEF,
    "struct": TiposToken.STRUCT,
}

TOKENS_FIXOS = {
    ",": TiposToken.COMMA,
    "[": TiposToken.OPEN_BRACKETS,
    "]": TiposToken.CLOSE_BRACKETS,
    "(": TiposToken.OPEN_PARENTHESES,
    ")": TiposToken.CLOSE_PARENTHESES,
    "{": TiposToken.OPEN_BRACES,
    "}": TiposToken.CLOSE_BRACES,
    "+": TiposToken.PLUS,
    "-": TiposToken.MINUS,
    "--": TiposToken.DECREMENT,
    "++": TiposToken.INCREMENT,
    "!": TiposToken.NEG,
    "=": TiposToken.ASSIGN,
    "==": TiposToken.EQUALS,
    "<": TiposToken.LESS_THAN,
    "<=": TiposToken.LESS_THAN_EQUAL,
    ">": TiposToken.GREATER_THAN,
    ">=": TiposToken.GREATER_THAN_EQUAL,
    "!=": TiposToken.DIFF,
    "||": TiposToken.OR,
    "&&": TiposToken.AND,
    "*": TiposToken.MULT,
    "/": TiposToken.DIV,
    "%": TiposToken.MOD,
    ";": TiposToken.SEMICOLON,
}


class TabelaSimbolos:
    """Associa cada lexema reconhecível ao seu tipo e índice estável."""

    def __init__(self) -> None:
        self.simbolos: dict[str, Simbolo] = {}
        self.proximoIndice = 0
        self.carregarTokensIniciais()

    def carregarTokensIniciais(self) -> None:
        for lexema, tipoToken in PALAVRAS_RESERVADAS.items():
            self.inserir(lexema, tipoToken, CategoriaSimbolo.RESERVADA)
        for lexema, tipoToken in TOKENS_FIXOS.items():
            self.inserir(lexema, tipoToken, CategoriaSimbolo.FIXO)

    def inserir(
        self,
        lexema: str,
        tipoToken: TiposToken,
        categoria: CategoriaSimbolo,
    ) -> Simbolo:
        simboloExistente = self.buscar(lexema)

        if simboloExistente is not None:
            return simboloExistente

        simbolo = Simbolo(
            indice=self.proximoIndice,
            lexema=lexema,
            tipoToken=tipoToken,
            categoria=categoria,
        )

        self.simbolos[lexema] = simbolo
        self.proximoIndice += 1

        return simbolo

    def buscar(self, lexema: str) -> Simbolo | None:
        """Retorna o símbolo ou None quando o lexema não está cadastrado."""
        return self.simbolos.get(lexema)

    def obterOuInserir(self, lexema: str, tipoToken: TiposToken) -> Simbolo:
        """Consulta todo lexema e cadastra os identificadores/literais novos."""
        simboloExistente = self.buscar(lexema)

        if simboloExistente is not None:
            return simboloExistente

        if lexema in PALAVRAS_RESERVADAS:
            return self.inserir(
                lexema,
                PALAVRAS_RESERVADAS[lexema],
                CategoriaSimbolo.RESERVADA,
            )

        if lexema in TOKENS_FIXOS:
            return self.inserir(
                lexema,
                TOKENS_FIXOS[lexema],
                CategoriaSimbolo.FIXO,
            )

        tiposLiterais = {
            TiposToken.NUM_INT,
            TiposToken.NUM_FLOAT,
            TiposToken.LITERAL,
            TiposToken.ASCII,
        }

        if tipoToken in tiposLiterais:
            categoria = CategoriaSimbolo.LITERAL
        elif tipoToken == TiposToken.ID:
            categoria = CategoriaSimbolo.IDENTIFICADOR
        else:
            categoria = CategoriaSimbolo.FIXO

        return self.inserir(lexema, tipoToken, categoria)

    def existe(self, lexema: str) -> bool:
        return lexema in self.simbolos

    def remover(self, lexema: str) -> bool:
        if lexema in self.simbolos:
            del self.simbolos[lexema]
            return True
        return False

    def quantidade(self) -> int:
        return len(self.simbolos)
