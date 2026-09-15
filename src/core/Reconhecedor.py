from src.AFD import AFD
from src.TiposToken import TiposToken
from src.core.LeitorTexto import LeitorTexto
from src.models.Token import Token

ESTADO_PARA_TOKEN = {
    # Identificadores e Literais
    "qID": TiposToken.ID,
    "qNUMINT": TiposToken.NUM_INT,
    "qNUMFLOAT": TiposToken.NUM_FLOAT,
    "qSTRING_FINAL": TiposToken.LITERAL,
    "qCHAR_FINAL": TiposToken.ASCII,
    
    # Operadores Aritméticos
    "qPLUS": TiposToken.PLUS,
    "qINC": TiposToken.INCREMENT,
    "qMINUS": TiposToken.MINUS,
    "qDEC": TiposToken.DECREMENT,
    "qMULT": TiposToken.MULT,
    "qDIV": TiposToken.DIV,
    "qMOD": TiposToken.MOD,
    
    # Atribuição e Relacionais
    "qASSIGN": TiposToken.ASSIGN,
    "qEQ": TiposToken.EQUALS,
    "qLT": TiposToken.LESS_THAN,
    "qLEQ": TiposToken.LESS_THAN_EQUAL,
    "qGT": TiposToken.GREATER_THAN,
    "qGEQ": TiposToken.GREATER_THAN_EQUAL,
    "qNOT": TiposToken.NEG,
    "qNEQ": TiposToken.DIFF,
    
    # Lógicos
    "qAND": TiposToken.AND,
    "qOR": TiposToken.OR,
    
    # Delimitadores
    "qLPARENT": TiposToken.OPEN_PARENTHESES,
    "qRPARENT": TiposToken.CLOSE_PARENTHESES,
    "qLBRACKET": TiposToken.OPEN_BRACKETS,
    "qRBRACKET": TiposToken.CLOSE_BRACKETS,
    "qLBRACE": TiposToken.OPEN_BRACES,
    "qRBRACE": TiposToken.CLOSE_BRACES,
    "qCOMMA": TiposToken.COMMA,
    "qSEMICOLON": TiposToken.SEMICOLON,
}


class Reconhecedor:
    """Aplica o AFD e devolve o maior prefixo reconhecido da entrada."""

    def __init__(self, caminhoAFD: str, caminhoFonte: str) -> None:
        self.afd = AFD(caminhoAFD)
        self.leitor = LeitorTexto("")
        self.leitor.carregarArquivo(caminhoFonte)

    def _ignorarEspacos(self) -> None:
        while not self.leitor.chegouAoFim():
            c = self.leitor.observarCaractere()
            if c and c in " \t\r\n":
                self.leitor.avancar()
            else:
                break

    def _consumirAteFechamento(self, lexema: str, delimitador: str) -> str:
        """Agrupa um literal inválido para produzir apenas um diagnóstico."""
        while not self.leitor.chegouAoFim():
            caractere = self.leitor.observarCaractere()
            if caractere in ("\n", "\r"):
                break
            consumido = self.leitor.avancar()
            lexema += consumido or ""
            if consumido == delimitador:
                break
        return lexema

    def proximoToken(self) -> Token:
        while True:
            self.afd.reiniciar()
            self._ignorarEspacos()

            if self.leitor.chegouAoFim():
                return Token(
                    TiposToken.END_OF_FILE,
                    "",
                    self.leitor.obterLinha(),
                    self.leitor.obterColuna(),
                )

            marcoInicial = self.leitor.criarMarco()
            lexema = ""
            linha = self.leitor.obterLinha()
            coluna = self.leitor.obterColuna()
            ultimoFinal: str | None = None
            ultimoLexema = ""
            ultimoMarcoFinal: tuple[int, int, int] | None = None
            estadoAntesFalha: str | None = None

            while not self.leitor.chegouAoFim():
                charAtual = self.leitor.observarCaractere()
                assert charAtual is not None
                estadoAnterior = self.afd.obterEstadoAtual()

                if self.afd.transicionar(charAtual):
                    lexema += self.leitor.avancar() or ""

                    if self.afd.ehEstadoFinal():
                        ultimoFinal = self.afd.obterEstadoAtual()
                        ultimoLexema = lexema
                        ultimoMarcoFinal = self.leitor.criarMarco()
                else:
                    estadoAntesFalha = estadoAnterior
                    break

            estadoAtual = self.afd.obterEstadoAtual()
            estadoIncompleto = estadoAntesFalha or estadoAtual

            if estadoIncompleto in {"qCOMMENT", "qCOMMENTSTAR"}:
                return Token(
                    TiposToken.UNKNOWN,
                    lexema,
                    linha,
                    coluna,
                    mensagemErro="Comentário não terminado",
                )

            if estadoIncompleto == "qSTRING":
                lexema = self._consumirAteFechamento(lexema, '"')
                return Token(
                    TiposToken.UNKNOWN,
                    lexema,
                    linha,
                    coluna,
                    mensagemErro="Literal de string não terminado",
                )

            if estadoIncompleto in {"qCHAR1", "qCHAR2"}:
                lexema = self._consumirAteFechamento(lexema, "'")
                return Token(
                    TiposToken.UNKNOWN,
                    lexema,
                    linha,
                    coluna,
                    mensagemErro="Literal de caractere inválido ou não terminado",
                )

            if estadoIncompleto == "qDOT":
                return Token(
                    TiposToken.UNKNOWN,
                    lexema,
                    linha,
                    coluna,
                    mensagemErro="Número decimal incompleto",
                )

            if ultimoFinal is not None and ultimoMarcoFinal is not None:
                self.leitor.restaurarMarco(ultimoMarcoFinal)
                if ultimoFinal == "qCOMMENTDONE":
                    continue

                tipo = ESTADO_PARA_TOKEN.get(ultimoFinal, TiposToken.UNKNOWN)
                return Token(tipo, ultimoLexema, linha, coluna)

            self.leitor.restaurarMarco(marcoInicial)
            charInvalido = self.leitor.avancar()
            return Token(
                TiposToken.UNKNOWN,
                charInvalido,
                linha,
                coluna,
                mensagemErro="Token não reconhecido",
            )