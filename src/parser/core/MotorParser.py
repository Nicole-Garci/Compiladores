from src.lexer.models.Token import Token
from src.lexer.TiposToken import TiposToken
from src.parser.SaidaParser import SaidaParser
from src.parser.core.FluxoTokens import FluxoTokens

class MotorParser:
    def __init__(self, fluxo: FluxoTokens, saida: SaidaParser) -> None:
        self.fluxo = fluxo
        self.saida = saida

    def entrar(self, nome: str) -> None:
        self.saida.naoTerminal(nome)

    def casar(self, esperado: TiposToken) -> Token:
        encontrou = self.fluxo.atual()

        if encontrou.tipo is not esperado:
            raise SyntaxError(
                f"Erro sintático em {encontrou.linha}:{encontrou.coluna}: Era esperado {esperado.name}, "
                f"mas foi encontrado {encontrou.tipo.name}"
            )

        self.saida.terminalCasado(encontrou)
        self.fluxo.avancar()

        return encontrou

    ## Análises Recursivas

    def program(self, token: Token):
        if self.fluxo.atual() != token:
            raise SyntaxError("Token não esperado")
        else: self.fluxo.avancar()

        self.typeDeclOne()

    def typeDeclOne(self):

    def restoDecl(self):

    def programLinha(self):

    def varDecl(self):

    def body(self):

    def bodyId(self):

    def idExprRest(self):

    def primType(self):

    def stmtNoId(self):

    def exprNoId(self):

    def atomNoId(self):

    def idList(self):

    def array(self):

    def formalList(self):

    def type(self):

    def stmtlist(self):

    def stmt(self):
        
    def exprList(self):
        
    def exprListLinha(self):
        
    def restoExprList(self):
        
    def Expr(self):
        
    def assignExpr(self):
        
    def assignLinha(self):
        
    def orExpr(self):
        
    def orLinha(self):
        
    def andExpr(self):
        
    def andLinha(self):
        
    def equalityExpr(self):
        
    def equalityLinha(self):
        
    def relExpr(self):
        
    def relLinha(self):
        
    def addExpr(self):
        
    def addLinha(self):
        
    def mulExpr(self):
        
    def mulLinha(self):
        
    def unaryExpr(self):
        
    def primary(self):
        
    def indexLinha(self):
        
    def atom(self):
        
    def callOpt(self):
        
    def unaryOp(self):
        
