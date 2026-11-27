import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.simulador.Simulador import Simulador
from src.simulador.core.UnidadeOperacoes import UnidadeOperacoes
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC
from src.tac.ContratoTAC import CONTRATOS_TAC


def op(categoria, valor):
    return OperandoTAC(categoria, valor)


def c(valor):
    return op('constante', valor)


def t(nome):
    return op('temporario', nome)


def g(indice):
    return op('global', indice)


def local(indice):
    return op('local', indice)


def label(nome):
    return InstrucaoTAC('label', (op('rotulo', nome),))


def ins(opcode, *operandos):
    return InstrucaoTAC(opcode, operandos)


def programa(*instrucoes, tamanho=4, quadro=0):
    return ProgramaTAC(tamanhoDados=tamanho, quadros={'main': (quadro, [])},
                       instrucoes=[label('main'), *instrucoes, ins('halt')])


class SimuladorTests(unittest.TestCase):
    def setUp(self):
        self.sim = Simulador()

    def test_construtor(self):
        self.assertEqual(self.sim.pc, 0)
        self.assertIsNone(self.sim.ir)
        self.assertEqual(self.sim.obterRastro(), [])
        self.assertEqual(self.sim.registradores.ler('$zero'), 0)
        with self.assertRaises(KeyError):
            self.sim.registradores.ler('$pc')

    def test_operacoes_delegadas_a_ula(self):
        casos = [('add', (7, 3), 10), ('sub', (7, 3), 4),
                 ('mul', (-7, 3), -21), ('div', (-7, 3), -2),
                 ('mod', (-7, 3), -1), ('neg', (7,), -7),
                 ('not', (0,), True), ('eq', (2, 2.0), True),
                 ('ne', (2, 3), True), ('lt', (2, 3), True),
                 ('le', (2, 2), True), ('gt', (3, 2), True),
                 ('ge', (3, 3), True)]
        original = UnidadeOperacoes.executar
        with patch.object(UnidadeOperacoes, 'executar', autospec=True,
                          side_effect=original) as executar:
            for opcode, valores, esperado in casos:
                with self.subTest(opcode=opcode):
                    self.sim.executar(programa(ins(opcode, t('resultado'), *(c(v) for v in valores)),
                                               ins('move', g(0), t('resultado'))))
                    self.assertEqual(self.sim.dados.ler('global', 0), esperado)
                    self.assertIs(type(self.sim.dados.ler('global', 0)), type(esperado))
            self.assertEqual(executar.call_count, 13)

    def test_memoria_move_load_store_e_enderecos(self):
        p = programa(
            ins('move', g(0), c(10)), ins('move', local(0), c(20)),
            ins('addr', t('pg'), g(0), c(1)),
            ins('addr', t('pl'), local(0), c(1)),
            ins('store', t('pg'), g(0)), ins('store', t('pl'), local(0)),
            ins('load', t('x'), t('pg')), ins('load', t('y'), t('pl')),
            ins('add', g(2), t('x'), t('y')),
            ins('move', t('copia'), t('pl')), ins('store', t('copia'), c(99)),
            ins('move', g(3), t('copia')), quadro=2,
        )
        self.sim.executar(p)
        self.assertEqual(self.sim.dados.ler('global', 1), 10)
        self.assertEqual(self.sim.dados.ler('local', 1), 99)
        self.assertEqual(self.sim.dados.ler('global', 2), 30)
        self.assertEqual(self.sim.dados.ler('global', 3), ('local', 1))
        self.assertEqual(self.sim.registradores.ler('$fp'), 0)
        self.assertEqual(self.sim.registradores.ler('$sp'), 2)
        self.assertIsNone(self.sim.registradores.ler('$ra'))
        self.assertIsNone(self.sim.registradores.ler('$v0'))

    def test_addr_deslocamento_escalado_e_negativo(self):
        self.sim.executar(programa(
            ins('addr', t('p'), g(0), c(3)),
            ins('addr', t('q'), t('p'), c(-2)),
            ins('store', t('q'), c(17)),
            ins('load', g(2), t('q')),
        ))
        self.assertEqual(self.sim.dados.ler('global', 1), 17)
        self.assertEqual(self.sim.dados.ler('global', 2), 17)

    def test_local_soma_fp_uma_vez(self):
        self.sim.executar(programa(quadro=2))
        base = self.sim.dados.reservarQuadro(2)
        self.sim.registradores.escrever('$fp', base)
        self.sim.executarInstrucao(ins('move', local(1), c(8)))
        self.sim.executarInstrucao(ins('addr', t('p'), local(0), c(1)))
        self.sim.executarInstrucao(ins('load', g(0), t('p')))
        self.assertEqual(self.sim.dados.ler('local', 3), 8)
        self.assertIsNone(self.sim.dados.ler('local', 1))
        self.assertEqual(self.sim.dados.ler('global', 0), 8)

    def test_laco_rastro_e_saltos(self):
        p = programa(
            ins('move', g(0), c(0)), label('laco'),
            ins('add', g(0), g(0), c(1)),
            ins('lt', t('cond'), g(0), c(3)),
            ins('if_true', t('cond'), op('rotulo', 'laco')),
            ins('goto', op('rotulo', 'fim')),
            ins('move', g(0), c(999)), label('fim'),
        )
        self.sim.executar(p)
        self.assertEqual(self.sim.dados.ler('global', 0), 3)
        indices = [pc for pc, _ in self.sim.obterRastro()]
        self.assertEqual(indices, [0, 1, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 6, 8, 9])
        self.assertIs(self.sim.ir, p.instrucoes[9])
        self.assertEqual(self.sim.pc, 10)
        copia = self.sim.obterRastro()
        copia.clear()
        self.assertEqual(len(self.sim.obterRastro()), 17)

    def test_condicionais_zero_e_nao_zero(self):
        for opcode in ('if_true', 'if_false'):
            for valor in (False, True, 0, -2, 0.0, 0.5):
                with self.subTest(opcode=opcode, valor=valor):
                    self.sim.executar(programa(
                        ins('move', g(0), c(1)),
                        ins(opcode, c(valor), op('rotulo', 'fim')),
                        ins('move', g(0), c(2)), label('fim'),
                    ))
                    salta = (valor != 0) == (opcode == 'if_true')
                    self.assertEqual(self.sim.dados.ler('global', 0), 1 if salta else 2)

    def test_entrada_nao_precisa_ser_primeira_e_halt_interrompe(self):
        p = ProgramaTAC(entrada='inicio', instrucoes=[
            ins('print', c('ignorado')), label('inicio'), ins('halt'), ins('read', t('x')),
        ])
        self.sim.executar(p)
        self.assertEqual([pc for pc, _ in self.sim.obterRastro()], [1, 2])
        self.assertEqual(self.sim.registradores.ler('$sp'), 0)

    def test_temporarios_nomes_distintos_sem_colisoes(self):
        self.sim.executar(programa(
            ins('move', t('t1'), c(1)), ins('move', t('t01'), c(2)),
            ins('move', t('outro'), c(3)),
            ins('add', g(0), t('t1'), t('t01')),
            ins('add', g(1), g(0), t('outro')),
        ))
        self.assertEqual(self.sim.dados.ler('global', 1), 6)

    def test_reinicializacao_apos_sucesso_e_falha(self):
        self.sim.executar(programa(ins('move', t('velho'), c(3)),
                                   ins('move', local(0), c(7)), quadro=2))
        self.sim.executar(programa(ins('move', g(0), c(9))))
        self.assertEqual(len(self.sim.obterRastro()), 3)
        self.assertEqual(self.sim.registradores.ler('$sp'), 0)
        with self.assertRaises(IndexError):
            self.sim.dados.ler('local', 0)
        with self.assertRaises(KeyError):
            self.sim.executar(programa(ins('move', g(0), t('velho'))))
        self.sim.executar(programa())
        self.assertEqual(len(self.sim.obterRastro()), 2)
        self.assertIsNone(self.sim.dados.ler('global', 0))

    def test_falha_contextualizada_preserva_causa_e_rastro(self):
        falha = InstrucaoTAC('div', (g(0), c(1), c(0)), linha=12, coluna=4)
        with self.assertRaises(ZeroDivisionError) as contexto:
            self.sim.executar(programa(ins('move', g(0), c(7)), falha,
                                       ins('move', g(0), c(99))))
        self.assertIn('PC 2', str(contexto.exception))
        self.assertIn('div, linha 12, coluna 4', str(contexto.exception))
        self.assertIsInstance(contexto.exception.__cause__, ZeroDivisionError)
        self.assertEqual(self.sim.dados.ler('global', 0), 7)
        self.assertIs(self.sim.ir, falha)
        self.assertEqual([pc for pc, _ in self.sim.obterRastro()], [0, 1])

    def test_programa_sem_halt_falha_na_busca(self):
        with self.assertRaises(IndexError) as contexto:
            self.sim.executar(ProgramaTAC(instrucoes=[label('main')]))
        self.assertIn('PC 1', str(contexto.exception))
        self.assertIsNone(self.sim.ir)
        self.assertEqual(len(self.sim.obterRastro()), 1)

    def test_programa_invalido_nao_executa(self):
        self.sim.executar(programa())
        with self.assertRaises(ValueError):
            self.sim.executar(programa(ins('goto', op('rotulo', 'ausente'))))
        self.assertEqual(self.sim.obterRastro(), [])
        self.assertIsNone(self.sim.ir)
        with self.assertRaises(TypeError):
            self.sim.executar(None)

    def test_metadados_invalidos(self):
        for tamanho in (True, -1, 1.5):
            with self.subTest(tamanho=tamanho):
                with self.assertRaises((TypeError, ValueError)):
                    self.sim.executar(programa(tamanho=tamanho))
                with self.assertRaises((TypeError, ValueError)):
                    self.sim.executar(programa(quadro=tamanho))
        for quadros in ([], {'main': 1}, {'main': (1, None)}, {'main': (1, [0])}):
            p = programa()
            p.quadros = quadros
            with self.assertRaises((TypeError, ValueError)):
                self.sim.executar(p)

    def test_operandos_invalidos(self):
        casos = [
            (ins('move', c(0), c(1)), ValueError),
            (ins('move', t(''), c(1)), TypeError),
            (ins('move', op('temporario', 0), c(1)), TypeError),
            (ins('move', g(0), op('funcao', 'f')), ValueError),
            (ins('move', g(0), op('desconhecido', 1)), ValueError),
            (ins('move', g(True), c(1)), TypeError),
            (ins('move', local(-1), c(1)), ValueError),
            (ins('move', g(4), c(1)), IndexError),
            (ins('load', g(0), local(0)), IndexError),
            (ins('load', g(0), c(0)), ValueError),
            (ins('addr', t('p'), g(0), c(True)), TypeError),
            (ins('addr', t('p'), g(0), c(0.5)), TypeError),
            (ins('addr', t('p'), g(0), c(-1)), ValueError),
            (ins('addr', t('p'), g(0), c(4)), IndexError),
            (ins('if_true', c('texto'), op('rotulo', 'main')), TypeError),
        ]
        for instrucao, erro in casos:
            with self.subTest(instrucao=instrucao):
                with self.assertRaises(erro):
                    self.sim.executar(programa(instrucao))

    def test_leitura_nao_inicializada(self):
        for instrucao in (ins('move', g(1), g(0)), ins('load', t('x'), g(0)),
                          ins('move', t('x'), local(0))):
            with self.subTest(instrucao=instrucao):
                with self.assertRaisesRegex(ValueError, 'não inicializado'):
                    self.sim.executar(programa(instrucao, quadro=1))
        with self.assertRaises(KeyError):
            self.sim.executar(programa(ins('move', g(0), t('ausente'))))

    def test_endereco_calculado_invalido_e_condicao_endereco(self):
        with self.assertRaises(TypeError):
            self.sim.executar(programa(ins('move', t('p'), c(1)),
                                       ins('store', t('p'), c(9))))
        with self.assertRaises(TypeError):
            self.sim.executar(programa(ins('addr', t('p'), g(0), c(0)),
                                       ins('if_true', t('p'), op('rotulo', 'main'))))

    def test_metodo_direto_valida_instrucao(self):
        with self.assertRaises(TypeError):
            self.sim.executarInstrucao(None)
        for instrucao in (ins('mystery'), ins('add', c(1))):
            with self.assertRaises(ValueError):
                self.sim.executarInstrucao(instrucao)

    def executarFuncoes(self, principal, funcoes, quadros=None, tamanho=4, quadro=0):
        p = programa(*principal, tamanho=tamanho, quadro=quadro)
        p.quadros.update(quadros or {})
        p.instrucoes.extend(funcoes)
        self.sim.executar(p)
        return p

    def test_funcao_sem_parametros_e_destinos(self):
        for destino in (g(0), local(0), t('resultado'), None):
            with self.subTest(destino=destino):
                principal = [ins('call', destino, op('funcao', 'f'), c(0))]
                if destino is not None:
                    principal.append(ins('move', g(1), destino))
                self.executarFuncoes(principal, [label('f'), ins('return', c(42))],
                                     {'f': (0, [])}, quadro=1)
                self.assertEqual(self.sim.registradores.ler('$v0'), 42)
                if destino is not None:
                    self.assertEqual(self.sim.dados.ler('global', 1), 42)
                self.assertEqual(self.sim.registradores.ler('$fp'), 0)
                self.assertEqual(self.sim.registradores.ler('$sp'), 1)
                self.assertIsNone(self.sim.registradores.ler('$ra'))

    def test_multiplos_parametros_ordem_e_deslocamentos(self):
        self.executarFuncoes([
            ins('move', t('arg'), c(7)), ins('param', t('arg')), ins('param', c(3)),
            ins('call', g(0), op('funcao', 'f'), c(2)),
        ], [label('f'), ins('sub', t('r'), local(2), local(0)), ins('return', t('r'))],
            {'f': (3, [2, 0])})
        self.assertEqual(self.sim.dados.ler('global', 0), 4)

    def test_retorno_sem_valor_e_destino_opcional(self):
        for retorno in (ins('return'), ins('return', None)):
            for destino in (None, g(0)):
                with self.subTest(retorno=retorno, destino=destino):
                    self.executarFuncoes([
                        ins('move', g(0), c(9)),
                        ins('call', destino, op('funcao', 'f'), c(0)),
                    ], [label('f'), retorno], {'f': (0, [])})
                    self.assertIsNone(self.sim.registradores.ler('$v0'))
                    self.assertEqual(self.sim.dados.ler('global', 0), 9 if destino is None else None)
        with self.assertRaisesRegex(ValueError, 'não inicializado'):
            self.executarFuncoes([
                ins('call', t('r'), op('funcao', 'f'), c(0)), ins('print', t('r')),
            ], [label('f'), ins('return')], {'f': (0, [])})

    def test_chamadas_aninhadas_preservam_locais_temporarios_e_ra(self):
        principal = [ins('move', local(0), c(10)), ins('move', t('x'), c(100)),
                     ins('call', t('r'), op('funcao', 'f'), c(0)),
                     ins('add', g(0), t('x'), t('r')), ins('move', g(1), local(0))]
        funcoes = [label('f'), ins('move', local(0), c(20)), ins('move', t('x'), c(200)),
                   ins('call', t('r'), op('funcao', 'h'), c(0)),
                   ins('add', t('r'), t('r'), t('x')),
                   ins('add', t('r'), t('r'), local(0)), ins('return', t('r')),
                   label('h'), ins('move', t('x'), c(999)), ins('return', c(3))]
        estados = []
        original = self.sim.executarInstrucao

        def observar(instrucao):
            original(instrucao)
            if instrucao.opcode in {'call', 'return'}:
                estados.append((instrucao.opcode, self.sim.pc,
                                tuple(self.sim.registradores.ler(n) for n in ('$fp', '$sp', '$ra', '$v0'))))

        with patch.object(self.sim, 'executarInstrucao', side_effect=observar):
            p = self.executarFuncoes(principal, funcoes, {'f': (1, []), 'h': (0, [])}, quadro=1)
        self.assertEqual(self.sim.dados.ler('global', 0), 323)
        self.assertEqual(self.sim.dados.ler('global', 1), 10)
        self.assertEqual(estados[0][2], (1, 2, 4, None))
        self.assertEqual(estados[1][2][:2], (2, 2))
        self.assertEqual(estados[2][2], (1, 2, 4, 3))
        self.assertEqual(estados[3][2], (0, 1, None, 223))
        self.assertEqual(estados[3][1], 4)
        self.assertEqual([i.opcode for _, i in self.sim.obterRastro()].count('call'), 2)
        self.assertEqual([i.opcode for _, i in self.sim.obterRastro()].count('return'), 2)
        self.assertEqual(self.sim.ir.opcode, 'halt')

    def test_recursao_fatorial(self):
        self.executarFuncoes([
            ins('param', c(6)), ins('call', g(0), op('funcao', 'fat'), c(1)),
        ], [label('fat'), ins('le', t('base'), local(0), c(1)),
            ins('if_true', t('base'), op('rotulo', 'base')),
            ins('move', t('n'), local(0)), ins('sub', t('menor'), local(0), c(1)),
            ins('param', t('menor')), ins('call', t('r'), op('funcao', 'fat'), c(1)),
            ins('mul', t('r'), t('n'), t('r')), ins('return', t('r')),
            label('base'), ins('return', c(1))], {'fat': (1, [0])})
        self.assertEqual(self.sim.dados.ler('global', 0), 720)
        self.assertEqual(self.sim.registradores.ler('$sp'), 0)
        self.assertIsNone(self.sim.registradores.ler('$ra'))
        rastro = self.sim.obterRastro()
        self.assertEqual(sum(i.opcode == 'call' for _, i in rastro), 6)
        self.assertEqual(sum(i.opcode == 'return' for _, i in rastro), 6)
        self.assertGreater(len(rastro), len(set(pc for pc, _ in rastro)))

    def test_quadros_zero_e_chamadas_consecutivas(self):
        self.executarFuncoes([
            ins('call', None, op('funcao', 'f'), c(0)),
            ins('call', g(0), op('funcao', 'f'), c(0)), ins('return', g(0)),
        ], [label('f'), ins('call', t('r'), op('funcao', 'h'), c(0)), ins('return', t('r')),
            label('h'), ins('return', c(8))], {'f': (0, []), 'h': (0, [])})
        self.assertEqual(self.sim.registradores.ler('$v0'), 8)
        self.assertEqual(self.sim.registradores.ler('$sp'), 0)
        with self.assertRaises(ValueError):
            self.sim.dados.liberarQuadro(0)

    def test_quantidade_argumentos_invalida(self):
        for quantidade, preparados in ((0, [1]), (2, [1]), (-1, []), (True, []), (1.0, []), (1, [])):
            with self.subTest(quantidade=quantidade, preparados=preparados):
                with self.assertRaises((TypeError, ValueError)):
                    self.executarFuncoes([
                        *(ins('param', c(v)) for v in preparados),
                        ins('call', None, op('funcao', 'f'), c(quantidade)),
                    ], [label('f'), ins('return')], {'f': (1, [0])}, quadro=2)
                self.assertEqual(self.sim.registradores.ler('$sp'), 2)
                self.assertIsNone(self.sim.registradores.ler('$ra'))

    def test_argumentos_pendentes_nao_vazam(self):
        for seguinte in (ins('halt'), ins('return'), label('extra'), ins('move', g(0), c(1))):
            with self.assertRaisesRegex(ValueError, 'Argumentos pendentes'):
                self.sim.executar(programa(ins('param', c(1)), seguinte))
        self.executarFuncoes([
            ins('param', c(9)), ins('call', g(0), op('funcao', 'f'), c(1)),
            ins('param', c(4)), ins('call', g(1), op('funcao', 'f'), c(1)),
        ], [label('f'), ins('return', local(0))], {'f': (1, [0])})
        self.assertEqual(self.sim.dados.ler('global', 0), 9)
        self.assertEqual(self.sim.dados.ler('global', 1), 4)

    def test_funcao_e_metadados_invalidos_preservam_contexto(self):
        casos = [(None, [], op('funcao', 'f')), ({}, [label('f')], op('funcao', 'f'))]
        for quadro in (None, 1, (1,), (True, []), (-1, []), (1, None),
                       (1, [True]), (1, [-1]), (1, [1]), (2, [0, 0])):
            casos.append(({'f': quadro}, [label('f')], op('funcao', 'f')))
        casos.append(({'f': (0, [])}, [label('f')], op('rotulo', 'f')))
        for quadros, corpo, funcao in casos:
            with self.subTest(quadros=quadros, funcao=funcao):
                with self.assertRaises((TypeError, ValueError, KeyError)):
                    self.executarFuncoes([
                        ins('move', local(0), c(12)), ins('move', t('x'), c(5)),
                        ins('call', g(0), funcao, c(0)),
                    ], corpo, quadros, quadro=1)
                self.assertEqual(self.sim.dados.ler('local', 0), 12)
                self.assertEqual(self.sim.registradores.ler(0), 5)
                self.assertEqual(self.sim.registradores.ler('$sp'), 1)
                self.assertIsNone(self.sim.registradores.ler('$ra'))

    def test_destino_call_invalido_antes_da_reserva(self):
        with self.assertRaises(ValueError):
            self.executarFuncoes([ins('call', c(1), op('funcao', 'f'), c(0))],
                                 [label('f'), ins('return')], {'f': (2, [])}, quadro=1)
        self.assertEqual(self.sim.registradores.ler('$sp'), 1)
        with self.assertRaises(IndexError):
            self.sim.dados.ler('local', 1)

    def test_retorno_main_com_e_sem_valor(self):
        for retorno, esperado in ((ins('return'), None), (ins('return', None), None),
                                  (ins('return', local(0)), 9)):
            self.sim.executar(programa(ins('move', local(0), c(9)), retorno,
                                       ins('move', g(0), c(999)), quadro=1))
            self.assertEqual(self.sim.registradores.ler('$v0'), esperado)
            self.assertEqual(self.sim.registradores.ler('$sp'), 0)
            self.assertEqual(self.sim.registradores.ler('$fp'), 0)
            self.assertIsNone(self.sim.registradores.ler('$ra'))
            self.assertIsNone(self.sim.dados.ler('global', 0))
            self.assertEqual(self.sim.ir.opcode, 'return')
            with self.assertRaises(IndexError):
                self.sim.dados.ler('local', 0)

    def test_endereco_do_chamador_preservado_na_funcao(self):
        self.executarFuncoes([
            ins('move', local(0), c(11)), ins('addr', t('p'), local(0), c(0)),
            ins('param', t('p')), ins('call', t('volta'), op('funcao', 'f'), c(1)),
            ins('load', g(0), t('volta')), ins('load', g(1), t('p')),
        ], [label('f'), ins('move', t('p'), local(0)), ins('store', t('p'), c(33)),
            ins('return', t('p'))], {'f': (1, [0])}, quadro=1)
        self.assertEqual(self.sim.dados.ler('global', 0), 33)
        self.assertEqual(self.sim.dados.ler('global', 1), 33)

    def test_deslocamento_direto_respeita_quadro_atual(self):
        with self.assertRaisesRegex(IndexError, 'quadro corrente'):
            self.executarFuncoes([ins('call', None, op('funcao', 'f'), c(0))],
                                 [label('f'), ins('move', local(0), c(1))],
                                 {'f': (0, [])}, quadro=2)
        # Mesmo quando a pilha foi ampliada externamente, não aumenta o quadro.
        self.sim.executar(programa(quadro=1))
        self.sim.dados.reservarQuadro(2)
        with self.assertRaisesRegex(IndexError, 'quadro corrente'):
            self.sim.executarInstrucao(ins('move', local(1), c(7)))

    def test_read_tipos_e_print(self):
        casos = [('42', 42, '42'), ('-12', -12, '-12'), ('2.5', 2.5, '2.5'),
                 ('1e2', 100.0, '100.0'), ('true', True, 'true'),
                 ('false', False, 'false'), ('a', 'a', 'a'),
                 ("'1'", '1', '1'), ("' '", ' ', ' '),
                 (r"'\n'", '\n', '\n')]
        for texto, esperado, saida in casos:
            with self.subTest(texto=texto):
                with patch('builtins.input', return_value=texto) as entrada, patch('builtins.print') as imprimir:
                    self.sim.executar(programa(ins('read', t('entrada')),
                                               ins('move', g(0), t('entrada')),
                                               ins('print', g(0))))
                entrada.assert_called_once_with()
                imprimir.assert_called_once_with(esperado if type(esperado) is not bool else saida)
                self.assertEqual(self.sim.dados.ler('global', 0), esperado)
                self.assertIs(type(self.sim.dados.ler('global', 0)), type(esperado))
        with patch('builtins.input', side_effect=['3', 'false']):
            self.sim.executar(programa(ins('read', local(0)), ins('read', g(0)),
                                       ins('move', g(1), local(0)), quadro=1))
        self.assertIs(self.sim.dados.ler('global', 0), False)
        self.assertEqual(self.sim.dados.ler('global', 1), 3)

    def test_read_erro_e_eof_contextualizados(self):
        for texto in ('', 'palavra', "'ab'", '1.2.3', 'nan', 'inf', '1e999', "'", "'\\xZZ'"):
            with self.subTest(texto=texto), patch('builtins.input', return_value=texto):
                with self.assertRaises(ValueError) as contexto:
                    self.sim.executar(programa(ins('move', g(0), c(9)), ins('read', g(0))))
                self.assertIn('PC 2 (read', str(contexto.exception))
                self.assertEqual(self.sim.dados.ler('global', 0), 9)
        with patch('builtins.input', side_effect=EOFError('fim')):
            with self.assertRaises(EOFError) as contexto:
                self.sim.executar(programa(ins('read', g(0))))
            self.assertIn('read', str(contexto.exception))
        with patch('builtins.input') as entrada:
            with self.assertRaises(ValueError):
                self.sim.executar(programa(ins('read', c(0))))
            entrada.assert_not_called()

    def test_print_rejeita_nao_inicializado_e_endereco(self):
        with patch('builtins.print') as imprimir:
            with self.assertRaises(ValueError):
                self.sim.executar(programa(ins('print', g(0))))
            with self.assertRaises(TypeError):
                self.sim.executar(programa(ins('addr', t('p'), g(0), c(0)), ins('print', t('p'))))
            imprimir.assert_not_called()
        with patch('builtins.print') as imprimir:
            self.sim.executar(programa(ins('print', c('texto')), ins('print', c(False))))
            self.assertEqual([chamada.args for chamada in imprimir.call_args_list], [('texto',), ('false',)])

    def test_reinicio_apos_falha_em_chamada_e_isolamento(self):
        with self.assertRaises(ZeroDivisionError):
            self.executarFuncoes([ins('param', c(1)), ins('call', None, op('funcao', 'f'), c(1))],
                                 [label('f'), ins('div', t('x'), c(1), c(0))], {'f': (1, [0])})
        self.executarFuncoes([ins('call', g(0), op('funcao', 'f'), c(0))],
                             [label('f'), ins('return', c(6))], {'f': (0, [])})
        self.assertEqual(self.sim.dados.ler('global', 0), 6)
        self.assertEqual(self.sim.registradores.ler('$sp'), 0)
        outra = Simulador()
        outra.executar(programa(ins('return', c(8))))
        self.assertEqual(self.sim.registradores.ler('$v0'), 6)
        self.assertEqual(outra.registradores.ler('$v0'), 8)
        self.assertNotEqual(self.sim.obterRastro(), outra.obterRastro())

    def test_halt_dentro_da_funcao_encerra_programa(self):
        self.executarFuncoes([ins('call', None, op('funcao', 'f'), c(0)), ins('move', g(0), c(8))],
                             [label('f'), ins('halt')], {'f': (1, [])})
        self.assertIsNone(self.sim.dados.ler('global', 0))
        self.assertEqual(self.sim.ir.opcode, 'halt')
        self.assertEqual(self.sim.registradores.ler('$sp'), 1)

    def test_rastro_exercita_todos_os_27_opcodes(self):
        principal = [ins('read', t('x')), ins('move', g(0), t('x'))]
        for opcode in ('add', 'sub', 'mul', 'div', 'mod', 'eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            principal.append(ins(opcode, t('r'), c(7), c(3)))
        principal.extend([
            ins('neg', t('r'), c(2)), ins('not', t('r'), c(0)),
            ins('addr', t('p'), g(0), c(1)), ins('store', t('p'), c(8)),
            ins('load', t('r'), t('p')), ins('print', t('r')),
            ins('if_true', c(False), op('rotulo', 'fim')),
            ins('if_false', c(True), op('rotulo', 'fim')),
            ins('goto', op('rotulo', 'fim')), label('fim'),
            ins('param', c(5)), ins('call', t('r'), op('funcao', 'f'), c(1)),
        ])
        with patch('builtins.input', return_value='4'), patch('builtins.print'):
            self.executarFuncoes(principal, [label('f'), ins('return', local(0))], {'f': (1, [0])})
        executados = {i.opcode for _, i in self.sim.obterRastro()}
        self.assertEqual(executados, set(CONTRATOS_TAC))


if __name__ == '__main__':
    unittest.main()
