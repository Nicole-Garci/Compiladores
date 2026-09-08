from src.GerenciadorErros import GerenciadorErros
from src.TabelaSimbolos import TabelaSimbolos
from src.TiposToken import TiposToken
from src.core.Reconhecedor import Reconhecedor
from src.models.Token import Token


class MotorLexer:
    """Orquestrador Lexer"""

    def __init__(self, reconhecedor: Reconhecedor, tabelaSimbolos: TabelaSimbolos, gerenciadorErros: GerenciadorErros):
        self.reconhecedor = reconhecedor
        self.tabSimbolos = tabelaSimbolos
        self.gerenciadorErros = gerenciadorErros
        self.tokens: list[Token] = list()

    def registrarSimbolo(self, token: Token) -> None:
        tipos = {
            TiposToken.ID, TiposToken.NUM_INT, TiposToken.NUM_FLOAT, TiposToken.LITERAL, TiposToken.ASCII
        }

        if token.tipo not in tipos: return

        if token.lexema is None: return

        simbolo = self.tabSimbolos.obterOuInserir(token.lexema, token.tipo)

        token.indiceSimbolo = simbolo.indice


    def processarToken(self, token: Token) -> None:
        if token.tipo == TiposToken.UNKNOWN:
            self.gerenciadorErros.registrarErro("Token não reconhecido", token.linha, token.coluna,
                                                token.lexema or "")
            return

        self.registrarSimbolo(token)
        self.tokens.append(token)

    def executar(self) -> list[Token]:
        self.tokens.clear()
        self.gerenciadorErros.limpar()

        while 1:
            token = self.reconhecedor.proximoToken()
            self.processarToken(token)

            if token.tipo == TiposToken.END_OF_FILE:
                break

        return list(self.tokens)