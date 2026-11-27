"""Opcodes suportados pelo contrato atual do código de três endereços."""

from dataclasses import dataclass

from .InstrucaoTAC import InstrucaoTAC
from .OperandoTAC import OperandoTAC


@dataclass(frozen=True)
class ContratoInstrucao:
    minimoOperandos: int
    maximoOperandos: int
    operandosOpcionais: tuple[int, ...] = ()
    descricao: str = ""


# A ordem dos operandos é a ordem usada nos exemplos de TAC e pelo simulador.
CONTRATOS_TAC: dict[str, ContratoInstrucao] = {
    "label": ContratoInstrucao(1, 1, descricao="marca um rótulo"),
    "move": ContratoInstrucao(2, 2, descricao="destino, origem"),
    "add": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "sub": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "mul": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "div": ContratoInstrucao(3, 3, descricao="destino, dividendo, divisor"),
    "mod": ContratoInstrucao(3, 3, descricao="destino, dividendo, divisor"),
    "neg": ContratoInstrucao(2, 2, descricao="destino, origem"),
    "not": ContratoInstrucao(2, 2, descricao="destino, origem"),
    "eq": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "ne": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "lt": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "le": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "gt": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "ge": ContratoInstrucao(3, 3, descricao="destino, esquerda, direita"),
    "addr": ContratoInstrucao(3, 3, descricao="destino, base, índice"),
    "load": ContratoInstrucao(2, 2, descricao="destino, endereço"),
    "store": ContratoInstrucao(2, 2, descricao="endereço, valor"),
    "goto": ContratoInstrucao(1, 1, descricao="rótulo de destino"),
    "if_true": ContratoInstrucao(2, 2, descricao="condição, rótulo de destino"),
    "if_false": ContratoInstrucao(2, 2, descricao="condição, rótulo de destino"),
    "param": ContratoInstrucao(1, 1, descricao="valor do argumento"),
    "call": ContratoInstrucao(
        3, 3, operandosOpcionais=(0,),
        descricao="destino opcional, função, quantidade de argumentos",
    ),
    "return": ContratoInstrucao(
        0, 1, operandosOpcionais=(0,), descricao="valor de retorno opcional",
    ),
    "read": ContratoInstrucao(1, 1, descricao="destino"),
    "print": ContratoInstrucao(1, 1, descricao="valor"),
    "halt": ContratoInstrucao(0, 0, descricao="encerra a execução"),
}


def validarInstrucaoTAC(instrucao: InstrucaoTAC) -> list[str]:
    """Valida opcode, quantidade de operandos e posições opcionais."""
    contrato = CONTRATOS_TAC.get(instrucao.opcode)
    if contrato is None:
        return [f"Opcode TAC desconhecido: '{instrucao.opcode}'"]

    quantidade = len(instrucao.operandos)
    if not contrato.minimoOperandos <= quantidade <= contrato.maximoOperandos:
        if contrato.minimoOperandos == contrato.maximoOperandos:
            esperado = str(contrato.minimoOperandos)
        else:
            esperado = f"entre {contrato.minimoOperandos} e {contrato.maximoOperandos}"
        return [
            f"Opcode '{instrucao.opcode}' espera {esperado} operandos; "
            f"recebeu {quantidade}"
        ]

    erros: list[str] = []
    for indice, operando in enumerate(instrucao.operandos):
        if operando is None and indice not in contrato.operandosOpcionais:
            erros.append(
                f"O operando {indice + 1} de '{instrucao.opcode}' é obrigatório"
            )
        elif operando is not None and not isinstance(operando, OperandoTAC):
            erros.append(
                f"O operando {indice + 1} de '{instrucao.opcode}' deve ser OperandoTAC"
            )
    return erros