from __future__ import annotations

import ast
from dataclasses import dataclass, field

from src.parser.ast.Nos import (
    Atribuicao, Bloco, Break, Chamada, Comando, ComandoExpr,
    DeclFuncao, DeclStruct, DeclVariavel, Expr, Id, If, Indexacao, Literal, NoAST,
    OpBinaria, OpUnaria, Parametro, Print, Programa, Readln, Return, While,
)
from src.semantico.Escopo import Escopo
from src.semantico.GerenciadorErrosSemanticos import GerenciadorErrosSemanticos
from src.semantico.models.ResultadoExpressao import ResultadoExpressao
from src.semantico.models.SimboloSemantico import (
    CATEGORIA_FUNCAO, CATEGORIA_PARAMETRO, CATEGORIA_VARIAVEL,
    CATEGORIA_VETOR, SimboloSemantico,
)
from src.semantico.models.TipoSemantico import (
    TIPO_BOOL, TIPO_CHAR, TIPO_ERRO, TIPO_FLOAT, TIPO_INT,
    TIPOS_PRIMITIVOS, TipoSemantico, tipoVetor,
)
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


REGIAO_GLOBAL = "global"
REGIAO_LOCAL = "local"
TIPO_TEXTO = TipoSemantico("string", 0)

OPERADORES_TAC = {
    "PLUS": "add",
    "MINUS": "sub",
    "MULT": "mul",
    "DIV": "div",
    "MOD": "mod",
    "EQUALS": "eq",
    "DIFF": "ne",
    "LESS_THAN": "lt",
    "LESS_THAN_EQUAL": "le",
    "GREATER_THAN": "gt",
    "GREATER_THAN_EQUAL": "ge",
}


@dataclass
class ContextoFuncao:
    simbolo: SimboloSemantico
    proximoDeslocamento: int = 0
    alvosBreak: list[str] = field(default_factory=list)


class MotorSemantico:
    """Verifica a AST e emite TAC diretamente executável pelo simulador.

    Cada primitivo ocupa uma posição. Vetores e structs ocupam sequências
    contíguas dessas posições; offsets nunca são convertidos para bytes ou
    registradores físicos.
    """

    def __init__(self, gerenciadorErros: GerenciadorErrosSemanticos) -> None:
        self.gerenciadorErros = gerenciadorErros
        self.escopoGlobal = Escopo()
        self.programaTAC = ProgramaTAC()
        self.tiposDeclarados: dict[str, TipoSemantico] = {}
        self.structs: list[TipoSemantico] = []
        self.escoposFuncoes: dict[str, Escopo] = {}
        self.assinaturas: dict[int, SimboloSemantico] = {}
        self._proximoTemporario = 0
        self._proximoRotulo = 0

    # Primeiro cadastra nomes e tipos; depois visita os corpos das funções.
    def executar(self, programa: Programa) -> ProgramaTAC:
        self.cadastrarGlobais(programa)
        self._validarEntrada(programa)

        for declaracao in programa.declaracoes:
            if isinstance(declaracao, DeclFuncao):
                self.visitarFuncao(declaracao)

        if not self.gerenciadorErros.obterErros():
            for erro in self.programaTAC.validar():
                self.gerenciadorErros.registrar(programa, f"TAC gerado inválido: {erro}")
        return self.programaTAC

    # Símbolos, tipos struct e assinaturas precisam existir antes de gerar TAC.
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
            self.programaTAC.tamanhoDados += max(tipo.tamanhoPosicoes, 1)

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
                    campo, f"Campo '{campo.nome}' declarado mais de uma vez no struct"
                )
                continue
            if (self._ehAgregado(tipoCampo)
                    and not self._ehVetorDeStruct(tipoCampo)):
                self.gerenciadorErros.registrar(
                    campo,
                    "Os campos de struct devem ser tipos primitivos escalares",
                )
            tipoStruct.campos[campo.nome] = (tipoCampo, tipoStruct.tamanhoPosicoes)
            tipoStruct.tamanhoBytes += max(tipoCampo.tamanhoPosicoes, 1)

        self.structs.append(tipoStruct)
        if nomeStruct:
            if nomeStruct in self.tiposDeclarados or nomeStruct in TIPOS_PRIMITIVOS:
                self.gerenciadorErros.registrar(no, f"Tipo '{nomeStruct}' declarado mais de uma vez")
            else:
                self.tiposDeclarados[nomeStruct] = tipoStruct
        return tipoStruct

    # Cada função recebe um quadro e um escopo próprios.
    def visitarFuncao(self, no: DeclFuncao) -> None:
        simboloFuncao = self.assinaturas[id(no)]
        if self.escopoGlobal.simbolos.get(no.nome) is not simboloFuncao:
            return

        if self._ehAgregado(simboloFuncao.tipo):
            self.gerenciadorErros.registrar(
                no, "Funções não podem retornar vetores ou structs nesta arquitetura"
            )

        escopo = Escopo(self.escopoGlobal)
        contexto = ContextoFuncao(simboloFuncao)
        deslocamentosParametros: list[int] = []

        for parametro, tipo in zip(no.parametros, simboloFuncao.parametros):
            deslocamento = self.cadastrarLocal(
                escopo, contexto, parametro, tipo, CATEGORIA_PARAMETRO
            )
            if deslocamento is not None:
                deslocamentosParametros.append(deslocamento)

        self._emitir("label", (self._op("rotulo", no.nome),), no)
        if no.nome == self.programaTAC.entrada:
            self._inicializarGlobais(no)

        self.visitarBloco(no.corpo, escopo, contexto, novoEscopo=False)
        if not self._retornaEmTodosOsCaminhos(no.corpo):
            if no.nome == self.programaTAC.entrada:
                # Como em C, main que chega ao fim retorna 0 implicitamente.
                self._emitir("return", (self._op("constante", 0),), no)
            else:
                self.gerenciadorErros.registrar(
                    no, f"A função '{no.nome}' pode terminar sem retornar um valor"
                )
                # Mantém o TAC parcial estruturalmente seguro; com erro
                # semântico ele não será entregue para execução.
                self._emitir("return", (), no)

        self.escoposFuncoes[no.nome] = escopo
        self.programaTAC.quadros[no.nome] = (
            contexto.proximoDeslocamento,
            deslocamentosParametros,
        )

    # Comandos geram fluxo de controle e delegam expressões ao visitante abaixo.
    def visitarBloco(
        self,
        no: Bloco,
        escopo: Escopo,
        contexto: ContextoFuncao,
        novoEscopo: bool = True,
    ) -> None:
        escopoBloco = Escopo(escopo) if novoEscopo else escopo
        for declaracao in no.declaracoes:
            tipo = self.resolverTipo(declaracao.tipo, declaracao.tamanho, declaracao)
            self.cadastrarLocal(
                escopoBloco, contexto, declaracao, tipo, self.categoriaVariavel(tipo)
            )
        for comando in no.comandos:
            self.visitarComando(comando, escopoBloco, contexto)

    def visitarComando(
        self, no: Comando | None, escopo: Escopo, contexto: ContextoFuncao
    ) -> None:
        if no is None:
            return
        if isinstance(no, Bloco):
            self.visitarBloco(no, escopo, contexto)
        elif isinstance(no, ComandoExpr):
            self.visitarExpressao(no.expr, escopo, contexto)
        elif isinstance(no, Print):
            valores: list[OperandoTAC] = []
            for argumento in no.argumentos:
                resultado = self.visitarExpressao(argumento, escopo, contexto)
                if self._ehAgregado(resultado.tipo):
                    self.gerenciadorErros.registrar(no, "print aceita apenas valores escalares")
                    continue
                valor = self._comoValor(resultado, argumento)
                snapshot = self._novoTemporario()
                self._emitir("move", (snapshot, valor), argumento)
                valores.append(snapshot)
            for valor in valores:
                self._emitir("print", (valor,), no)
        elif isinstance(no, Readln):
            alvo = self.visitarExpressao(no.alvo, escopo, contexto)
            if not self._validarAlvo(alvo, no, permitirStruct=False):
                return
            if self._ehAgregado(alvo.tipo) or alvo.tipo.nome == TIPO_TEXTO.nome:
                self.gerenciadorErros.registrar(no, "readln exige uma variável escalar")
                return
            endereco = alvo.deslocamento
            tipoLeitura = self._op("constante", alvo.tipo.nome)
            if endereco is not None and endereco.categoria in {REGIAO_GLOBAL, REGIAO_LOCAL} and not alvo.indireto:
                self._emitir("read", (endereco, tipoLeitura), no)
            else:
                temporario = self._novoTemporario()
                self._emitir("read", (temporario, tipoLeitura), no)
                if endereco is not None:
                    self._emitir("store", (endereco, temporario), no)
        elif isinstance(no, Return):
            if self._ehAgregado(contexto.simbolo.tipo):
                self.gerenciadorErros.registrar(no, "return de vetor ou struct não é suportado")
                return
            resultado = self.visitarExpressao(no.valor, escopo, contexto)
            if self._ehAgregado(resultado.tipo):
                self.gerenciadorErros.registrar(no, "return de vetor ou struct não é suportado")
                return
            if not self._tiposAtribuiveis(contexto.simbolo.tipo, resultado.tipo):
                self._erroTipo(
                    no,
                    f"return de '{resultado.tipo.paraString()}' incompatível com "
                    f"'{contexto.simbolo.tipo.paraString()}'",
                )
            valor = self._converter(
                self._comoValor(resultado, no.valor), resultado.tipo,
                contexto.simbolo.tipo, no,
            )
            self._emitir("return", (valor,), no)
        elif isinstance(no, If):
            condicao = self.visitarExpressao(no.condicao, escopo, contexto)
            self._exigirBool(condicao, no.condicao or no)
            valor = self._comoValor(condicao, no.condicao)
            rotuloSenao = self._novoRotulo()
            rotuloFim = self._novoRotulo()
            self._emitir("if_false", (valor, self._op("rotulo", rotuloSenao)), no)
            self.visitarComando(no.entao, escopo, contexto)
            self._emitir("goto", (self._op("rotulo", rotuloFim),), no)
            self._emitir("label", (self._op("rotulo", rotuloSenao),), no)
            self.visitarComando(no.senao, escopo, contexto)
            self._emitir("label", (self._op("rotulo", rotuloFim),), no)
        elif isinstance(no, While):
            rotuloInicio = self._novoRotulo()
            rotuloFim = self._novoRotulo()
            self._emitir("label", (self._op("rotulo", rotuloInicio),), no)
            condicao = self.visitarExpressao(no.condicao, escopo, contexto)
            self._exigirBool(condicao, no.condicao or no)
            self._emitir(
                "if_false",
                (self._comoValor(condicao, no.condicao), self._op("rotulo", rotuloFim)),
                no,
            )
            contexto.alvosBreak.append(rotuloFim)
            self.visitarComando(no.corpo, escopo, contexto)
            contexto.alvosBreak.pop()
            self._emitir("goto", (self._op("rotulo", rotuloInicio),), no)
            self._emitir("label", (self._op("rotulo", rotuloFim),), no)
        elif isinstance(no, Break):
            if not contexto.alvosBreak:
                self.gerenciadorErros.registrar(no, "break só pode ser usado dentro de while")
            else:
                self._emitir("goto", (self._op("rotulo", contexto.alvosBreak[-1]),), no)
        else:
            self.gerenciadorErros.registrar(no, f"Comando não suportado: {type(no).__name__}")

    # Expressões devolvem tipo, valor TAC e, quando aplicável, endereço gravável.
    def visitarExpressao(
        self,
        no: Expr | None,
        escopo: Escopo,
        contexto: ContextoFuncao | None = None,
    ) -> ResultadoExpressao:
        if no is None:
            return self._erroExpressao(None, "Expressão ausente")
        if isinstance(no, Literal):
            return self._visitarLiteral(no)
        if isinstance(no, Id):
            return self._visitarId(no, escopo)
        if isinstance(no, Indexacao):
            return self._visitarIndexacao(no, escopo, contexto)
        if isinstance(no, Atribuicao):
            return self._visitarAtribuicao(no, escopo, contexto)
        if isinstance(no, OpBinaria):
            return self._visitarOpBinaria(no, escopo, contexto)
        if isinstance(no, OpUnaria):
            return self._visitarOpUnaria(no, escopo, contexto)
        if isinstance(no, Chamada):
            return self._visitarChamada(no, escopo, contexto)
        return self._erroExpressao(no, f"Expressão não suportada: {type(no).__name__}")

    def _visitarLiteral(self, no: Literal) -> ResultadoExpressao:
        try:
            if no.tipo == "NUM_INT":
                tipo, valor = TIPO_INT, int(no.valor or "")
            elif no.tipo == "NUM_FLOAT":
                tipo, valor = TIPO_FLOAT, float(no.valor or "")
            elif no.tipo == "ASCII":
                valor = ast.literal_eval(no.valor or "")
                if type(valor) is not str or len(valor) != 1:
                    raise ValueError("Literal char deve conter um caractere")
                tipo = TIPO_CHAR
            elif no.tipo == "LITERAL":
                valor = ast.literal_eval(no.valor or "")
                if type(valor) is not str:
                    raise ValueError("Literal de texto inválido")
                tipo = TIPO_TEXTO
            elif no.tipo in {"TRUE", "FALSE"}:
                tipo, valor = TIPO_BOOL, no.tipo == "TRUE"
            else:
                return self._erroExpressao(no, f"Literal não reconhecido: {no.tipo}")
        except (SyntaxError, ValueError, TypeError, OverflowError) as erro:
            return self._erroExpressao(no, f"Literal inválido: {erro}")
        operando = self._op("constante", valor)
        return ResultadoExpressao(tipo, operando)

    def _visitarId(self, no: Id, escopo: Escopo) -> ResultadoExpressao:
        simbolo = escopo.buscar(no.nome)
        if simbolo is None:
            return self._erroExpressao(no, f"Identificador '{no.nome}' não declarado")
        if simbolo.categoria == CATEGORIA_FUNCAO:
            return self._erroExpressao(no, f"'{no.nome}' é função; use uma chamada")
        if simbolo.endereco is None:
            return self._erroExpressao(no, f"Identificador '{no.nome}' não possui endereço")
        agregado = self._ehAgregado(simbolo.tipo)
        indireto = agregado and simbolo.categoria == CATEGORIA_PARAMETRO
        return ResultadoExpressao(
            tipo=simbolo.tipo,
            operando=None if agregado else simbolo.endereco,
            deslocamento=simbolo.endereco,
            atribuivel=True,
            indireto=indireto,
        )

    def _visitarIndexacao(
        self, no: Indexacao, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        vetor = self.visitarExpressao(no.vetor, escopo, contexto)
        indice = self.visitarExpressao(no.indice, escopo, contexto)
        if vetor.tipo.ehErro():
            return self._resultadoErro()
        if vetor.tipo.ehStruct():
            return self._visitarCampoIndexado(vetor, indice, no)
        if not vetor.tipo.ehVetor():
            return self._erroExpressao(no, "Indexação exige um vetor")
        if indice.tipo.nome != TIPO_INT.nome and not indice.tipo.ehErro():
            self.gerenciadorErros.registrar(no.indice or no, "Índice de vetor deve ser int")
        tipoElemento = vetor.tipo.elemento or TIPO_ERRO
        tamanhoElemento = max(tipoElemento.tamanhoPosicoes, 1)
        valorIndice = self._constanteInteira(no.indice)
        if valorIndice is not None and vetor.tipo.comprimento is not None:
            if valorIndice < 0 or valorIndice >= vetor.tipo.comprimento:
                self.gerenciadorErros.registrar(
                    no, f"Índice {valorIndice} fora dos limites do vetor "
                    f"(tamanho {vetor.tipo.comprimento})",
                )

        base = self._obterBase(vetor, no)
        if (valorIndice is not None and not vetor.indireto
                and base.categoria in {REGIAO_GLOBAL, REGIAO_LOCAL}):
            endereco = self._op(base.categoria, base.valor + valorIndice * tamanhoElemento)
        else:
            indiceOperando = self._comoValor(indice, no.indice)
            if tamanhoElemento == 1:
                deslocamento = indiceOperando
            else:
                deslocamento = self._novoTemporario()
                self._emitir(
                    "mul",
                    (deslocamento, indiceOperando, self._op("constante", tamanhoElemento)),
                    no,
                )
            endereco = self._novoTemporario()
            self._emitir("addr", (endereco, base, deslocamento), no)

        return ResultadoExpressao(
            tipo=tipoElemento,
            operando=None,
            deslocamento=endereco,
            atribuivel=True,
        )

    def _visitarCampoIndexado(
        self,
        struct: ResultadoExpressao,
        indice: ResultadoExpressao,
        no: Indexacao,
    ) -> ResultadoExpressao:
        """Interpreta p[n] como o n-ésimo campo de uma struct escalar."""
        if indice.tipo.ehErro():
            return self._resultadoErro()
        if indice.tipo.nome != TIPO_INT.nome:
            return self._erroExpressao(
                no.indice or no, "Índice de campo de struct deve ser int"
            )

        numeroCampo = self._constanteInteira(no.indice)
        if numeroCampo is None:
            return self._erroExpressao(
                no.indice or no,
                "O índice de campo de struct deve ser um literal inteiro constante",
            )

        campos = list(struct.tipo.campos.values())
        if numeroCampo < 0 or numeroCampo >= len(campos):
            return self._erroExpressao(
                no,
                f"Índice de campo {numeroCampo} fora dos limites da struct "
                f"'{struct.tipo.nome}' ({len(campos)} campo(s))",
            )

        # dict preserva a ordem da declaração; cada campo guarda tipo e offset.
        tipoCampo, deslocamentoCampo = campos[numeroCampo]
        base = self._obterBase(struct, no)
        if (not struct.indireto
                and base.categoria in {REGIAO_GLOBAL, REGIAO_LOCAL}):
            endereco = self._op(
                base.categoria, base.valor + deslocamentoCampo
            )
        else:
            endereco = self._enderecoComOffset(base, deslocamentoCampo, no)

        return ResultadoExpressao(
            tipo=tipoCampo,
            deslocamento=endereco,
            atribuivel=True,
        )

    def _visitarAtribuicao(
        self, no: Atribuicao, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        alvo = self.visitarExpressao(no.alvo, escopo, contexto)
        valor = self.visitarExpressao(no.valor, escopo, contexto)
        if not self._validarAlvo(alvo, no.alvo or no):
            return self._resultadoErro()
        resultado = self._armazenar(alvo, valor, no)
        if resultado is None:
            return self._resultadoErro()
        return ResultadoExpressao(alvo.tipo, resultado)

    def _visitarOpBinaria(
        self, no: OpBinaria, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        if no.operador in {"AND", "OR"}:
            return self._visitarLogica(no, escopo, contexto)

        esquerda = self.visitarExpressao(no.esquerda, escopo, contexto)
        direita = self.visitarExpressao(no.direita, escopo, contexto)
        opcode = OPERADORES_TAC.get(no.operador)
        if opcode is None:
            return self._erroExpressao(no, f"Operador não reconhecido: {no.operador}")
        tipo = self._tipoOperacao(no, esquerda.tipo, direita.tipo)
        valorEsquerda = self._comoValor(esquerda, no.esquerda)
        valorDireita = self._comoValor(direita, no.direita)
        if tipo.ehErro():
            return self._resultadoErro()
        temporario = self._novoTemporario()
        self._emitir(
            opcode, (temporario, valorEsquerda, valorDireita), no
        )
        return ResultadoExpressao(tipo, temporario)

    def _visitarLogica(
        self, no: OpBinaria, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        esquerda = self.visitarExpressao(no.esquerda, escopo, contexto)
        self._exigirBool(esquerda, no.esquerda or no)
        valorEsquerda = self._comoValor(esquerda, no.esquerda)
        resultado = self._novoTemporario()
        rotuloAtalho = self._novoRotulo()
        rotuloFim = self._novoRotulo()

        if no.operador == "AND":
            self._emitir(
                "if_false", (valorEsquerda, self._op("rotulo", rotuloAtalho)), no
            )
            direita = self.visitarExpressao(no.direita, escopo, contexto)
            self._exigirBool(direita, no.direita or no)
            self._emitir("move", (resultado, self._comoValor(direita, no.direita)), no)
            self._emitir("goto", (self._op("rotulo", rotuloFim),), no)
            self._emitir("label", (self._op("rotulo", rotuloAtalho),), no)
            self._emitir("move", (resultado, self._op("constante", False)), no)
        else:
            self._emitir(
                "if_true", (valorEsquerda, self._op("rotulo", rotuloAtalho)), no
            )
            direita = self.visitarExpressao(no.direita, escopo, contexto)
            self._exigirBool(direita, no.direita or no)
            self._emitir("move", (resultado, self._comoValor(direita, no.direita)), no)
            self._emitir("goto", (self._op("rotulo", rotuloFim),), no)
            self._emitir("label", (self._op("rotulo", rotuloAtalho),), no)
            self._emitir("move", (resultado, self._op("constante", True)), no)

        self._emitir("label", (self._op("rotulo", rotuloFim),), no)
        tipo = TIPO_BOOL if esquerda.tipo.nome == TIPO_BOOL.nome else TIPO_ERRO
        if direita.tipo.nome != TIPO_BOOL.nome and not direita.tipo.ehErro():
            tipo = TIPO_ERRO
        return ResultadoExpressao(tipo, resultado)

    def _tipoOperacao(
        self, no: OpBinaria, esquerda: TipoSemantico, direita: TipoSemantico
    ) -> TipoSemantico:
        if esquerda.ehErro() or direita.ehErro():
            return TIPO_ERRO
        op = no.operador
        if op in {"PLUS", "MINUS", "MULT", "DIV"}:
            if self._ehNumerico(esquerda) and self._ehNumerico(direita):
                return TIPO_FLOAT if "float" in {esquerda.nome, direita.nome} else TIPO_INT
            self.gerenciadorErros.registrar(no, f"Operador {op} exige operandos numéricos")
            return TIPO_ERRO
        if op == "MOD":
            if esquerda.nome == TIPO_INT.nome and direita.nome == TIPO_INT.nome:
                return TIPO_INT
            self.gerenciadorErros.registrar(no, "O operador % exige operandos int")
            return TIPO_ERRO
        if op in {"EQUALS", "DIFF"}:
            if (self._ehNumerico(esquerda) and self._ehNumerico(direita)) or self._mesmoTipo(esquerda, direita):
                if self._ehAgregado(esquerda) or esquerda.nome == TIPO_TEXTO.nome:
                    self.gerenciadorErros.registrar(no, "Comparação de agregado/texto não suportada")
                    return TIPO_ERRO
                return TIPO_BOOL
            self.gerenciadorErros.registrar(no, "Operandos de igualdade devem ter tipos compatíveis")
            return TIPO_ERRO
        if op in {"LESS_THAN", "LESS_THAN_EQUAL", "GREATER_THAN", "GREATER_THAN_EQUAL"}:
            if self._ehNumerico(esquerda) and self._ehNumerico(direita):
                return TIPO_BOOL
            self.gerenciadorErros.registrar(no, f"Operador relacional {op} exige operandos numéricos")
            return TIPO_ERRO
        return self._erroTipo(no, f"Operador binário não suportado: {op}")

    def _visitarOpUnaria(
        self, no: OpUnaria, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        valor = self.visitarExpressao(no.operando, escopo, contexto)
        if no.operador == "NEG":
            if valor.tipo.nome != TIPO_BOOL.nome and not valor.tipo.ehErro():
                self.gerenciadorErros.registrar(no, "O operador ! exige um operando bool")
                return self._resultadoErro()
            temporario = self._novoTemporario()
            self._emitir("not", (temporario, self._comoValor(valor, no.operando)), no)
            return ResultadoExpressao(TIPO_BOOL, temporario)

        if no.operador in {"INCREMENT", "DECREMENT"}:
            if not self._validarAlvo(valor, no.operando or no, permitirStruct=False):
                return self._resultadoErro()
            if not self._ehNumerico(valor.tipo):
                self.gerenciadorErros.registrar(no, "++ e -- exigem um lvalue numérico")
                return self._resultadoErro()
            atual = self._comoValor(valor, no.operando)
            temporario = self._novoTemporario()
            opcode = "add" if no.operador == "INCREMENT" else "sub"
            self._emitir(
                opcode, (temporario, atual, self._op("constante", 1)), no
            )
            self._armazenarOperando(valor, temporario, no)
            return ResultadoExpressao(valor.tipo, temporario)

        return self._erroExpressao(no, f"Operador unário não suportado: {no.operador}")

    def _visitarChamada(
        self, no: Chamada, escopo: Escopo, contexto: ContextoFuncao | None
    ) -> ResultadoExpressao:
        # Respeita sombreamento local: um identificador local não pode ser
        # ignorado para chamar uma função global de mesmo nome.
        simbolo = escopo.buscar(no.nome)
        resultados = [self.visitarExpressao(arg, escopo, contexto) for arg in no.argumentos]
        if simbolo is None:
            return self._erroExpressao(no, f"Função '{no.nome}' não declarada")
        if simbolo.categoria != CATEGORIA_FUNCAO:
            return self._erroExpressao(no, f"'{no.nome}' não é uma função")
        if len(resultados) != len(simbolo.parametros):
            self.gerenciadorErros.registrar(
                no, f"Função '{no.nome}' espera {len(simbolo.parametros)} argumento(s), "
                f"mas recebeu {len(resultados)}",
            )

        valores: list[OperandoTAC] = []
        for indice, resultado in enumerate(resultados):
            if indice < len(simbolo.parametros):
                esperado = simbolo.parametros[indice]
                if not self._tipoParametroCompativel(esperado, resultado.tipo):
                    self.gerenciadorErros.registrar(
                        no.argumentos[indice],
                        f"Argumento {indice + 1} de '{no.nome}' tem tipo "
                        f"'{resultado.tipo.paraString()}'; esperado '{esperado.paraString()}'",
                    )
                if self._ehAgregado(esperado) and self._ehAgregado(resultado.tipo):
                    valor = self._ponteiro(resultado, no.argumentos[indice])
                else:
                    valor = self._converter(
                        self._comoValor(resultado, no.argumentos[indice]),
                        resultado.tipo, esperado, no.argumentos[indice],
                    )
            else:
                valor = self._comoValor(resultado, no.argumentos[indice])
            snapshot = self._novoTemporario()
            self._emitir("move", (snapshot, valor), no.argumentos[indice])
            valores.append(snapshot)

        # O simulador exige que todos os param sejam consecutivos e seguidos
        # imediatamente pelo call; por isso os argumentos são avaliados antes.
        for valor in valores:
            self._emitir("param", (valor,), no)
        destino = self._novoTemporario()
        self._emitir(
            "call",
            (destino, self._op("funcao", no.nome), self._op("constante", len(valores))),
            no,
        )
        if self._ehAgregado(simbolo.tipo):
            self.gerenciadorErros.registrar(no, "Função não pode retornar vetor ou struct")
            return self._resultadoErro()
        return ResultadoExpressao(simbolo.tipo, destino)

    # Leitura e escrita de posições, inclusive endereços calculados por índice.
    def _armazenar(
        self, alvo: ResultadoExpressao, valor: ResultadoExpressao, no: NoAST
    ) -> OperandoTAC | None:
        if self._ehErro(alvo.tipo) or self._ehErro(valor.tipo):
            return None
        if alvo.tipo.ehVetor():
            self.gerenciadorErros.registrar(no, "Atribuição de vetor inteiro não é suportada")
            return None
        if alvo.tipo.ehStruct():
            if not self._mesmoTipo(alvo.tipo, valor.tipo):
                self.gerenciadorErros.registrar(no, "Atribuição entre structs de tipos diferentes")
                return None
            self._copiarStruct(alvo, valor, no)
            return self._ponteiro(alvo, no)
        if self._ehAgregado(valor.tipo) or not self._tiposAtribuiveis(alvo.tipo, valor.tipo):
            self.gerenciadorErros.registrar(
                no, f"Não é possível atribuir '{valor.tipo.paraString()}' a "
                f"'{alvo.tipo.paraString()}'",
            )
            return None
        operando = self._converter(self._comoValor(valor, no), valor.tipo, alvo.tipo, no)
        self._armazenarOperando(alvo, operando, no)
        return operando

    def _armazenarOperando(
        self, alvo: ResultadoExpressao, valor: OperandoTAC, no: NoAST
    ) -> None:
        endereco = alvo.deslocamento
        if endereco is None:
            self.gerenciadorErros.registrar(no, "Destino sem endereço gravável")
        elif endereco.categoria in {REGIAO_GLOBAL, REGIAO_LOCAL} and not alvo.indireto:
            self._emitir("move", (endereco, valor), no)
        else:
            self._emitir("store", (endereco, valor), no)

    def _copiarStruct(
        self, destino: ResultadoExpressao, origem: ResultadoExpressao, no: NoAST
    ) -> None:
        ponteiroDestino = self._ponteiro(destino, no)
        ponteiroOrigem = self._ponteiro(origem, no)
        for indice in range(max(destino.tipo.tamanhoPosicoes, 1)):
            enderecoOrigem = self._enderecoComOffset(ponteiroOrigem, indice, no)
            valor = self._novoTemporario()
            self._emitir("load", (valor, enderecoOrigem), no)
            enderecoDestino = self._enderecoComOffset(ponteiroDestino, indice, no)
            self._emitir("store", (enderecoDestino, valor), no)

    def _validarAlvo(
        self,
        resultado: ResultadoExpressao,
        no: NoAST,
        *,
        permitirStruct: bool = True,
    ) -> bool:
        if not resultado.atribuivel or resultado.deslocamento is None:
            if not resultado.tipo.ehErro():
                self.gerenciadorErros.registrar(no, "A expressão precisa ser uma variável gravável")
            return False
        if not permitirStruct and resultado.tipo.ehStruct():
            self.gerenciadorErros.registrar(no, "A operação exige um valor escalar")
            return False
        return True

    def _comoValor(self, resultado: ResultadoExpressao, no: NoAST | None) -> OperandoTAC:
        if self._ehAgregado(resultado.tipo):
            return self._ponteiro(resultado, no)
        if resultado.operando is not None:
            return resultado.operando
        if resultado.deslocamento is not None:
            temporario = self._novoTemporario()
            self._emitir("load", (temporario, resultado.deslocamento), no)
            return temporario
        return self._op("constante", 0)

    def _obterBase(self, resultado: ResultadoExpressao, no: NoAST) -> OperandoTAC:
        if resultado.deslocamento is None:
            self.gerenciadorErros.registrar(no, "Agregado sem endereço")
            return self._op("global", 0)
        if resultado.indireto:
            temporario = self._novoTemporario()
            self._emitir("load", (temporario, resultado.deslocamento), no)
            return temporario
        return resultado.deslocamento

    def _ponteiro(self, resultado: ResultadoExpressao, no: NoAST | None) -> OperandoTAC:
        if resultado.indireto:
            if resultado.deslocamento is None:
                self.gerenciadorErros.registrar(no, "Parâmetro agregado sem endereço")
                return self._op("temporario", "t_erro")
            temporario = self._novoTemporario()
            self._emitir("load", (temporario, resultado.deslocamento), no)
            return temporario
        if resultado.deslocamento is not None:
            if resultado.deslocamento.categoria == "temporario":
                return resultado.deslocamento
            temporario = self._novoTemporario()
            self._emitir(
                "addr", (temporario, resultado.deslocamento, self._op("constante", 0)), no
            )
            return temporario
        if resultado.operando is not None:
            return resultado.operando
        self.gerenciadorErros.registrar(no, "Agregado sem endereço")
        return self._op("temporario", "t_erro")

    def _enderecoComOffset(
        self, base: OperandoTAC, deslocamento: int, no: NoAST
    ) -> OperandoTAC:
        if deslocamento == 0:
            return base
        endereco = self._novoTemporario()
        self._emitir(
            "addr", (endereco, base, self._op("constante", deslocamento)), no
        )
        return endereco

    def _converter(
        self,
        valor: OperandoTAC,
        tipoOrigem: TipoSemantico,
        tipoDestino: TipoSemantico,
        no: NoAST | None,
    ) -> OperandoTAC:
        if tipoOrigem.nome == TIPO_INT.nome and tipoDestino.nome == TIPO_FLOAT.nome:
            convertido = self._novoTemporario()
            self._emitir(
                "mul", (convertido, valor, self._op("constante", 1.0)), no
            )
            return convertido
        return valor

    def _tipoParametroCompativel(
        self, esperado: TipoSemantico, recebido: TipoSemantico
    ) -> bool:
        if esperado.ehErro() or recebido.ehErro():
            return True
        if esperado.ehVetor():
            return (
                recebido.ehVetor()
                and esperado.elemento is not None
                and recebido.elemento is not None
                and self._mesmoTipo(esperado.elemento, recebido.elemento)
                and (recebido.comprimento or 0) >= (esperado.comprimento or 0)
            )
        if esperado.ehStruct():
            return self._mesmoTipo(esperado, recebido)
        return self._tiposAtribuiveis(esperado, recebido)

    def _tiposAtribuiveis(
        self, destino: TipoSemantico, origem: TipoSemantico
    ) -> bool:
        if destino.ehErro() or origem.ehErro():
            return True
        if self._mesmoTipo(destino, origem):
            return True
        # Conversão numérica de alargamento; float -> int continua sendo erro.
        return destino.nome == TIPO_FLOAT.nome and origem.nome == TIPO_INT.nome

    def _mesmoTipo(self, esquerda: TipoSemantico, direita: TipoSemantico) -> bool:
        if esquerda.ehErro() or direita.ehErro():
            return True
        if esquerda.ehVetor() or direita.ehVetor():
            return (
                esquerda.ehVetor()
                and direita.ehVetor()
                and esquerda.comprimento == direita.comprimento
                and esquerda.elemento is not None
                and direita.elemento is not None
                and self._mesmoTipo(esquerda.elemento, direita.elemento)
            )
        if esquerda.ehStruct() or direita.ehStruct():
            return esquerda is direita
        return esquerda.nome == direita.nome

    def _exigirBool(self, resultado: ResultadoExpressao, no: NoAST) -> None:
        if resultado.tipo.nome != TIPO_BOOL.nome and not resultado.tipo.ehErro():
            self.gerenciadorErros.registrar(no, "A condição deve ter tipo bool")

    @staticmethod
    def _ehNumerico(tipo: TipoSemantico) -> bool:
        return tipo.nome in {TIPO_INT.nome, TIPO_FLOAT.nome}

    @staticmethod
    def _ehAgregado(tipo: TipoSemantico) -> bool:
        return tipo.ehVetor() or tipo.ehStruct()

    @staticmethod
    def _ehVetorDeStruct(tipo: TipoSemantico) -> bool:
        return tipo.ehVetor() and tipo.elemento is not None and tipo.elemento.ehStruct()

    @staticmethod
    def _ehErro(tipo: TipoSemantico) -> bool:
        return tipo.ehErro()

    def _constanteInteira(self, no: Expr | None) -> int | None:
        if isinstance(no, Literal) and no.tipo == "NUM_INT":
            try:
                return int(no.valor or "")
            except ValueError:
                return None
        return None

    def _retornaEmTodosOsCaminhos(self, comando: Comando | None) -> bool:
        if isinstance(comando, Return):
            return True
        if isinstance(comando, Bloco):
            return any(self._retornaEmTodosOsCaminhos(item) for item in comando.comandos)
        if isinstance(comando, If):
            return (
                comando.entao is not None
                and comando.senao is not None
                and self._retornaEmTodosOsCaminhos(comando.entao)
                and self._retornaEmTodosOsCaminhos(comando.senao)
            )
        return False

    def _inicializarGlobais(self, no: NoAST) -> None:
        for simbolo in self.escopoGlobal.simbolos.values():
            if simbolo.endereco is None or simbolo.endereco.categoria != REGIAO_GLOBAL:
                continue
            for indice, valor in enumerate(self._valoresPadrao(simbolo.tipo)):
                endereco = self._op(REGIAO_GLOBAL, simbolo.endereco.valor + indice)
                self._emitir("move", (endereco, self._op("constante", valor)), no)

    def _valoresPadrao(self, tipo: TipoSemantico) -> list[object]:
        if tipo.ehVetor() and tipo.elemento is not None:
            return [
                valor
                for _ in range(tipo.comprimento or 0)
                for valor in self._valoresPadrao(tipo.elemento)
            ]
        if tipo.ehStruct():
            valores: list[object] = [0] * max(tipo.tamanhoPosicoes, 1)
            for tipoCampo, deslocamento in tipo.campos.values():
                campo = self._valoresPadrao(tipoCampo)
                valores[deslocamento:deslocamento + len(campo)] = campo
            return valores
        if tipo.nome == TIPO_FLOAT.nome:
            return [0.0]
        if tipo.nome == TIPO_BOOL.nome:
            return [False]
        if tipo.nome == TIPO_CHAR.nome:
            return ["\0"]
        return [0]

    def _validarEntrada(self, programa: Programa) -> None:
        simbolo = self.escopoGlobal.simbolos.get(self.programaTAC.entrada)
        if simbolo is None or simbolo.categoria != CATEGORIA_FUNCAO:
            self.gerenciadorErros.registrar(
                programa, f"A função de entrada '{self.programaTAC.entrada}' não foi declarada"
            )
            return
        if simbolo.parametros:
            self.gerenciadorErros.registrar(programa, "A função main não pode receber parâmetros")
        if simbolo.tipo.nome != TIPO_INT.nome and not simbolo.tipo.ehErro():
            self.gerenciadorErros.registrar(programa, "A função main deve retornar int")

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
            endereco=self._op(REGIAO_LOCAL, deslocamento),
            linha=no.linha,
            coluna=no.coluna,
        )
        if not self.inserir(escopo, simbolo, no):
            return None
        # Vetores e structs passados como parâmetros são referências para a
        # primeira posição. Variáveis locais agregadas ocupam todas as posições.
        tamanho = (
            1 if categoria == CATEGORIA_PARAMETRO and self._ehAgregado(tipo)
            else max(tipo.tamanhoPosicoes, 1)
        )
        contexto.proximoDeslocamento += tamanho
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
            tipo = TIPO_ERRO
        if tamanho is None:
            return tipo
        if tamanho <= 0:
            self.gerenciadorErros.registrar(
                no, f"O tamanho do vetor '{getattr(no, 'nome', '')}' deve ser maior que zero"
            )
            return tipoVetor(tipo, 1)
        if tipo.ehStruct():
            self.gerenciadorErros.registrar(
                no,
                "Vetores de structs não são suportados; declare uma struct sem tamanho de vetor",
            )
        return tipoVetor(tipo, tamanho)

    def emitir(self, instrucao: InstrucaoTAC) -> None:
        """Mantém a API de emissão usada pelo protótipo semântico anterior."""
        self.programaTAC.instrucoes.append(instrucao)

    def _emitir(
        self, opcode: str, operandos: tuple[OperandoTAC | None, ...], no: NoAST | None
    ) -> None:
        self.emitir(InstrucaoTAC(
            opcode,
            operandos,
            linha=getattr(no, "linha", 0),
            coluna=getattr(no, "coluna", 0),
        ))

    def _novoTemporario(self) -> OperandoTAC:
        nome = f"t{self._proximoTemporario}"
        self._proximoTemporario += 1
        return self._op("temporario", nome)

    def _novoRotulo(self) -> str:
        # '_' não faz parte dos identificadores aceitos no lexer, então este
        # namespace não pode colidir com o nome de uma função C--.
        nome = f"__L{self._proximoRotulo}"
        self._proximoRotulo += 1
        return nome

    @staticmethod
    def _op(categoria: str, valor: object) -> OperandoTAC:
        return OperandoTAC(categoria, valor)

    def _resultadoErro(self) -> ResultadoExpressao:
        return ResultadoExpressao(TIPO_ERRO, self._op("constante", 0))

    def _erroTipo(self, no: NoAST | None, mensagem: str) -> TipoSemantico:
        self.gerenciadorErros.registrar(no, mensagem)
        return TIPO_ERRO

    def _erroExpressao(
        self, no: NoAST | None, mensagem: str
    ) -> ResultadoExpressao:
        self.gerenciadorErros.registrar(no, mensagem)
        return self._resultadoErro()

    @staticmethod
    def categoriaVariavel(tipo: TipoSemantico) -> str:
        return CATEGORIA_VETOR if tipo.ehVetor() else CATEGORIA_VARIAVEL
