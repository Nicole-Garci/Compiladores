import argparse
import sys
from pathlib import Path

from src.Lexer import Lexer


CAMINHO_AFD = Path(__file__).resolve().parent / "src" / "AFD.json"


def parser() -> argparse.ArgumentParser:
    analisadorArgumentos = argparse.ArgumentParser(
        description="Executa o analisador lexico da linguagem C--."
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

    for token in tokens:
        print(token.paraString())

    erros = lexer.obterErros()
    sys.stdout.flush()

    for erro in erros:
        print(erro.paraString(), file=sys.stderr)

    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
