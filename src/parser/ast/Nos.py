from dataclasses import dataclass, field

from src.lexer.models.Token import Token


@dataclass
class NoAST:

    linha: int = field(default=0, kw_only=True)
    coluna: int = field(default=0, kw_only=True)



@dataclass
class Expr(NoAST):
    pass


@dataclass
class Id(Expr):
    nome: str


@dataclass
class Literal(Expr):
    tipo: str
    valor: str | None


@dataclass
class OpBinaria(Expr):
    operador: str
    esquerda: Expr | None
    direita: Expr | None


@dataclass
class OpUnaria(Expr):
    operador: str
    operando: Expr | None


@dataclass
class Atribuicao(Expr):
    alvo: Expr | None
    valor: Expr | None


@dataclass
class Indexacao(Expr):
    vetor: Expr | None
    indice: Expr | None


@dataclass
class Chamada(Expr):
    nome: str
    argumentos: list[Expr] = field(default_factory=list)



@dataclass
class Comando(NoAST):
    pass


@dataclass
class Bloco(Comando):
    declaracoes: list["DeclVariavel"] = field(default_factory=list)
    comandos: list[Comando] = field(default_factory=list)


@dataclass
class If(Comando):
    condicao: Expr | None
    entao: Comando | None
    senao: Comando | None


@dataclass
class While(Comando):
    condicao: Expr | None
    corpo: Comando | None


@dataclass
class Break(Comando):
    pass


@dataclass
class Print(Comando):
    argumentos: list[Expr] = field(default_factory=list)


@dataclass
class Readln(Comando):
    alvo: Expr | None


@dataclass
class Return(Comando):
    valor: Expr | None


@dataclass
class ComandoExpr(Comando):
    expr: Expr | None



@dataclass
class Declaracao(NoAST):
    pass


@dataclass
class DeclVariavel(Declaracao):
    tipo: str
    nome: str
    tamanho: int | None = None


@dataclass
class Parametro(NoAST):
    tipo: str
    nome: str
    tamanho: int | None = None


@dataclass
class DeclStruct(Declaracao):
    campos: list[DeclVariavel] = field(default_factory=list)


@dataclass
class DeclFuncao(Declaracao):
    tipoRetorno: str
    nome: str
    parametros: list[Parametro] = field(default_factory=list)
    corpo: Bloco = field(default_factory=Bloco)


@dataclass
class Programa(NoAST):
    declaracoes: list[Declaracao] = field(default_factory=list)

No = NoAST


def nomeTipo(token: Token) -> str:
    return token.lexema or token.tipo.name.lower()


def literalDoToken(token: Token) -> Literal:
    return Literal(token.tipo.name, token.lexema,
                   linha=token.linha, coluna=token.coluna)
