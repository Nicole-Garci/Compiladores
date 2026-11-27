import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.simulador.Simulador import Simulador
from src.tac.ProgramaTAC import ProgramaTAC
from src.semantico.models.TipoSemantico import (
    TIPO_INT, TIPO_FLOAT, TIPO_BOOL, TIPO_CHAR, tipoVetor,
)
# Reutiliza somente os construtores TAC; não importa a classe de testes.
from test_simulador import c, t, g, local, op, ins, label, programa

EXEMPLOS = Path(__file__).resolve().parent / 'tac'


class SimuladorFuncionalTests(unittest.TestCase):
    def executarExemplo(self, nome, entrada=''):
        tac = ProgramaTAC.carregar(str(EXEMPLOS / nome))
        self.assertEqual(tac.validar(), [])
        simulador = Simulador()
        saida = io.StringIO()
        # Usa input/print reais sobre streams controlados: inclui quebras de linha.
        with patch('sys.stdin', io.StringIO(entrada)), redirect_stdout(saida):
            simulador.executar(tac)
        return tac, simulador, saida.getvalue()

    def test_expressao_composta_serializada(self):
        tac, sim, saida = self.executarExemplo('expressao.json')
        # ((17 - 5) * (-7 + 2)) / 5 + (-17 % 5), com divisão truncada.
        self.assertEqual(saida, '-14\n-3.5\n')
        self.assertEqual(sim.dados.ler('global', 0), -14)
        self.assertEqual(sim.dados.ler('global', 1), -3.5)
        self.assertEqual(sim.obterRastro(), list(enumerate(tac.instrucoes)))

    def test_lacos_aninhados_vetor_linearizado_e_rastro_completo(self):
        tac, sim, saida = self.executarExemplo('matriz.json')
        self.assertEqual(saida, '36\n')
        self.assertEqual([sim.dados.ler('global', i) for i in range(7)],
                         [0, 1, 2, 10, 11, 12, 36])
        # Oráculo por blocos conhecidos, sem interpretar opcodes ou condições.
        indices = [0, 1, 2]
        for _ in range(2):
            indices += list(range(3, 7))
            for _ in range(3):
                indices += list(range(7, 20))
            indices += [7, 8, 9, 20, 21, 22]
        indices += [3, 4, 5, 23, 24, 25]
        self.assertEqual(sim.obterRastro(), [(pc, tac.instrucoes[pc]) for pc in indices])
        self.assertEqual(sim.pc, 26)
        self.assertIs(sim.ir, tac.instrucoes[25])

    def test_structs_campos_e_vetor_interno_conforme_layout(self):
        # Sem executar o analisador: verifica as larguras do modelo existente.
        tipos = (TIPO_INT, TIPO_FLOAT, TIPO_BOOL, TIPO_CHAR, tipoVetor(TIPO_INT, 2))
        deslocamentos = []
        tamanho = 0
        for tipo in tipos:
            deslocamentos.append(tamanho)
            tamanho += tipo.tamanhoBytes
        self.assertEqual((deslocamentos, tamanho), ([0, 1, 2, 3, 4], 6))
        _, sim, saida = self.executarExemplo('structs.json')
        self.assertEqual(saida, '42\n2.5\ntrue\nA\n15\n')
        valores = [sim.dados.ler('global', i) for i in range(6, 12)]
        self.assertEqual(valores, [42, 2.5, True, 'A', 7, 8])
        self.assertEqual([type(v) for v in valores], [int, float, bool, str, int, int])
        self.assertEqual(sim.dados.ler('global', 0), 11)
        self.assertTrue(all(sim.dados.ler('global', i) is None for i in range(1, 6)))

    def test_fibonacci_duas_chamadas_por_ativacao_e_rastro(self):
        # Inclui os dois casos-base e recursão ramificada, além do fatorial já existente.
        for n, esperado, chamadas in ((0, 0, 1), (1, 1, 1), (2, 1, 3), (8, 21, 67)):
            with self.subTest(n=n):
                tac, sim, saida = self.executarExemplo('fibonacci.json', f'{n}\n')
                self.assertEqual(saida, f'{esperado}\n')
                self.assertEqual(sim.dados.ler('global', 0), esperado)
                self.assertEqual(sim.registradores.ler('$v0'), esperado)
                self.assertEqual(tuple(sim.registradores.ler(r) for r in ('$zero', '$fp', '$sp', '$ra')),
                                 (0, 0, 0, None))
                rastro = sim.obterRastro()
                self.assertEqual(sum(i.opcode == 'call' for _, i in rastro), chamadas)
                self.assertEqual(sum(i.opcode == 'return' for _, i in rastro), chamadas + 1)
                with self.assertRaises(IndexError):
                    sim.dados.ler('local', 0)
                if n == 2:
                    indices = [0, 1, 2, 3, 6, 7, 8, 9, 10, 11,
                               6, 7, 8, 17, 18, 12, 13, 14,
                               6, 7, 8, 17, 18, 15, 16, 4, 5]
                    self.assertEqual(rastro, [(pc, tac.instrucoes[pc]) for pc in indices])
                    self.assertEqual(sim.pc, 6)
                    self.assertIs(sim.ir, tac.instrucoes[5])

    def test_reutilizacao_de_quadro_limpa_valores_e_preserva_chamador(self):
        tac = programa(ins('move', local(0), c(123)),
                       ins('call', g(0), op('funcao', 'primeira'), c(0)),
                       ins('call', g(1), op('funcao', 'segunda'), c(0)), quadro=1)
        tac.quadros.update({'primeira': (2, []), 'segunda': (2, [])})
        tac.instrucoes.extend([
            label('primeira'), ins('move', local(0), c(55)), ins('move', local(1), c(66)),
            ins('return', local(0)), label('segunda'), ins('load', t('velho'), local(1)),
            ins('return', t('velho')),
        ])
        sim = Simulador()
        reservas = []
        despachar = sim.executarInstrucao

        def observar(instrucao):
            despachar(instrucao)
            if instrucao.opcode == 'call':
                base = sim.registradores.ler('$fp')
                reservas.append((base, sim.dados.ler('local', base), sim.dados.ler('local', base + 1)))

        with patch.object(sim, 'executarInstrucao', side_effect=observar):
            with self.assertRaisesRegex(ValueError, 'não inicializado') as contexto:
                sim.executar(tac)
        self.assertEqual(reservas, [(1, None, None), (1, None, None)])
        self.assertEqual(sim.dados.ler('local', 0), 123)
        self.assertEqual(sim.dados.ler('global', 0), 55)
        self.assertIsNone(sim.dados.ler('global', 1))
        self.assertIn('load', str(contexto.exception))
        self.assertEqual(sim.obterRastro()[-1][1].opcode, 'label')

    def test_exemplos_preservam_serializacao_e_tipos(self):
        nomes = {'expressao.json', 'matriz.json', 'structs.json', 'fibonacci.json'}
        self.assertEqual({p.name for p in EXEMPLOS.glob('*.json')}, nomes)
        with TemporaryDirectory() as pasta:
            for nome in sorted(nomes):
                with self.subTest(nome=nome):
                    original = ProgramaTAC.carregar(str(EXEMPLOS / nome))
                    destino = str(Path(pasta) / nome)
                    original.salvar(destino)
                    copia = ProgramaTAC.carregar(destino)
                    self.assertEqual(original, copia)
                    self.assertEqual(copia.validar(), [])
                    for antes, depois in zip(original.instrucoes, copia.instrucoes):
                        for a, b in zip(antes.operandos, depois.operandos):
                            if a is not None:
                                self.assertIs(type(a.valor), type(b.valor))

    def test_erro_de_saida_dentro_da_funcao_preserva_causa_e_contexto(self):
        tac = programa(ins('call', None, op('funcao', 'f'), c(0)), quadro=1)
        tac.quadros['f'] = (1, [])
        falha = ins('print', c(7))
        tac.instrucoes.extend([label('f'), falha, ins('return')])
        sim = Simulador()
        with patch('builtins.print', side_effect=OSError('saída indisponível')):
            with self.assertRaises(OSError) as contexto:
                sim.executar(tac)
        self.assertIn('PC 4 (print', str(contexto.exception))
        self.assertIsInstance(contexto.exception.__cause__, OSError)
        self.assertIs(sim.ir, falha)
        self.assertEqual([pc for pc, _ in sim.obterRastro()], [0, 1, 3])
        self.assertEqual(sim.registradores.ler('$fp'), 1)
        self.assertEqual(sim.registradores.ler('$ra'), 2)
        sim.executar(programa(ins('return', c(0))))
        self.assertEqual(sim.registradores.ler('$sp'), 0)
        self.assertIsNone(sim.registradores.ler('$ra'))


if __name__ == '__main__':
    unittest.main()
