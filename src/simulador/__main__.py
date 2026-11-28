import argparse
import sys
from pathlib import Path

from src.simulador.cli import executarPrograma
from src.tac.ProgramaTAC import ProgramaTAC
from src.tac.LeitorTAC import carregarTAC, diagnosticosTAC


def main(argv: list[str] | None = None) -> int:
    """Executa TAC: 0 sucesso, 1 falha de execução/validação, 2 entrada inválida."""
    argumentos = argparse.ArgumentParser(
        description="Executa um programa TAC JSON ou textual (.tac) e apresenta o rastro de execução."
    )
    argumentos.add_argument("arquivo", help="caminho do arquivo TAC JSON ou textual (.tac)")
    opcoes = argumentos.parse_args(argv)

    try:
        textual = Path(opcoes.arquivo).suffix.lower() == ".tac"
        programa = (carregarTAC(opcoes.arquivo) if textual
                    else ProgramaTAC.carregar(opcoes.arquivo))
    except (OSError, UnicodeError, ValueError, TypeError) as erro:
        print(f"Erro ao carregar TAC: {erro}", file=sys.stderr)
        return 2

    if textual:
        erros = diagnosticosTAC(programa)
        if erros:
            print("Erro no simulador: " + "\n".join(erros), file=sys.stderr)
            return 1

    return executarPrograma(programa, mostrarRastro=True)


if __name__ == "__main__":
    raise SystemExit(main())
