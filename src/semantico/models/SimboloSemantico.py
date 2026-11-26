from __future__ import annotations

from dataclasses import dataclass, field

from src.tac.OperandoTAC import OperandoTAC

from .TipoSemantico import TipoSemantico


CATEGORIA_VARIAVEL = "variavel"
CATEGORIA_VETOR = "vetor"
CATEGORIA_PARAMETRO = "parametro"
CATEGORIA_FUNCAO = "funcao"


@dataclass
class SimboloSemantico:
    nome: str
    categoria: str
    tipo: TipoSemantico
    endereco: OperandoTAC | None = None
    parametros: list[TipoSemantico] = field(
        default_factory=list
    )
    linha: int = 0
    coluna: int = 0
