from src.lexer.GerenciadorErros import GerenciadorErros
from src.lexer.TabelaSimbolos import TabelaSimbolos
from src.lexer.TiposToken import TiposToken
from src.lexer.core.Reconhecedor import Reconhecedor
from src.lexer.models.Token import Token


class MotorLexer:
    """Orquestrador Lexer"""

    def __init__(
        self,
        reconhecedor: Reconhecedor,
        tabelaSimbolos: TabelaSimbolos,
        gerenciadorErros: GerenciadorErros,
    ) -> None:
        self.reconhecedor = reconhecedor
        self.tabSimbolos = tabelaSimbolos
        self.gerenciadorErros = gerenciadorErros
        self.tokens: list[Token] = list()

    def processarToken(self, token: Token) -> None:
        if token.tipo == TiposToken.UNKNOWN:
            self.gerenciadorErros.registrarErro(
                token.mensagemErro or "Token não reconhecido",
                token.linha,
                token.coluna,
                token.lexema or "",
            )
            return

        if token.tipo != TiposToken.END_OF_FILE and token.lexema is not None:
            simbolo = self.tabSimbolos.obterOuInserir(token.lexema, token.tipo)
            token.tipo = simbolo.tipoToken
            token.indiceSimbolo = simbolo.indice

        self.tokens.append(token)

    def executar(self) -> list[Token]:
        self.tokens.clear()
        self.gerenciadorErros.limpar()

        while True:
            token = self.reconhecedor.proximoToken()
            self.processarToken(token)

            if token.tipo == TiposToken.END_OF_FILE:
                break

        return list(self.tokens)
