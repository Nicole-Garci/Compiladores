from TabelaSimbolos import TabelaSimbolos
from TiposToken import TiposToken, Token

def executar_testes():
    print("--- Testando a Tabela de Símbolos ---")
    tabela = TabelaSimbolos()
    
    # Testando busca de palavra reservada carregada automaticamente[cite: 2]
    tipo_reservada = tabela.buscar("if")
    print(f"Busca por 'if': {tipo_reservada}")
    
    # Testando busca de um identificador novo (deve retornar ID)[cite: 2]
    tipo_id = tabela.buscar("contador")
    print(f"Busca por 'contador': {tipo_id}")

    print("\n--- Testando a Geração de Tokens ---")
    # Criando um token de número inteiro[cite: 3]
    token_int = Token(TiposToken.NUM_INT, "100", linha=1, coluna=4)
    print(f"Token formatado (NUM_INT): {token_int.para_string()}")
    
    # Criando um token de palavra-chave[cite: 3]
    token_if = Token(TiposToken.IF, "if", linha=2, coluna=1)
    print(f"Token formatado (IF): {token_if.para_string()}")

if __name__ == "__main__":
    executar_testes()