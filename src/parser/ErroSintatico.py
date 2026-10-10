from dataclasses import dataclass, field

from src.lexer.models.Token import Token
from src.lexer.TiposToken import TiposToken


@dataclass(frozen=True)
class ErroSintatico:
    """Representa um erro encontrado durante a análise sintática."""

    mensagem: str
    encontrado: Token
    esperados: frozenset[TiposToken] = field(
        default_factory=frozenset
    )
    recuperacao: str = ""

    @property
    def linha(self) -> int:
        return self.encontrado.linha

    @property
    def coluna(self) -> int:
        return self.encontrado.coluna

    def paraString(self) -> str:
        texto = (
            f"\nErro sintático na linha {self.linha}, "
            f"coluna {self.coluna}: {self.mensagem}"
        )

        texto += (
            f"\nEncontrado: {self.encontrado.tipo.name} "
            f"('{self.encontrado.lexema}')"
        )

        if self.esperados:
            esperados = ", ".join(
                sorted(tipo.name for tipo in self.esperados)
            )
            texto += f"\nEsperado: {esperados}"

        if self.recuperacao:
            texto += f"\nRecuperação: {self.recuperacao}"

        return texto

    def __str__(self) -> str:
        return self.paraString()