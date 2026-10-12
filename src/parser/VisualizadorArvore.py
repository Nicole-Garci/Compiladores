from dataclasses import fields, is_dataclass
from typing import TextIO

from anytree import Node, RenderTree

from src.parser.ast.Nos import No

CAMPOS_POSICAO = {"linha", "coluna"}


class VisualizadorArvore:
    def converter(self, no: No, pai: Node | None = None, rotulo: str = "") -> Node:
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

        noAnytree = Node(nome, parent=pai, origem=no)

        for rotuloFilho, valor in filhos:
            if valor is None:
                Node(f"{rotuloFilho}: <erro>", parent=noAnytree, origem=None)
            else:
                self.converter(valor, noAnytree, rotuloFilho)

        return noAnytree

    @staticmethod
    def campoGuardaNo(campo) -> bool:
        anotacao = str(campo.type)
        return "Expr" in anotacao or "Comando" in anotacao

    def imprimir(self, raiz: No, destino: TextIO | None = None) -> None:
        for prefixo, _, no in RenderTree(self.converter(raiz)):
            print(f"{prefixo}{no.name}", file=destino)

    def exportarImagem(self, raiz: No, caminho: str) -> None:
        from anytree.exporter import UniqueDotExporter

        def atributosNo(no: Node) -> str:
            rotulo = no.name.replace("\\", "\\\\").replace('"', '\\"')
            return f'label="{rotulo}"'

        UniqueDotExporter(
            self.converter(raiz), nodeattrfunc=atributosNo
        ).to_picture(caminho)
