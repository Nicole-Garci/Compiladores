import sys
import unittest
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.simulador.core.UnidadeOperacoes import UnidadeOperacoes


class UnidadeOperacoesTests(unittest.TestCase):
    def setUp(self):
        self.unidade = UnidadeOperacoes()

    def test_aritmetica(self):
        for opcode, a, b, esperado in (
            ('add', -3, 5, 2), ('sub', 3, 5, -2), ('mul', -3, 5, -15),
            ('add', 2, 0.5, 2.5), ('sub', 2.5, 1, 1.5),
            ('mul', 2, 1.5, 3.0),
        ):
            with self.subTest(opcode=opcode, a=a):
                resultado = self.unidade.executar(opcode, a, b)
                self.assertEqual(resultado, esperado)
                self.assertIs(type(resultado), type(esperado))

    def test_divisao_e_resto_inteiros(self):
        for a, b, quociente, resto in (
            (7, 3, 2, 1), (-7, 3, -2, -1), (7, -3, -2, 1),
            (-7, -3, 2, -1), (-2, 3, 0, -2), (0, -3, 0, 0),
            (-6, 3, -2, 0),
        ):
            with self.subTest(a=a, b=b):
                q = self.unidade.executar('div', a, b)
                r = self.unidade.executar('mod', a, b)
                self.assertIs(type(q), int)
                self.assertEqual((q, r), (quociente, resto))
                self.assertEqual(a, q * b + r)

    def test_inteiros_grandes_sem_conversao_float(self):
        grande = 10 ** 400
        self.assertEqual(self.unidade.executar('add', grande, 1), grande + 1)
        self.assertEqual(self.unidade.executar('mul', grande, 2), grande * 2)
        self.assertEqual(self.unidade.executar('div', -(grande * 3 + 2), 3), -grande)
        self.assertEqual(self.unidade.executar('mod', -(grande * 3 + 2), 3), -2)
        self.assertIs(self.unidade.executar('gt', grande + 1, grande), True)

    def test_divisao_real(self):
        for a, b in ((7.0, 2), (7, 2.0), (-7.0, 2.0)):
            with self.subTest(a=a, b=b):
                resultado = self.unidade.executar('div', a, b)
                self.assertIs(type(resultado), float)
                self.assertEqual(resultado, a / b)

    def test_unarias(self):
        self.assertEqual(self.unidade.executar('neg', -4), 4)
        self.assertEqual(self.unidade.executar('neg', 1.5), -1.5)
        for valor, esperado in ((False, True), (True, False), (0, True),
                                (-0.0, True), (-3, False), (0.1, False)):
            with self.subTest(valor=valor):
                self.assertIs(self.unidade.executar('not', valor), esperado)

    def test_comparacoes(self):
        for opcode, a, b, esperado in (
            ('eq', 2, 2.0, True), ('eq', 1, 2, False),
            ('ne', 1, 2, True), ('ne', 2.0, 2, False),
            ('lt', -1, 0.5, True), ('lt', 1, 1, False),
            ('le', 1, 1.0, True), ('le', 2, 1, False),
            ('gt', 2, 1.5, True), ('gt', 1, 1, False),
            ('ge', 1, 1, True), ('ge', 0, 1, False),
            ('eq', True, True, True), ('ne', False, True, True),
        ):
            with self.subTest(opcode=opcode, a=a, b=b):
                self.assertIs(self.unidade.executar(opcode, a, b), esperado)

    def test_tipos_incompativeis(self):
        for opcode in ('add', 'sub', 'mul', 'div', 'mod', 'eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            for invalido in (True, '2', [], object()):
                with self.subTest(opcode=opcode, invalido=invalido):
                    with self.assertRaises(TypeError):
                        self.unidade.executar(opcode, invalido, 2)
                    with self.assertRaises(TypeError):
                        self.unidade.executar(opcode, 2, invalido)
        for opcode in ('add', 'lt'):
            with self.assertRaises(TypeError):
                self.unidade.executar(opcode, 'a', 'b')
        self.assertIs(self.unidade.executar('eq', 'a', 'a'), True)
        self.assertIs(self.unidade.executar('ne', 'a', 'b'), True)
        for opcode in ('eq', 'ne'):
            with self.assertRaises(TypeError):
                self.unidade.executar(opcode, 'texto', 'texto')
        for opcode in ('neg', 'not'):
            for invalido in (None, 'a', []):
                with self.assertRaises(TypeError):
                    self.unidade.executar(opcode, invalido)
        with self.assertRaises(TypeError):
            self.unidade.executar('neg', True)
        with self.assertRaises(TypeError):
            self.unidade.executar('lt', False, True)
        for a, b in ((2.0, 1), (2, 1.0)):
            with self.assertRaises(TypeError):
                self.unidade.executar('mod', a, b)

    def test_aridade(self):
        for opcode in ('neg', 'not'):
            with self.assertRaises(TypeError):
                self.unidade.executar(opcode, 1, 2)
        for opcode in ('add', 'sub', 'mul', 'div', 'mod', 'eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            with self.assertRaises(TypeError):
                self.unidade.executar(opcode, 1)
        with self.assertRaises(TypeError):
            self.unidade.executar('neg')
        with self.assertRaises(TypeError):
            self.unidade.executar('add', 1, 2, 3)

    def test_divisor_zero(self):
        for opcode, zero in (('div', 0), ('div', 0.0), ('div', -0.0), ('mod', 0)):
            with self.subTest(opcode=opcode, zero=zero):
                with self.assertRaises(ZeroDivisionError):
                    self.unidade.executar(opcode, 5, zero)

    def test_opcode_invalido(self):
        for opcode in ('ADD', '', 'addr', 'load', 'store', 'move', 'goto', 'call', 'print', 'and'):
            with self.assertRaises(ValueError):
                self.unidade.executar(opcode, 1, 2)
        for opcode in (None, [], 1):
            with self.assertRaises(TypeError):
                self.unidade.executar(opcode, 1, 2)


if __name__ == '__main__':
    unittest.main()
