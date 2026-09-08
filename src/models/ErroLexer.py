from dataclasses import dataclass


@dataclass(frozen=True)
class ErroLexer:
    mensagem: str
    linha: int
    coluna: int
    lexema: str

    def paraString(self) -> str:
        return(
            f"Erro léxico na linha {self.linha}, "
            f"coluna {self.coluna}: {self.mensagem}. "
            f"Lexema: {self.lexema!r}"
        )