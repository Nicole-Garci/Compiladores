"""Fachada pública do analisador sintático."""

from src.lexer.models.Token import Token
from src.parser.ErroSintatico import ErroSintatico
from src.parser.GerenciadorErrosSintaticos import GerenciadorErrosSintaticos
from src.parser.SaidaParser import SaidaParser
from src.parser.ast.Nos import Programa
from src.parser.core.FluxoTokens import FluxoTokens
from src.parser.core.MotorParser import MotorParser


class Parser:
    """Recebe tokens do lexer e executa uma análise sintática isolada."""

    def __init__(
        self,
        gerenciadorErros: GerenciadorErrosSintaticos | None = None,
        saida: SaidaParser | None = None,
    ) -> None:
        self.gerenciadorErros = gerenciadorErros or GerenciadorErrosSintaticos()
        self.saida = saida or SaidaParser()

    def analisar(self, tokens: list[Token]) -> Programa:
        if not tokens:
            raise ValueError("A análise sintática precisa receber tokens do lexer")

        self.gerenciadorErros.limpar()
        fluxo = FluxoTokens(tokens)
        motor = MotorParser(fluxo, self.saida, self.gerenciadorErros)
        return motor.executar()

    def obterErros(self) -> list[ErroSintatico]:
        return self.gerenciadorErros.obterErros()
