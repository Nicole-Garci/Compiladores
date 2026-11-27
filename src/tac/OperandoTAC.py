from dataclasses import dataclass


@dataclass(frozen=True)
class OperandoTAC:
    categoria: str
    valor: int | float | bool | str

    def __post_init__(self) -> None:
        if not isinstance(self.categoria, str) or not self.categoria:
            raise ValueError("A categoria do operando deve ser uma string não vazia.")
        if not isinstance(self.valor, (int, float, bool, str)):
            raise TypeError("O valor do operando deve ser int, float, bool ou str.")

    def paraString(self) -> str:
        return f"{self.categoria}[{self.valor}]"