"""Leitura da representação textual TAC, sem executar ou redefinir contratos."""
import ast
import math
import re
from pathlib import Path

from .InstrucaoTAC import InstrucaoTAC
from .OperandoTAC import OperandoTAC
from .ProgramaTAC import ProgramaTAC


class ErroLeituraTAC(ValueError):
    def __init__(self, mensagem, linha, coluna):
        self.linha, self.coluna = linha, coluna
        super().__init__(f"linha {linha}, coluna {coluna}: {mensagem}")


class _Linha:
    def __init__(self, texto, numero):
        self.texto, self.numero, self.pos = texto, numero, 0

    def erro(self, mensagem):
        raise ErroLeituraTAC(mensagem, self.numero, self.pos + 1)

    def espacos(self):
        while self.pos < len(self.texto) and self.texto[self.pos].isspace():
            self.pos += 1

    def token(self, padrao, mensagem):
        self.espacos()
        match = re.match(padrao, self.texto[self.pos:])
        if not match:
            self.erro(mensagem)
        self.pos += len(match[0])
        return match[0]

    def fim(self):
        self.espacos()
        return self.pos == len(self.texto) or self.texto[self.pos] == '#'

    def valor(self):
        self.espacos()
        inicio = self.pos
        if self.pos < len(self.texto) and self.texto[self.pos] in "\"'":
            literal = self.token(r""""(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'""", 'Literal não terminado')
            try:
                return ast.literal_eval(literal)
            except (SyntaxError, ValueError):
                self.pos = inicio
                self.erro('Escape ou literal inválido')
        bruto = self.token(r'[^\]\s,#]+', 'Esperado valor do operando')
        if bruto in ('true', 'True', 'false', 'False'):
            return bruto.lower() == 'true'
        if re.fullmatch(r'[+-]?\d+', bruto):
            return int(bruto)
        if re.fullmatch(r'[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?', bruto):
            valor = float(bruto)
            if math.isfinite(valor):
                return valor
        elif re.fullmatch(r'[A-Za-z_$][\w.$-]*', bruto):
            return bruto
        self.pos = inicio
        self.erro('Valor inválido; use aspas para texto')

    def operando(self):
        categoria = self.token(r'[A-Za-z_][\w]*', 'Esperado categoria[valor] ou _')
        if categoria == '_':
            return None
        self.token(r'\[', "Esperado '['")
        # Nomes nunca são convertidos em booleanos ou números.
        if categoria in ('temporario', 'rotulo', 'funcao'):
            self.espacos()
            if self.pos < len(self.texto) and self.texto[self.pos] in "\"'":
                valor = self.valor()
            else:
                valor = self.token(r'[^\]\s,#]+', 'Esperado nome')
        else:
            valor = self.valor()
        self.token(r'\]', "Esperado ']'")
        return OperandoTAC(categoria, valor)


def lerTAC(texto: str) -> ProgramaTAC:
    """Constrói um programa; validação semântica permanece em validar()/simulador."""
    programa = ProgramaTAC()
    diretivas = set()
    for numero, textoLinha in enumerate(texto.splitlines(), 1):
        linha = _Linha(textoLinha, numero)
        if linha.fim():
            continue
        if textoLinha[linha.pos] == '.':
            diretiva = linha.token(r'\.\w+', 'Esperada diretiva')
            chave = diretiva
            if diretiva == '.entrada':
                programa.entrada = linha.token(r'[^\s#]+', 'Esperado nome de entrada')
            elif diretiva == '.dados':
                programa.tamanhoDados = int(linha.token(r'\d+', 'Esperado tamanho não negativo'))
            elif diretiva == '.quadro':
                nome = linha.token(r'[^\s#]+', 'Esperado nome do quadro')
                chave = (diretiva, nome)
                tamanho = int(linha.token(r'\d+', 'Esperado tamanho não negativo'))
                linha.token(r'\[', "Esperado '[' dos parâmetros")
                deslocamentos = []
                linha.espacos()
                if linha.pos < len(textoLinha) and textoLinha[linha.pos] != ']':
                    while True:
                        deslocamentos.append(int(linha.token(r'[+-]?\d+', 'Esperado deslocamento inteiro')))
                        linha.espacos()
                        if linha.pos >= len(textoLinha) or textoLinha[linha.pos] != ',':
                            break
                        linha.pos += 1
                linha.token(r'\]', "Esperado ']' dos parâmetros")
                programa.quadros[nome] = (tamanho, deslocamentos)
            else:
                linha.erro(f'Diretiva desconhecida: {diretiva}')
            if chave in diretivas:
                linha.erro('Diretiva duplicada')
            diretivas.add(chave)
        else:
            # Os índices de ProgramaTAC.paraString() são apenas anotações.
            prefixo = re.match(r'\d+:\s*', textoLinha[linha.pos:])
            if prefixo:
                linha.pos += len(prefixo[0])
            coluna = linha.pos + 1
            opcode = linha.token(r'[A-Za-z_][\w]*', 'Esperado opcode')
            operandos = []
            if not linha.fim():
                while True:
                    operandos.append(linha.operando())
                    if linha.fim():
                        break
                    linha.token(',', "Esperada ',' entre operandos")
            programa.instrucoes.append(InstrucaoTAC(opcode, tuple(operandos), numero, coluna))
        if not linha.fim():
            linha.erro('Conteúdo inesperado no fim da linha')
    return programa


def carregarTAC(caminho: str) -> ProgramaTAC:
    return lerTAC(Path(caminho).read_text(encoding='utf-8'))


def diagnosticosTAC(programa: ProgramaTAC) -> list[str]:
    """Acrescenta localização aos diagnósticos do contrato existente."""
    resultado = []
    for erro in programa.validar():
        match = re.match(r'Instrução (\d+):', erro)
        instrucao = programa.instrucoes[int(match[1])] if match else None
        if erro.startswith('Rótulo duplicado:'):
            nome = erro.split("'", 2)[1]
            instrucao = next((i for i in reversed(programa.instrucoes)
                              if i.opcode == 'label' and i.operandos
                              and i.operandos[0] is not None
                              and i.operandos[0].valor == nome), None)
        linha, coluna = (instrucao.linha, instrucao.coluna) if instrucao else (1, 1)
        resultado.append(f'linha {linha}, coluna {coluna}: {erro}')
    return resultado
