from typing import TextIO

import sys

from src.lexer.models.Token import Token


class SaidaParser:

    def __init__(self, destino: TextIO | None = None, *, habilitada: bool = True) -> None:
        self.habilitada = habilitada
        if destino is not None:
            self.destino = destino
        else:
            self.destino = sys.stdout

    def naoTerminal(self, nome: str) -> None:
        if self.habilitada:
            print(nome, file=self.destino)

    def terminalCasado(self, token: Token) -> None:
        if self.habilitada:
            print(f"Match: {token.paraString()}", file=self.destino)
