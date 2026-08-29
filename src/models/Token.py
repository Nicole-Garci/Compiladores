from src.TiposToken import TiposToken


class Token:
    tipo: TiposToken
    lexema: str
    linha: int
    coluna: int
    indiceSimbolo: int | None = None

    """TODO: Implement functions"""