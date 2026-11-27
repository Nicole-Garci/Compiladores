from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.ProgramaTAC import ProgramaTAC


class MemoriaInstrucoes:
    """Armazena TAC validado, preservando labels e seus índices originais."""

    def __init__(self) -> None:
        self._instrucoes: list[InstrucaoTAC] = []
        self._rotulos: dict[str, int] = {}

    def carregar(self, programa: ProgramaTAC) -> None:
        """Substitui o conteúdo somente após validar e preparar o programa."""
        if not isinstance(programa, ProgramaTAC):
            raise TypeError("O programa deve ser ProgramaTAC.")
        erros = programa.validar()
        if erros:
            raise ValueError("Programa TAC inválido:\n" + "\n".join(erros))

        instrucoes = list(programa.instrucoes)
        rotulos = {
            instrucao.operandos[0].valor: indice
            for indice, instrucao in enumerate(instrucoes)
            if instrucao.opcode == "label"
        }
        self._instrucoes = instrucoes
        self._rotulos = rotulos

    def buscar(self, pc: int) -> InstrucaoTAC:
        if not isinstance(pc, int) or isinstance(pc, bool):
            raise TypeError("O PC deve ser inteiro.")
        if pc < 0:
            raise ValueError("O PC não pode ser negativo.")
        if pc >= len(self._instrucoes):
            raise IndexError(f"PC {pc} fora da memória de instruções.")
        return self._instrucoes[pc]

    def resolverRotulo(self, nome: str) -> int:
        if not isinstance(nome, str):
            raise TypeError("O nome do rótulo deve ser uma string.")
        if nome not in self._rotulos:
            raise KeyError(f"Rótulo não definido: '{nome}'.")
        return self._rotulos[nome]
