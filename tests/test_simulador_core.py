import sys
import unittest
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.simulador.core.BancoRegistradores import BancoRegistradores
from src.simulador.core.MemoriaDados import MemoriaDados
from src.simulador.core.MemoriaInstrucoes import MemoriaInstrucoes
from src.simulador.core.UnidadeOperacoes import UnidadeOperacoes
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.tac.ProgramaTAC import ProgramaTAC


def op(categoria, valor):
    return OperandoTAC(categoria, valor)


class SimuladorCoreTests(unittest.TestCase):
    def test_tac_operacoes_dados_e_destino_de_salto(self):
        programa = ProgramaTAC(tamanhoDados=1, instrucoes=[
            InstrucaoTAC('label', (op('rotulo', 'main'),)),
            InstrucaoTAC('add', (op('temporario', 't0'), op('constante', 7), op('constante', 5))),
            InstrucaoTAC('store', (op('global', 0), op('temporario', 't0'))),
            InstrucaoTAC('goto', (op('rotulo', 'fim'),)),
            InstrucaoTAC('label', (op('rotulo', 'fim'),)),
            InstrucaoTAC('halt'),
        ])
        instrucoes = MemoriaInstrucoes()
        dados = MemoriaDados(programa.tamanhoDados)
        banco = BancoRegistradores()
        unidade = UnidadeOperacoes()
        instrucoes.carregar(programa)
        pc = instrucoes.resolverRotulo(programa.entrada)
        self.assertEqual(instrucoes.buscar(pc).opcode, 'label')
        soma = instrucoes.buscar(pc + 1)
        self.assertEqual(soma.operandos[0].valor, 't0')
        banco.escrever(0, unidade.executar(soma.opcode, soma.operandos[1].valor, soma.operandos[2].valor))
        escrita = instrucoes.buscar(pc + 2)
        destino = escrita.operandos[0]
        dados.escrever(destino.categoria, destino.valor, banco.ler(0))
        self.assertEqual(dados.ler('global', 0), 12)
        banco.escrever(1, unidade.executar('mul', dados.ler('global', 0), 2))
        self.assertEqual(banco.ler(1), 24)
        salto = instrucoes.buscar(pc + 3)
        pc = instrucoes.resolverRotulo(salto.operandos[0].valor)
        self.assertEqual(pc, 4)
        self.assertEqual(instrucoes.buscar(pc).opcode, 'label')
        self.assertEqual(instrucoes.buscar(pc + 1).opcode, 'halt')

    def test_chamadas_aninhadas_restauram_quadros_e_registradores(self):
        programa = ProgramaTAC(quadros={'main': (1, []), 'f': (1, [])}, instrucoes=[
            InstrucaoTAC('label', (op('rotulo', 'main'),)),
            InstrucaoTAC('call', (op('temporario', 't1'), op('funcao', 'f'), op('constante', 0))),
            InstrucaoTAC('halt'),
            InstrucaoTAC('label', (op('rotulo', 'f'),)),
            InstrucaoTAC('neg', (op('temporario', 't0'), op('constante', -8))),
            InstrucaoTAC('return', (op('temporario', 't0'),)),
        ])
        instrucoes = MemoriaInstrucoes()
        instrucoes.carregar(programa)
        dados = MemoriaDados(programa.tamanhoDados)
        banco = BancoRegistradores()
        unidade = UnidadeOperacoes()
        baseMain = dados.reservarQuadro(programa.quadros['main'][0])
        banco.escrever('$fp', baseMain)
        banco.escrever('$sp', baseMain + 1)
        banco.escrever(0, 10)
        dados.escrever('local', baseMain, 10)
        estadoMain = tuple(banco.ler(nome) for nome in ('$fp', '$sp', '$ra'))
        temporariosMain = banco.trocarTemporarios({})
        baseFilho = dados.reservarQuadro(programa.quadros['f'][0])
        banco.escrever('$fp', baseFilho)
        banco.escrever('$sp', baseFilho + 1)
        banco.escrever('$ra', 2)
        banco.escrever(0, 20)
        dados.escrever('local', banco.ler('$fp'), 20)
        estadoFilho = tuple(banco.ler(nome) for nome in ('$fp', '$sp', '$ra'))
        temporariosFilho = banco.trocarTemporarios({})
        baseNeto = dados.reservarQuadro(programa.quadros['f'][0])
        banco.escrever('$fp', baseNeto)
        banco.escrever('$sp', baseNeto + 1)
        banco.escrever('$ra', 5)
        instrucao = instrucoes.buscar(instrucoes.resolverRotulo('f') + 1)
        banco.escrever(0, unidade.executar(instrucao.opcode, instrucao.operandos[1].valor))
        dados.escrever('local', banco.ler('$fp'), banco.ler(0))
        self.assertEqual(dados.ler('local', baseNeto), 8)
        banco.escrever('$v0', banco.ler(0))
        dados.liberarQuadro(baseNeto)
        banco.trocarTemporarios(temporariosFilho)
        for nome, valor in zip(('$fp', '$sp', '$ra'), estadoFilho):
            banco.escrever(nome, valor)
        self.assertEqual(banco.ler(0), 20)
        self.assertEqual(dados.ler('local', banco.ler('$fp')), 20)
        self.assertEqual(tuple(banco.ler(n) for n in ('$fp', '$sp', '$ra')), estadoFilho)
        with self.assertRaises(IndexError):
            dados.ler('local', baseNeto)
        dados.liberarQuadro(baseFilho)
        banco.trocarTemporarios(temporariosMain)
        for nome, valor in zip(('$fp', '$sp', '$ra'), estadoMain):
            banco.escrever(nome, valor)
        banco.escrever(1, banco.ler('$v0'))
        self.assertEqual((banco.ler(0), banco.ler(1)), (10, 8))
        self.assertEqual(dados.ler('local', baseMain), 10)
        self.assertEqual(tuple(banco.ler(n) for n in ('$fp', '$sp', '$ra')), estadoMain)
        self.assertEqual(banco.ler('$zero'), 0)
        dados.liberarQuadro(baseMain)
        with self.assertRaises(IndexError):
            dados.ler('local', 0)


if __name__ == '__main__':
    unittest.main()
