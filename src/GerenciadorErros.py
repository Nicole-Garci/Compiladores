class GerenciadorErros:
    """Gerencia os erros léxicos encontrados durante a análise."""

    def __init__(self):
        self.erros: list[str] = []
        self.quantidadeErros: int = 0

    def registrarErro(
        self,
        mensagem: str,
        linha: int,
        coluna: int
    ) -> None:
        """Registra um erro léxico informando linha e coluna."""

        erro = (
            f"Erro léxico na linha {linha}, "
            f"coluna {coluna}: {mensagem}"
        )

        self.erros.append(erro)
        self.quantidadeErros += 1

    def registrarCaractereInvalido(
        self,
        caractere: str,
        linha: int,
        coluna: int
    ) -> None:
        """Registra a ocorrência de um caractere inválido."""

        mensagem = f"caractere inválido {caractere!r}"

        self.registrarErro(
            mensagem,
            linha,
            coluna
        )

    def possuiErros(self) -> bool:
        """Informa se algum erro foi registrado."""

        return self.quantidadeErros > 0

    def obterQuantidadeErros(self) -> int:
        """Retorna a quantidade de erros registrados."""

        return self.quantidadeErros

    def exibirErros(self) -> None:
        """Exibe todos os erros registrados."""

        for erro in self.erros:
            print(erro)

    def limparErros(self) -> None:
        """Remove todos os erros registrados."""

        self.erros.clear()
        self.quantidadeErros = 0