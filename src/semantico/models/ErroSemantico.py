from dataclasses import dataclass


@dataclass(frozen=True)
class ErroSemantico:
    mensagem: str
    linha: int
    coluna: int

    def paraString(self) -> str:
        return (
            f"Erro semântico na linha {self.linha}, "
            f"coluna {self.coluna}: {self.mensagem}"
        )
