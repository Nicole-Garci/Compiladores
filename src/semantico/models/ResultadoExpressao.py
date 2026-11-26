from __future__ import annotations

from dataclasses import dataclass

from src.tac.OperandoTAC import OperandoTAC

from .TipoSemantico import TipoSemantico


@dataclass
class ResultadoExpressao:
    tipo: TipoSemantico
    operando: OperandoTAC | None = None
    deslocamento: OperandoTAC | None = None
    atribuivel: bool = False
