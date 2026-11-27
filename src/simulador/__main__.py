import argparse
import sys

from src.simulador.Simulador import Simulador
from src.tac.ProgramaTAC import ProgramaTAC


def main(argv: list[str] | None = None) -> int:
    """Executa TAC: 0 sucesso, 1 falha de execução/validação, 2 entrada inválida."""
    argumentos = argparse.ArgumentParser(
        description="Executa um programa TAC JSON e apresenta o rastro de execução."
    )
    argumentos.add_argument("arquivo", help="caminho do arquivo TAC JSON")
    opcoes = argumentos.parse_args(argv)

    try:
        programa = ProgramaTAC.carregar(opcoes.arquivo)
    except (OSError, UnicodeError, ValueError, TypeError) as erro:
        print(f"Erro ao carregar TAC: {erro}", file=sys.stderr)
        return 2

    simulador = Simulador()
    try:
        simulador.executar(programa)
        rastro = simulador.obterRastro()
        print("\nRastro de execução:")
        for ordem, (pc, instrucao) in enumerate(rastro, start=1):
            print(f"{ordem}: PC {pc} | {instrucao.paraString()}")
        print(f"Total de instruções executadas: {len(rastro)}")
    except (TypeError, ValueError, KeyError, IndexError, ArithmeticError,
            RuntimeError, EOFError, OSError) as erro:
        print(f"Erro no simulador: {erro}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
