import argparse
import subprocess
import sys
from pathlib import Path

from src.parser.GerenciadorErrosSintaticos import GerenciadorErrosSintaticos
from src.parser.Parser import Parser
from src.parser.SaidaParser import SaidaParser
from src.lexer.Lexer import Lexer
from src.semantico.AnalisadorSemantico import AnalisadorSemantico
from src.simulador.cli import executarPrograma


CAMINHO_AFD = Path(__file__).resolve().parent / "src" / "lexer" / "AFD.json"


def parser() -> argparse.ArgumentParser:
    analisadorArgumentos = argparse.ArgumentParser(
        description="Compila um arquivo C-- e gera código de três endereços em JSON."
    )
    analisadorArgumentos.add_argument(
        "arquivo",
        help="caminho do arquivo-fonte .cmm",
    )
    analisadorArgumentos.add_argument(
        "--arvore",
        action="store_true",
        help="imprime a árvore de sintaxe abstrata ao final da compilação sem --executar",
    )
    analisadorArgumentos.add_argument(
        "--imagem",
        metavar="ARQUIVO",
        help="salva a árvore como imagem, ex.: arvore.png (requer Graphviz)",
    )
    analisadorArgumentos.add_argument(
        "--tabela",
        action="store_true",
        help="imprime a tabela de símbolos ao final da compilação sem --executar",
    )
    analisadorArgumentos.add_argument(
        "-o",
        "--tac-saida",
        metavar="ARQUIVO",
        help="caminho de saída do TAC (padrão: <nome>.tac.json ao lado do fonte)",
    )
    analisadorArgumentos.add_argument(
        "--executar",
        action="store_true",
        help="compila e executa, exibindo a saída do programa",
    )
    return analisadorArgumentos


def mostrarArvore(programa, argumentos: argparse.Namespace, parcial: bool) -> bool:
    try:
        from src.parser.VisualizadorArvore import VisualizadorArvore

        visualizador = VisualizadorArvore()

        if argumentos.arvore and not argumentos.executar:
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
    fonte = Path(argumentos.arquivo)
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
        saida=SaidaParser(habilitada=not argumentos.executar),
    )
    programa = analisadorSintatico.analisar(tokens)

    errosParser = analisadorSintatico.obterErros()
    sys.stdout.flush()

    if argumentos.imagem or (argumentos.arvore and not argumentos.executar):
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

    if argumentos.tabela and not argumentos.executar:
        print("\nTabela de símbolos:")
        for linha in analisadorSemantico.descreverTabela():
            print(linha)
        sys.stdout.flush()

    if programaTAC is None:
        print("\nErros semânticos encontrados:", file=sys.stderr)
        for erro in sorted(errosSemanticos, key=lambda erro: (erro.linha, erro.coluna)):
            print(erro.paraString(), file=sys.stderr)
        return 1

    errosTAC = programaTAC.validar()
    if errosTAC:
        for erro in errosTAC:
            print(f"Erro no TAC: {erro}", file=sys.stderr)
        return 1

    saida = fonte.with_suffix(".tac.json")
    if argumentos.tac_saida is not None:
        saida = Path(argumentos.tac_saida)
    try:
        programaTAC.salvar(saida)
    except (OSError, ValueError) as erro:
        print(f"Erro ao gravar TAC: {erro}", file=sys.stderr)
        return 2

    if argumentos.executar:
        return executarPrograma(programaTAC, mostrarRastro=False)
    print(f"TAC gerado em {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
