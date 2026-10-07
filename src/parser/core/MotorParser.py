from pathlib import Path

from src.lexer.Lexer import Lexer
from src.lexer.models.Token import Token
from src.lexer.TiposToken import TiposToken
from src.parser.SaidaParser import SaidaParser
from src.parser.core.FluxoTokens import FluxoTokens

class MotorParser:
    def __init__(self, fluxo: FluxoTokens, saida: SaidaParser) -> None:
        self.fluxo = fluxo
        self.saida = saida

    def entrar(self, nome: str) -> None:
        self.saida.naoTerminal(nome)

    def casar(self, esperado: TiposToken) -> Token:
        encontrou = self.fluxo.atual()

        if encontrou.tipo is not esperado:
            raise SyntaxError(
                f"Erro sintático em {encontrou.linha}:{encontrou.coluna}: Era esperado {esperado.name}, "
                f"mas foi encontrado {encontrou.tipo.name}"
            )

        self.saida.terminalCasado(encontrou)
        self.fluxo.avancar()

        return encontrou
