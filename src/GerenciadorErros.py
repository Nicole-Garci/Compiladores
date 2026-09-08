from src.models.ErroLexer import ErroLexer


class GerenciadorErros:
    """Gerencia os erros léxicos encontrados durante a análise."""

    def __init__(self):
        self.erros: list[ErroLexer] = []

    def registrarErro(self, mensagem: str, linha: int, coluna: int, lexema: str) -> ErroLexer:
        """Registra um erro léxico informando linha e coluna."""
        erro = ErroLexer(mensagem, linha, coluna, lexema)
        self.erros.append(erro)

        return erro


    def registrarCaractereInvalido(self, caractere: str, linha: int, coluna: int) -> ErroLexer:
        """Registra a ocorrência de um caractere inválido."""
        return self.registrarErro("Caractere inválido", linha, coluna, caractere)


    def possuiErros(self) -> bool:
        """Informa se algum erro foi registrado."""
        return bool(self.erros)

    def quantidade(self) -> int:
        """Retorna a quantidade de erros registrados."""
        return len(self.erros)

    def obterErros(self) -> list[ErroLexer]:
        """Retorna todos os erros registrados."""
        return list(self.erros)

    def limpar(self) -> None:
        """Remove todos os erros registrados."""
        self.erros.clear()