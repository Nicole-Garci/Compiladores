import argparse
import subprocess
import sys
from pathlib import Path

from src.parser.GerenciadorErrosSintaticos import GerenciadorErrosSintaticos
from src.parser.Parser import Parser
from src.parser.SaidaParser import SaidaParser
from src.lexer.Lexer import Lexer
from src.semantico.AnalisadorSemantico import AnalisadorSemantico


CAMINHO_AFD = Path(__file__).resolve().parent / "src" / "lexer" / "AFD.json"


def parser() -> argparse.ArgumentParser:
    analisadorArgumentos = argparse.ArgumentParser(
        description="Executa o compilador da linguagem C--."
    )
    analisadorArgumentos.add_argument(
        "arquivo",
        help="caminho do arquivo-fonte .cmm",
    )
    analisadorArgumentos.add_argument(
        "--arvore",
        action="store_true",
        help="imprime a árvore de sintaxe abstrata ao final",
    )
    analisadorArgumentos.add_argument(
        "--imagem",
        metavar="ARQUIVO",
        help="salva a árvore como imagem, ex.: arvore.png (requer Graphviz)",
    )
    analisadorArgumentos.add_argument(
        "--tabela",
        action="store_true",
        help="imprime a tabela de símbolos da análise semântica ao final",
    )
    analisadorArgumentos.add_argument(
        "--tac",
        metavar="ARQUIVO",
        help="salva o TAC gerado em JSON",
    )
    analisadorArgumentos.add_argument(
        "--executar",
        action="store_true",
        help="executa o TAC gerado e imprime o rastro do simulador",
    )
    return analisadorArgumentos


def mostrarArvore(programa, argumentos: argparse.Namespace, parcial: bool) -> bool:
    try:
        from src.parser.VisualizadorArvore import VisualizadorArvore

        visualizador = VisualizadorArvore()

        if argumentos.arvore:
            titulo = "Árvore sintática abstrata"
            if parcial:
                titulo += " (parcial: houve erros na análise)"
            print(f"\n{titulo}:")
            visualizador.imprimir(programa)
            sys.stdout.flush()

        if argumentos.imagem:
            visualizador.exportarImagem(programa, argumentos.imagem)
    except (ImportError, OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as erro:
        print(f"Não foi possível visualizar a árvore: {erro}", file=sys.stderr)
        return False

    return True


def main(argv: list[str] | None = None) -> int:
    argumentos = parser().parse_args(argv)
    lexer = Lexer(str(CAMINHO_AFD))

    try:
        tokens = lexer.analisarArquivo(argumentos.arquivo)
    except (ValueError, FileNotFoundError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2

    # for token in tokens:
    #     print(token.paraString())

    errosLexer = lexer.obterErros()
    sys.stdout.flush()

    if errosLexer:
        print("\nErros léxicos encontrados:", file=sys.stderr)
        for erro in errosLexer:
            print(erro.paraString(), file=sys.stderr)
        return 1

    analisadorSintatico = Parser(
        gerenciadorErros=GerenciadorErrosSintaticos(
            destino=sys.stderr, imprimirAoRegistrar=True
        ),
        saida=SaidaParser(),
    )
    programa = analisadorSintatico.analisar(tokens)

    errosParser = analisadorSintatico.obterErros()
    sys.stdout.flush()

    if argumentos.arvore or argumentos.imagem:
        if not mostrarArvore(programa, argumentos, parcial=bool(errosParser)):
            return 2

    if errosParser:
        #print("\nErros sintáticos encontrados:", file=sys.stderr)
        #for erro in errosParser:
        #    print(erro.paraString(), file=sys.stderr)
        return 1

    analisadorSemantico = AnalisadorSemantico()
    programaTAC = analisadorSemantico.analisar(programa)
    errosSemanticos = analisadorSemantico.obterErros()

    if argumentos.tabela:
        print("\nTabela de símbolos:")
        for linha in analisadorSemantico.descreverTabela():
            print(linha)
        sys.stdout.flush()

    if errosSemanticos:
        print("\nErros semânticos encontrados:", file=sys.stderr)
        for erro in sorted(errosSemanticos, key=lambda erro: (erro.linha, erro.coluna)):
            print(erro.paraString(), file=sys.stderr)
        return 1

    if programaTAC is None:
        print("Erro: não foi possível gerar o TAC.", file=sys.stderr)
        return 1

    if argumentos.tac:
        try:
            programaTAC.salvar(argumentos.tac)
        except (OSError, TypeError, ValueError) as erro:
            print(f"Erro ao salvar TAC: {erro}", file=sys.stderr)
            return 2

    if argumentos.executar:
        from src.simulador.Simulador import Simulador

        simulador = Simulador()
        try:
            simulador.executar(programaTAC)
        except (TypeError, ValueError, KeyError, IndexError, ArithmeticError,
                RuntimeError, EOFError, OSError) as erro:
            print(f"Erro no simulador: {erro}", file=sys.stderr)
            return 1
        print("\nRastro de execução:")
        for ordem, (pc, instrucao) in enumerate(simulador.obterRastro(), start=1):
            print(f"{ordem}: PC {pc} | {instrucao.paraString()}")
        print(f"Total de instruções executadas: {len(simulador.rastro)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
