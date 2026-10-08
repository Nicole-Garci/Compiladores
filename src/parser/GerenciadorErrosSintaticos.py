from src.lexer.models.Token import Token
from src.lexer.TiposToken import TiposToken
from src.parser.ErroSintatico import ErroSintatico


class GerenciadorErrosSintaticos:
    """Gerencia os erros encontrados durante a análise sintática."""

    def __init__(self):
        self.erros: list[ErroSintatico] = []

    def registrar(
        self,
        token: Token,
        mensagem: str,
        esperados: set[TiposToken] | None = None,
        recuperacao: str = "",
    ) -> ErroSintatico:

        erro = ErroSintatico(
            mensagem=mensagem,
            linha=token.linha,
            coluna=token.coluna,
            encontrado=token,
            esperados=frozenset(
                esperados if esperados is not None else ()
            ),
            recuperacao=recuperacao,
        )

        self.erros.append(erro)

        return erro

    def obterErros(self) -> list[ErroSintatico]:
        return list(self.erros)

    def possuiErros(self) -> bool:
        return bool(self.erros)

    def quantidade(self) -> int:
        return len(self.erros)

    def limpar(self) -> None:
        self.erros.clear()