from __future__ import annotations

from dataclasses import dataclass, field

from .TipoSemantico import TipoSemantico


@dataclass
class SimboloSemantico:
    nome: str
    categoria: str
    tipo: TipoSemantico
    endereco: OperandoTAC | None = None
    parametros: list[TipoSemantico] = field(
        default_factory=list
    )