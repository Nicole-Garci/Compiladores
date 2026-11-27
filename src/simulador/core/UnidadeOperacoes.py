import operator


class UnidadeOperacoes:
    """Operações sobre valores, sem acesso ao estado do simulador.
    Decisões provisórias: int/float podem se misturar; bool não é número.
    Divisão inteira trunca para zero e mod aceita somente inteiros.
    Comparações são numéricas, exceto eq/ne entre booleanos. Strings
    (inclusive char) não são convertidas. not aceita bool ou número e
    testa igualdade com zero. None representa ausência do segundo operando.
    Inteiros não têm overflow artificial; floats seguem a aritmética Python.
    """

    def executar(self, opcode: str, a: object, b: object = None) -> object:
        if not isinstance(opcode, str):
            raise TypeError("O opcode deve ser uma string.")
        if opcode not in {
            "add", "sub", "mul", "div", "mod", "neg", "not",
            "eq", "ne", "lt", "le", "gt", "ge",
        }:
            raise ValueError(f"Opcode não suportado pela unidade: '{opcode}'.")

        if opcode in {"neg", "not"}:
            if b is not None:
                raise TypeError(f"'{opcode}' exige somente um operando.")
            if opcode == "not" and type(a) is bool:
                return not a
            self._validarNumero(a)
            return -a if opcode == "neg" else a == 0

        if b is None:
            raise TypeError(f"'{opcode}' exige dois operandos.")
        if opcode in {"eq", "ne"} and type(a) is bool and type(b) is bool:
            return a == b if opcode == "eq" else a != b

        self._validarNumero(a)
        self._validarNumero(b)
        if opcode == "mod" and (type(a) is not int or type(b) is not int):
            raise TypeError("'mod' exige operandos inteiros.")
        if opcode in {"div", "mod"}:
            if b == 0:
                raise ZeroDivisionError(f"Operação '{opcode}' com divisor zero.")
            if type(a) is int and type(b) is int:
                quociente = abs(a) // abs(b)
                if (a < 0) != (b < 0):
                    quociente = -quociente
                return quociente if opcode == "div" else a - quociente * b
            return a / b

        operacoes = {
            "add": operator.add, "sub": operator.sub, "mul": operator.mul,
            "eq": operator.eq, "ne": operator.ne, "lt": operator.lt,
            "le": operator.le, "gt": operator.gt, "ge": operator.ge,
        }
        return operacoes[opcode](a, b)

    @staticmethod
    def _validarNumero(valor: object) -> None:
        if type(valor) not in (int, float):
            raise TypeError("O operando deve ser int ou float, sem bool.")
