import sys
import unittest
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.simulador.core.BancoRegistradores import BancoRegistradores


class BancoRegistradoresTests(unittest.TestCase):
    def setUp(self):
        self.banco = BancoRegistradores()

    def test_inicializacao(self):
        for chave in ("$zero", "$sp", "$fp"):
            self.assertEqual(self.banco.ler(chave), 0)
        for chave in ("$ra", "$v0"):
            self.assertIsNone(self.banco.ler(chave))
        with self.assertRaises(KeyError):
            self.banco.ler(0)

    def test_leitura_escrita_e_sobrescrita(self):
        for chave in ("$sp", "$fp", "$ra", "$v0", 0, 100):
            with self.subTest(chave=chave):
                valor = object()
                self.banco.escrever(chave, valor)
                self.assertIs(self.banco.ler(chave), valor)
                self.banco.escrever(chave, None)
                self.assertIsNone(self.banco.ler(chave))

    def test_zero_somente_leitura(self):
        for valor in (0, 1, None):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    self.banco.escrever("$zero", valor)
                self.assertEqual(self.banco.ler("$zero"), 0)

    def test_chaves_invalidas(self):
        casos = [(True, TypeError), (False, TypeError), (1.0, TypeError),
                 (None, TypeError), ([], TypeError), (-1, ValueError),
                 ("$pc", KeyError), ("t0", KeyError), ("0", KeyError),
                 ("", KeyError), ("$r0", KeyError)]
        for chave, erro in casos:
            with self.subTest(chave=chave):
                with self.assertRaises(erro):
                    self.banco.ler(chave)
                with self.assertRaises(erro):
                    self.banco.escrever(chave, 9)

    def test_troca_preserva_especiais_e_isola_dicionarios(self):
        self.banco.escrever(0, "anterior")
        self.banco.escrever("$fp", 7)
        valor = []
        novos = {1: valor}
        anteriores = self.banco.trocarTemporarios(novos)
        self.assertEqual(anteriores, {0: "anterior"})
        novos[1] = "alterado"
        anteriores[0] = "alterado"
        self.assertIs(self.banco.ler(1), valor)
        self.assertEqual(self.banco.ler("$fp"), 7)
        with self.assertRaises(KeyError):
            self.banco.ler(0)
        self.assertEqual(self.banco.trocarTemporarios({}), {1: valor})
        with self.assertRaises(KeyError):
            self.banco.ler(1)

    def test_troca_invalida_nao_altera_estado(self):
        self.banco.escrever(0, "preservado")
        casos = [(None, TypeError), ([], TypeError), ({True: 1}, TypeError),
                 ({"t0": 1}, TypeError), ({1.0: 1}, TypeError),
                 ({2: "valido", -1: "invalido"}, ValueError)]
        for novos, erro in casos:
            with self.subTest(novos=novos):
                with self.assertRaises(erro):
                    self.banco.trocarTemporarios(novos)
                self.assertEqual(self.banco.ler(0), "preservado")
                with self.assertRaises(KeyError):
                    self.banco.ler(2)

    def test_isolamento_de_instancias(self):
        outro = BancoRegistradores()
        self.banco.escrever("$sp", 8)
        self.banco.escrever(0, 3)
        self.assertEqual(outro.ler("$sp"), 0)
        with self.assertRaises(KeyError):
            outro.ler(0)

    def test_restauracao_de_chamadas_aninhadas(self):
        self.banco.escrever(0, "main")
        principal = self.banco.trocarTemporarios({})
        self.banco.escrever(0, "chamada")
        chamada = self.banco.trocarTemporarios({})
        self.banco.escrever(0, "recursiva")
        self.assertEqual(self.banco.trocarTemporarios(chamada), {0: "recursiva"})
        self.assertEqual(self.banco.ler(0), "chamada")
        self.banco.trocarTemporarios(principal)
        self.assertEqual(self.banco.ler(0), "main")
        principal[0] = "alterado"
        self.assertEqual(self.banco.ler(0), "main")


if __name__ == "__main__":
    unittest.main()
