from src.parser.GerenciadorErrosSintaticos import GerenciadorErrosSintaticos
from src.lexer.models.Token import Token
from src.lexer.TiposToken import TiposToken
from src.parser.SaidaParser import SaidaParser
from src.parser.core.FluxoTokens import FluxoTokens
from src.parser.ast.Nos import (
    Atribuicao, Bloco, Break, Chamada, Comando, ComandoExpr, DeclFuncao,
    DeclStruct, DeclVariavel, Expr, Id, If, Indexacao, OpBinaria, OpUnaria,
    Parametro, Print, Programa, Readln, Return, While, literalDoToken, nomeTipo,
)

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

INICIO_STMT = INICIO_STMT_SEM_ID | {TiposToken.ID}

COMANDOS_COM_PALAVRA_RESERVADA = {
    TiposToken.IF,
    TiposToken.WHILE,
    TiposToken.BREAK,
    TiposToken.PRINT,
    TiposToken.READLN,
    TiposToken.RETURN,
    TiposToken.OPEN_BRACES,
}

INICIO_COMANDO_SEGURO = {
    TiposToken.IF,
    TiposToken.WHILE,
    TiposToken.BREAK,
    TiposToken.PRINT,
    TiposToken.READLN,
    TiposToken.RETURN,
}

# Pontos em que um delimitador ausente pode ser inserido sem consumir o
# primeiro token da construção seguinte.
SEGUIDORES_PARA_INSERCAO = {
    TiposToken.CLOSE_PARENTHESES: {
        TiposToken.SEMICOLON,
        TiposToken.OPEN_BRACES,
    },
    TiposToken.CLOSE_BRACKETS: {
        TiposToken.SEMICOLON,
        TiposToken.COMMA,
        TiposToken.CLOSE_PARENTHESES,
        TiposToken.ASSIGN,
        TiposToken.CLOSE_BRACES,
    },
    TiposToken.SEMICOLON: INICIO_STMT | INICIO_TIPO | {
        TiposToken.TYPEDEF,
        TiposToken.CLOSE_BRACES,
        TiposToken.END_OF_FILE,
    },
}

class MotorParser:
    def __init__(self, fluxo: FluxoTokens, saida: SaidaParser, erros: GerenciadorErrosSintaticos) -> None:
        self.fluxo = fluxo
        self.saida = saida
        self.erros = erros
        self.programa = Programa(linha=1, coluna=1)

    def entrar(self, nome: str) -> None:
        self.saida.naoTerminal(nome)

    def casar(self, esperado: TiposToken) -> Token:
        encontrou = self.fluxo.atual()

        if encontrou.tipo is not esperado:
            proxima_posicao = self.fluxo.posicao() + 1
            if (not self.fluxo.chegouAoFim()
                    and proxima_posicao < len(self.fluxo.tokens)
                    and self.fluxo.tokens[proxima_posicao].tipo is esperado):
                self.erros.registrar(
                    token=encontrou,
                    mensagem="Token inesperado",
                    esperados={esperado},
                    recuperacao=f"Token {encontrou.tipo.name} descartado",
                )
                self.fluxo.avancar()
                encontrou = self.fluxo.atual()

            elif encontrou.tipo in SEGUIDORES_PARA_INSERCAO.get(esperado, set()):
                self.erros.registrar(
                    token=encontrou,
                    mensagem=f"Token {esperado.name} ausente",
                    esperados={esperado},
                    recuperacao=f"Token {esperado.name} inserido antes de {encontrou.tipo.name}",
                )
                return Token(
                    tipo=esperado,
                    lexema=None,
                    linha=encontrou.linha,
                    coluna=encontrou.coluna,
                )

            else:
                self.falhar("Token inesperado", {esperado})

        self.saida.terminalCasado(encontrou)
        self.fluxo.avancar()

        return encontrou

    def executar(self) -> Programa:
        if self.fluxo.chegouAoFim():
            self.erros.registrar(
                token=self.fluxo.atual(),
                mensagem="O programa precisa conter uma declaração",
                esperados=INICIO_TIPO | {TiposToken.TYPEDEF},
            )
            return self.programa

        while not self.fluxo.chegouAoFim():
            inicio = self.fluxo.posicao()
            try:
                self.program()
            except SyntaxError:
                self.sincronizarDeclaracao(inicio)

        self.casar(TiposToken.END_OF_FILE)
        return self.programa

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

    def sincronizarComando(self, inicio: int, pararEmElse: bool = False) -> None:
        """Descarta o comando com erro e preserva o fechamento do bloco atual."""
        nivel = 0
        for token in self.fluxo.tokens[inicio:self.fluxo.posicao()]:
            if token.tipo is TiposToken.OPEN_BRACES:
                nivel += 1
            elif token.tipo is TiposToken.CLOSE_BRACES:
                nivel = max(0, nivel - 1)

        while not self.fluxo.chegouAoFim():
            tipo = self.fluxo.atual().tipo

            if nivel == 0:
                if pararEmElse and tipo is TiposToken.ELSE:
                    return
                if tipo is TiposToken.CLOSE_BRACES:
                    return
                if tipo is TiposToken.SEMICOLON:
                    self.fluxo.avancar()
                    return
                if self.fluxo.posicao() > inicio and tipo in INICIO_COMANDO_SEGURO:
                    return

            if tipo is TiposToken.OPEN_BRACES:
                nivel += 1
            elif tipo is TiposToken.CLOSE_BRACES:
                nivel -= 1
                self.fluxo.avancar()
                if nivel == 0:
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
            self.programa.declaracoes.append(self.typeDeclOne())
            self.program()
            return

        if token.tipo in INICIO_TIPO:
            tipo = self.type()
            nome = self.casar(TiposToken.ID)
            self.restoDecl(tipo, nome)
            return

        self.falhar(
            "Início de declaração inválido",
            INICIO_TIPO | {TiposToken.TYPEDEF},
        )

    def typeDeclOne(self) -> DeclStruct:
        self.entrar("TypeDeclOne")

        inicio = self.casar(TiposToken.TYPEDEF)
        self.casar(TiposToken.STRUCT)
        struct = DeclStruct(linha=inicio.linha, coluna=inicio.coluna)

        self.casar(TiposToken.OPEN_BRACES)
        tipo = self.type()
        struct.campos.extend(self.idList(tipo))
        self.casar(TiposToken.SEMICOLON)
        struct.campos.extend(self.varDecl())
        self.casar(TiposToken.CLOSE_BRACES)

        self.casar(TiposToken.SEMICOLON)
        return struct



    def restoDecl(self, tipo: Token, nome: Token):
        self.entrar("RestoDecl")

        tipoAtual = self.fluxo.atual().tipo

        if tipoAtual is TiposToken.OPEN_PARENTHESES:
            funcao = DeclFuncao(nomeTipo(tipo), nome.lexema,
                                linha=nome.linha, coluna=nome.coluna)
            self.programa.declaracoes.append(funcao)

            self.casar(TiposToken.OPEN_PARENTHESES)
            funcao.parametros = self.formalList()
            self.casar(TiposToken.CLOSE_PARENTHESES)

            abre = self.casar(TiposToken.OPEN_BRACES)
            funcao.corpo = Bloco(linha=abre.linha, coluna=abre.coluna)
            self.body(funcao.corpo)
            self.casar(TiposToken.CLOSE_BRACES)
            self.programLinha()

        elif tipoAtual in {TiposToken.OPEN_BRACKETS, TiposToken.COMMA, TiposToken.SEMICOLON}:
            primeira = DeclVariavel(nomeTipo(tipo), nome.lexema, self.array(),
                                    linha=nome.linha, coluna=nome.coluna)
            self.programa.declaracoes.append(primeira)
            self.programa.declaracoes.extend(self.idListLinha(tipo))
            self.casar(TiposToken.SEMICOLON)
            self.program()

        else:
            self.falhar("Declaração inválida",
                        {TiposToken.OPEN_PARENTHESES} |
                        {TiposToken.OPEN_BRACKETS, TiposToken.COMMA, TiposToken.SEMICOLON}
            )



    def programLinha(self):
        self.entrar("Program'")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.TYPEDEF or tipo in INICIO_TIPO:
            self.program()

        elif tipo is TiposToken.END_OF_FILE:
            return # Progrma' -> epsilon
        else:
            self.falhar("Continuação do programa inválida",
                        INICIO_TIPO | {TiposToken.END_OF_FILE, TiposToken.TYPEDEF}
            )

    def varDecl(self) -> list[DeclVariavel]:
        self.entrar("VarDecl")

        tipo = self.fluxo.atual().tipo

        if tipo in INICIO_TIPO:
            tipoToken = self.type()
            declaracoes = self.idList(tipoToken)
            self.casar(TiposToken.SEMICOLON)
            return declaracoes + self.varDecl()

        elif tipo is TiposToken.CLOSE_BRACES:
            return [] # Vardecl -> epsilon

        else:
            self.falhar("Declaração de variável inválida", INICIO_TIPO | 
                        {TiposToken.CLOSE_BRACES}
            )

    def body(self, bloco: Bloco):
        inicio = self.fluxo.posicao()
        try:
            tipo = self.fluxo.atual().tipo

            if tipo in PRIMARIOS_TIPO:
                tipoToken = self.primType()
                bloco.declaracoes.extend(self.idList(tipoToken))
                self.casar(TiposToken.SEMICOLON)
                self.body(bloco)

            elif tipo is TiposToken.ID:
                idToken = self.casar(TiposToken.ID)
                self.bodyId(bloco, idToken)

            elif tipo in INICIO_STMT_SEM_ID:
                self.adicionarComando(bloco, self.stmtNoId())
                bloco.comandos.extend(self.stmtlist())

            elif tipo is TiposToken.CLOSE_BRACES:
                return # Body -> epsilon

            else:
                self.falhar("Corpo de função inválido",
                            PRIMARIOS_TIPO
                            | {TiposToken.ID, TiposToken.CLOSE_BRACES}
                            | INICIO_STMT_SEM_ID,
                )
        except SyntaxError:
            if self.fluxo.chegouAoFim():
                raise
            self.sincronizarComando(inicio)
            bloco.comandos.extend(self.stmtlist())


    def bodyId(self, bloco: Bloco, idToken: Token):
        self.entrar("BodyId")

        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.ID:
            bloco.declaracoes.extend(self.idList(idToken))
            self.casar(TiposToken.SEMICOLON)
            self.body(bloco)
        elif tipo in CONTINUACAO_ID_EXPR:
            expr = self.idExprRest(idToken)
            self.adicionarComando(
                bloco,
                ComandoExpr(expr, linha=idToken.linha, coluna=idToken.coluna),
            )
            self.casar(TiposToken.SEMICOLON)
            bloco.comandos.extend(self.stmtlist())
        else:
            self.falhar("Continuação após identificador inválida",
                        {TiposToken.ID} | CONTINUACAO_ID_EXPR
            )

    def idExprRest(self, idToken: Token) -> Expr:
        self.entrar("IdExprRest")

        base = self.callOpt(idToken)
        base = self.indexLinha(base)
        return self.continuarExpr(base)

    def continuarExpr(self, base: Expr) -> Expr:
        base = self.mulLinha(base)
        base = self.addLinha(base)
        base = self.relLinha(base)
        base = self.equalityLinha(base)
        base = self.andLinha(base)
        base = self.orLinha(base)
        return self.assignLinha(base)

    def adicionarComando(self, bloco: Bloco, comando: Comando | None) -> None:
        if comando is not None:
            bloco.comandos.append(comando)

    def primType(self) -> Token:
        self.entrar("PrimType")
        tipo = self.fluxo.atual().tipo

        if tipo in PRIMARIOS_TIPO:
            return self.casar(tipo)

        self.falhar("Tipo primitivo inválido", PRIMARIOS_TIPO)

    def stmtNoId(self) -> Comando:
        self.entrar("StmtNoId")

        tipo = self.fluxo.atual().tipo

        if tipo in (UNARIOS_OP | INICIO_ATOM_NO_ID):
            token = self.fluxo.atual()
            expr = self.exprNoId()
            self.casar(TiposToken.SEMICOLON)
            return ComandoExpr(expr, linha=token.linha, coluna=token.coluna)

        if tipo in COMANDOS_COM_PALAVRA_RESERVADA:
            return self.comandoComPalavraReservada()

        self.falhar(
            "Comando inválido",
            UNARIOS_OP
            | INICIO_ATOM_NO_ID
            | COMANDOS_COM_PALAVRA_RESERVADA,
        )


    def exprNoId(self) -> Expr:
        self.entrar("ExprNoId")

        tipo = self.fluxo.atual().tipo

        if tipo in UNARIOS_OP:
            operador = self.unaryOp()
            base = OpUnaria(operador.tipo.name, self.unaryExpr(),
                            linha=operador.linha, coluna=operador.coluna)
            return self.continuarExpr(base)

        elif tipo in ATOM:
            base = self.atomNoId()
            base = self.indexLinha(base)
            return self.continuarExpr(base)

        else:
            self.falhar("Expressão inválida",
                        UNARIOS_OP | ATOM
            )


    def atomNoId(self) -> Expr:
        self.entrar("AtomNoId")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.OPEN_PARENTHESES:
            self.casar(TiposToken.OPEN_PARENTHESES)
            interna = self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            return interna
        elif tipo in INICIO_ATOM_NO_ID:
            return literalDoToken(self.casar(tipo))
        else:
            self.falhar("Expressão atômica sem identificador inválida", INICIO_ATOM_NO_ID)

    def idList(self, tipo: Token) -> list[DeclVariavel]:
        self.entrar("idList")

        nome = self.casar(TiposToken.ID)
        primeira = DeclVariavel(nomeTipo(tipo), nome.lexema, self.array(),
                                linha=nome.linha, coluna=nome.coluna)
        return [primeira] + self.idListLinha(tipo)

    def idListLinha(self, tipo: Token) -> list[DeclVariavel]:
        self.entrar("idList'")
        tipoAtual = self.fluxo.atual().tipo

        if tipoAtual is TiposToken.COMMA:
            self.casar(TiposToken.COMMA)
            nome = self.casar(TiposToken.ID)
            declaracao = DeclVariavel(nomeTipo(tipo), nome.lexema, self.array(),
                                      linha=nome.linha, coluna=nome.coluna)
            return [declaracao] + self.idListLinha(tipo)

        elif tipoAtual is TiposToken.SEMICOLON:
            return [] # IdListLinha -. epsilon

        else:
            self.falhar("Continuação da lista de identificadores inválida",
                        {TiposToken.COMMA, TiposToken.SEMICOLON})

    def array(self) -> int | None:
        self.entrar("Array")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.OPEN_BRACKETS:
            self.casar(TiposToken.OPEN_BRACKETS)
            tamanho = self.casar(TiposToken.NUM_INT)
            self.casar(TiposToken.CLOSE_BRACKETS)
            return int(tamanho.lexema) if tamanho.lexema is not None else None

        elif tipo in { TiposToken.COMMA, TiposToken.SEMICOLON, TiposToken.CLOSE_PARENTHESES}:
            return None # Array -> epsilon

        else:
            self.falhar("Sufixo de array inválido",
                        {TiposToken.OPEN_BRACKETS, TiposToken.COMMA, TiposToken.SEMICOLON, TiposToken.CLOSE_PARENTHESES}
            )

    def formalList(self) -> list[Parametro]:
        self.entrar("FormalList")
        tipo = self.fluxo.atual().tipo

        if tipo in INICIO_TIPO:
            tipoToken = self.type()
            nome = self.casar(TiposToken.ID)
            parametro = Parametro(nomeTipo(tipoToken), nome.lexema, self.array(),
                                  linha=nome.linha, coluna=nome.coluna)
            return [parametro] + self.formalRest()

        elif tipo is TiposToken.CLOSE_PARENTHESES:
            return [] # FormalList -> epsilon

        else:
            self.falhar("Lista de parâmetros inválida",
                        INICIO_TIPO | {TiposToken.CLOSE_PARENTHESES}
            )

    def formalRest(self) -> list[Parametro]:
        self.entrar("FormalRest")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.COMMA:
            self.casar(TiposToken.COMMA)
            tipoToken = self.type()
            nome = self.casar(TiposToken.ID)
            parametro = Parametro(nomeTipo(tipoToken), nome.lexema, self.array(),
                                  linha=nome.linha, coluna=nome.coluna)
            return [parametro] + self.formalRest()

        elif tipo is TiposToken.CLOSE_PARENTHESES:
            return [] # FormalRest -> epsilon

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

    def stmtlist(self) -> list[Comando]:
        comandos: list[Comando] = []
        while True:
            self.entrar("StmtList")
            tipo = self.fluxo.atual().tipo

            if tipo is TiposToken.CLOSE_BRACES:
                return comandos # StmtList -> epsilon

            if tipo is TiposToken.END_OF_FILE:
                self.falhar(
                    "Fim de arquivo dentro de um bloco",
                    {TiposToken.CLOSE_BRACES},
                )

            inicio = self.fluxo.posicao()
            try:
                if tipo not in INICIO_STMT:
                    self.falhar(
                        "Lista de comandos (StmtList) inválida",
                        INICIO_STMT | {TiposToken.CLOSE_BRACES},
                    )
                comando = self.stmt()
                if comando is not None:
                    comandos.append(comando)
            except SyntaxError:
                if self.fluxo.chegouAoFim():
                    raise
                self.sincronizarComando(inicio)

    def stmt(self) -> Comando:
        self.entrar("Stmt")
        tipo = self.fluxo.atual().tipo

        if tipo in COMANDOS_COM_PALAVRA_RESERVADA:
            return self.comandoComPalavraReservada()

        elif tipo in (UNARIOS_OP | INICIO_ATOM_NO_ID | {TiposToken.ID}):
            token = self.fluxo.atual()
            expr = self.expr()
            self.casar(TiposToken.SEMICOLON)
            return ComandoExpr(expr, linha=token.linha, coluna=token.coluna)

        else:
            self.falhar(
                "Comando (Stmt) inválido",
                UNARIOS_OP
                | INICIO_ATOM_NO_ID
                | {TiposToken.ID}
                | COMANDOS_COM_PALAVRA_RESERVADA,
            )

    def comandoComPalavraReservada(self) -> Comando:
        token = self.fluxo.atual()
        tipo = token.tipo
        posicao = {"linha": token.linha, "coluna": token.coluna}

        if tipo is TiposToken.IF:
            self.casar(TiposToken.IF)
            self.casar(TiposToken.OPEN_PARENTHESES)
            condicao = self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            inicio_consequente = self.fluxo.posicao()
            entao = None
            try:
                entao = self.stmt()
            except SyntaxError:
                if self.fluxo.chegouAoFim():
                    raise
                self.sincronizarComando(inicio_consequente, pararEmElse=True)
            self.casar(TiposToken.ELSE)
            senao = self.stmt()
            return If(condicao, entao, senao, **posicao)

        if tipo is TiposToken.WHILE:
            self.casar(TiposToken.WHILE)
            self.casar(TiposToken.OPEN_PARENTHESES)
            condicao = self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            return While(condicao, self.stmt(), **posicao)

        if tipo is TiposToken.BREAK:
            self.casar(TiposToken.BREAK)
            self.casar(TiposToken.SEMICOLON)
            return Break(**posicao)

        if tipo is TiposToken.PRINT:
            self.casar(TiposToken.PRINT)
            self.casar(TiposToken.OPEN_PARENTHESES)
            argumentos = self.exprList()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            self.casar(TiposToken.SEMICOLON)
            return Print(argumentos, **posicao)

        if tipo is TiposToken.READLN:
            self.casar(TiposToken.READLN)
            self.casar(TiposToken.OPEN_PARENTHESES)
            alvo = self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            self.casar(TiposToken.SEMICOLON)
            return Readln(alvo, **posicao)

        if tipo is TiposToken.RETURN:
            self.casar(TiposToken.RETURN)
            valor = self.expr()
            self.casar(TiposToken.SEMICOLON)
            return Return(valor, **posicao)

        self.casar(TiposToken.OPEN_BRACES)
        comandos = self.stmtlist()
        self.casar(TiposToken.CLOSE_BRACES)
        return Bloco(comandos=comandos, **posicao)

    def exprList(self) -> list[Expr]:
        self.entrar("ExprList")
        tipo = self.fluxo.atual().tipo

        if tipo in (UNARIOS_OP | INICIO_ATOM_NO_ID | {TiposToken.ID}):
            return self.exprListLinha()

        elif tipo is TiposToken.CLOSE_PARENTHESES:
            return []

        else:
            self.falhar(
                "Lista de expressões (ExprList) inválida",
                UNARIOS_OP | INICIO_ATOM_NO_ID | {TiposToken.ID, TiposToken.CLOSE_PARENTHESES}
            )

    def exprListLinha(self) -> list[Expr]:
        self.entrar("ExprList'")

        primeira = self.expr()
        return [primeira] + self.restoExprList()

    def restoExprList(self) -> list[Expr]:
        self.entrar("RestoExprList")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.COMMA:
            self.casar(TiposToken.COMMA)
            return self.exprListLinha()

        # epsilon
        elif tipo is TiposToken.CLOSE_PARENTHESES:
            return []

        else:
            self.falhar(
                "Continuação da lista de expressões inválida",
                {TiposToken.COMMA, TiposToken.CLOSE_PARENTHESES}
            )

    def expr(self) -> Expr:
        self.entrar("Expr")

        return self.assignExpr()

    def assignExpr(self) -> Expr:
        self.entrar("AssignExpr")

        alvo = self.orExpr()
        return self.assignLinha(alvo)

    def assignLinha(self, alvo: Expr) -> Expr:
        self.entrar("AssignLinha")

        if self.fluxo.verificar(TiposToken.ASSIGN):
            igual = self.casar(TiposToken.ASSIGN)
            valor = self.assignExpr()
            return Atribuicao(alvo, valor, linha=igual.linha, coluna=igual.coluna)

        return alvo 

    def operacaoBinaria(self, esquerda: Expr, operandoDireito) -> OpBinaria:
        operador = self.casar(self.fluxo.atual().tipo)
        direita = operandoDireito()
        return OpBinaria(operador.tipo.name, esquerda, direita,
                         linha=operador.linha, coluna=operador.coluna)

    def orExpr(self) -> Expr:
        self.entrar("OrExpr")

        return self.orLinha(self.andExpr())

    def orLinha(self, esquerda: Expr) -> Expr:
        self.entrar("OrLinha")

        if self.fluxo.verificar(TiposToken.OR):
            return self.orLinha(self.operacaoBinaria(esquerda, self.andExpr))

        return esquerda

    def andExpr(self) -> Expr:
        self.entrar("AndExpr")

        return self.andLinha(self.equalityExpr())

    def andLinha(self, esquerda: Expr) -> Expr:
        self.entrar("AndLinha")

        if self.fluxo.verificar(TiposToken.AND):
            return self.andLinha(self.operacaoBinaria(esquerda, self.equalityExpr))

        return esquerda

    def equalityExpr(self) -> Expr:
        self.entrar("EqualityExpr")

        return self.equalityLinha(self.relExpr())

    def equalityLinha(self, esquerda: Expr) -> Expr:
        self.entrar("EqualityLinha")
        tipo = self.fluxo.atual().tipo

        if tipo in {TiposToken.EQUALS, TiposToken.DIFF}:
            return self.equalityLinha(self.operacaoBinaria(esquerda, self.relExpr))

        return esquerda

    def relExpr(self) -> Expr:
        self.entrar("RelExpr")

        return self.relLinha(self.addExpr())

    def relLinha(self, esquerda: Expr) -> Expr:
        self.entrar("RelLinha")
        tipo = self.fluxo.atual().tipo

        if tipo in {
            TiposToken.LESS_THAN,
            TiposToken.LESS_THAN_EQUAL,
            TiposToken.GREATER_THAN,
            TiposToken.GREATER_THAN_EQUAL,
        }:
            return self.relLinha(self.operacaoBinaria(esquerda, self.addExpr))

        return esquerda


    def addExpr(self) -> Expr:
        self.entrar("AddExpr")

        return self.addLinha(self.mulExpr())

    def addLinha(self, esquerda: Expr) -> Expr:
        self.entrar("AddLinha")
        tipo = self.fluxo.atual().tipo

        if tipo in {TiposToken.PLUS, TiposToken.MINUS}:
            return self.addLinha(self.operacaoBinaria(esquerda, self.mulExpr))

        return esquerda

    def mulExpr(self) -> Expr:
        self.entrar("MulExpr")

        return self.mulLinha(self.unaryExpr())

    def mulLinha(self, esquerda: Expr) -> Expr:
        self.entrar("MulLinha")
        tipo = self.fluxo.atual().tipo

        if tipo in {TiposToken.MULT, TiposToken.DIV, TiposToken.MOD}:
            return self.mulLinha(self.operacaoBinaria(esquerda, self.unaryExpr))

        return esquerda

    def unaryExpr(self) -> Expr:
        self.entrar("UnaryExpr")
        tipo = self.fluxo.atual().tipo

        if tipo in UNARIOS_OP:
            operador = self.unaryOp()
            return OpUnaria(operador.tipo.name, self.unaryExpr(),
                            linha=operador.linha, coluna=operador.coluna)

        return self.primary()

    def primary(self) -> Expr:
        self.entrar("Primary")

        return self.indexLinha(self.atom())

    def indexLinha(self, base: Expr) -> Expr:
        self.entrar("IndexLinha")

        if self.fluxo.verificar(TiposToken.OPEN_BRACKETS):
            abre = self.casar(TiposToken.OPEN_BRACKETS)
            indice = self.expr()
            self.casar(TiposToken.CLOSE_BRACKETS)
            no = Indexacao(base, indice, linha=abre.linha, coluna=abre.coluna)
            return self.indexLinha(no)

        return base

    def atom(self) -> Expr:
        self.entrar("Atom")
        tipo = self.fluxo.atual().tipo

        if tipo is TiposToken.ID:
            nome = self.casar(TiposToken.ID)
            return self.callOpt(nome)

        elif tipo is TiposToken.OPEN_PARENTHESES:
            self.casar(TiposToken.OPEN_PARENTHESES)
            interna = self.expr()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            return interna

        elif tipo in (ATOM - {TiposToken.OPEN_PARENTHESES}):
            return literalDoToken(self.casar(tipo))

        else:
            self.falhar(
                "expressão atômica (Atom) inválido",
                ATOM | {TiposToken.ID}
            )

    def callOpt(self, nome: Token) -> Expr:
        self.entrar("CallOpt")

        if self.fluxo.verificar(TiposToken.OPEN_PARENTHESES):
            self.casar(TiposToken.OPEN_PARENTHESES)
            argumentos = self.exprList()
            self.casar(TiposToken.CLOSE_PARENTHESES)
            return Chamada(nome.lexema, argumentos,
                           linha=nome.linha, coluna=nome.coluna)

        return Id(nome.lexema, linha=nome.linha, coluna=nome.coluna)

    def unaryOp(self) -> Token:
        self.entrar("UnaryOp")
        tipo = self.fluxo.atual().tipo

        if tipo in UNARIOS_OP:
            return self.casar(tipo)

        else:
            self.falhar("Operador Unário (UnaryOP) inválido", UNARIOS_OP)
