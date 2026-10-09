from typing import TextIO

import sys

from src.lexer.models.Token import Token


class SaidaParser:

    def __init__(self, destino: TextIO | None = None) -> None:
        if destino is not None:
            self.destino = destino
        else:
            self.destino = sys.stdout

    def naoTerminal(self, nome: str) -> None:
        print(nome, file=self.destino)

    def terminalCasado(self, token: Token) -> None:
        print(f"Match: {token.paraString()}", file=self.destino)
