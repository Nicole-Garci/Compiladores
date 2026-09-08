from pathlib import Path

from src.GerenciadorErros import GerenciadorErros
from src.TabelaSimbolos import TabelaSimbolos
from src.core.MotorLexer import MotorLexer
from src.core.Reconhecedor import Reconhecedor
from src.models.ErroLexer import ErroLexer
from src.models.Token import Token


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

        m = MotorLexer(reconhecedor, self.tabSimbolos, self.gerenciadorErros)

        return m.executar()

