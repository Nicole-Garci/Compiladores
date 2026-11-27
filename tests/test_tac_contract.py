import sys
import unittest
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


def op(categoria: str, valor: int | float | bool | str) -> OperandoTAC:
    return OperandoTAC(categoria, valor)


class ContratoTACTests(unittest.TestCase):
    def test_instrucao_reconhecida_com_aridade_correta(self):
        instrucao = InstrucaoTAC(
            "add", (op("temporario", "t0"), op("constante", 1), op("constante", 2))
        )

        self.assertEqual(instrucao.validar(), [])

    def test_rejeita_opcode_desconhecido_e_aridade_incorreta(self):
        self.assertTrue(InstrucaoTAC("mystery").validar())
        self.assertTrue(InstrucaoTAC("add", (op("constante", 1),)).validar())

    def test_aplica_operandos_opcionais_de_chamada_e_retorno(self):
        chamada = InstrucaoTAC(
            "call", (None, op("funcao", "sem_retorno"), op("constante", 0))
        )
        retorno = InstrucaoTAC("return", (None,))

        self.assertEqual(chamada.validar(), [])
        self.assertEqual(retorno.validar(), [])
        self.assertTrue(InstrucaoTAC("store", (None, op("constante", 1))).validar())

    def test_programa_detecta_rotulos_duplicados_e_destino_ausente(self):
        programa = ProgramaTAC(instrucoes=[
            InstrucaoTAC("label", (op("rotulo", "inicio"),)),
            InstrucaoTAC("goto", (op("rotulo", "ausente"),)),
            InstrucaoTAC("label", (op("rotulo", "inicio"),)),
        ])

        erros = programa.validar()
        self.assertTrue(any("não definido" in erro for erro in erros))
        self.assertTrue(any("duplicado" in erro for erro in erros))

    def test_programa_valido_nao_tem_erros(self):
        programa = ProgramaTAC(entrada="inicio", instrucoes=[
            InstrucaoTAC("label", (op("rotulo", "inicio"),)),
            InstrucaoTAC("if_true", (op("constante", True), op("rotulo", "fim"))),
            InstrucaoTAC("goto", (op("rotulo", "fim"),)),
            InstrucaoTAC("label", (op("rotulo", "fim"),)),
            InstrucaoTAC("return"),
        ])

        self.assertEqual(programa.validar(), [])


if __name__ == "__main__":
    unittest.main()