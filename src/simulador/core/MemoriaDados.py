class MemoriaDados:
    """Memória por posições; leituras reservadas ainda não escritas retornam None."""

    def __init__(self, tamanhoDados: int = 0) -> None:
        self._validarInteiro(tamanhoDados, "Tamanho dos dados")
        self._dadosEstaticos: dict[int, object] = {
            endereco: None for endereco in range(tamanhoDados)
        }
        self._pilha: list[object] = []
        self._basesQuadros: list[int] = []

    def reservarQuadro(self, tamanho: int) -> int:
        """Reserva posições e registra também quadros vazios."""
        self._validarInteiro(tamanho, "Tamanho do quadro")
        base = len(self._pilha)
        self._pilha.extend([None] * tamanho)
        self._basesQuadros.append(base)
        return base

    def liberarQuadro(self, base: int) -> None:
        """Libera somente o quadro do topo, cuja base deve coincidir.
        Quadros vazios podem compartilhar a base. Cada chamada remove
        somente o registro mais recente, mesmo nesse caso.
        """
        self._validarInteiro(base, "Base do quadro")
        if not self._basesQuadros or base != self._basesQuadros[-1]:
            raise ValueError("A base deve pertencer ao quadro mais recente.")
        del self._pilha[base:]
        self._basesQuadros.pop()

    def ler(self, regiao: str, endereco: int) -> object:
        """Lê uma posição reservada; endereços locais são absolutos."""
        self._validarAcesso(regiao, endereco)
        if regiao == "global":
            return self._dadosEstaticos[endereco]
        return self._pilha[endereco]

    def escrever(self, regiao: str, endereco: int, valor: object) -> None:
        """Escreve em uma posição já reservada da região indicada."""
        self._validarAcesso(regiao, endereco)
        if regiao == "global":
            self._dadosEstaticos[endereco] = valor
        else:
            self._pilha[endereco] = valor

    def _validarAcesso(self, regiao: str, endereco: int) -> None:
        if not isinstance(regiao, str):
            raise TypeError("A região deve ser uma string.")
        if regiao not in {"global", "local"}:
            raise ValueError(f"Região de memória desconhecida: '{regiao}'.")
        self._validarInteiro(endereco, "Endereço")
        tamanho = len(self._dadosEstaticos) if regiao == "global" else len(self._pilha)
        if endereco >= tamanho:
            raise IndexError(f"Endereço {endereco} fora da região '{regiao}'.")

    @staticmethod
    def _validarInteiro(valor: int, nome: str) -> None:
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise TypeError(f"{nome} deve ser inteiro.")
        if valor < 0:
            raise ValueError(f"{nome} não pode ser negativo.")
