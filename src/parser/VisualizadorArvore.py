from dataclasses import fields, is_dataclass
from pathlib import Path
import shutil
import subprocess
from typing import TextIO

from src.parser.ast.Nos import NoAST


CAMPOS_POSICAO = {"linha", "coluna"}


class VisualizadorArvore:
    @staticmethod
    def campoGuardaNo(campo) -> bool:
        anotacao = str(campo.type)
        return "Expr" in anotacao or "Comando" in anotacao

    def descrever(self, no: NoAST, rotulo: str = "") -> tuple[str, list[tuple[str, NoAST | None]]]:
        atributos = []
        filhos = []

        for campo in fields(no):
            if campo.name in CAMPOS_POSICAO:
                continue

            valor = getattr(no, campo.name)
            if isinstance(valor, list):
                filhos.extend(
                    (f"{campo.name}[{i}]", item) for i, item in enumerate(valor)
                )
            elif is_dataclass(valor):
                filhos.append((campo.name, valor))
            elif valor is not None:
                atributos.append(f"{campo.name}={valor}")
            elif self.campoGuardaNo(campo):
                filhos.append((campo.name, None))

        nome = type(no).__name__
        if atributos:
            nome += f" ({', '.join(atributos)})"
        if rotulo:
            nome = f"{rotulo}: {nome}"
        return nome, filhos

    def imprimir(self, raiz: NoAST, destino: TextIO | None = None) -> None:
        def visitar(no: NoAST, prefixo: str, rotulo: str, ultimo: bool, inicial: bool) -> None:
            nome, filhos = self.descrever(no, rotulo)
            conector = "" if inicial else ("`-- " if ultimo else "|-- ")
            print(f"{prefixo}{conector}{nome}", file=destino)
            prefixoFilhos = "" if inicial else prefixo + ("    " if ultimo else "|   ")

            for indice, (rotuloFilho, valor) in enumerate(filhos):
                ultimoFilho = indice == len(filhos) - 1
                if valor is None:
                    conectorFilho = "`-- " if ultimoFilho else "|-- "
                    print(f"{prefixoFilhos}{conectorFilho}{rotuloFilho}: <erro>", file=destino)
                else:
                    visitar(valor, prefixoFilhos, rotuloFilho, ultimoFilho, False)

        visitar(raiz, "", "", True, True)

    def exportarImagem(self, raiz: NoAST, caminho: str) -> None:
        dot = shutil.which("dot")
        if dot is None:
            raise RuntimeError(
                "o comando 'dot' do Graphviz não foi encontrado no PATH. "
                "Instale o Graphviz ou adicione sua pasta bin ao PATH; "
                "confirme com 'dot -V' no mesmo terminal"
            )

        formato = Path(caminho).suffix.lower().lstrip(".")
        if formato not in {"png", "svg", "pdf", "jpg", "jpeg"}:
            raise ValueError("a imagem deve ter extensão .png, .svg, .pdf, .jpg ou .jpeg")

        def escapar(texto: str) -> str:
            return (texto.replace("\\", "\\\\")
                         .replace('"', '\\"')
                         .replace("\r", "")
                         .replace("\n", "\\n"))

        linhas = [
            'digraph Arvore {',
            '  graph [charset="UTF-8"];',
            '  node [shape=box, fontname="Arial"];',
        ]
        proximo = 0

        def adicionar(nome: str, pai: int | None) -> int:
            nonlocal proximo
            indice = proximo
            proximo += 1
            linhas.append(f'  n{indice} [label="{escapar(nome)}"];')
            if pai is not None:
                linhas.append(f"  n{pai} -> n{indice};")
            return indice

        def visitar(no: NoAST, rotulo: str = "", pai: int | None = None) -> None:
            nome, filhos = self.descrever(no, rotulo)
            atual = adicionar(nome, pai)
            for rotuloFilho, valor in filhos:
                if valor is None:
                    adicionar(f"{rotuloFilho}: <erro>", atual)
                else:
                    visitar(valor, rotuloFilho, atual)

        visitar(raiz)
        linhas.append("}")

        try:
            subprocess.run(
                [dot, f"-T{formato}", "-o", caminho],
                input="\n".join(linhas),
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
        except FileNotFoundError as erro:
            raise RuntimeError(
                "não foi possível executar o Graphviz ('dot'); "
                "confirme com 'dot -V' no mesmo terminal"
            ) from erro
        except subprocess.CalledProcessError as erro:
            detalhe = (erro.stderr or "").strip() or str(erro)
            raise RuntimeError(f"Graphviz não conseguiu gerar '{caminho}': {detalhe}") from erro
