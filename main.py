import argparse
import sys

from src.TabelaSimbolos import TabelaSimbolos
from src.TiposToken import TiposToken
from src.core.Reconhecedor import Reconhecedor
from src.models.ErroLexer import ErroLexer
from src.models.Token import Token


def parser() -> argparse.ArgumentParser:
    """TODO: implement parser"""

def main(argv: list[str] | None = None) -> int:
    """TODO: implement main"""
    print("Teste Token: " + Token(TiposToken.ID, 'x1', 1, 1).paraString())

    table = TabelaSimbolos()
    print("\n" + table.buscar('if').__str__())
    print("\n" + table.obterOuInserir('contador', tiposToken=TiposToken.ID).__str__())
    print("\nQtde Simb: " + table.quantidade().__str__())

    print("\nReconhecedor: ")
    r = Reconhecedor('src/AFD.json', 'tests/arquivoTexto')
    print(r.proximoToken().paraString())

    r.leitor.carregarTexto('12.a')
    print("\n12.a: " + [(r.proximoToken().paraString()) for i in range(3)].__str__())

    r.leitor.carregarTexto('&x')
    a = r.proximoToken(); b = r.proximoToken()
    print("\n&x: " + (a.tipo.name, a.lexema).__str__() + "\t" + (b.tipo.name, b.lexema).__str__())

    e = ErroLexer('literal não finalizado', 3, 8, '"abc')
    print(f"\n{e}"); print(e.paraString())


if __name__ == main():
    main(sys.argv)