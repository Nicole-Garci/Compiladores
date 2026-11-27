import ast
import math
import re
from dataclasses import dataclass

from src.simulador.core.BancoRegistradores import BancoRegistradores
from src.simulador.core.MemoriaDados import MemoriaDados
from src.simulador.core.MemoriaInstrucoes import MemoriaInstrucoes
from src.simulador.core.UnidadeOperacoes import UnidadeOperacoes
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


@dataclass
class _ContextoChamada:
    pc: int
    fp: int
    sp: int
    ra: object
    quadro: tuple[int, int]
    temporarios: dict[int, object]
    nomes: dict[str, int]
    destino: int | tuple[str, int] | None


class Simulador:
    """Executor TAC sequencial, com PC exclusivo e endereços (região, índice).

    O rastro contém instruções concluídas, incluindo label e halt. Em falhas,
    IR identifica a instrução tentada e a exceção informa seu PC de origem.
    O quadro inicial permanece reservado após halt para inspeção dos resultados.
    """

    def __init__(self) -> None:
        self._reiniciar()

    def _reiniciar(self) -> None:
        self.instrucoes = MemoriaInstrucoes()
        self.dados = MemoriaDados()
        self.registradores = BancoRegistradores()
        self.operacoes = UnidadeOperacoes()
        self.pc: int = 0
        self.ir: InstrucaoTAC | None = None
        self.rastro: list[tuple[int, InstrucaoTAC]] = []
        self._temporarios: dict[str, int] = {}
        self._encerrado = False
        self._quadros: dict[str, tuple[int, list[int]]] = {}
        self._quadroAtual: tuple[int, int] = (0, 0)
        self._chamadas: list[_ContextoChamada] = []
        self._argumentos: list[object] = []

    def executar(self, programa: ProgramaTAC) -> None:
        """Reinicia o estado, carrega TAC e executa até halt ou uma exceção.

        Quadro de entrada ausente equivale a tamanho zero. SP indica a próxima
        posição livre. Não há término implícito ao ultrapassar o código.
        """
        self._reiniciar()
        self.instrucoes.carregar(programa)
        self.dados = MemoriaDados(programa.tamanhoDados)
        if not isinstance(programa.quadros, dict):
            raise TypeError("Os quadros devem ser um dicionário.")
        self._quadros = programa.quadros.copy()
        tamanho, parametros = self._validarQuadro(
            self._quadros.get(programa.entrada, (0, []))
        )
        if parametros:
            raise ValueError("A função de entrada não recebe argumentos.")
        base = self.dados.reservarQuadro(tamanho)
        self._quadroAtual = (base, tamanho)
        self.registradores.escrever("$fp", base)
        self.registradores.escrever("$sp", base + tamanho)
        self.pc = self.instrucoes.resolverRotulo(programa.entrada)

        while not self._encerrado:
            pcAtual = self.pc
            self.ir = None
            try:
                self.ir = self.instrucoes.buscar(pcAtual)
                self.pc = pcAtual + 1
                self.executarInstrucao(self.ir)
            except (TypeError, ValueError, KeyError, IndexError,
                    ArithmeticError, RuntimeError, EOFError, OSError) as erro:
                self._encerrado = True
                contexto = f"Erro de execução no PC {pcAtual}"
                if self.ir is not None:
                    contexto += (
                        f" ({self.ir.opcode}, linha {self.ir.linha}, "
                        f"coluna {self.ir.coluna})"
                    )
                raise type(erro)(f"{contexto}: {erro}") from erro
            self.rastro.append((pcAtual, self.ir))

    def obterRastro(self) -> list[tuple[int, InstrucaoTAC]]:
        """Retorna cópia da sequência cronológica de instruções concluídas."""
        return self.rastro.copy()

    def executarInstrucao(self, instrucao: InstrucaoTAC) -> None:
        """Despacha uma instrução; o ciclo cuida de IR, avanço padrão e rastro.

        Chamadas diretas não avançam automaticamente o PC nem registram rastro.
        Saltos alteram PC e halt sinaliza o término ao ciclo.
        """
        if not isinstance(instrucao, InstrucaoTAC):
            raise TypeError("A instrução deve ser InstrucaoTAC.")
        erros = instrucao.validar()
        if erros:
            raise ValueError("; ".join(erros))
        opcode = instrucao.opcode
        operandos = instrucao.operandos
        if self._argumentos and opcode not in {"param", "call"}:
            raise ValueError("Argumentos pendentes devem ser seguidos por call.")
        if opcode == "param":
            self._argumentos.append(self._valor(operandos[0]))
        elif opcode == "call":
            self._chamar(*operandos)
        elif opcode == "return":
            valor = self._valor(operandos[0]) if operandos and operandos[0] is not None else None
            self._retornar(valor)
        elif opcode == "print":
            valor = self._valor(operandos[0])
            if type(valor) not in (int, float, bool, str):
                raise TypeError("print não aceita endereços internos ou objetos.")
            print(("true" if valor else "false") if type(valor) is bool else valor)
        elif opcode == "label":
            self._rotulo(operandos[0])
        elif opcode == "halt":
            self._encerrado = True
        elif opcode == "goto":
            self.pc = self._rotulo(operandos[0])
        elif opcode in {"if_true", "if_false"}:
            condicao = self._valor(operandos[0])
            if type(condicao) not in (bool, int, float):
                raise TypeError("A condição deve ser booleana ou numérica.")
            alvo = self._rotulo(operandos[1])
            if (condicao != 0) == (opcode == "if_true"):
                self.pc = alvo
        elif opcode == "store":
            regiao, indice = self._endereco(operandos[0])
            self.dados.escrever(regiao, indice, self._valor(operandos[1]))
        else:
            destino = self._destino(operandos[0])
            if opcode == "read":
                tipoEsperado = (
                    operandos[1].valor if len(operandos) == 2 else None
                )
                resultado = self._lerEntrada(tipoEsperado)
            elif opcode == "move":
                resultado = self._valor(operandos[1])
            elif opcode == "load":
                regiao, indice = self._endereco(operandos[1])
                resultado = self._inicializado(self.dados.ler(regiao, indice))
            elif opcode == "addr":
                regiao, base = self._endereco(operandos[1])
                deslocamento = self._valor(operandos[2])
                if type(deslocamento) is not int:
                    raise TypeError("O deslocamento de addr deve ser inteiro.")
                # Deslocamento já escalado; não se aplica largura de tipo aqui.
                resultado = (regiao, base + deslocamento)
                self._validarEndereco(resultado)
            else:
                a = self._valor(operandos[1])
                b = self._valor(operandos[2]) if len(operandos) == 3 else None
                resultado = self.operacoes.executar(opcode, a, b)
            self._escreverDestino(destino, resultado)

    def _chamar(
        self, destino: OperandoTAC | None, funcao: OperandoTAC, quantidade: OperandoTAC
    ) -> None:
        if funcao.categoria != "funcao" or not isinstance(funcao.valor, str) or not funcao.valor:
            raise ValueError("call exige função com nome string não vazio.")
        alvo = self.instrucoes.resolverRotulo(funcao.valor)
        if funcao.valor not in self._quadros:
            raise ValueError(f"Quadro da função '{funcao.valor}' não definido.")
        tamanho, deslocamentos = self._validarQuadro(self._quadros[funcao.valor])
        numero = self._valor(quantidade)
        if type(numero) is not int:
            raise TypeError("A quantidade de argumentos deve ser inteira.")
        if numero < 0 or numero != len(self._argumentos) or numero != len(deslocamentos):
            raise ValueError("Quantidade de argumentos incompatível com param ou quadro.")
        # Resolve inclusive destinos locais no contexto do chamador, antes de
        # reservar o quadro. Depois destas validações, as escritas cabem na reserva.
        alvoRetorno = self._destino(destino) if destino is not None else None
        fp = self.registradores.ler("$fp")
        sp = self.registradores.ler("$sp")
        ra = self.registradores.ler("$ra")
        base = self.dados.reservarQuadro(tamanho)
        anteriores = self.registradores.trocarTemporarios({})
        self._chamadas.append(_ContextoChamada(
            self.pc, fp, sp, ra, self._quadroAtual, anteriores,
            self._temporarios, alvoRetorno,
        ))
        self._temporarios = {}
        self._quadroAtual = (base, tamanho)
        self.registradores.escrever("$fp", base)
        self.registradores.escrever("$sp", base + tamanho)
        self.registradores.escrever("$ra", self.pc)
        self.registradores.escrever("$v0", None)
        for deslocamento, valor in zip(deslocamentos, self._argumentos):
            self.dados.escrever("local", base + deslocamento, valor)
        self._argumentos = []
        self.pc = alvo

    def _retornar(self, valor: object) -> None:
        # O operando já foi resolvido no contexto da função que está retornando.
        self.dados.liberarQuadro(self._quadroAtual[0])
        self.registradores.escrever("$v0", valor)
        if not self._chamadas:
            self.registradores.escrever("$fp", 0)
            self.registradores.escrever("$sp", 0)
            self.registradores.escrever("$ra", None)
            self._quadroAtual = (0, 0)
            self._encerrado = True
            return
        contexto = self._chamadas.pop()
        self.registradores.trocarTemporarios(contexto.temporarios)
        self._temporarios = contexto.nomes
        self._quadroAtual = contexto.quadro
        self.registradores.escrever("$fp", contexto.fp)
        self.registradores.escrever("$sp", contexto.sp)
        self.registradores.escrever("$ra", contexto.ra)
        self.pc = contexto.pc
        if contexto.destino is not None:
            # Sem valor: armazena None (não inicializado), sem inventar tipo/zero.
            self._escreverDestino(contexto.destino, valor)

    def _escreverDestino(self, destino: int | tuple[str, int], valor: object) -> None:
        if isinstance(destino, int):
            self.registradores.escrever(destino, valor)
        else:
            self.dados.escrever(*destino, valor)

    @staticmethod
    def _validarQuadro(quadro: object) -> tuple[int, list[int]]:
        if not isinstance(quadro, tuple) or len(quadro) != 2:
            raise TypeError("O quadro deve ser (tamanho, deslocamentos dos parâmetros).")
        tamanho, deslocamentos = quadro
        if type(tamanho) is not int or not isinstance(deslocamentos, list):
            raise TypeError("Tamanho deve ser inteiro e deslocamentos devem ser lista.")
        if tamanho < 0:
            raise ValueError("O tamanho do quadro não pode ser negativo.")
        if any(type(indice) is not int for indice in deslocamentos):
            raise TypeError("Deslocamentos de parâmetros devem ser inteiros.")
        if any(indice < 0 or indice >= tamanho for indice in deslocamentos):
            raise ValueError("Parâmetro fora dos limites do quadro.")
        if len(set(deslocamentos)) != len(deslocamentos):
            raise ValueError("Deslocamentos de parâmetros duplicados.")
        return tamanho, deslocamentos.copy()

    @staticmethod
    def _lerEntrada(tipoEsperado: str | None = None) -> int | float | bool | str:
        """Lê o tipo informado pelo TAC; TAC antigo sem tipo usa inferência.

        Char pode vir entre aspas simples para representar espaço ou escapes.
        Entrada real não finita e texto incompatível com o tipo são rejeitados.
        """
        texto = input().strip()
        if tipoEsperado is not None:
            if tipoEsperado == "bool":
                if texto in {"true", "false"}:
                    return texto == "true"
                raise ValueError("Entrada inválida: esperado true ou false.")
            if tipoEsperado == "int":
                if re.fullmatch(r"[+-]?[0-9]+", texto):
                    return int(texto)
                raise ValueError("Entrada inválida: esperado int.")
            if tipoEsperado == "float":
                if not re.fullmatch(
                    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?",
                    texto,
                ):
                    raise ValueError("Entrada inválida: esperado float.")
                valor = float(texto)
                if math.isfinite(valor):
                    return valor
                raise ValueError("Entrada real fora da faixa finita.")
            if tipoEsperado == "char":
                if texto.startswith("'") and texto.endswith("'"):
                    try:
                        valor = ast.literal_eval(texto)
                    except (SyntaxError, ValueError) as erro:
                        raise ValueError("Literal de caractere inválido.") from erro
                    if type(valor) is str and len(valor) == 1:
                        return valor
                elif len(texto) == 1 and texto not in {"'", '"'}:
                    return texto
                raise ValueError("Entrada inválida: esperado char.")
            raise ValueError(f"Tipo de entrada desconhecido: '{tipoEsperado}'.")
        if texto in {"true", "false"}:
            return texto == "true"
        if re.fullmatch(r"[+-]?[0-9]+", texto):
            return int(texto)
        if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", texto):
            valor = float(texto)
            if not math.isfinite(valor):
                raise ValueError("Entrada real fora da faixa finita.")
            return valor
        if texto.startswith("'") and texto.endswith("'"):
            try:
                valor = ast.literal_eval(texto)
            except (SyntaxError, ValueError) as erro:
                raise ValueError("Literal de caractere inválido.") from erro
            if type(valor) is str and len(valor) == 1:
                return valor
        elif len(texto) == 1 and texto not in {"'", '"'}:
            return texto
        raise ValueError("Entrada inválida: esperado int, float, bool ou char.")

    def _temporario(self, operando: OperandoTAC) -> int:
        nome = operando.valor
        if not isinstance(nome, str) or not nome:
            raise TypeError("O temporário deve ter nome string não vazio.")
        # A categoria TAC não exige a sintaxe tN. Cada nome recebe uma chave
        # estável por ativação, sem colisões entre t0, t00 ou outros nomes.
        if nome not in self._temporarios:
            self._temporarios[nome] = len(self._temporarios)
        return self._temporarios[nome]

    def _destino(self, operando: OperandoTAC) -> int | tuple[str, int]:
        if not isinstance(operando, OperandoTAC):
            raise TypeError("O destino deve ser OperandoTAC.")
        if operando.categoria == "temporario":
            return self._temporario(operando)
        if operando.categoria in {"global", "local"}:
            return self._endereco(operando)
        raise ValueError(f"Categoria não atribuível: '{operando.categoria}'.")

    def _valor(self, operando: OperandoTAC) -> object:
        if not isinstance(operando, OperandoTAC):
            raise TypeError("O valor deve ser representado por OperandoTAC.")
        if operando.categoria == "constante":
            return operando.valor
        if operando.categoria == "temporario":
            return self._inicializado(self.registradores.ler(self._temporario(operando)))
        if operando.categoria in {"global", "local"}:
            return self._inicializado(self.dados.ler(*self._endereco(operando)))
        raise ValueError(f"Categoria inválida como valor: '{operando.categoria}'.")

    def _endereco(self, operando: OperandoTAC) -> tuple[str, int]:
        if not isinstance(operando, OperandoTAC):
            raise TypeError("O endereço deve ser representado por OperandoTAC.")
        if operando.categoria in {"global", "local"}:
            indice = operando.valor
            if type(indice) is not int:
                raise TypeError("O deslocamento de memória deve ser inteiro.")
            if indice < 0:
                raise ValueError("O deslocamento de memória não pode ser negativo.")
            if operando.categoria == "local":
                if indice >= self._quadroAtual[1]:
                    raise IndexError("Deslocamento local fora do quadro corrente.")
                indice += self.registradores.ler("$fp")
            endereco = (operando.categoria, indice)
        elif operando.categoria == "temporario":
            endereco = self._valor(operando)
        else:
            raise ValueError("Endereço exige global, local ou temporário de endereço.")
        self._validarEndereco(endereco)
        return endereco

    def _validarEndereco(self, endereco: object) -> None:
        if (not isinstance(endereco, tuple) or len(endereco) != 2
                or not isinstance(endereco[0], str)
                or type(endereco[1]) is not int):
            raise TypeError("Endereço calculado deve ser (região, índice inteiro).")
        # Usa a API pública para validar região e limites; None é válido aqui,
        # pois validar o endereço não significa consumir seu conteúdo.
        self.dados.ler(*endereco)

    def _rotulo(self, operando: OperandoTAC) -> int:
        if not isinstance(operando, OperandoTAC) or operando.categoria != "rotulo":
            raise ValueError("O alvo deve ser um operando da categoria rotulo.")
        return self.instrucoes.resolverRotulo(operando.valor)

    @staticmethod
    def _inicializado(valor: object) -> object:
        if valor is None:
            raise ValueError("Leitura de valor não inicializado.")
        return valor
