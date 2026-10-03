"""Verificador LL(1) baseado em Appel, *Modern Compiler Implementation in C*.

* pp.59-61 do PDF: nullable, FIRST, FOLLOW e Algoritmo 3.13;
* p. 62 do PDF: construção da tabela preditiva e conflitos;
* pp. 63-64 do PDF: recursão à esquerda e sua eliminação.
"""

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


EPSILON = "ε"
EOF = "$"


@dataclass(frozen=True)
class Producao:
    esquerda: str
    direita: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.esquerda} -> {' '.join(self.direita) if self.direita else EPSILON}"


@dataclass(frozen=True)
class Gramatica:
    inicial: str
    producoes: tuple[Producao, ...]
    naoTerminais: frozenset[str]
    terminais: frozenset[str]


def lerGramatica(texto: str) -> Gramatica:
    """Lê o formato .g deste projeto; uma regra `A -> ... | ε` por linha."""

    regras: list[tuple[str, list[str]]] = []

    for numero, linha in enumerate(texto.splitlines(), 1):
        linha = linha.split("#", 1)[0].strip()

        if not linha:
            continue

        if linha.count("->") != 1:
            raise ValueError(f"Linha {numero}: esperado exatamente um '->'")

        esquerda, alternativas = (parte.strip() for parte in linha.split("->"))

        if not esquerda or len(esquerda.split()) != 1:
            raise ValueError(f"Linha {numero}: lado esquerdo inválido")

        for alternativa in re.split(r"\s+\|\s+", alternativas):
            alternativa = alternativa.strip()

            if not alternativa:
                raise ValueError(f"Linha {numero}: alternativa vazia; use {EPSILON}")

            direita = alternativa.split()

            if direita == [EPSILON] or direita == ["epsilon"]:
                direita = []

            elif EPSILON in direita or "epsilon" in direita:
                raise ValueError(f"Linha {numero}: {EPSILON} deve aparecer sozinho")

            regras.append((esquerda, direita))

    if not regras:
        raise ValueError("Gramática sem produções")

    naoTerminais = frozenset(esquerda for esquerda, _ in regras)
    producoes = tuple(Producao(esquerda, tuple(direita)) for esquerda, direita in regras)
    terminais = frozenset(
        simbolo
        for producao in producoes
        for simbolo in producao.direita
        if simbolo not in naoTerminais
    )

    if EOF in terminais or EOF in naoTerminais:
        raise ValueError("'$' é reservado para o fim da entrada")

    return Gramatica(regras[0][0], producoes, naoTerminais, terminais)


@dataclass
class Analise:
    nullable: set[str]
    first: dict[str, set[str]]
    follow: dict[str, set[str]]
    tabela: dict[tuple[str, str], list[Producao]]

    @property
    def conflitos(self) -> dict[tuple[str, str], list[Producao]]:
        return {celula: regras for celula, regras in self.tabela.items() if len(regras) > 1}


def firstSequencia(
    sequencia: tuple[str, ...], nullable: set[str], first: dict[str, set[str]]
) -> tuple[set[str], bool]:
    """Estende FIRST a sequências; Appel, p. 50 (PDF p. 61)."""
    resultado: set[str] = set()
    for simbolo in sequencia:
        resultado.update(first[simbolo])
        if simbolo not in nullable:
            return resultado, False

    return resultado, True


def analisar(gramatica: Gramatica) -> Analise:
    """Aplica o Algoritmo 3.13 (PDF 61) e a tabela (PDF 62)"""

    nullable: set[str] = set()
    first = {simbolo: set() for simbolo in gramatica.naoTerminais}
    first.update({terminal: {terminal} for terminal in gramatica.terminais})
    follow = {simbolo: set() for simbolo in gramatica.naoTerminais}
    follow[gramatica.inicial].add(EOF)

    mudou = True
    while mudou:
        mudou = False

        for producao in gramatica.producoes:
            esquerda, direita = producao.esquerda, producao.direita
            inicio, vazia = firstSequencia(direita, nullable, first)
            antes = len(first[esquerda])
            first[esquerda].update(inicio)
            mudou |= len(first[esquerda]) != antes

            if vazia and esquerda not in nullable:
                nullable.add(esquerda)
                mudou = True

            for indice, simbolo in enumerate(direita):
                if simbolo not in gramatica.naoTerminais:
                    continue
                seguintes, resto_vazio = firstSequencia(direita[indice + 1 :], nullable, first)
                antes = len(follow[simbolo])
                follow[simbolo].update(seguintes)

                if resto_vazio:
                    follow[simbolo].update(follow[esquerda])
                mudou |= len(follow[simbolo]) != antes

    tabela: dict[tuple[str, str], list[Producao]] = defaultdict(list)
    for producao in gramatica.producoes:
        inicio, vazia = firstSequencia(producao.direita, nullable, first)
        previsao = inicio | (follow[producao.esquerda] if vazia else set())

        for terminal in previsao:
            tabela[(producao.esquerda, terminal)].append(producao)

    return Analise(nullable, first, follow, dict(tabela))


def ciclosRecursaoEsquerda(gramatica: Gramatica, nullable: set[str]) -> list[tuple[str, ...]]:
    """Detecta ciclos por prefixos anuláveis,
    ref https://github.com/mna/pigeon/blob/master/ast/ast.go e https://web.cs.wpi.edu/~kal/PLT/PLT4.1.2.html"""
    arestas: dict[str, set[str]] = {nt: set() for nt in gramatica.naoTerminais}
    for producao in gramatica.producoes:
        for simbolo in producao.direita:
            if simbolo not in gramatica.naoTerminais:
                break

            arestas[producao.esquerda].add(simbolo)

            if simbolo not in nullable:
                break

    ciclos: set[tuple[str, ...]] = set()
    for inicio in sorted(arestas):
        def visitar(atual: str, caminho: tuple[str, ...]) -> None:
            for proximo in sorted(arestas[atual]):
                if proximo == inicio:
                    ciclo = caminho + (inicio,)
                    partes = ciclo[:-1]
                    rotacoes = [partes[i:] + partes[:i] for i in range(len(partes))]
                    ciclos.add(min(rotacoes))

                elif proximo not in caminho:
                    visitar(proximo, caminho + (proximo,))

        visitar(inicio, (inicio,))
    return sorted(ciclo + (ciclo[0],) for ciclo in ciclos)


def relatorio(gramatica: Gramatica) -> str:
    analise = analisar(gramatica)
    linhas = [f"Inicial: {gramatica.inicial}", "", "nullable / FIRST / FOLLOW:"]

    for nt in sorted(gramatica.naoTerminais):
        linhas.append(
            f"  {nt}: nullable={'sim' if nt in analise.nullable else 'não'}; "
            f"FIRST={{{', '.join(sorted(analise.first[nt]))}}}; "
            f"FOLLOW={{{', '.join(sorted(analise.follow[nt]))}}}"
        )

    ciclos = ciclosRecursaoEsquerda(gramatica, analise.nullable)
    linhas.extend(["", f"Recursão à esquerda: {len(ciclos)} ciclo(s)"])
    linhas.extend(f"  {' -> '.join(ciclo)}" for ciclo in ciclos)
    linhas.append(f"Conflitos LL(1): {len(analise.conflitos)} célula(s)")
    for (nt, terminal), producoes in sorted(analise.conflitos.items()):
        linhas.append(f"  M[{nt}, {terminal}]: {' ; '.join(map(str, producoes))}")
    if not ciclos and not analise.conflitos:
        linhas.append("Gramática LL(1): sim")
    else:
        linhas.append("Gramática LL(1): não")
    return "\n".join(linhas)


def main() -> int:
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("gramatica", type=Path)
    arquivo = argumentos.parse_args().gramatica

    try:
        gramatica = lerGramatica(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        argumentos.error(str(erro))

    print(relatorio(gramatica))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
