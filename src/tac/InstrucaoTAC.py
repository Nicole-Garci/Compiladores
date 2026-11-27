from __future__ import annotations

from dataclasses import dataclass

from .OperandoTAC import OperandoTAC


@dataclass(frozen=True)
class InstrucaoTAC:
    opcode: str
    operandos: tuple[OperandoTAC | None, ...] = ()
    linha: int = 0
    coluna: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.opcode, str) or not self.opcode:
            raise ValueError("O opcode deve ser uma string não vazia.")
        operandos = tuple(self.operandos)
        if any(op is not None and not isinstance(op, OperandoTAC) for op in operandos):
            raise TypeError("Cada operando deve ser OperandoTAC ou None.")
        object.__setattr__(self, "operandos", operandos)
        if (not isinstance(self.linha, int) or isinstance(self.linha, bool)
                or not isinstance(self.coluna, int) or isinstance(self.coluna, bool)):
            raise TypeError("Linha e coluna devem ser inteiros.")
        if self.linha < 0 or self.coluna < 0:
            raise ValueError("Linha e coluna não podem ser negativas.")

    def paraString(self) -> str:
        """Retorna uma representação legível da instrução TAC."""
        operandos = ", ".join(
            "_" if operando is None else operando.paraString()
            for operando in self.operandos
        )
        return f"{self.opcode} {operandos}".rstrip()

    def validar(self) -> list[str]:
        """Devolve problemas de acordo com o conjunto de opcodes TAC definido."""
        from .ContratoTAC import validarInstrucaoTAC

        return validarInstrucaoTAC(self)