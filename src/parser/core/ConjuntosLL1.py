"""Conjuntos da gramática LL(1) e pontos de recuperação do parser."""

from src.lexer.TiposToken import TiposToken


class ConjuntosLL1:
    """Centraliza as decisões preditivas da gramática """

    INICIO_TIPO = {
        TiposToken.INT, TiposToken.FLOAT, TiposToken.BOOL,
        TiposToken.CHAR, TiposToken.ID,
    }

    PRIMARIOS_TIPO = {
        TiposToken.INT, TiposToken.FLOAT, TiposToken.CHAR, TiposToken.BOOL,
    }

    UNARIOS_OP = {TiposToken.DECREMENT, TiposToken.INCREMENT, TiposToken.NEG}

    ATOM = {
        TiposToken.NUM_INT, TiposToken.NUM_FLOAT, TiposToken.LITERAL,
        TiposToken.ASCII, TiposToken.OPEN_PARENTHESES,
        TiposToken.TRUE, TiposToken.FALSE,
    }

    INICIO_ATOM_NO_ID = ATOM

    INICIO_EXPR = UNARIOS_OP | ATOM | {TiposToken.ID}

    INICIO_STMT_SEM_ID = {
        TiposToken.IF, TiposToken.WHILE, TiposToken.BREAK,
        TiposToken.PRINT, TiposToken.READLN, TiposToken.RETURN,
        TiposToken.OPEN_BRACES,
    } | UNARIOS_OP | ATOM

    INICIO_STMT = INICIO_STMT_SEM_ID | {TiposToken.ID}

    COMANDOS_COM_PALAVRA_RESERVADA = {
        TiposToken.IF, TiposToken.WHILE, TiposToken.BREAK,
        TiposToken.PRINT, TiposToken.READLN, TiposToken.RETURN,
        TiposToken.OPEN_BRACES,
    }

    CONTINUACAO_ID_EXPR = {
        TiposToken.OPEN_PARENTHESES, TiposToken.OPEN_BRACKETS,
        TiposToken.MULT, TiposToken.DIV, TiposToken.MOD,
        TiposToken.PLUS, TiposToken.MINUS,
        TiposToken.LESS_THAN, TiposToken.LESS_THAN_EQUAL,
        TiposToken.GREATER_THAN, TiposToken.GREATER_THAN_EQUAL,
        TiposToken.EQUALS, TiposToken.DIFF,
        TiposToken.AND, TiposToken.OR, TiposToken.ASSIGN,
        TiposToken.SEMICOLON,
    }

    def __init__(self) -> None:
        # Conjuntos FIRST e FOLLOW consultados pelo motor, conforme
        # gramaticaCompleta_4.g. Body e StmtList aceitam epsilon.
        self.FIRSTS: dict[str, set[TiposToken]] = {
            "Program": self.INICIO_TIPO | {TiposToken.TYPEDEF},
            "Type": set(self.INICIO_TIPO),
            "PrimType": set(self.PRIMARIOS_TIPO),
            "Stmt": set(self.INICIO_STMT),
            "StmtList": set(self.INICIO_STMT),
            "Expr": set(self.INICIO_EXPR),
            "Body": self.PRIMARIOS_TIPO | self.INICIO_STMT,
            "VarDecl": set(self.INICIO_TIPO),
            "FormalList": set(self.INICIO_TIPO),
            "Array": {TiposToken.OPEN_BRACKETS},
        }

        self.FOLLOW: dict[str, set[TiposToken]] = {
            "Program": {TiposToken.END_OF_FILE},
            "Stmt": self.INICIO_STMT | {
                TiposToken.ELSE, TiposToken.CLOSE_BRACES,
            },
            "StmtList": {TiposToken.CLOSE_BRACES},
            "Expr": {
                TiposToken.CLOSE_PARENTHESES, TiposToken.COMMA,
                TiposToken.SEMICOLON, TiposToken.CLOSE_BRACKETS,
            },
        }

        self.NULLABLE: set[str] = {
            "Program'", "VarDecl", "Body", "IdExprRest", "idList'", "Array",
            "FormalList", "FormalRest", "StmtList", "ExprList",
            "RestoExprList", "Assign'", "Or'", "And'",
            "Equality'", "Rel'", "Add'", "Mul'", "Index'", "CallOpt",
        }

        # Um delimitador ausente pode ser inserido diante desses tokens sem
        # consumir o início da construção seguinte.
        self.SEGUIDORES_PARA_INSERCAO: dict[TiposToken, set[TiposToken]] = {
            TiposToken.CLOSE_PARENTHESES: self.FIRSTS["Stmt"] | {
                TiposToken.SEMICOLON, TiposToken.OPEN_BRACES,
            },
            TiposToken.CLOSE_BRACKETS: self.FOLLOW["Expr"] | {
                TiposToken.ASSIGN, TiposToken.CLOSE_BRACES,
            },
            TiposToken.SEMICOLON: (
                self.FOLLOW["Stmt"] | self.FIRSTS["Program"]
                | self.FOLLOW["Program"]
            ),
            TiposToken.CLOSE_BRACES: self.FOLLOW["Program"],
        }

        self.NOMES_DELIMITADORES = {
            TiposToken.CLOSE_PARENTHESES: "')'",
            TiposToken.CLOSE_BRACKETS: "']'",
            TiposToken.CLOSE_BRACES: "'}'",
            TiposToken.SEMICOLON: "';'",
        }
