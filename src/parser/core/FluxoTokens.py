from src.lexer.TiposToken import TiposToken
from src.lexer.models.Token import Token


class FluxoTokens:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tuple(tokens)
        self.indice = 0

    def atual(self) -> Token:
        return self.tokens[self.indice]

    def avancar(self) -> Token:
        consomiu = self.atual()

        if not self.chegouAoFim():
            self.indice += 1

        return consomiu

    def chegouAoFim(self) -> bool:
        return self.verificar(TiposToken.END_OF_FILE)

    def verificar(self, tipo: TiposToken) -> bool:
        return self.atual().tipo is tipo

    def posicao(self) -> int:
        return self.indice