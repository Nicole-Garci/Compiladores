from __future__ import annotations

from dataclasses import dataclass

from src.parser.ast.Nos import (
    Bloco, Comando, DeclFuncao, DeclStruct, DeclVariavel, Expr, If, NoAST,
    Parametro, Programa, While,
)
from src.semantico.Escopo import Escopo
from src.semantico.GerenciadorErrosSemanticos import GerenciadorErrosSemanticos
from src.semantico.models.ResultadoExpressao import ResultadoExpressao
from src.semantico.models.SimboloSemantico import (
    CATEGORIA_FUNCAO, CATEGORIA_PARAMETRO, CATEGORIA_VARIAVEL, CATEGORIA_VETOR,
    SimboloSemantico,
)
from src.semantico.models.TipoSemantico import (
    TIPO_ERRO, TIPOS_PRIMITIVOS, TipoSemantico, tipoVetor,
)
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


REGIAO_GLOBAL = "global"
REGIAO_LOCAL = "local"


@dataclass
class ContextoFuncao:
    simbolo: SimboloSemantico
    proximoDeslocamento: int = 0
    dentroDeLaco: bool = False


class MotorSemantico:
    def __init__(self, gerenciadorErros: GerenciadorErrosSemanticos) -> None:
        self.gerenciadorErros = gerenciadorErros
        self.escopoGlobal = Escopo()
        self.programaTAC = ProgramaTAC()
        self.tiposDeclarados: dict[str, TipoSemantico] = {}
        self.structs: list[TipoSemantico] = []
        self.escoposFuncoes: dict[str, Escopo] = {}
        self.assinaturas: dict[int, SimboloSemantico] = {}

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

        for parametro, tipo in zip(no.parametros, simboloFuncao.parametros):
            deslocamento = self.cadastrarLocal(
                escopo, contexto, parametro, tipo, CATEGORIA_PARAMETRO
            )
            if deslocamento is not None:
                deslocamentosParametros.append(deslocamento)

        self.visitarBloco(no.corpo, escopo, contexto, novoEscopo=False)

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
        if isinstance(no, Bloco):
            self.visitarBloco(no, escopo, contexto)
        elif isinstance(no, If):
            self.visitarComando(no.entao, escopo, contexto)
            self.visitarComando(no.senao, escopo, contexto)
        elif isinstance(no, While):
            dentroDeLacoAnterior = contexto.dentroDeLaco
            contexto.dentroDeLaco = True
            self.visitarComando(no.corpo, escopo, contexto)
            contexto.dentroDeLaco = dentroDeLacoAnterior

    def visitarExpressao(self, no: Expr | None, escopo: Escopo) -> ResultadoExpressao:
        raise NotImplementedError("Verificação de expressões ainda não implementada")

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
            tipo = TIPO_ERRO

        if tamanho is None:
            return tipo

        if tamanho <= 0:
            self.gerenciadorErros.registrar(
                no, f"O tamanho do vetor '{getattr(no, 'nome', '')}' deve ser maior que zero"
            )
            return tipoVetor(tipo, 1)

        return tipoVetor(tipo, tamanho)

    @staticmethod
    def categoriaVariavel(tipo: TipoSemantico) -> str:
        return CATEGORIA_VETOR if tipo.ehVetor() else CATEGORIA_VARIAVEL
