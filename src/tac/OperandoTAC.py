from dataclasses import dataclass


@dataclass(frozen=True)
class OperandoTAC:
    categoria: str
    valor: int | float | bool | str

    def paraString(self) -> str:
        return f"{self.categoria}[{self.valor}]"
