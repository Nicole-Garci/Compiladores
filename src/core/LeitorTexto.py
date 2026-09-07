"""Leitura e navegacao pelo texto-fonte."""

from os import PathLike
from pathlib import Path


class LeitorTexto:
    """Mantem o texto de entrada e a posicao atual de leitura."""

    def __init__(self, texto: str = "") -> None:
        self.carregarTexto(texto)

    def carregarTexto(self, texto: str) -> None:
        """Substitui a entrada e retorna o cursor para o inicio."""
        self.texto = texto
        self.tamanho = len(texto)
        self.posicao = 0
        self.linha = 1
        self.coluna = 1

    def carregarArquivo(
        self,
        nomeArquivo: str | PathLike[str],
        encoding: str = "utf-8",
    ) -> bool:
        """Carrega um arquivo e informa se a operacao foi bem-sucedida."""
        try:
            texto = Path(nomeArquivo).read_text(encoding=encoding)
        except (OSError, UnicodeError):
            return False

        self.carregarTexto(texto)
        return True

    def obterLinha(self) -> int:
        return self.linha

    def obterColuna(self) -> int:
        return self.coluna

    def obterPosicao(self) -> int:
        return self.posicao

    def chegouAoFim(self) -> bool:
        return self.posicao >= self.tamanho

    def observarCaractere(self, deslocamento: int = 0) -> str | None:
        indice = self.posicao + deslocamento
        if indice < 0 or indice >= self.tamanho:
            return None
        return self.texto[indice]

    def avancar(self) -> str | None:
        """Retorna o caractere atual e avanca o cursor uma posicao."""
        if self.chegouAoFim():
            return None

        caractere = self.texto[self.posicao]
        caractereAnterior = self.texto[self.posicao - 1] if self.posicao else None
        self.posicao += 1

        if caractere == "\r":
            self.linha += 1
            self.coluna = 1
        elif caractere == "\n":
            if caractereAnterior != "\r":
                self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1

        return caractere

    def criarMarco(self):
        """Salva a posição, linha e coluna atuais"""
        return self.posicao, self.linha, self.coluna

    def restaurarMarco(self, marco: tuple[int, int, int]):
        """Restaura uma posição salva anteriormente"""
        self.posicao, self.linha, self.coluna = marco
