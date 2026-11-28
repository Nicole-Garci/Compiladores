from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile

from .InstrucaoTAC import InstrucaoTAC
from .OperandoTAC import OperandoTAC


@dataclass
class ProgramaTAC:
    entrada: str = "main"
    tamanhoDados: int = 0
    quadros: dict[str, tuple[int, list[int]]] = field(default_factory=dict)
    instrucoes: list[InstrucaoTAC] = field(default_factory=list)

    def salvar(self, caminho: str | Path) -> None:
        """Salva o programa TAC em JSON UTF-8.

        O formato conserva a ordem das instruções e os tipos dos valores dos
        operandos, além dos metadados usados pelo simulador.
        """
        dados = {
            "versao": 1,
            "entrada": self.entrada,
            "tamanhoDados": self.tamanhoDados,
            "quadros": {
                nome: {
                    "tamanho": tamanho,
                    "deslocamentosParametros": deslocamentos,
                }
                for nome, (tamanho, deslocamentos) in self.quadros.items()
            },
            "instrucoes": [
                {
                    "opcode": instrucao.opcode,
                    "operandos": [
                        None if operando is None else {
                            "categoria": operando.categoria,
                            "valor": operando.valor,
                        }
                        for operando in instrucao.operandos
                    ],
                    "linha": instrucao.linha,
                    "coluna": instrucao.coluna,
                }
                for instrucao in self.instrucoes
            ],
        }
        destino = Path(caminho).resolve()
        temporario = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=destino.parent, delete=False
            ) as arquivo:
                temporario = Path(arquivo.name)
                json.dump(dados, arquivo, ensure_ascii=False, indent=2, allow_nan=False)
                arquivo.write("\n")
            temporario.replace(destino)
        finally:
            if temporario is not None:
                temporario.unlink(missing_ok=True)

    @staticmethod
    def carregar(caminho: str) -> ProgramaTAC:
        """Carrega um programa gravado por :meth:`salvar`."""
        with Path(caminho).open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, dict):
            raise ValueError("Arquivo TAC inválido: a raiz do JSON deve ser um objeto.")
        if dados.get("versao") != 1:
            raise ValueError(
                f"Versão do arquivo TAC não suportada: {dados.get('versao')!r}."
            )

        try:
            quadrosJson = dados["quadros"]
            instrucoesJson = dados["instrucoes"]
            if not isinstance(quadrosJson, dict) or not isinstance(instrucoesJson, list):
                raise TypeError("'quadros' deve ser objeto e 'instrucoes' deve ser lista")

            quadros: dict[str, tuple[int, list[int]]] = {}
            for nome, quadro in quadrosJson.items():
                if not isinstance(quadro, dict):
                    raise TypeError(f"Quadro de '{nome}' deve ser um objeto")
                tamanho = quadro["tamanho"]
                deslocamentos = quadro["deslocamentosParametros"]
                if (not isinstance(tamanho, int) or isinstance(tamanho, bool)
                        or not isinstance(deslocamentos, list)
                        or any(not isinstance(valor, int) or isinstance(valor, bool)
                               for valor in deslocamentos)):
                    raise TypeError(f"Dados inválidos no quadro de '{nome}'")
                quadros[nome] = (tamanho, deslocamentos)

            instrucoes: list[InstrucaoTAC] = []
            for indice, instrucaoJson in enumerate(instrucoesJson):
                if not isinstance(instrucaoJson, dict):
                    raise TypeError(f"A instrução {indice} deve ser um objeto")
                operandosJson = instrucaoJson["operandos"]
                if not isinstance(operandosJson, list):
                    raise TypeError(f"Os operandos da instrução {indice} devem ser lista")

                operandos: list[OperandoTAC | None] = []
                for operandoJson in operandosJson:
                    if operandoJson is None:
                        operandos.append(None)
                        continue
                    if not isinstance(operandoJson, dict):
                        raise TypeError(f"Operando inválido na instrução {indice}")
                    operandos.append(OperandoTAC(
                        categoria=operandoJson["categoria"],
                        valor=operandoJson["valor"],
                    ))

                instrucoes.append(InstrucaoTAC(
                    opcode=instrucaoJson["opcode"],
                    operandos=tuple(operandos),
                    linha=instrucaoJson.get("linha", 0),
                    coluna=instrucaoJson.get("coluna", 0),
                ))

            entrada = dados["entrada"]
            tamanhoDados = dados["tamanhoDados"]
            if not isinstance(entrada, str):
                raise TypeError("'entrada' deve ser string")
            if (not isinstance(tamanhoDados, int) or isinstance(tamanhoDados, bool)
                    or tamanhoDados < 0):
                raise TypeError("'tamanhoDados' deve ser inteiro não negativo")

            return ProgramaTAC(
                entrada=entrada,
                tamanhoDados=tamanhoDados,
                quadros=quadros,
                instrucoes=instrucoes,
            )
        except (KeyError, TypeError, ValueError) as erro:
            raise ValueError(f"Arquivo TAC inválido: {erro}") from erro

    def paraString(self) -> str:
        """Formata o conteúdo do programa como texto TAC legível."""
        return "\n".join(
            f"{indice}: {instrucao.paraString()}"
            for indice, instrucao in enumerate(self.instrucoes)
        )

    def validar(self) -> list[str]:
        """Valida instruções e referências a rótulos sem executar o programa."""
        erros: list[str] = []
        rotulos: dict[str, int] = {}

        for indice, instrucao in enumerate(self.instrucoes):
            erros.extend(
                f"Instrução {indice}: {erro}"
                for erro in instrucao.validar()
            )
            if instrucao.opcode != "label" or not instrucao.operandos:
                continue
            operando = instrucao.operandos[0]
            if (operando is None or operando.categoria != "rotulo"
                    or not isinstance(operando.valor, str) or not operando.valor):
                erros.append(
                    f"Instrução {indice}: 'label' exige operando rotulo com nome string"
                )
                continue
            if operando.valor in rotulos:
                erros.append(f"Rótulo duplicado: '{operando.valor}'")
            else:
                rotulos[operando.valor] = indice

        if self.entrada not in rotulos:
            erros.append(f"Rótulo de entrada '{self.entrada}' não definido")

        for indice, instrucao in enumerate(self.instrucoes):
            if instrucao.opcode not in {"goto", "if_true", "if_false"}:
                continue
            if not instrucao.operandos:
                continue
            alvo = instrucao.operandos[-1]
            if alvo is None or alvo.categoria != "rotulo" or not isinstance(alvo.valor, str):
                erros.append(
                    f"Instrução {indice}: '{instrucao.opcode}' exige alvo da categoria rotulo"
                )
            elif alvo.valor not in rotulos:
                erros.append(
                    f"Instrução {indice}: rótulo de destino '{alvo.valor}' não definido"
                )

        return erros
