import json
import re
from pathlib import Path

class AFD:
    """Autômato finito determinístico configurado em JSON."""

    def __init__(self, caminhoJson: str) -> None:
        with Path(caminhoJson).open("r", encoding="utf-8") as arquivo:
            data = json.load(arquivo)
            
        self.estadoInicial = data["initial_state"]
        self.estados = {int(k): v for k, v in data["states"].items()}
        self.estadosFinais = set(data["final_states"])
        self.estadoErro = next(
            (numero for numero, nome in self.estados.items() if nome == "qERRO"),
            None,
        )

        if self.estadoInicial not in self.estados:
            raise ValueError("Estado inicial do AFD não foi declarado")
        if not self.estadosFinais.issubset(self.estados):
            raise ValueError("O AFD contém estado final não declarado")
        
        self.transicoes: dict[int, list[tuple[int, str]]] = {}
        for transicao in data["transitions"]:
            estadoOrigem = transicao["from"]
            estadoDestino = transicao["to"]
            condicao = transicao["read"]
            
            self.transicoes.setdefault(estadoOrigem, []).append(
                (estadoDestino, condicao)
            )
            
        self.estadoAtual = self.estadoInicial

    def reiniciar(self) -> None:
        self.estadoAtual = self.estadoInicial

    def ehEstadoFinal(self) -> bool:
        return self.estadoAtual in self.estadosFinais

    def obterEstadoAtual(self) -> str:
        return self.estados.get(self.estadoAtual, "qUNKNOWN")

    def ehEstadoDeErro(self) -> bool:
        return self.estadoErro is not None and self.estadoAtual == self.estadoErro

    def transicionar(self, caractere: str) -> bool:
        if self.estadoAtual not in self.transicoes:
            return False
            
        for estadoDestino, condicao in self.transicoes[self.estadoAtual]:
            if self._avaliarCondicao(caractere, condicao):
                self.estadoAtual = estadoDestino
                return True
                
        if self.estadoErro is not None:
            self.estadoAtual = self.estadoErro
        return False

    def _avaliarCondicao(self, caractere: str, condicao: str) -> bool:
        if caractere == condicao:
            return True
            
        if condicao == "letra":
            return bool(re.fullmatch(r"[a-zA-Z]", caractere))

        if condicao == "dígito":
            return bool(re.fullmatch(r"[0-9]", caractere))

        if condicao == "letra | dígito":
            return bool(re.fullmatch(r"[a-zA-Z0-9]", caractere))

        if "whitespace" in condicao:
            return caractere in (" ", "\t", "\n", "\r")

        if condicao == "caractere ≠ *":
            return caractere != "*"

        if condicao == "caractere ≠ * e ≠ /":
            return caractere not in ("*", "/")

        if condicao == "caractere ≠ \" e ≠ quebra de linha":
            return caractere not in ('"', "\n", "\r")

        if condicao == "ASCII válido":
            return (
                len(caractere) == 1
                and caractere.isascii()
                and caractere not in ("'", "\n", "\r")
            )

        return False