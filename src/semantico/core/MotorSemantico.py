from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag, auto
from math import isfinite

from src.parser.ast.Nos import (
    Atribuicao, Bloco, Break, Chamada, Comando, ComandoExpr, DeclFuncao,
    DeclStruct, DeclVariavel, Expr, Id, If, Indexacao, Literal, NoAST,
    OpBinaria, OpUnaria, Parametro, Print, Programa, Readln, Return, While,
)
from src.semantico.Escopo import Escopo
from src.semantico.GerenciadorErrosSemanticos import GerenciadorErrosSemanticos
from src.semantico.models.ResultadoExpressao import ResultadoExpressao
from src.semantico.models.SimboloSemantico import (
    CATEGORIA_FUNCAO, CATEGORIA_PARAMETRO, CATEGORIA_VARIAVEL, CATEGORIA_VETOR,
    SimboloSemantico,
)
from src.semantico.models.TipoSemantico import (
    TIPO_BOOL, TIPO_CHAR, TIPO_ERRO, TIPO_FLOAT, TIPO_INT, TIPOS_PRIMITIVOS,
    TipoSemantico, tipoVetor,
)
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


REGIAO_GLOBAL = "global"
REGIAO_LOCAL = "local"
TIPO_TEXTO = TipoSemantico("texto", 1)
ARITMETICA = {"PLUS": "add", "MINUS": "sub", "MULT": "mul", "DIV": "div", "MOD": "mod"}
COMPARACOES = {
    "EQUALS": "eq", "DIFF": "ne", "LESS_THAN": "lt", "LESS_THAN_EQUAL": "le",
    "GREATER_THAN": "gt", "GREATER_THAN_EQUAL": "ge",
}


class Fluxo(IntFlag):
    CONTINUA = auto()
    RETORNA = auto()
    INTERROMPE = auto()


@dataclass
class ContextoFuncao:
    simbolo: SimboloSemantico
    proximoDeslocamento: int = 0
    saidaLaco: OperandoTAC | None = None
    destinoRetorno: OperandoTAC | None = None


class MotorSemantico:
    def __init__(self, gerenciadorErros: GerenciadorErrosSemanticos) -> None:
        self.gerenciadorErros = gerenciadorErros
        self.escopoGlobal = Escopo()
        self.programaTAC = ProgramaTAC()
        self.tiposDeclarados: dict[str, TipoSemantico] = {}
        self.structs: list[TipoSemantico] = []
        self.escoposFuncoes: dict[str, Escopo] = {}
        self.assinaturas: dict[int, SimboloSemantico] = {}
        self.proximoTemporario = 0
        self.proximoRotulo = 0

    def executar(self, programa: Programa) -> ProgramaTAC:
        self.cadastrarGlobais(programa)

        for declaracao in programa.declaracoes:
            if isinstance(declaracao, DeclFuncao):
                self.visitarFuncao(declaracao)

        return self.programaTAC

    def cadastrarGlobais(self, programa: Programa) -> None:
        for declaracao in programa.declaracoes:
            if isinstance(declaracao, DeclStruct):
                self.validarStruct(declaracao)
            elif isinstance(declaracao, DeclVariavel):
                self.cadastrarVariavelGlobal(declaracao)
            elif isinstance(declaracao, DeclFuncao):
                self.cadastrarAssinatura(declaracao)

    def cadastrarVariavelGlobal(self, no: DeclVariavel) -> None:
        tipo = self.resolverTipo(no.tipo, no.tamanho, no)
        endereco = OperandoTAC(REGIAO_GLOBAL, self.programaTAC.tamanhoDados)
        simbolo = SimboloSemantico(
            nome=no.nome,
            categoria=self.categoriaVariavel(tipo),
            tipo=tipo,
            endereco=endereco,
            linha=no.linha,
            coluna=no.coluna,
        )

        if self.inserir(self.escopoGlobal, simbolo, no):
            self.programaTAC.tamanhoDados += tipo.tamanhoBytes

    def cadastrarAssinatura(self, no: DeclFuncao) -> None:
        tipoRetorno = self.resolverTipo(no.tipoRetorno, None, no)
        tiposParametros = [
            self.resolverTipo(parametro.tipo, parametro.tamanho, parametro)
            for parametro in no.parametros
        ]
        simbolo = SimboloSemantico(
            nome=no.nome,
            categoria=CATEGORIA_FUNCAO,
            tipo=tipoRetorno,
            parametros=tiposParametros,
            linha=no.linha,
            coluna=no.coluna,
        )
        self.assinaturas[id(no)] = simbolo
        self.inserir(self.escopoGlobal, simbolo, no)

    def validarStruct(self, no: DeclStruct) -> TipoSemantico:
        nomeStruct = no.nome
        tipoStruct = TipoSemantico(
            nome=f"struct {nomeStruct}" if nomeStruct else f"struct #{len(self.structs) + 1}",
            tamanhoBytes=0,
        )

        for campo in no.campos:
            tipoCampo = self.resolverTipo(campo.tipo, campo.tamanho, campo)

            if campo.nome in tipoStruct.campos:
                self.gerenciadorErros.registrar(
                    campo,
                    f"Campo '{campo.nome}' declarado mais de uma vez no struct",
                )
                continue

            tipoStruct.campos[campo.nome] = (tipoCampo, tipoStruct.tamanhoBytes)
            tipoStruct.tamanhoBytes += tipoCampo.tamanhoBytes

        self.structs.append(tipoStruct)

        if nomeStruct:
            if nomeStruct in self.tiposDeclarados or nomeStruct in TIPOS_PRIMITIVOS:
                self.gerenciadorErros.registrar(
                    no, f"Tipo '{nomeStruct}' declarado mais de uma vez"
                )
            else:
                self.tiposDeclarados[nomeStruct] = tipoStruct

        return tipoStruct

    def visitarFuncao(self, no: DeclFuncao) -> None:
        simboloFuncao = self.assinaturas[id(no)]
        escopo = Escopo(self.escopoGlobal)
        contexto = ContextoFuncao(simboloFuncao)
        deslocamentosParametros: list[int] = []

        self.instrucao(no, "label", OperandoTAC("rotulo", no.nome))
        if simboloFuncao.tipo.ehAgregado():
            # O primeiro parâmetro interno aponta para a área do chamador.
            destino = self.reservarLocal(contexto, 1)
            contexto.destinoRetorno = self.fixarValor(no, destino)
            deslocamentosParametros.append(destino.valor)

        for parametro, tipo in zip(no.parametros, simboloFuncao.parametros):
            deslocamento = self.cadastrarLocal(
                escopo, contexto, parametro, tipo, CATEGORIA_PARAMETRO
            )
            if deslocamento is not None:
                deslocamentosParametros.append(deslocamento)
                if tipo.ehAgregado():
                    destino = OperandoTAC(REGIAO_LOCAL, deslocamento)
                    origem = self.fixarValor(parametro, destino)
                    self.copiar(parametro, destino, origem, tipo)

        fluxo = self.visitarBloco(no.corpo, escopo, contexto, novoEscopo=False)
        if fluxo & Fluxo.CONTINUA:
            self.erro(no, f"A função '{no.nome}' pode terminar sem return")
        if no.nome == self.programaTAC.entrada and deslocamentosParametros:
            self.erro(no, "A função de entrada main exige zero parâmetros e retorno escalar")

        if self.escopoGlobal.simbolos.get(no.nome) is not simboloFuncao:
            return

        self.escoposFuncoes[no.nome] = escopo
        self.programaTAC.quadros[no.nome] = (
            contexto.proximoDeslocamento,
            deslocamentosParametros,
        )

    def visitarBloco(
        self,
        no: Bloco,
        escopo: Escopo,
        contexto: ContextoFuncao,
        novoEscopo: bool = True,
    ) -> Fluxo:
        escopoBloco = Escopo(escopo) if novoEscopo else escopo

        for declaracao in no.declaracoes:
            tipo = self.resolverTipo(declaracao.tipo, declaracao.tamanho, declaracao)
            self.cadastrarLocal(
                escopoBloco, contexto, declaracao, tipo, self.categoriaVariavel(tipo)
            )

        fluxo = Fluxo.CONTINUA
        for comando in no.comandos:
            fluxoComando = self.visitarComando(comando, escopoBloco, contexto)
            if fluxo & Fluxo.CONTINUA:
                fluxo = (fluxo & ~Fluxo.CONTINUA) | fluxoComando
        return fluxo

    def visitarComando(
        self, no: Comando | None, escopo: Escopo, contexto: ContextoFuncao
    ) -> Fluxo:
        if isinstance(no, Bloco):
            return self.visitarBloco(no, escopo, contexto)
        if isinstance(no, If):
            return self.visitarIf(no, escopo, contexto)
        if isinstance(no, While):
            return self.visitarWhile(no, escopo, contexto)
        if isinstance(no, Break):
            if contexto.saidaLaco is None:
                self.erro(no, "break fora de um laço")
                return Fluxo.CONTINUA
            self.instrucao(no, "goto", contexto.saidaLaco)
            return Fluxo.INTERROMPE
        if isinstance(no, Return):
            self.visitarReturn(no, escopo, contexto)
            return Fluxo.RETORNA
        if isinstance(no, ComandoExpr):
            self.visitarExpressao(no.expr, escopo, contexto)
        elif isinstance(no, Print):
            for argumento in no.argumentos:
                resultado = self.visitarExpressao(argumento, escopo, contexto)
                valor = self.valorEscalar(argumento, resultado)
                if valor is not None:
                    self.instrucao(argumento, "print", valor)
        elif isinstance(no, Readln):
            self.visitarReadln(no, escopo, contexto)
        return Fluxo.CONTINUA

    def visitarIf(self, no: If, escopo: Escopo, contexto: ContextoFuncao) -> Fluxo:
        condicao = self.condicaoBooleana(no.condicao, escopo, contexto)
        senao, fim = self.rotulo(), self.rotulo()
        self.instrucao(no, "if_false", condicao, senao)
        fluxoEntao = self.visitarComando(no.entao, escopo, contexto)
        self.instrucao(no, "goto", fim)
        self.instrucao(no, "label", senao)
        fluxoSenao = self.visitarComando(no.senao, escopo, contexto)
        self.instrucao(no, "label", fim)
        if condicao.categoria == "constante":
            return fluxoEntao if condicao.valor else fluxoSenao
        return fluxoEntao | fluxoSenao

    def visitarWhile(self, no: While, escopo: Escopo, contexto: ContextoFuncao) -> Fluxo:
        inicio, fim = self.rotulo(), self.rotulo()
        self.instrucao(no, "label", inicio)
        condicao = self.condicaoBooleana(no.condicao, escopo, contexto)
        self.instrucao(no, "if_false", condicao, fim)
        anterior = contexto.saidaLaco
        contexto.saidaLaco = fim
        fluxoCorpo = self.visitarComando(no.corpo, escopo, contexto)
        contexto.saidaLaco = anterior
        self.instrucao(no, "goto", inicio)
        self.instrucao(no, "label", fim)
        if condicao.categoria == "constante":
            if not condicao.valor:
                return Fluxo.CONTINUA
            saida = Fluxo.CONTINUA if fluxoCorpo & Fluxo.INTERROMPE else Fluxo(0)
            return saida | (fluxoCorpo & Fluxo.RETORNA)
        return Fluxo.CONTINUA | (fluxoCorpo & Fluxo.RETORNA)

    def condicaoBooleana(
        self, no: Expr | None, escopo: Escopo, contexto: ContextoFuncao
    ) -> OperandoTAC:
        resultado = self.visitarExpressao(no, escopo, contexto)
        if resultado.tipo == TIPO_BOOL:
            return self.valorEscalar(no, resultado)
        if not resultado.tipo.ehErro():
            self.erro(no, "A condição deve ter tipo bool")
        return OperandoTAC("constante", False)

    def visitarReturn(self, no: Return, escopo: Escopo, contexto: ContextoFuncao) -> None:
        resultado = self.visitarExpressao(no.valor, escopo, contexto)
        esperado = contexto.simbolo.tipo
        if resultado.tipo.ehErro() or esperado.ehErro():
            return
        if resultado.tipo != esperado:
            self.erro(
                no, f"Retorno incompatível: esperado {esperado.nome}, recebido {resultado.tipo.nome}"
            )
        elif contexto.destinoRetorno is not None:
            self.copiar(no, contexto.destinoRetorno, resultado.operando, esperado)
            self.instrucao(no, "return")
        else:
            self.instrucao(no, "return", self.valorEscalar(no, resultado))

    def visitarReadln(self, no: Readln, escopo: Escopo, contexto: ContextoFuncao) -> None:
        resultado = self.visitarExpressao(no.alvo, escopo, contexto)
        if resultado.tipo.ehErro():
            return
        if not resultado.atribuivel or resultado.tipo.ehAgregado():
            self.erro(no, "readln exige um destino escalar atribuível")
            return
        destino = self.temporario() if resultado.indireto else resultado.operando
        self.instrucao(no, "read", destino, OperandoTAC("constante", resultado.tipo.nome))
        if resultado.indireto:
            self.gravar(no, resultado, destino)

    def visitarExpressao(
        self, no: Expr | None, escopo: Escopo, contexto: ContextoFuncao | None = None
    ) -> ResultadoExpressao:
        if isinstance(no, Literal):
            return self.visitarLiteral(no)
        if isinstance(no, Id):
            simbolo = escopo.buscar(no.nome)
            if simbolo is None or simbolo.endereco is None:
                return self.erro(no, f"'{no.nome}' não designa uma variável visível")
            return ResultadoExpressao(simbolo.tipo, simbolo.endereco, atribuivel=True)
        if isinstance(no, Atribuicao):
            return self.visitarAtribuicao(no, escopo, contexto)
        if isinstance(no, Indexacao):
            return self.visitarIndexacao(no, escopo, contexto)
        if isinstance(no, OpBinaria):
            return self.visitarBinaria(no, escopo, contexto)
        if isinstance(no, OpUnaria):
            return self.visitarUnaria(no, escopo, contexto)
        if isinstance(no, Chamada):
            return self.visitarChamada(no, escopo, contexto)
        return self.erro(no, "Expressão ausente ou inválida")

    def visitarLiteral(self, no: Literal) -> ResultadoExpressao:
        if no.tipo in {"TRUE", "FALSE"}:
            tipo, valor = TIPO_BOOL, no.tipo == "TRUE"
        else:
            try:
                if no.tipo == "NUM_INT":
                    tipo, valor = TIPO_INT, int(no.valor)
                elif no.tipo == "NUM_FLOAT":
                    tipo, valor = TIPO_FLOAT, float(no.valor)
                    if not isfinite(valor):
                        return self.erro(no, "Literal real fora da faixa finita")
                elif no.tipo in {"ASCII", "LITERAL"}:
                    tipo = TIPO_CHAR if no.tipo == "ASCII" else TIPO_TEXTO
                    valor = no.valor[1:-1]
                    if tipo == TIPO_CHAR and len(valor) != 1:
                        return self.erro(no, "Literal char deve conter um caractere")
                else:
                    return self.erro(no, "Tipo de literal desconhecido")
            except (TypeError, ValueError):
                return self.erro(no, "Literal inválido")
        return ResultadoExpressao(tipo, OperandoTAC("constante", valor))

    def visitarAtribuicao(
        self, no: Atribuicao, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        alvo = self.visitarExpressao(no.alvo, escopo, contexto)
        origem = self.visitarExpressao(no.valor, escopo, contexto)
        if alvo.tipo.ehErro() or origem.tipo.ehErro():
            return ResultadoExpressao(TIPO_ERRO)
        if not alvo.atribuivel:
            return self.erro(no, "O destino da atribuição não é atribuível")
        if alvo.tipo != origem.tipo:
            return self.erro(
                no, f"Atribuição incompatível: {alvo.tipo.nome} recebe {origem.tipo.nome}"
            )
        if alvo.tipo.ehAgregado():
            self.copiar(no, alvo.operando, origem.operando, alvo.tipo)
            return ResultadoExpressao(alvo.tipo, alvo.operando, indireto=alvo.indireto)
        valor = self.fixarValor(no, self.valorEscalar(no, origem))
        self.gravar(no, alvo, valor)
        return ResultadoExpressao(alvo.tipo, valor)

    def visitarIndexacao(
        self, no: Indexacao, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        base = self.visitarExpressao(no.vetor, escopo, contexto)
        indice = self.visitarExpressao(no.indice, escopo, contexto)
        tipo = base.tipo
        if tipo.ehErro() or indice.tipo.ehErro():
            return ResultadoExpressao(TIPO_ERRO)
        if not tipo.ehAgregado():
            return self.erro(no, "Indexação aplicada a um tipo escalar")
        if indice.tipo != TIPO_INT:
            return self.erro(no.indice, "O índice deve ter tipo int")
        literal = isinstance(no.indice, Literal) and no.indice.tipo == "NUM_INT"
        if tipo.ehVetor():
            elemento = tipo.elemento
            valor = self.valorEscalar(no.indice, indice)
            if literal:
                if not 0 <= valor.valor < tipo.comprimento:
                    return self.erro(no.indice, "Índice fora dos limites do vetor")
                deslocamento = OperandoTAC("constante", valor.valor * elemento.tamanhoBytes)
            else:
                valor = self.fixarValor(no.indice, valor)
                limite = OperandoTAC("constante", tipo.comprimento)
                self.instrucao(no.indice, "bounds", valor, limite)
                deslocamento = valor
                if elemento.tamanhoBytes != 1:
                    deslocamento = self.temporario()
                    largura = OperandoTAC("constante", elemento.tamanhoBytes)
                    self.instrucao(no, "mul", deslocamento, valor, largura)
        else:
            if not literal:
                return self.erro(no.indice, "O campo da struct exige um índice inteiro literal")
            campos = list(tipo.campos.values())
            posicao = indice.operando.valor
            if not 0 <= posicao < len(campos):
                return self.erro(no.indice, "Índice fora dos campos da struct")
            elemento, offset = campos[posicao]
            deslocamento = OperandoTAC("constante", offset)
        endereco = self.endereco(no, base.operando, deslocamento)
        return ResultadoExpressao(elemento, endereco, atribuivel=base.atribuivel, indireto=True)

    def visitarBinaria(
        self, no: OpBinaria, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        if no.operador in {"AND", "OR"}:
            return self.visitarLogica(no, escopo, contexto)
        esquerdo = self.visitarExpressao(no.esquerda, escopo, contexto)
        a = self.fixarValor(no, self.valorEscalar(no.esquerda, esquerdo))
        direito = self.visitarExpressao(no.direita, escopo, contexto)
        b = self.valorEscalar(no.direita, direito)
        if a is None or b is None:
            return ResultadoExpressao(TIPO_ERRO)

        tipos = {esquerdo.tipo.nome, direito.tipo.nome}
        numericos = tipos <= {"int", "float"}
        if no.operador in ARITMETICA:
            if not numericos or (no.operador == "MOD" and tipos != {"int"}):
                return self.erro(no, "Tipos incompatíveis na operação aritmética")
            opcode = ARITMETICA[no.operador]
            tipo = TIPO_FLOAT if "float" in tipos else TIPO_INT
        elif no.operador in COMPARACOES:
            igualdadeBooleana = tipos == {"bool"} and no.operador in {"EQUALS", "DIFF"}
            if not numericos and not igualdadeBooleana:
                return self.erro(no, "Tipos incompatíveis na comparação")
            opcode, tipo = COMPARACOES[no.operador], TIPO_BOOL
        else:
            return self.erro(no, "Operador binário desconhecido")
        destino = self.temporario()
        self.instrucao(no, opcode, destino, a, b)
        return ResultadoExpressao(tipo, destino)

    def visitarLogica(
        self, no: OpBinaria, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        esquerdo = self.visitarExpressao(no.esquerda, escopo, contexto)
        valido = esquerdo.tipo == TIPO_BOOL
        destino, fim = self.temporario(), self.rotulo()
        if valido:
            ehOu = no.operador == "OR"
            self.instrucao(no, "move", destino, OperandoTAC("constante", ehOu))
            salto = "if_true" if ehOu else "if_false"
            self.instrucao(no, salto, self.valorEscalar(no.esquerda, esquerdo), fim)
        elif not esquerdo.tipo.ehErro():
            self.erro(no.esquerda, "Operador lógico exige operandos bool")
        direito = self.visitarExpressao(no.direita, escopo, contexto)
        if direito.tipo != TIPO_BOOL:
            valido = False
            if not direito.tipo.ehErro():
                self.erro(no.direita, "Operador lógico exige operandos bool")
        if valido:
            self.instrucao(no, "move", destino, self.valorEscalar(no.direita, direito))
        self.instrucao(no, "label", fim)
        return ResultadoExpressao(TIPO_BOOL, destino) if valido else ResultadoExpressao(TIPO_ERRO)

    def visitarUnaria(
        self, no: OpUnaria, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        resultado = self.visitarExpressao(no.operando, escopo, contexto)
        if resultado.tipo.ehErro():
            return resultado
        destino = self.temporario()
        if no.operador == "NEG":
            if resultado.tipo != TIPO_BOOL:
                return self.erro(no, "O operador ! exige um operando bool")
            self.instrucao(no, "not", destino, self.valorEscalar(no, resultado))
        elif no.operador in {"INCREMENT", "DECREMENT"}:
            if not resultado.atribuivel or resultado.tipo not in (TIPO_INT, TIPO_FLOAT):
                mensagem = "Incremento e decremento exigem um destino numérico atribuível"
                return self.erro(no, mensagem)
            opcode = "add" if no.operador == "INCREMENT" else "sub"
            valor = self.valorEscalar(no, resultado)
            self.instrucao(no, opcode, destino, valor, OperandoTAC("constante", 1))
            self.gravar(no, resultado, destino)
        else:
            return self.erro(no, "Operador unário desconhecido")
        return ResultadoExpressao(resultado.tipo, destino)

    def visitarChamada(
        self, no: Chamada, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        simbolo = escopo.buscar(no.nome)
        ehFuncao = simbolo is not None and simbolo.categoria == CATEGORIA_FUNCAO
        esperados = simbolo.parametros if ehFuncao else []
        valido = ehFuncao and len(esperados) == len(no.argumentos)
        if not ehFuncao:
            self.erro(no, f"'{no.nome}' não designa uma função visível")
        elif not valido:
            self.erro(
                no, f"'{no.nome}' espera {len(esperados)} argumento(s), recebeu {len(no.argumentos)}"
            )

        parametros: list[OperandoTAC] = []
        for posicao, argumento in enumerate(no.argumentos):
            resultado = self.visitarExpressao(argumento, escopo, contexto)
            if posicao >= len(esperados) or resultado.tipo.ehErro() or esperados[posicao].ehErro():
                valido = False
                continue
            esperado = esperados[posicao]
            if esperado != resultado.tipo:
                self.erro(
                    argumento,
                    f"Argumento {posicao + 1} de '{no.nome}': esperado {esperado.nome}, "
                    f"recebido {resultado.tipo.nome}",
                )
                valido = False
            elif esperado.ehAgregado():
                if contexto is None:
                    return self.erro(no, "Chamada com agregado fora de um quadro de função")
                copia = self.reservarLocal(contexto, esperado.tamanhoBytes)
                self.copiar(argumento, copia, resultado.operando, esperado)
                parametros.append(self.endereco(argumento, copia))
            else:
                valor = self.valorEscalar(argumento, resultado)
                parametros.append(self.fixarValor(argumento, valor))

        if not valido or simbolo.tipo.ehErro():
            return ResultadoExpressao(TIPO_ERRO)
        if simbolo.tipo.ehAgregado():
            if contexto is None:
                return self.erro(no, "Retorno agregado exige um quadro de função")
            resultado = self.reservarLocal(contexto, simbolo.tipo.tamanhoBytes)
            parametros.insert(0, self.endereco(no, resultado))
            destino = None
        else:
            resultado = destino = self.temporario()
        # O simulador espera um lote contíguo de param, inclusive em chamadas aninhadas.
        for valor in parametros:
            self.instrucao(no, "param", valor)
        funcao = OperandoTAC("funcao", no.nome)
        self.instrucao(no, "call", destino, funcao, OperandoTAC("constante", len(parametros)))
        return ResultadoExpressao(simbolo.tipo, resultado)

    def erro(self, no: NoAST | None, mensagem: str) -> ResultadoExpressao:
        self.gerenciadorErros.registrar(no, mensagem)
        return ResultadoExpressao(TIPO_ERRO)

    def instrucao(self, no: NoAST, opcode: str, *operandos: OperandoTAC | None) -> None:
        self.emitir(InstrucaoTAC(opcode, operandos, no.linha, no.coluna))

    def temporario(self) -> OperandoTAC:
        nome = f"t{self.proximoTemporario}"
        self.proximoTemporario += 1
        return OperandoTAC("temporario", nome)

    def rotulo(self) -> OperandoTAC:
        # O ponto separa os rótulos internos dos identificadores da linguagem.
        nome = f".L{self.proximoRotulo}"
        self.proximoRotulo += 1
        return OperandoTAC("rotulo", nome)

    def valorEscalar(self, no: NoAST, resultado: ResultadoExpressao) -> OperandoTAC | None:
        if resultado.tipo.ehErro():
            return None
        if resultado.tipo.ehAgregado():
            self.erro(no, f"Esperado valor escalar, recebido {resultado.tipo.nome}")
            return None
        if resultado.indireto:
            valor = self.temporario()
            self.instrucao(no, "load", valor, resultado.operando)
            return valor
        return resultado.operando

    def fixarValor(self, no: NoAST, valor: OperandoTAC | None) -> OperandoTAC | None:
        if valor is None or valor.categoria not in {REGIAO_LOCAL, REGIAO_GLOBAL}:
            return valor
        copia = self.temporario()
        self.instrucao(no, "move", copia, valor)
        return copia

    def gravar(self, no: NoAST, destino: ResultadoExpressao, valor: OperandoTAC) -> None:
        opcode = "store" if destino.indireto else "move"
        self.instrucao(no, opcode, destino.operando, valor)

    def endereco(
        self, no: NoAST, base: OperandoTAC, deslocamento: OperandoTAC | None = None
    ) -> OperandoTAC:
        destino = self.temporario()
        if deslocamento is None:
            deslocamento = OperandoTAC("constante", 0)
        self.instrucao(no, "addr", destino, base, deslocamento)
        return destino

    def copiar(self, no: NoAST, destino: OperandoTAC, origem: OperandoTAC, tipo: TipoSemantico) -> None:
        self.instrucao(no, "copy", destino, origem, OperandoTAC("constante", tipo.tamanhoBytes))

    @staticmethod
    def reservarLocal(contexto: ContextoFuncao, tamanho: int) -> OperandoTAC:
        endereco = OperandoTAC(REGIAO_LOCAL, contexto.proximoDeslocamento)
        contexto.proximoDeslocamento += tamanho
        return endereco

    def emitir(self, instrucao: InstrucaoTAC) -> None:
        self.programaTAC.instrucoes.append(instrucao)

    def cadastrarLocal(
        self,
        escopo: Escopo,
        contexto: ContextoFuncao,
        no: DeclVariavel | Parametro,
        tipo: TipoSemantico,
        categoria: str,
    ) -> int | None:
        deslocamento = contexto.proximoDeslocamento
        simbolo = SimboloSemantico(
            nome=no.nome,
            categoria=categoria,
            tipo=tipo,
            endereco=OperandoTAC(REGIAO_LOCAL, deslocamento),
            linha=no.linha,
            coluna=no.coluna,
        )

        if not self.inserir(escopo, simbolo, no):
            return None

        contexto.proximoDeslocamento += tipo.tamanhoBytes
        return deslocamento

    def inserir(self, escopo: Escopo, simbolo: SimboloSemantico, no: NoAST) -> bool:
        if escopo.inserir(simbolo):
            return True

        anterior = escopo.simbolos[simbolo.nome]
        self.gerenciadorErros.registrar(
            no,
            f"'{simbolo.nome}' já foi declarado neste escopo "
            f"(linha {anterior.linha}, coluna {anterior.coluna})",
        )
        return False

    def resolverTipo(
        self, nomeTipo: str, tamanho: int | None, no: NoAST
    ) -> TipoSemantico:
        if nomeTipo in TIPOS_PRIMITIVOS:
            tipo = TIPOS_PRIMITIVOS[nomeTipo]
        elif nomeTipo in self.tiposDeclarados:
            tipo = self.tiposDeclarados[nomeTipo]
        else:
            self.gerenciadorErros.registrar(no, f"Tipo '{nomeTipo}' não declarado")
            return TIPO_ERRO

        if tamanho is None:
            return tipo

        if tamanho <= 0:
            self.gerenciadorErros.registrar(
                no, f"O tamanho do vetor '{getattr(no, 'nome', '')}' deve ser maior que zero"
            )
            return TIPO_ERRO

        return tipoVetor(tipo, tamanho)

    @staticmethod
    def categoriaVariavel(tipo: TipoSemantico) -> str:
        return CATEGORIA_VETOR if tipo.ehVetor() else CATEGORIA_VARIAVEL
