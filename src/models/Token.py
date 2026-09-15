from dataclasses import dataclass

from src.TiposToken import NOMES_TOKEN, TiposToken


@dataclass
class Token:
    tipo: TiposToken
    lexema: str | None
    linha: int
    coluna: int
    indiceSimbolo: int | None = None
    mensagemErro: str | None = None

    def paraString(self) -> str:
        nomeTipo = NOMES_TOKEN.get(self.tipo, "UNKNOWN")

        tiposComLexema = {
            TiposToken.ID, TiposToken.NUM_INT, TiposToken.NUM_FLOAT,
        }

        if self.tipo in tiposComLexema:
            return f"{nomeTipo}.{self.lexema}"

        return nomeTipo