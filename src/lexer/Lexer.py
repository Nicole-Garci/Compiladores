from pathlib import Path

from src.lexer.GerenciadorErros import GerenciadorErros
from src.lexer.TabelaSimbolos import TabelaSimbolos
from src.lexer.core.MotorLexer import MotorLexer
from src.lexer.core.Reconhecedor import Reconhecedor
from src.lexer.models.ErroLexer import ErroLexer
from src.lexer.models.Token import Token


class Lexer:
    """Fachada do analisador lexico."""

    def __init__(self, caminhoAFD: str):
        self.caminhoAFD = caminhoAFD
        self.tabSimbolos = TabelaSimbolos()
        self.gerenciadorErros = GerenciadorErros()

    def obterTabelaSimbolos(self) -> TabelaSimbolos:
        return self.tabSimbolos

    def obterErros(self) -> list[ErroLexer]:
        return self.gerenciadorErros.obterErros()

    def analisarArquivo(self, caminhoFonte: str) -> list[Token]:
        path = Path(caminhoFonte)

        if path.suffix.lower() != ".cmm":
            ext = path.suffix or "sem extensão"
            raise ValueError(
                f"Extensão inválida: {ext}. "
                f"Espera-se um arquivo '*.cmm'"
            )

        if not path.is_file():
            raise FileNotFoundError(
                f"Arquivo {path} não encontrado."
            )

        self.tabSimbolos = TabelaSimbolos()
        self.gerenciadorErros = GerenciadorErros()

        reconhecedor = Reconhecedor(self.caminhoAFD, caminhoFonte)
        motor = MotorLexer(
            reconhecedor,
            self.tabSimbolos,
            self.gerenciadorErros,
        )
        return motor.executar()
