from src.TiposToken import TiposToken
from src.models.Simbolo import Simbolo, CategoriaSimbolo

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

class TabelaSimbolos:
    def __init__(self):
        self.simbolos: dict[str, Simbolo] = {}
        self.proximoIndice = 0
        self.carregar_palavras_reservadas()

    def carregar_palavras_reservadas(self):
        # Carrega as palavras reservadas iniciais da linguagem
        for lexema, tipoToken in PALAVRAS_RESERVADAS.items():
            self.inserir(lexema, tipoToken, CategoriaSimbolo.RESERVADA)

    def inserir(self, lexema: str, tipo_token: TiposToken, categoria: CategoriaSimbolo) -> Simbolo:
        simboloExistente = self.buscar(lexema)

        if simboloExistente is not None:
            return simboloExistente

        simbolo = Simbolo(indice=self.proximoIndice, lexema=lexema, tipoToken=tipo_token, categoria=categoria)

        # Insere um novo símbolo na tabela
        self.simbolos[lexema] = simbolo
        self.proximoIndice += 1

        return simbolo

    def buscar(self, lexema: str) -> Simbolo | None:
        """Retorna o símbolo ou None quando o lexema não está cadastrado."""
        return self.simbolos.get(lexema)

    def obterOuInserir(self, lexema: str, tiposToken: TiposToken) -> Simbolo:
        simboloExistente = self.buscar(lexema)

        if simboloExistente is not None:
            return simboloExistente

        tiposLiterais = {TiposToken.NUM_INT, TiposToken.NUM_FLOAT, TiposToken.LITERAL, TiposToken.ASCII}

        if tiposToken in tiposLiterais:
            categoria = CategoriaSimbolo.LITERAL
        else: categoria = CategoriaSimbolo.IDENTIFICADOR

        return self.inserir(lexema, tiposToken, categoria)

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