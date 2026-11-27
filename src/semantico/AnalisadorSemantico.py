from __future__ import annotations

from src.parser.ast.Nos import Programa
from src.semantico.Escopo import Escopo
from src.semantico.GerenciadorErrosSemanticos import GerenciadorErrosSemanticos
from src.semantico.core.MotorSemantico import MotorSemantico
from src.semantico.models.ErroSemantico import ErroSemantico
from src.tac.ProgramaTAC import ProgramaTAC


class AnalisadorSemantico:
    def __init__(
        self, gerenciadorErros: GerenciadorErrosSemanticos | None = None
    ) -> None:
        self.gerenciadorErros = gerenciadorErros or GerenciadorErrosSemanticos()
        self.motor: MotorSemantico | None = None

    def analisar(self, programa: Programa) -> ProgramaTAC | None:
        self.gerenciadorErros.limpar()
        self.motor = MotorSemantico(self.gerenciadorErros)
        programaTAC = self.motor.executar(programa)

        if self.gerenciadorErros.obterErros():
            return None
        return programaTAC

    def obterErros(self) -> list[ErroSemantico]:
        return self.gerenciadorErros.obterErros()

    def obterEscopoGlobal(self) -> Escopo | None:
        return self.motor.escopoGlobal if self.motor else None

    def descreverTabela(self) -> list[str]:
        if self.motor is None:
            return []

        linhas = ["Escopo global:"]
        for simbolo in self.motor.escopoGlobal.simbolos.values():
            linhas.append("  " + self.descreverSimbolo(simbolo))

        for tipoStruct in self.motor.structs:
            linhas.append(f"{tipoStruct.nome} ({tipoStruct.tamanhoPosicoes} posição(ões)):")
            for nomeCampo, (tipoCampo, deslocamento) in tipoStruct.campos.items():
                linhas.append(
                    f"  {nomeCampo}: {tipoCampo.paraString()}, deslocamento {deslocamento}"
                )

        for nomeFuncao, escopo in self.motor.escoposFuncoes.items():
            tamanho, _ = self.motor.programaTAC.quadros.get(nomeFuncao, (0, []))
            linhas.append(f"Função {nomeFuncao} (quadro de tamanho {tamanho}):")
            for simbolo in escopo.simbolos.values():
                linhas.append("  " + self.descreverSimbolo(simbolo))

        linhas.append(f"Posições da área global: {self.motor.programaTAC.tamanhoDados}")
        return linhas

    @staticmethod
    def descreverSimbolo(simbolo) -> str:
        texto = f"{simbolo.nome}: {simbolo.categoria} {simbolo.tipo.paraString()}"
        if simbolo.parametros:
            texto += "(" + ", ".join(t.paraString() for t in simbolo.parametros) + ")"
        elif simbolo.categoria == "funcao":
            texto += "()"
        if simbolo.endereco is not None:
            texto += f" em {simbolo.endereco.paraString()}"
        return texto
