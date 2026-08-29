# Classe responsável por ler e manipular o texto de entrada.

class LeitorTexto:

    """ 
    Atributos:
        texto (str): O texto de entrada.
        tamanho (int): O tamanho do texto.
        posicao (int): A posição atual no texto.
        linha (int): A linha atual no texto.
        coluna (int): A coluna atual no texto. 
    """

    def __init__(self):
        self.texto = ""
        self.tamanho = 0
        self.posicao = 0
        self.linha = 1
        self.coluna = 1

    # Retorna a linha atual do texto.
    def obter_linha(self):
        return self.linha

    # Retorna a coluna atual do texto.
    def obter_coluna(self):
        return self.coluna

    # Retorna a posição atual do texto.
    def obter_posicao(self):
        return self.posicao

    # Verifica se o texto acabou.
    def chegou_ao_fim(self):
        return self.posicao >= self.tamanho

    # Carrega o arquivo de texto e inicializa os atributos da classe.
    def carregar_arquivo(self, nome_arquivo):
        try:
            with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
                self.texto = arquivo.read()

            self.tamanho = len(self.texto)
            self.posicao = 0
            self.linha = 1
            self.coluna = 1

            return True

        except (OSError, UnicodeError):
            return False

    # Observa o caractere na posição atual do texto, com um deslocamento opcional.
    def observar_caractere(self, deslocamento=0):
        indice = self.posicao + deslocamento

        if indice < 0 or indice >= self.tamanho:
            return None

        return self.texto[indice]

    # Retorna o caractere atual e avança uma posição.
    def avancar(self):
        if self.chegou_ao_fim():
            return None

        caractere = self.texto[self.posicao]

        self.posicao += 1

        if caractere == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1

        return caractere