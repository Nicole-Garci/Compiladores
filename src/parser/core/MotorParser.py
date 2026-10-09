from src.parser.GerenciadorErrosSintaticos import GerenciadorErrosSintaticos
from src.lexer.models.Token import Token
from src.lexer.TiposToken import TiposToken
from src.parser.SaidaParser import SaidaParser
from src.parser.core.FluxoTokens import FluxoTokens

INICIO_TIPO = {
    TiposToken.INT,
    TiposToken.FLOAT,
    TiposToken.BOOL,
    TiposToken.CHAR,
    TiposToken.ID,
}

INICIO_STMT_SEM_ID = {
    TiposToken.IF,
    TiposToken.WHILE,
    TiposToken.BREAK,
    TiposToken.PRINT,
    TiposToken.READLN,
    TiposToken.RETURN,
    TiposToken.OPEN_BRACES,
    TiposToken.INCREMENT,
    TiposToken.DECREMENT,
    TiposToken.NEG,
    TiposToken.NUM_INT,
    TiposToken.NUM_FLOAT,
    TiposToken.LITERAL,
    TiposToken.ASCII,
    TiposToken.OPEN_PARENTHESES,
    TiposToken.TRUE,
    TiposToken.FALSE,
}

PRIMARIOS_TIPO = {TiposToken.INT, TiposToken.FLOAT, TiposToken.CHAR, TiposToken.BOOL}

CONTINUACAO_ID_EXPR = {
    TiposToken.OPEN_PARENTHESES,
    TiposToken.OPEN_BRACKETS,
    TiposToken.MULT, TiposToken.DIV, TiposToken.MOD,
    TiposToken.PLUS, TiposToken.MINUS,
    TiposToken.LESS_THAN, TiposToken.LESS_THAN_EQUAL,
    TiposToken.GREATER_THAN, TiposToken.GREATER_THAN_EQUAL,
    TiposToken.EQUALS, TiposToken.DIFF,
    TiposToken.AND, TiposToken.OR, TiposToken.ASSIGN,
    TiposToken.SEMICOLON,
}

UNARIOS_OP = {TiposToken.DECREMENT, TiposToken.INCREMENT, TiposToken.NEG}

ATOM = {
    TiposToken.NUM_INT,
    TiposToken.NUM_FLOAT,
    TiposToken.LITERAL,
    TiposToken.ASCII,
    TiposToken.OPEN_PARENTHESES,
    TiposToken.TRUE,
    TiposToken.FALSE
}

INICIO_ATOM_NO_ID = {
    TiposToken.NUM_INT,
    TiposToken.NUM_FLOAT,
    TiposToken.LITERAL,
    TiposToken.ASCII,
    TiposToken.OPEN_PARENTHESES,
    TiposToken.TRUE,
    TiposToken.FALSE,
}

class MotorParser:
    def __init__(self, fluxo: FluxoTokens, saida: SaidaParser, erros: GerenciadorErrosSintaticos) -> None:
        self.fluxo = fluxo
        self.saida = saida
        self.erros = erros

    def entrar(self, nome: str) -> None:
        self.saida.naoTerminal(nome)

    def casar(self, esperado: TiposToken) -> Token:
        encontrou = self.fluxo.atual()

        if encontrou.tipo is not esperado:
            self.falhar(
                "Token inesperado",
                {esperado}
            )

        self.saida.terminalCasado(encontrou)
        self.fluxo.avancar()

        return encontrou

    def executar(self) -> None:
        if self.fluxo.chegouAoFim():
            self.erros.registrar(
                token=self.fluxo.atual(),
                mensagem="O programa precisa conter uma declaração",
                esperados=INICIO_TIPO | {TiposToken.TYPEDEF},
            )
            return

        while not self.fluxo.chegouAoFim():
            inicio = self.fluxo.posicao()
            try:
                self.program()
            except SyntaxError:
                self.sincronizarDeclaracao(inicio)

        self.casar(TiposToken.END_OF_FILE)

    def sincronizarDeclaracao(self, inicio: int) -> None:
        """Descarta a declaração com erro e procura a próxima declaração global."""
        nivel = 0
        for token in self.fluxo.tokens[inicio:self.fluxo.posicao()]:
            if token.tipo is TiposToken.OPEN_BRACES:
                nivel += 1
            elif token.tipo is TiposToken.CLOSE_BRACES:
                nivel = max(0, nivel - 1)

        while not self.fluxo.chegouAoFim():
            tipo = self.fluxo.atual().tipo

            if nivel == 0:
                if tipo is TiposToken.SEMICOLON:
                    self.fluxo.avancar()
                    return
                if self.fluxo.posicao() > inicio:
                    if tipo in PRIMARIOS_TIPO | {TiposToken.TYPEDEF}:
                        return
                    proximo = self.fluxo.posicao() + 1
                    if (tipo is TiposToken.ID
                            and proximo < len(self.fluxo.tokens)
                            and self.fluxo.tokens[proximo].tipo is TiposToken.ID):
                        return

            if tipo is TiposToken.OPEN_BRACES:
                nivel += 1
            elif tipo is TiposToken.CLOSE_BRACES and nivel > 0:
                nivel -= 1
                self.fluxo.avancar()
                if nivel == 0:
                    if self.fluxo.verificar(TiposToken.SEMICOLON):
                        self.fluxo.avancar()
                    return
                continue

            self.fluxo.avancar()

    def falhar(self, mensagem: str, esperados: set[TiposToken]) -> None:
        self.erros.registrar(
            token=self.fluxo.atual(),
            mensagem=mensagem,
            esperados=esperados,
        )
        raise SyntaxError

    ## Análises Recursivas

    def program(self):
        self.entrar("Program")
        token = self.fluxo.atual()

        if token.tipo is TiposToken.TYPEDEF:
            self.typeDeclOne()
            self.program()
            return

        if token.tipo in INICIO_TIPO:
            self.type()
            self.casar(TiposToken.ID)
            self.restoDecl()
            return

        self.falhar(
            "Início de declaração inválido",
            INICIO_TIPO | {TiposToken.TYPEDEF},
        )

    def typeDeclOne(self):
        self.entrar("TypeDeclOne")

        self.casar(TiposToken.TYPEDEF)
        self.casar(TiposToken.STRUCT)

        self.casar(TiposToken.OPEN_BRACES)
        self.type()
        self.idList()
        self.casar(TiposToken.SEMICOLON)
        self.varDecl()
        self.casar(TiposToken.CLOSE_BRACES)

        self.casar(TiposToken.SEMICOLON)



    def restoDecl(self):
        self.entrar("RestoDecl")

        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.OPEN_PARENTHESES:
            self.casar(TiposToken.OPEN_PARENTHESES)
            self.formalList()
            self.casar(TiposToken.CLOSE_PARENTHESES)

            self.casar(TiposToken.OPEN_BRACES)
            self.body()
            self.casar(TiposToken.CLOSE_BRACES)
            self.programLinha()

        elif tipo in {TiposToken.OPEN_BRACKETS, TiposToken.COMMA, TiposToken.SEMICOLON}:
            self.array()
            self.idListLinha()
            self.casar(TiposToken.SEMICOLON)
            self.program()

        else:
            self.falhar("Declaração inválida",
                        {TiposToken.OPEN_PARENTHESES} |
                        {TiposToken.OPEN_BRACKETS, TiposToken.COMMA, TiposToken.SEMICOLON}
            )



    def programLinha(self):
        self.entrar("Program")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.TYPEDEF or tipo in INICIO_TIPO:
            self.program()

        elif tipo is TiposToken.END_OF_FILE:
            return # Progrma' -> epsilon
        else:
            self.falhar("Continuação do programa inválida",
                        INICIO_TIPO | {TiposToken.END_OF_FILE, TiposToken.TYPEDEF}
            )

    def varDecl(self):
        self.entrar("VarDecl")

        tipo = self.fluxo.atual().tipo

        if tipo in INICIO_TIPO:
            self.type()
            self.idList()
            self.casar(TiposToken.SEMICOLON)
            self.varDecl()

        elif tipo is TiposToken.CLOSE_BRACES:
            return # Vardecl -> epsilon

        else:
            self.falhar("Declaração de variável inválida", INICIO_TIPO | 
                        {TiposToken.CLOSE_BRACES}
            )

    def body(self):
        self.entrar("Body")
        tipo = self.fluxo.atual().tipo

        if tipo in PRIMARIOS_TIPO:
            self.primType()
            self.idList()
            self.casar(TiposToken.SEMICOLON)
            self.body()

        elif tipo is TiposToken.ID:
            self.casar(TiposToken.ID)
            self.bodyId()

        elif tipo in INICIO_STMT_SEM_ID:
            self.stmtNoId()
            self.stmtlist()

        elif tipo is TiposToken.CLOSE_BRACES:
            return # Body -> epsilon

        else:
            self.falhar("Corpo de função inválido",
                        PRIMARIOS_TIPO
                        | {TiposToken.ID, TiposToken.CLOSE_BRACES}
                        | INICIO_STMT_SEM_ID,
            )


    def bodyId(self):
        self.entrar("BodyId")

        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.ID:
            self.idList()
            self.casar(TiposToken.SEMICOLON)
            self.body()
        elif tipo in CONTINUACAO_ID_EXPR:
            self.idExprRest()
            self.casar(TiposToken.SEMICOLON)
            self.stmtlist()
        else:
            self.falhar("Continuação após identificador inválida",
                        {TiposToken.ID} | CONTINUACAO_ID_EXPR
            )

    def idExprRest(self):
        self.entrar("IdExprRest")

        self.callOpt()
        self.indexLinha()
        self.mulLinha()
        self.addLinha()
        self.relLinha()
        self.equalityLinha()
        self.andLinha()
        self.orLinha()
        self.assignLinha()

    def primType(self):
        self.entrar("PrimType")
        tipo = self.fluxo.atual().tipo

        if tipo in PRIMARIOS_TIPO:
            self.casar(tipo)
            return

        self.falhar("Tipo primitivo inválido", PRIMARIOS_TIPO)

    def stmtNoId(self):
        self.entrar("StmtNoId")

        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.IF:
            self.casar(TiposToken.IF)

            self.casar(TiposToken.OPEN_PARENTHESES)
            self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)

            self.stmt()
            self.casar(TiposToken.ELSE)
            self.stmt()

        elif tipo is TiposToken.WHILE:
            self.casar(TiposToken.WHILE)

            self.casar(TiposToken.OPEN_PARENTHESES)
            self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            self.stmt()

        elif tipo is TiposToken.BREAK:
            self.casar(TiposToken.BREAK)
            self.casar(TiposToken.SEMICOLON)

        elif tipo is TiposToken.PRINT:
            self.casar(TiposToken.PRINT)
            self.casar(TiposToken.OPEN_PARENTHESES)
            self.exprList()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            self.casar(TiposToken.SEMICOLON)

        elif tipo is TiposToken.READLN:
            self.casar(TiposToken.READLN)
            self.casar(TiposToken.OPEN_PARENTHESES)
            self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            self.casar(TiposToken.SEMICOLON)

        elif tipo is TiposToken.RETURN:
            self.casar(TiposToken.RETURN)
            self.expr()
            self.casar(TiposToken.SEMICOLON)

        elif tipo is TiposToken.OPEN_BRACES:
            self.casar(TiposToken.OPEN_BRACES)
            self.stmtlist()
            self.casar(TiposToken.CLOSE_BRACES)

        elif tipo in (UNARIOS_OP | INICIO_ATOM_NO_ID):
            self.exprNoId()
            self.casar(TiposToken.SEMICOLON)

        else:
            self.falhar(
                "Comando inválido",
                UNARIOS_OP
                | INICIO_ATOM_NO_ID
                | {
                    TiposToken.OPEN_BRACES,
                    TiposToken.RETURN,
                    TiposToken.READLN,
                    TiposToken.PRINT,
                    TiposToken.BREAK,
                    TiposToken.WHILE,
                    TiposToken.IF,
                },
            )


    def exprNoId(self):
        self.entrar("ExprNoId")

        tipo = self.fluxo.atual().tipo

        if tipo in UNARIOS_OP:
            self.unaryOp()
            self.unaryExpr()
            self.mulLinha()
            self.addLinha()
            self.relLinha()
            self.equalityLinha()
            self.andLinha()
            self.orLinha()
            self.assignLinha()

        elif tipo in ATOM:
            self.atomNoId()
            self.indexLinha()
            self.mulLinha()
            self.addLinha()
            self.relLinha()
            self.equalityLinha()
            self.andLinha()
            self.orLinha()
            self.assignLinha()

        else:
            self.falhar("Expressão inválida",
                        UNARIOS_OP | ATOM
            )


    def atomNoId(self):
        self.entrar("")

    def idList(self):
        self.entrar("idList")

        self.casar(TiposToken.ID)
        self.array()
        self.idListLinha()

    def idListLinha(self):
        self.entrar("idList'")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.COMMA:
            self.casar(TiposToken.COMMA)
            self.casar(TiposToken.ID)
            self.array()
            self.idListLinha()

        elif tipo is TiposToken.SEMICOLON:
            return # IdListLinha -. epsilon

        else:
            self.falhar("Continuação da lista de identificadores inválida",
                        {TiposToken.COMMA, TiposToken.SEMICOLON})

    def array(self):
        self.entrar("Array")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.OPEN_BRACKETS:
            self.casar(TiposToken.OPEN_BRACKETS)
            self.casar(TiposToken.NUM_INT)
            self.casar(TiposToken.CLOSE_BRACKETS)

        elif tipo in { TiposToken.COMMA, TiposToken.SEMICOLON, TiposToken.CLOSE_PARENTHESES}:
            return # Array -> epsilon

        else:
            self.falhar("Sufixo de array inválido",
                        {TiposToken.OPEN_BRACKETS, TiposToken.COMMA, TiposToken.SEMICOLON, TiposToken.CLOSE_PARENTHESES}
            )

    def formalList(self):
        self.entrar("FormalList")
        tipo = self.fluxo.atual().tipo

        if tipo in INICIO_TIPO:
            self.type()
            self.casar(TiposToken.ID)
            self.array()
            self.formalRest()

        elif tipo is TiposToken.CLOSE_PARENTHESES:
            return # FormalList -> epsilon

        else:
            self.falhar("Lista de parâmetros inválida",
                        INICIO_TIPO | {TiposToken.CLOSE_PARENTHESES}
            )

    def formalRest(self):
        self.entrar("FormalRest")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.COMMA:
            self.casar(TiposToken.COMMA)
            self.type()
            self.casar(TiposToken.ID)
            self.array()
            self.formalRest()

        elif tipo is TiposToken.CLOSE_PARENTHESES:
            return # FormalRest -> epsilon

        else:
            self.falhar("Continuação da lista de parâmetros inválida",
                        {TiposToken.COMMA} |
                        {TiposToken.OPEN_BRACKETS, TiposToken.COMMA, TiposToken.SEMICOLON, TiposToken.CLOSE_PARENTHESES}
            )


    def type(self) -> Token | None:
        self.entrar("Type")
        token = self.fluxo.atual()

        if token.tipo in INICIO_TIPO:
            return self.casar(token.tipo)

        self.falhar("Tipo Inválido", INICIO_TIPO)

    def stmtlist(self):
        self.entrar("")

    def stmt(self):
        self.entrar("")

    def exprList(self):
        self.entrar("")

    def exprListLinha(self):
        self.entrar("")

    def restoExprList(self):
        self.entrar("")

    def expr(self):
        self.entrar("")

    def assignExpr(self):
        self.entrar("")

    def assignLinha(self):
        self.entrar("")

    def orExpr(self):
        self.entrar("")

    def orLinha(self):
        self.entrar("")

    def andExpr(self):
        self.entrar("")

    def andLinha(self):
        self.entrar("")

    def equalityExpr(self):
        self.entrar("")

    def equalityLinha(self):
        self.entrar("")

    def relExpr(self):
        self.entrar("")

    def relLinha(self):
        self.entrar("")

    def addExpr(self):
        self.entrar("")

    def addLinha(self):
        self.entrar("")

    def mulExpr(self):
        self.entrar("")

    def mulLinha(self):
        self.entrar("")

    def unaryExpr(self):
        self.entrar("")

    def primary(self):
        self.entrar("")

    def indexLinha(self):
        self.entrar("")

    def atom(self):
        self.entrar("")

    def callOpt(self):
        self.entrar("")

    def unaryOp(self):
        self.entrar("")

