from __future__ import annotations

from dataclasses import dataclass, field

from .InstrucaoTAC import InstrucaoTAC


@dataclass
class ProgramaTAC:
    entrada: str = "main"
    tamanhoDados: int = 0
    quadros: dict[str, tuple[int, list[int]]] = field(default_factory=dict)
    instrucoes: list[InstrucaoTAC] = field(default_factory=list)

    def salvar(self, caminho: str) -> None:
        raise NotImplementedError("Gravação do código de três endereços ainda não implementada")

    @staticmethod
    def carregar(caminho: str) -> ProgramaTAC:
        raise NotImplementedError("Leitura do código de três endereços ainda não implementada")
