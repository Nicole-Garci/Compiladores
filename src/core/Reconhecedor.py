from src.AFD import AFD
from src.TabelaSimbolos import TabelaSimbolos
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

        marcoInicial = self.leitor.criarMarco()
        
        lexema = ""
        linha = self.leitor.obterLinha()
        coluna = self.leitor.obterColuna()
        ultimoFinal = None
        ultimoLexema = ""
        ultimoMarcoFinal = None

        while not self.leitor.chegouAoFim():
            charAtual = self.leitor.observarCaractere(0)

            if self.afd.transicionar(charAtual):
                lexema += self.leitor.avancar()

                if self.afd.eh_estado_final():
                    ultimoFinal = self.afd.obter_estado_atual()
                    ultimoLexema = lexema
                    ultimoMarcoFinal = self.leitor.criarMarco()
            else:
                break

        if ultimoFinal is not None:
            self.leitor.restaurarMarco(ultimoMarcoFinal)

            tipo = ESTADO_PARA_TOKEN.get(ultimoFinal, TiposToken.UNKNOWN)
            if ultimoFinal == "qCOMMENTDONE":
                return self.proximoToken()

            if tipo == TiposToken.ID:
                simbolo = self.tabelaSimbolos.buscar(ultimoLexema)

                if simbolo is not None:
                    tipo = simbolo.tipoToken

            return Token(tipo, ultimoLexema, linha, coluna)

        self.leitor.restaurarMarco(marcoInicial)
        charInvalido = self.leitor.avancar()

        return Token(TiposToken.UNKNOWN, charInvalido, linha, coluna)