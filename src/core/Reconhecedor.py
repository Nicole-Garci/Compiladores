import sys
from pathlib import Path
from LeitorTexto import LeitorTexto
SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(SRC_DIR))
from AFD import AFD
from TiposToken import TiposToken, Token
from TabelaSimbolos import TabelaSimbolos

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

PALAVRAS_RESERVADAS = {
    "int": TiposToken.INT,
    "float": TiposToken.FLOAT,
    "char": TiposToken.CHAR,
    "bool": TiposToken.BOOL,
    "if": TiposToken.IF,
    "else": TiposToken.ELSE,
    "while": TiposToken.WHILE,
    "readln": TiposToken.READLN,
    "print": TiposToken.PRINT,
    "break": TiposToken.BREAK,
    "return": TiposToken.RETURN,
    "true": TiposToken.TRUE,
    "false": TiposToken.FALSE
}

class Reconhecedor:
    def __init__(self, json_filepath, code_filepath):
        self.afd = AFD(json_filepath)
        self.tabelaSimbolos = TabelaSimbolos()
        self.leitor = LeitorTexto("")
        sucesso = self.leitor.carregarArquivo(code_filepath)
        if not sucesso:
            raise FileNotFoundError(f"Erro: O arquivo '{code_filepath}' não foi encontrado.")
        

    def _ignorar_espacos(self):
        while not self.leitor.chegouAoFim():
            c = self.leitor.observarCaractere()
            if c and c in " \t\r\n":
                self.leitor.avancar()
            else:
                break

    def proximoToken(self):
        self.afd.reiniciar()
        self._ignorar_espacos()

        if self.leitor.chegouAoFim():
            return Token(TiposToken.END_OF_FILE, "", self.leitor.obterLinha(), self.leitor.obterColuna())
        
        lexema = ""
        linha = self.leitor.obterLinha()
        coluna = self.leitor.obterColuna()
        ultimoFinal = None
        ultimoLexema = ""

        while not self.leitor.chegouAoFim():
            charAtual = self.leitor.observarCaractere(0)

            if self.afd.transicionar(charAtual):
                lexema += self.leitor.avancar()

                if self.afd.eh_estado_final():
                    ultimoFinal = self.afd.obter_estado_atual()
                    ultimoLexema = lexema
            else:
                break

        if ultimoFinal is not None:
            tipo = ESTADO_PARA_TOKEN.get(ultimoFinal, TiposToken.UNKNOWN)
            if ultimoFinal == "qCOMMENTDONE":
                return self.proximoToken()

            if tipo == TiposToken.ID and ultimoLexema in PALAVRAS_RESERVADAS:
                tipo = PALAVRAS_RESERVADAS[ultimoLexema]

            return Token(tipo, ultimoLexema, linha, coluna)
        
        charInvalido = self.leitor.avancar()
        return Token(TiposToken.UNKNOWN, charInvalido, linha, coluna)