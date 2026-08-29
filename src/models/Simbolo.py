from enum import Enum

from src.TiposToken import TiposToken


class CategoriaSimbolo(str, Enum):
    RESERVADA = "palavra reservada"
    IDENTIFICADOR = "identificador"
    LITERAL = "literal"


class Simbolo:
    indice: int
    lexema: str
    tipoToken: TiposToken
    categoria: CategoriaSimbolo

