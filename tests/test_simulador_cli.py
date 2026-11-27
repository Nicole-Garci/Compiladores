import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


class SimuladorCLITests(unittest.TestCase):
    def executarCLI(self, *argumentos, entrada=''):
        return subprocess.run(
            [sys.executable, '-B', '-m', 'src.simulador', *map(str, argumentos)],
            cwd=RAIZ_PROJETO, input=entrada, text=True, encoding='utf-8',
            capture_output=True, timeout=10,
        )

    def test_quatro_exemplos_saida_e_rastro(self):
        casos = [
            ('expressao.json', '', '-14\n-3.5\n', 12),
            ('matriz.json', '', '36\n', 107),
            ('structs.json', '', '42\n2.5\ntrue\nA\n15\n', 35),
            ('fibonacci.json', '2\n', '1\n', 27),
        ]
        for nome, entrada, saida, total in casos:
            with self.subTest(nome=nome):
                caminho = Path('tests/tac') / nome
                resultado = self.executarCLI(caminho, entrada=entrada)
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                self.assertEqual(resultado.stderr, '')
                self.assertTrue(resultado.stdout.startswith(saida + '\nRastro de execução:\n'))
                self.assertTrue(resultado.stdout.endswith(f'Total de instruções executadas: {total}\n'))
                linhas = re.findall(r'^(\d+): PC (\d+) \| (.+)$', resultado.stdout, re.MULTILINE)
                self.assertEqual(len(linhas), total)
                self.assertEqual([int(ordem) for ordem, _, _ in linhas], list(range(1, total + 1)))
                programa = ProgramaTAC.carregar(str(RAIZ_PROJETO / caminho))
                for _, pc, texto in linhas:
                    self.assertEqual(texto, programa.instrucoes[int(pc)].paraString())
                if nome == 'fibonacci.json':
                    self.assertEqual([int(pc) for _, pc, _ in linhas],
                                     [0, 1, 2, 3, 6, 7, 8, 9, 10, 11,
                                      6, 7, 8, 17, 18, 12, 13, 14,
                                      6, 7, 8, 17, 18, 15, 16, 4, 5])
                if nome == 'matriz.json':
                    self.assertEqual(sum(pc == '7' for _, pc, _ in linhas), 8)

    def test_help(self):
        resultado = self.executarCLI('--help')
        self.assertEqual(resultado.returncode, 0)
        self.assertIn('arquivo', resultado.stdout)
        self.assertIn('--help', resultado.stdout)
        self.assertIn('TAC JSON', resultado.stdout)
        self.assertEqual(resultado.stderr, '')

    def test_argumentos_invalidos(self):
        for argumentos in ((), ('--inexistente',)):
            with self.subTest(argumentos=argumentos):
                resultado = self.executarCLI(*argumentos)
                self.assertEqual(resultado.returncode, 2)
                self.assertNotEqual(resultado.stderr, '')
                self.assertEqual(resultado.stdout, '')

    def test_arquivo_inexistente_e_diretorio(self):
        with TemporaryDirectory() as pasta:
            for caminho in (Path(pasta) / 'ausente.json', Path(pasta)):
                resultado = self.executarCLI(caminho)
                self.assertEqual(resultado.returncode, 2)
                self.assertIn('Erro ao carregar TAC', resultado.stderr)
                self.assertEqual(resultado.stdout, '')

    def test_json_estrutura_versao_e_codificacao_invalidos(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'invalido.json'
            for conteudo in (b'{', b'[]', b'{"versao": 2}', b'{"versao": 1}', b'\xff'):
                with self.subTest(conteudo=conteudo):
                    caminho.write_bytes(conteudo)
                    resultado = self.executarCLI(caminho)
                    self.assertEqual(resultado.returncode, 2)
                    self.assertIn('Erro ao carregar TAC', resultado.stderr)
                    self.assertNotIn('Traceback', resultado.stderr)
                    self.assertEqual(resultado.stdout, '')

    def test_tac_invalido(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'programa.json'
            ProgramaTAC(instrucoes=[InstrucaoTAC('desconhecido')]).salvar(str(caminho))
            resultado = self.executarCLI(caminho)
            self.assertEqual(resultado.returncode, 1)
            self.assertIn('Opcode TAC desconhecido', resultado.stderr)
            self.assertIn("Rótulo de entrada 'main' não definido", resultado.stderr)
            self.assertEqual(resultado.stdout, '')

    def test_erro_execucao_contextualizado_sem_rastro_de_sucesso(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'erro.json'
            programa = ProgramaTAC(instrucoes=[
                InstrucaoTAC('label', (OperandoTAC('rotulo', 'main'),)),
                InstrucaoTAC('print', (OperandoTAC('constante', 'antes'),)),
                InstrucaoTAC('div', (OperandoTAC('temporario', 'x'),
                                     OperandoTAC('constante', 1), OperandoTAC('constante', 0)),
                            linha=8, coluna=3),
                InstrucaoTAC('halt'),
            ])
            programa.salvar(str(caminho))
            resultado = self.executarCLI(caminho)
            self.assertEqual(resultado.returncode, 1)
            self.assertEqual(resultado.stdout, 'antes\n')
            self.assertIn('PC 2 (div, linha 8, coluna 3)', resultado.stderr)
            self.assertNotIn('Traceback', resultado.stderr)
            self.assertNotIn('Rastro', resultado.stdout)

    def test_entrada_invalida_e_fim_de_arquivo(self):
        for entrada in ('palavra\n', ''):
            with self.subTest(entrada=entrada):
                resultado = self.executarCLI('tests/tac/fibonacci.json', entrada=entrada)
                self.assertEqual(resultado.returncode, 1)
                self.assertIn('PC 1 (read', resultado.stderr)
                self.assertNotIn('Traceback', resultado.stderr)
                self.assertEqual(resultado.stdout, '')

    def test_caminho_com_espacos_e_execucao_sem_print(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'programa sem print.json'
            ProgramaTAC(instrucoes=[
                InstrucaoTAC('label', (OperandoTAC('rotulo', 'main'),)),
                InstrucaoTAC('halt'),
            ]).salvar(str(caminho))
            resultado = self.executarCLI(caminho)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual(resultado.stdout,
                             '\nRastro de execução:\n1: PC 0 | label rotulo[main]\n'
                             '2: PC 1 | halt\nTotal de instruções executadas: 2\n')
            self.assertEqual(resultado.stderr, '')


if __name__ == '__main__':
    unittest.main()
