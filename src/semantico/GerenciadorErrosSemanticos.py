from __future__ import annotations

from typing import Any

from .models.ErroSemantico import ErroSemantico


class GerenciadorErrosSemanticos:
    def __init__(self):
        self.erros: list[ErroSemantico] = []

    def registrar(self, noAST: Any, mensagem: str) -> ErroSemantico:
        linha = getattr(noAST, "linha", 0)
        coluna = getattr(noAST, "coluna", 0)

        erro = ErroSemantico(
            mensagem=mensagem,
            linha=linha,
            coluna=coluna
        )

        self.erros.append(erro)
        return erro

    def obterErros(self) -> list[ErroSemantico]:
        return self.erros.copy()

    def limpar(self) -> None:
        self.erros.clear()
