import sys
import unittest
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.simulador.core.MemoriaInstrucoes import MemoriaInstrucoes
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


def rotulo(nome):
    return InstrucaoTAC('label', (OperandoTAC('rotulo', nome),))


class MemoriaInstrucoesTests(unittest.TestCase):
    def setUp(self):
        self.memoria = MemoriaInstrucoes()
        self.programa = ProgramaTAC(instrucoes=[
            rotulo('main'), InstrucaoTAC('goto', (OperandoTAC('rotulo', 'fim'),)),
            rotulo('fim'), InstrucaoTAC('halt'),
        ])

    def test_memoria_vazia(self):
        with self.assertRaises(IndexError):
            self.memoria.buscar(0)
        with self.assertRaises(KeyError):
            self.memoria.resolverRotulo('main')

    def test_carregamento_preserva_ordem_labels_e_identidade(self):
        self.memoria.carregar(self.programa)
        for pc, instrucao in enumerate(self.programa.instrucoes):
            self.assertIs(self.memoria.buscar(pc), instrucao)
        self.assertEqual(self.memoria.resolverRotulo('main'), 0)
        self.assertEqual(self.memoria.resolverRotulo('fim'), 2)

    def test_copia_superficial(self):
        self.memoria.carregar(self.programa)
        primeira = self.programa.instrucoes[0]
        self.programa.instrucoes.clear()
        self.assertIs(self.memoria.buscar(0), primeira)
        self.assertEqual(self.memoria.buscar(3).opcode, 'halt')
        self.assertEqual(self.memoria.resolverRotulo('fim'), 2)

    def test_programas_invalidos_preservam_estado_e_diagnosticos(self):
        self.memoria.carregar(self.programa)
        invalidos = [
            ProgramaTAC(),
            ProgramaTAC(instrucoes=[rotulo('main'), rotulo('main')]),
            ProgramaTAC(instrucoes=[rotulo('main'), InstrucaoTAC('mystery')]),
            ProgramaTAC(instrucoes=[rotulo('main'), InstrucaoTAC('add')]),
            ProgramaTAC(instrucoes=[InstrucaoTAC('label', (OperandoTAC('constante', 1),))]),
        ]
        for opcode in ('goto', 'if_true', 'if_false'):
            for alvo in (OperandoTAC('rotulo', 'ausente'), OperandoTAC('constante', 3)):
                operandos = (alvo,) if opcode == 'goto' else (OperandoTAC('constante', True), alvo)
                invalidos.append(ProgramaTAC(instrucoes=[rotulo('main'), InstrucaoTAC(opcode, operandos)]))
        for programa in invalidos:
            with self.subTest(programa=programa):
                with self.assertRaises(ValueError) as contexto:
                    self.memoria.carregar(programa)
                for erro in programa.validar():
                    self.assertIn(erro, str(contexto.exception))
                self.assertIs(self.memoria.buscar(0), self.programa.instrucoes[0])
                self.assertEqual(self.memoria.resolverRotulo('fim'), 2)

    def test_tipo_programa_invalido(self):
        self.memoria.carregar(self.programa)
        for programa in (None, [], 'programa'):
            with self.assertRaises(TypeError):
                self.memoria.carregar(programa)
        self.assertEqual(self.memoria.resolverRotulo('fim'), 2)

    def test_limites_pc(self):
        self.memoria.carregar(self.programa)
        for pc, erro in ((-1, ValueError), (True, TypeError), (False, TypeError),
                         (1.0, TypeError), (None, TypeError), ('0', TypeError),
                         ([], TypeError), (4, IndexError), (100, IndexError)):
            with self.subTest(pc=pc):
                with self.assertRaises(erro):
                    self.memoria.buscar(pc)

    def test_rotulos_invalidos(self):
        self.memoria.carregar(self.programa)
        for nome in ('ausente', '', 'MAIN'):
            with self.assertRaises(KeyError):
                self.memoria.resolverRotulo(nome)
        for nome in (None, 0, True, []):
            with self.assertRaises(TypeError):
                self.memoria.resolverRotulo(nome)

    def test_recarregamento_substitui_todo_estado(self):
        self.memoria.carregar(self.programa)
        novo = ProgramaTAC(entrada='novo', instrucoes=[rotulo('novo')])
        self.memoria.carregar(novo)
        self.assertIs(self.memoria.buscar(0), novo.instrucoes[0])
        self.assertEqual(self.memoria.resolverRotulo('novo'), 0)
        for nome in ('main', 'fim'):
            with self.assertRaises(KeyError):
                self.memoria.resolverRotulo(nome)
        with self.assertRaises(IndexError):
            self.memoria.buscar(1)

    def test_isolamento_instancias(self):
        outra = MemoriaInstrucoes()
        outra.carregar(self.programa)
        self.memoria.carregar(ProgramaTAC(entrada='outro', instrucoes=[rotulo('outro')]))
        self.assertEqual(outra.resolverRotulo('fim'), 2)
        with self.assertRaises(KeyError):
            outra.resolverRotulo('outro')


if __name__ == '__main__':
    unittest.main()
