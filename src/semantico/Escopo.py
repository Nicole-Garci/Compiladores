
from __future__ import annotations

from .models.SimboloSemantico import SimboloSemantico


class Escopo:
    def __init__(self, pai: Escopo | None = None):
        self.pai = pai
        self.simbolos: dict[str, SimboloSemantico] = {}

    def inserir(self, simbolo: SimboloSemantico) -> bool:
        if simbolo.nome in self.simbolos:
            return False

        self.simbolos[simbolo.nome] = simbolo
        return True

    def buscar(self, nome: str) -> SimboloSemantico | None:
        if nome in self.simbolos:
            return self.simbolos[nome]

        if self.pai is not None:
            return self.pai.buscar(nome)

        return None
