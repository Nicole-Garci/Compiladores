from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TipoSemantico:
    nome: str
    tamanhoBytes: int
    elemento: TipoSemantico | None = None
    comprimento: int | None = None
    campos: dict[str, tuple[TipoSemantico, int]] = field(
        default_factory=dict
    )