from __future__ import annotations

from dataclasses import dataclass

from .OperandoTAC import OperandoTAC


@dataclass(frozen=True)
class InstrucaoTAC:
    opcode: str
    operandos: tuple[OperandoTAC | None, ...] = ()
    linha: int = 0
    coluna: int = 0
