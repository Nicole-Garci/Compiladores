from dataclasses import dataclass
from enum import Enum

from src.TiposToken import TiposToken


class CategoriaSimbolo(str, Enum):
    RESERVADA = "palavra reservada"
    IDENTIFICADOR = "identificador"
    LITERAL = "literal"
    FIXO = "operador ou delimitador"


@dataclass(frozen=True)
class Simbolo:
    indice: int
    lexema: str
    tipoToken: TiposToken
    categoria: CategoriaSimbolo

