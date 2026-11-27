
class BancoRegistradores:

    def __init__(self) -> None:
        self._especiais: dict[str, object] = {
            "$zero": 0,
            "$sp": 0,
            "$fp": 0,
            "$ra": None,
            "$v0": None,
        }

        self._temporarios: dict[int, object] = {}

    def ler(self, chave: str | int) -> object:
        self._validarChave(chave)

        if isinstance(chave, str):
            return self._especiais[chave]

        if chave not in self._temporarios:
            raise KeyError(
                f"Temporário {chave} não inicializado."
            )

        return self._temporarios[chave]

    def escrever(self, chave: str | int, valor: object) -> None:
        self._validarChave(chave)

        if isinstance(chave, str):
            if chave == "$zero":
                raise ValueError(
                    "O registrador '$zero' é somente leitura."
                )

            self._especiais[chave] = valor

        else:
            self._temporarios[chave] = valor

    def trocarTemporarios(
        self, novos: dict[int, object]
    ) -> dict[int, object]:

        if not isinstance(novos, dict):
            raise TypeError(
                "Os temporários devem ser um dicionário."
            )

        novosTemporarios = novos.copy()

        for chave in novosTemporarios:
            if not isinstance(chave, int) or isinstance(chave, bool):
                raise TypeError(
                    "As chaves dos temporários devem ser inteiros."
                )

            self._validarChave(chave)

        anteriores = self._temporarios
        self._temporarios = novosTemporarios

        return anteriores

    def _validarChave(self, chave: str | int) -> None:
        if isinstance(chave, bool) or not isinstance(chave, (str, int)):
            raise TypeError(
                "A chave deve ser uma string ou um inteiro."
            )

        if isinstance(chave, str):
            if chave not in self._especiais:
                raise KeyError(
                    f"Registrador especial desconhecido: '{chave}'."
                )

        elif chave < 0:
            raise ValueError(
                "O índice do temporário não pode ser negativo."
            )
