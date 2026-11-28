import sys

from src.simulador.Simulador import Simulador
from src.tac.ProgramaTAC import ProgramaTAC


def executarPrograma(programa: ProgramaTAC, *, mostrarRastro: bool) -> int:
    """Executa o TAC e, quando solicitado, exibe o rastro após o sucesso."""
    simulador = Simulador()
    try:
        simulador.executar(programa)
    except (TypeError, ValueError, KeyError, IndexError, ArithmeticError,
            RuntimeError, EOFError, OSError) as erro:
        print(f"Erro no simulador: {erro}", file=sys.stderr)
        return 1

    if mostrarRastro:
        rastro = simulador.obterRastro()
        print("\nRastro de execução:")
        for ordem, (pc, instrucao) in enumerate(rastro, start=1):
            print(f"{ordem}: PC {pc} | {instrucao.paraString()}")
        print(f"Total de instruções executadas: {len(rastro)}")
    return 0
