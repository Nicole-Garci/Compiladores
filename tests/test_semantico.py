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

from src.lexer.Lexer import Lexer
from src.parser.Parser import Parser
from src.parser.SaidaParser import SaidaParser
from src.semantico.AnalisadorSemantico import AnalisadorSemantico
from src.simulador.Simulador import Simulador


CAMINHO_AFD = RAIZ_PROJETO / "src" / "lexer" / "AFD.json"


class SemanticoTACIntegracaoTests(unittest.TestCase):
    """Integra lexer, parser, semântico, TAC e simulador em casos curtos."""

    def compilar(self, fonte):
        with TemporaryDirectory(prefix="cmm-semantico-") as pasta:
            caminho = Path(pasta) / "caso.cmm"
            caminho.write_text(fonte, encoding="utf-8")

            lexer = Lexer(str(CAMINHO_AFD))
            tokens = lexer.analisarArquivo(str(caminho))
            self.assertEqual(lexer.obterErros(), [])

            parser = Parser(saida=SaidaParser(io.StringIO()))
            arvore = parser.analisar(tokens)
            self.assertEqual(parser.obterErros(), [])

            analisador = AnalisadorSemantico()
            tac = analisador.analisar(arvore)
            if tac is not None:
                self.assertEqual(tac.validar(), [])
            return tac, analisador

    def executar(self, fonte, entrada=""):
        tac, analisador = self.compilar(fonte)
        self.assertEqual(analisador.obterErros(), [])
        self.assertIsNotNone(tac)

        simulador = Simulador()
        saida = io.StringIO()
        with patch("sys.stdin", io.StringIO(entrada)), redirect_stdout(saida):
            simulador.executar(tac)
        return tac, simulador, saida.getvalue()

    def erros_semanticos(self, fonte):
        tac, analisador = self.compilar(fonte)
        mensagens = [erro.mensagem for erro in analisador.obterErros()]
        self.assertIsNone(tac)
        self.assertTrue(mensagens)
        return "\n".join(mensagens)

    def test_precedencia_conversao_e_comparacoes(self):
        _, _, saida = self.executar("""
            int main() {
                int inteiro;
                float real;
                bool resultado;
                inteiro = 2 + 3 * 4;
                real = inteiro / 2.0;
                resultado = (inteiro == 14) && (real > 6.0);
                print(inteiro);
                print(real);
                print(resultado);
                return 0;
            }
        """)
        self.assertEqual(saida, "14\n7.0\ntrue\n")

    def test_operadores_binarios_geram_valores_esperados(self):
        expressoes = (
            ("2 + 3", "5"),
            ("7 - 9", "-2"),
            ("3 * 4", "12"),
            ("(0 - 17) / 5", "-3"),
            ("(0 - 17) % 5", "-2"),
            ("2 == 2", "true"),
            ("2 != 2", "false"),
            ("2 < 3", "true"),
            ("2 <= 2", "true"),
            ("3 > 2", "true"),
            ("3 >= 3", "true"),
            ("true == false", "false"),
            ("'a' != 'b'", "true"),
        )
        prints = "\n".join(f"print({expr});" for expr, _ in expressoes)
        _, _, saida = self.executar(
            f"int main() {{ {prints} return 0; }}"
        )
        self.assertEqual(saida, "".join(f"{valor}\n" for _, valor in expressoes))

    def test_promocao_int_float_em_argumento_e_retorno(self):
        _, _, saida = self.executar("""
            float metade(float valor) { return valor / 2.0; }
            float receberInteiro(int valor) { return valor; }
            int main() {
                print(metade(5));
                print(receberInteiro(3));
                return 0;
            }
        """)
        self.assertEqual(saida, "2.5\n3.0\n")

    def test_incremento_decremento_e_negacao_logica(self):
        _, _, saida = self.executar("""
            int main() {
                int valor;
                bool ativo;
                valor = 4;
                ++valor;
                --valor;
                ativo = !false;
                print(valor);
                print(ativo);
                return 0;
            }
        """)
        self.assertEqual(saida, "4\ntrue\n")

    def test_atribuicao_como_expressao_divisao_e_resto_inteiros(self):
        _, _, saida = self.executar("""
            int main() {
                int a;
                int b;
                a = (b = 7) + 3;
                print(a);
                print(b);
                print((0 - 17) / 5);
                print((0 - 17) % 5);
                return 0;
            }
        """)
        self.assertEqual(saida, "10\n7\n-3\n-2\n")

    def test_operadores_logicos_curto_circuitam_chamadas(self):
        _, _, saida = self.executar("""
            bool efeito() {
                print(99);
                return true;
            }
            int main() {
                bool resultado;
                resultado = false && efeito();
                print(resultado);
                resultado = true || efeito();
                print(resultado);
                return 0;
            }
        """)
        self.assertEqual(saida, "false\ntrue\n")

    def test_bloco_aninhado_acessa_variavel_local(self):
        _, _, saida = self.executar("""
            int main() {
                int valor;
                valor = 1;
                {
                    valor = 2;
                    print(valor);
                }
                print(valor);
                return 0;
            }
        """)
        self.assertEqual(saida, "2\n2\n")

    def test_while_break_if_else_e_retorno_implicito_de_main(self):
        _, _, saida = self.executar("""
            int main() {
                int indice;
                int soma;
                indice = 0;
                soma = 0;
                while (indice < 10) {
                    indice = indice + 1;
                    if (indice == 5) { break; } else { }
                    soma = soma + indice;
                }
                print(soma);
            }
        """)
        self.assertEqual(saida, "10\n")

    def test_chamadas_aninhadas_recursao_e_argumentos(self):
        _, _, saida = self.executar("""
            int fatorial(int n) {
                if (n <= 1) { return 1; }
                else { return n * fatorial(n - 1); }
            }
            int somar(int a, int b) { return a + b; }
            int main() {
                print(somar(fatorial(5), 1));
                return 0;
            }
        """)
        self.assertEqual(saida, "121\n")

    def test_funcao_com_retorno_em_ambos_os_ramos(self):
        _, _, saida = self.executar("""
            int escolher(bool condicao) {
                if (condicao) { return 1; }
                else { return 2; }
            }
            int main() {
                print(escolher(true));
                print(escolher(false));
                return 0;
            }
        """)
        self.assertEqual(saida, "1\n2\n")

    def test_vetor_com_indice_dinamico_passado_por_referencia(self):
        _, _, saida = self.executar("""
            int somar(int valores[4]) {
                int i;
                int total;
                i = 0;
                total = 0;
                while (i < 4) {
                    total = total + valores[i];
                    i = i + 1;
                }
                return total;
            }
            int main() {
                int dados[4];
                dados[0] = 1;
                dados[1] = 2;
                dados[2] = 3;
                dados[3] = 4;
                print(somar(dados));
                return 0;
            }
        """)
        self.assertEqual(saida, "10\n")

    def test_readln_grava_em_elemento_de_vetor_parametro(self):
        _, _, saida = self.executar("""
            int preencher(int valores[2]) {
                readln(valores[1]);
                return valores[1];
            }
            int main() {
                int dados[2];
                print(preencher(dados));
                return 0;
            }
        """, "42\n")
        self.assertEqual(saida, "42\n")

    def test_variaveis_globais_iniciam_com_valor_padrao(self):
        _, _, saida = self.executar("""
            int inteiro;
            float real;
            bool logico;
            char caractere;
            int main() {
                float convertido;
                convertido = inteiro;
                print(inteiro);
                print(real);
                print(logico);
                print(caractere);
                print(convertido);
                return 0;
            }
        """)
        self.assertEqual(saida, "0\n0.0\nfalse\n\0\n0.0\n")

    def test_indice_constante_acessa_campos_da_struct_por_ordem(self):
        tac, _, saida = self.executar("""
            typedef struct {
                int x;
                float y;
            } Ponto;
            int main() {
                Ponto p;
                p[0] = 10;
                p[1] = 2.5;
                print(p[0]);
                print(p[1] + 0.5);
                return 0;
            }
        """)
        self.assertEqual(saida, "10\n3.0\n")
        self.assertEqual(tac.quadros["main"], (2, []))

    def test_acesso_a_campos_de_struct_passada_a_funcao(self):
        tac, _, saida = self.executar("""
            typedef struct { int x; int y; } Ponto;
            int somar(Ponto p) { return p[0] + p[1]; }
            int main() {
                Ponto p;
                p[0] = 8;
                p[1] = 9;
                print(somar(p));
                return 0;
            }
        """)
        self.assertEqual(saida, "17\n")
        self.assertEqual(tac.quadros["somar"], (1, [0]))
        self.assertEqual(tac.quadros["main"], (2, []))

    def test_ordem_tipos_mistos_copia_e_incremento_de_campos(self):
        tac, _, saida = self.executar("""
            typedef struct {
                int x, y;
                bool ativo;
                char letra;
            } Registro;
            int main() {
                Registro origem;
                Registro copia;
                origem[0] = 7;
                origem[1] = 8;
                origem[2] = true;
                origem[3] = 'k';
                copia = origem;
                ++copia[0];
                print(origem[0]);
                print(copia[0]);
                print(copia[1]);
                print(copia[2]);
                print(copia[3]);
                print(copia[2] && true);
                print(copia[3] == 'k');
                return 0;
            }
        """)
        self.assertEqual(saida, "7\n8\n8\ntrue\nk\ntrue\ntrue\n")
        self.assertEqual(tac.quadros["main"], (8, []))

    def test_offsets_de_struct_global_e_atribuicao_encadeada(self):
        tac, simulador, saida = self.executar("""
            typedef struct { int x; float y; } Ponto;
            int antes;
            Ponto original, meio;
            int depois;
            int main() {
                Ponto local;
                original[0] = 3;
                original[1] = 4.5;
                local = meio = original;
                print(local[0]);
                print(local[1]);
                return 0;
            }
        """)
        self.assertEqual(saida, "3\n4.5\n")
        self.assertEqual(tac.tamanhoDados, 6)
        self.assertEqual([simulador.dados.ler("global", i) for i in range(6)],
                         [0, 3, 4.5, 3, 4.5, 0])

    def test_struct_passada_a_funcao_reflete_escritas_do_parametro(self):
        _, _, saida = self.executar("""
            typedef struct { int x; int y; } Ponto;
            int alterar(Ponto p) {
                p[0] = 12;
                return 0;
            }
            int main() {
                Ponto p;
                p[0] = 4;
                alterar(p);
                print(p[0]);
                return 0;
            }
        """)
        self.assertEqual(saida, "12\n")

    def test_acesso_a_campo_pode_ser_destino_de_readln(self):
        _, _, saida = self.executar("""
            typedef struct { int x; float y; } Ponto;
            int main() {
                Ponto p;
                readln(p[1]);
                print(p[1]);
                return 0;
            }
        """, "2.75\n")
        self.assertEqual(saida, "2.75\n")

    def test_leitura_tipa_int_float_bool_char(self):
        _, _, saida = self.executar("""
            int main() {
                int inteiro;
                float real;
                bool logico;
                char caractere;
                readln(inteiro);
                readln(real);
                readln(logico);
                readln(caractere);
                print(inteiro);
                print(real);
                print(logico);
                print(caractere);
                print(caractere == 'x');
                return 0;
            }
        """, "7\n1.25\ntrue\nx\n")
        self.assertEqual(saida, "7\n1.25\ntrue\nx\ntrue\n")

    def test_variavel_local_sem_inicializacao_falha_em_execucao(self):
        tac, analisador = self.compilar("""
            int main() {
                int valor;
                print(valor);
                return 0;
            }
        """)
        self.assertEqual(analisador.obterErros(), [])
        with self.assertRaisesRegex(ValueError, "não inicializado"):
            Simulador().executar(tac)

    def test_rejeita_atribuicao_incompativel_e_sombreamento_de_funcao(self):
        casos = (
            ("int main() { int x; x = true; return 0; }", "Não é possível atribuir"),
            (
                "int f() { return 1; } int main() { int f; return f(); }",
                "não é uma função",
            ),
        )
        for fonte, esperado in casos:
            with self.subTest(esperado=esperado):
                self.assertIn(esperado, self.erros_semanticos(fonte))

    def test_rejeita_indice_constante_fora_dos_limites(self):
        mensagens = self.erros_semanticos(
            "int main() { int valores[2]; valores[2] = 7; return 0; }"
        )
        self.assertIn("fora dos limites", mensagens)

    def test_rejeita_vetor_menor_que_parametro_e_destino_nao_gravavel(self):
        casos = (
            (
                "int f(int valores[4]) { return 0; } "
                "int main() { int pequenos[2]; return f(pequenos); }",
                "Argumento 1",
            ),
            ("int main() { 1 = 2; return 0; }", "variável gravável"),
        )
        for fonte, esperado in casos:
            with self.subTest(esperado=esperado):
                self.assertIn(esperado, self.erros_semanticos(fonte))

    def test_rejeita_indices_invalidos_em_struct(self):
        casos = (
            (
                "typedef struct { int x; int y; } Ponto; "
                "int main() { Ponto p; int i; i = 0; print(p[i]); return 0; }",
                "literal inteiro constante",
            ),
            (
                "typedef struct { int x; } Ponto; "
                "int main() { Ponto p; print(p[0.0]); return 0; }",
                "deve ser int",
            ),
            (
                "typedef struct { int x; int y; } Ponto; "
                "int main() { Ponto p; print(p[2]); return 0; }",
                "fora dos limites da struct",
            ),
            (
                "typedef struct { int x; } Ponto; "
                "int main() { Ponto p; p[0] = 1.5; return 0; }",
                "Não é possível atribuir",
            ),
            (
                "typedef struct { int x; } Ponto; "
                "int main() { Ponto p; print(p[0][0]); return 0; }",
                "Indexação exige um vetor",
            ),
        )
        for fonte, esperado in casos:
            with self.subTest(esperado=esperado):
                self.assertIn(esperado, self.erros_semanticos(fonte))

    def test_rejeita_vetores_e_campos_agregados_de_struct(self):
        casos = (
            (
                "typedef struct { int x; int y; } Ponto; "
                "Ponto pontos[2]; int main() { return 0; }",
                "Vetores de structs não são suportados",
            ),
            (
                "typedef struct { int x; } Ponto; "
                "typedef struct { Ponto origem; } Linha; "
                "int main() { return 0; }",
                "campos de struct devem ser tipos primitivos escalares",
            ),
            (
                "typedef struct { int valores[2]; } Grupo; "
                "int main() { return 0; }",
                "campos de struct devem ser tipos primitivos escalares",
            ),
        )
        for fonte, esperado in casos:
            with self.subTest(esperado=esperado):
                self.assertIn(esperado, self.erros_semanticos(fonte))

    def test_structs_diferentes_nao_sao_compativeis(self):
        mensagens = self.erros_semanticos("""
            typedef struct { int x; } A;
            typedef struct { int x; } B;
            int main() {
                A a;
                B b;
                a = b;
                return 0;
            }
        """)
        self.assertIn("structs de tipos diferentes", mensagens)

    def test_rejeita_argumento_condicao_break_e_retorno_invalidos(self):
        casos = (
            (
                "int f(int x) { return x; } int main() { return f(); }",
                "espera 1 argumento",
            ),
            (
                "int main() { if (1) { return 0; } else { return 1; } }",
                "condição deve ter tipo bool",
            ),
            ("int main() { break; return 0; }", "break só pode"),
            (
                "int f() { print(1); } int main() { return 0; }",
                "pode terminar sem retornar",
            ),
        )
        for fonte, esperado in casos:
            with self.subTest(esperado=esperado):
                self.assertIn(esperado, self.erros_semanticos(fonte))

    def test_rejeita_float_para_int_e_argumento_read_invalido(self):
        mensagens = self.erros_semanticos(
            "int main() { int x; x = 1.5; return 0; }"
        )
        self.assertIn("Não é possível atribuir", mensagens)

        tac, analisador = self.compilar("""
            int main() { int x; readln(x); return 0; }
        """)
        self.assertEqual(analisador.obterErros(), [])
        with patch("sys.stdin", io.StringIO("abc\n")):
            with self.assertRaisesRegex(ValueError, "esperado int"):
                Simulador().executar(tac)


if __name__ == "__main__":
    unittest.main()
