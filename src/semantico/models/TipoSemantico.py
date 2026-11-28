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

    def ehVetor(self) -> bool:
        return self.elemento is not None

    def ehStruct(self) -> bool:
        return not self.ehVetor() and self.nome.startswith("struct ")

    def ehAgregado(self) -> bool:
        return self.ehVetor() or self.ehStruct()

    def ehErro(self) -> bool:
        return self.nome == "erro"

    def paraString(self) -> str:
        return self.nome


TAMANHO_POSICAO = 1

TIPO_INT = TipoSemantico("int", TAMANHO_POSICAO)
TIPO_FLOAT = TipoSemantico("float", TAMANHO_POSICAO)
TIPO_CHAR = TipoSemantico("char", TAMANHO_POSICAO)
TIPO_BOOL = TipoSemantico("bool", TAMANHO_POSICAO)
TIPO_ERRO = TipoSemantico("erro", TAMANHO_POSICAO)

TIPOS_PRIMITIVOS = {
    tipo.nome: tipo for tipo in (TIPO_INT, TIPO_FLOAT, TIPO_CHAR, TIPO_BOOL)
}


def tipoVetor(elemento: TipoSemantico, comprimento: int) -> TipoSemantico:
    return TipoSemantico(
        nome=f"{elemento.nome}[{comprimento}]",
        tamanhoBytes=elemento.tamanhoBytes * comprimento,
        elemento=elemento,
        comprimento=comprimento,
    )
