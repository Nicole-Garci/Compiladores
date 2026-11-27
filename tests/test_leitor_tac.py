import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.tac.ContratoTAC import CONTRATOS_TAC
from src.tac.LeitorTAC import lerTAC, carregarTAC, diagnosticosTAC, ErroLeituraTAC
from src.tac.ProgramaTAC import ProgramaTAC


class LeitorTACTests(unittest.TestCase):
    def cli(self, caminho, entrada=''):
        return subprocess.run([sys.executable, '-B', '-m', 'src.simulador', str(caminho)],
                              input=entrada, text=True, capture_output=True, cwd=RAIZ, timeout=10)

    def test_equivalencia_modelos_tipos_saida_e_rastro_completo(self):
        for nome, entrada, total in [('expressao', '', 12), ('matriz', '', 107),
                                     ('structs', '', 35), ('fibonacci', '8\n', 539)]:
            with self.subTest(nome=nome):
                base = RAIZ / 'tests/tac' / nome
                a = ProgramaTAC.carregar(str(base.with_suffix('.json')))
                b = carregarTAC(str(base.with_suffix('.tac')))
                self.assertEqual((a.entrada, a.tamanhoDados, a.quadros),
                                 (b.entrada, b.tamanhoDados, b.quadros))
                self.assertEqual(diagnosticosTAC(b), [])
                self.assertEqual(len(a.instrucoes), len(b.instrucoes))
                for x, y in zip(a.instrucoes, b.instrucoes):
                    self.assertEqual((x.opcode, x.operandos), (y.opcode, y.operandos))
                    for ox, oy in zip(x.operandos, y.operandos):
                        if ox is not None:
                            self.assertIs(type(ox.valor), type(oy.valor))
                ja = self.cli(base.with_suffix('.json'), entrada)
                ta = self.cli(base.with_suffix('.tac'), entrada)
                self.assertEqual((ta.returncode, ta.stderr), (0, ''))
                self.assertEqual((ja.returncode, ja.stderr), (0, ''))
                self.assertEqual(ja.stdout, ta.stdout)
                self.assertIn(f'Total de instruções executadas: {total}', ta.stdout)

    def test_todos_opcodes_e_opcionais(self):
        self.assertEqual(len(CONTRATOS_TAC), 27)
        for opcode, contrato in CONTRATOS_TAC.items():
            ops = ['constante[1]'] * contrato.maximoOperandos
            for indice in contrato.operandosOpcionais:
                ops[indice] = '_'
            i = lerTAC(opcode + ' ' + ', '.join(ops)).instrucoes[0]
            self.assertEqual(i.validar(), [])
        self.assertEqual(lerTAC('return').instrucoes[0].operandos, ())
        self.assertEqual(lerTAC('return _').instrucoes[0].operandos, (None,))

    def test_paraString_indices_e_localizacao(self):
        original = ProgramaTAC.carregar(str(RAIZ / 'tests/tac/structs.json'))
        lido = lerTAC(original.paraString())
        self.assertEqual(lido.paraString(), original.paraString())
        i = lerTAC('\n # comentário\n  99: halt # fim').instrucoes[0]
        self.assertEqual((i.linha, i.coluna), (3, 7))

    def test_literais_e_delimitadores_em_aspas(self):
        casos = [('1', 1), ('-2', -2), ('+3', 3), ('1e2', 100.0),
                 ('.5', .5), ('-3.5', -3.5), ('true', True), ('False', False),
                 ('A', 'A'), ("'1'", '1'), ('"true"', 'true'),
                 ("']'", ']'), ("'#'", '#'), ("','", ','),
                 (r"'\n'", '\n'), (r"'\''", "'"), ('"á"', 'á')]
        for literal, esperado in casos:
            with self.subTest(literal=literal):
                valor = lerTAC(f'print constante[{literal}] # fim').instrucoes[0].operandos[0].valor
                self.assertEqual(valor, esperado)
                self.assertIs(type(valor), type(esperado))
        self.assertEqual(lerTAC('goto rotulo[true]').instrucoes[0].operandos[0].valor, 'true')

    def test_metadados_e_padroes(self):
        p = lerTAC('.entrada inicio\n.dados 8\n.quadro inicio 0 []\n.quadro f 4 [0, 2]\n')
        self.assertEqual((p.entrada, p.tamanhoDados, p.quadros),
                         ('inicio', 8, {'inicio': (0, []), 'f': (4, [0, 2])}))
        self.assertEqual(lerTAC('').entrada, 'main')

    def test_sintaxe_invalida_com_localizacao(self):
        for texto in ['print constante[1', 'print constante[]', "print constante['x]",
                      'print constante[1e999]', 'print constante[2x]',
                      'add temporario[t] constante[1]', 'return _,', 'halt lixo',
                      '.foo 1', '.dados -1', '.dados true', '.dados 1 lixo',
                      '.quadro f 1 [0,]', '.quadro f 2 [true]', '.quadro f 2',
                      '.dados 1\n.dados 2', '.quadro f 0 []\n.quadro f 0 []']:
            with self.subTest(texto=texto):
                with self.assertRaises(ErroLeituraTAC) as cm:
                    lerTAC(texto)
                self.assertGreater(cm.exception.linha, 0)
                self.assertGreater(cm.exception.coluna, 0)
        with self.assertRaisesRegex(ErroLeituraTAC, 'linha 2, coluna 20'):
            lerTAC('# cabeçalho\n  print constante[1')

    def test_validacao_reutilizada_e_localizada(self):
        for texto, mensagem in [('label rotulo[main]\nxyz', 'Opcode TAC desconhecido'),
                                 ('label rotulo[main]\nadd', 'espera 3'),
                                 ('label rotulo[main]\nprint _', 'obrigatório'),
                                 ('label rotulo[main]\ngoto rotulo[x]', 'não definido'),
                                 ('label rotulo[main]\nlabel rotulo[main]', 'duplicado')]:
            erros = diagnosticosTAC(lerTAC(texto))
            self.assertTrue(any('linha 2, coluna 1' in e and mensagem in e for e in erros), erros)
        self.assertIn('linha 1, coluna 1', diagnosticosTAC(lerTAC(''))[0])

    def test_cli_codigos_e_contexto(self):
        with TemporaryDirectory() as pasta:
            p = Path(pasta) / 'arquivo com espaços.tac'
            casos = [('print constante[', 2, 'linha 1, coluna'),
                     ('label rotulo[main]\nxyz', 1, 'linha 2, coluna 1'),
                     ('label rotulo[main]\ndiv temporario[t], constante[1], constante[0]',
                      1, 'PC 1 (div, linha 2, coluna 1)'),
                     ('label rotulo[main]\nreturn', 0, '')]
            for texto, codigo, mensagem in casos:
                p.write_text(texto, encoding='utf-8')
                r = self.cli(p)
                self.assertEqual(r.returncode, codigo, r.stderr)
                self.assertIn(mensagem, r.stderr)
                self.assertNotIn('Traceback', r.stderr)
            p.write_bytes(b'\xff')
            self.assertEqual(self.cli(p).returncode, 2)
        self.assertEqual(self.cli(RAIZ / 'tests/tac/soma.tac').returncode, 0)


if __name__ == '__main__':
    unittest.main()
