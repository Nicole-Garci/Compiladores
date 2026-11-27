from __future__ import annotations

from dataclasses import dataclass

from src.tac.OperandoTAC import OperandoTAC

from .TipoSemantico import TipoSemantico


@dataclass
class ResultadoExpressao:
    """Resultado sintetizado ao visitar uma expressão.

    ``operando`` representa o valor TAC quando ele já está disponível.
    ``deslocamento`` representa o endereço gravável de um lvalue, direto
    (global/local) ou calculado (temporário). Parâmetros agregados guardam
    um endereço dentro do quadro e, por isso, usam ``indireto=True``.
    """

    tipo: TipoSemantico
    operando: OperandoTAC | None = None
    deslocamento: OperandoTAC | None = None
    atribuivel: bool = False
    indireto: bool = False
