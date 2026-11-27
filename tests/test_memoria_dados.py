import sys
import unittest
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.simulador.core.MemoriaDados import MemoriaDados


class MemoriaDadosTests(unittest.TestCase):
    def test_memoria_inicial_vazia(self):
        memoria = MemoriaDados()
        for regiao in ("global", "local"):
            with self.assertRaises(IndexError):
                memoria.ler(regiao, 0)
            with self.assertRaises(IndexError):
                memoria.escrever(regiao, 0, 1)
        with self.assertRaises(ValueError):
            memoria.liberarQuadro(0)

    def test_posicoes_iniciais_e_regioes_independentes(self):
        memoria = MemoriaDados(2)
        self.assertEqual(memoria.reservarQuadro(2), 0)
        for regiao in ("global", "local"):
            for endereco in range(2):
                self.assertIsNone(memoria.ler(regiao, endereco))
        memoria.escrever("global", 0, "global")
        memoria.escrever("local", 0, "local")
        self.assertEqual(memoria.ler("global", 0), "global")
        self.assertEqual(memoria.ler("local", 0), "local")
        for regiao in ("global", "local"):
            valor = []
            memoria.escrever(regiao, 1, valor)
            self.assertIs(memoria.ler(regiao, 1), valor)
            memoria.escrever(regiao, 1, None)
            self.assertIsNone(memoria.ler(regiao, 1))

    def test_limites_de_leitura_e_escrita(self):
        memoria = MemoriaDados(2)
        memoria.reservarQuadro(2)
        for regiao in ("global", "local"):
            for endereco in (2, 100):
                with self.subTest(regiao=regiao, endereco=endereco):
                    with self.assertRaises(IndexError):
                        memoria.ler(regiao, endereco)
                    with self.assertRaises(IndexError):
                        memoria.escrever(regiao, endereco, 5)

    def test_argumentos_inteiros_invalidos(self):
        memoria = MemoriaDados(1)
        memoria.reservarQuadro(1)
        for valor, erro in ((True, TypeError), (False, TypeError),
                            (1.0, TypeError), (None, TypeError),
                            ("1", TypeError), ([], TypeError), (-1, ValueError)):
            with self.subTest(valor=valor):
                for operacao in (MemoriaDados, memoria.reservarQuadro,
                                 memoria.liberarQuadro):
                    with self.assertRaises(erro):
                        operacao(valor)
                for regiao in ("global", "local"):
                    with self.assertRaises(erro):
                        memoria.ler(regiao, valor)
                    with self.assertRaises(erro):
                        memoria.escrever(regiao, valor, 5)
        self.assertEqual(memoria.reservarQuadro(1), 1)

    def test_regioes_invalidas(self):
        memoria = MemoriaDados(1)
        for regiao, erro in ((None, TypeError), ([], TypeError), (True, TypeError),
                            ("", ValueError), ("GLOBAL", ValueError),
                            ("pilha", ValueError)):
            with self.subTest(regiao=regiao):
                with self.assertRaises(erro):
                    memoria.ler(regiao, 0)
                with self.assertRaises(erro):
                    memoria.escrever(regiao, 0, 1)

    def test_quadros_aninhados_enderecos_absolutos_e_lifo(self):
        memoria = MemoriaDados(1)
        memoria.escrever("global", 0, "estatico")
        principal = memoria.reservarQuadro(2)
        filho = memoria.reservarQuadro(3)
        self.assertEqual((principal, filho), (0, 2))
        memoria.escrever("local", 0, "principal")
        memoria.escrever("local", filho + 2, "filho")
        for base in (principal, 3, 99):
            with self.assertRaises(ValueError):
                memoria.liberarQuadro(base)
        self.assertEqual(memoria.ler("local", 4), "filho")
        memoria.liberarQuadro(filho)
        with self.assertRaises(IndexError):
            memoria.ler("local", filho)
        with self.assertRaises(IndexError):
            memoria.escrever("local", filho, 1)
        self.assertEqual(memoria.ler("local", 0), "principal")
        self.assertEqual(memoria.reservarQuadro(3), filho)
        self.assertIsNone(memoria.ler("local", 4))
        memoria.liberarQuadro(filho)
        memoria.liberarQuadro(principal)
        self.assertEqual(memoria.ler("global", 0), "estatico")
        with self.assertRaises(ValueError):
            memoria.liberarQuadro(principal)

    def test_quadros_vazios_consecutivos_sao_registrados(self):
        memoria = MemoriaDados()
        self.assertEqual(memoria.reservarQuadro(0), 0)
        self.assertEqual(memoria.reservarQuadro(0), 0)
        with self.assertRaises(IndexError):
            memoria.ler("local", 0)
        memoria.liberarQuadro(0)
        memoria.liberarQuadro(0)
        with self.assertRaises(ValueError):
            memoria.liberarQuadro(0)

    def test_quadro_vazio_no_topo_impede_liberar_quadro_anterior(self):
        memoria = MemoriaDados()
        memoria.reservarQuadro(2)
        memoria.escrever("local", 1, "preservado")
        self.assertEqual(memoria.reservarQuadro(0), 2)
        with self.assertRaises(ValueError):
            memoria.liberarQuadro(0)
        memoria.liberarQuadro(2)
        self.assertEqual(memoria.ler("local", 1), "preservado")
        memoria.liberarQuadro(0)

    def test_bases_iguais_liberam_um_quadro_por_chamada(self):
        memoria = MemoriaDados()
        memoria.reservarQuadro(0)
        memoria.reservarQuadro(0)
        self.assertEqual(memoria.reservarQuadro(2), 0)
        memoria.liberarQuadro(0)
        with self.assertRaises(IndexError):
            memoria.ler("local", 0)
        memoria.liberarQuadro(0)
        memoria.liberarQuadro(0)
        with self.assertRaises(ValueError):
            memoria.liberarQuadro(0)

    def test_isolamento_de_instancias(self):
        primeira = MemoriaDados(1)
        segunda = MemoriaDados(1)
        primeira.escrever("global", 0, 9)
        primeira.reservarQuadro(1)
        primeira.escrever("local", 0, 8)
        self.assertIsNone(segunda.ler("global", 0))
        with self.assertRaises(IndexError):
            segunda.ler("local", 0)
        with self.assertRaises(ValueError):
            segunda.liberarQuadro(0)


if __name__ == "__main__":
    unittest.main()
