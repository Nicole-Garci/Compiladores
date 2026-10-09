import argparse
import sys
from pathlib import Path

from src.parser.GerenciadorErrosSintaticos import GerenciadorErrosSintaticos
from src.parser.SaidaParser import SaidaParser
from src.parser.core.FluxoTokens import FluxoTokens
from src.parser.core.MotorParser import MotorParser
from src.lexer.Lexer import Lexer


CAMINHO_AFD = Path(__file__).resolve().parent / "src" / "lexer" / "AFD.json"


def parser() -> argparse.ArgumentParser:
    analisadorArgumentos = argparse.ArgumentParser(
        description="Executa o compilador da linguagem C--."
    )
    analisadorArgumentos.add_argument(
        "arquivo",
        help="caminho do arquivo-fonte .cmm",
    )
    return analisadorArgumentos


def main(argv: list[str] | None = None) -> int:
    argumentos = parser().parse_args(argv)
    lexer = Lexer(str(CAMINHO_AFD))

    try:
        tokens = lexer.analisarArquivo(argumentos.arquivo)
    except (ValueError, FileNotFoundError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2

    # for token in tokens:
    #     print(token.paraString())

    errosLexer = lexer.obterErros()
    sys.stdout.flush()

    if errosLexer:
        print("\nErros léxicos encontrados: ")
        for erro in errosLexer:
            print(erro.paraString(), file=sys.stderr)
        return 1

    erros = GerenciadorErrosSintaticos()
    fluxo = FluxoTokens(tokens)
    saida = SaidaParser()
    motor = MotorParser(fluxo, saida, erros)
    motor.executar()

    errosParser = erros.obterErros()
    sys.stdout.flush()


    if errosParser:
        print("\nErros sintáticos encontrados:", file=sys.stderr)
        erros.imprimirErros()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
