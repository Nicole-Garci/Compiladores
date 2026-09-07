"""
Testando a classe GerenciadorErros.
Para executar este teste, utilize o seguinte comando:
python3 -m tests.teste_gerenciador_erros"""

from src.GerenciadorErros import GerenciadorErros


gerenciador = GerenciadorErros()

print("1 - Estado inicial")
print("Possui erros:", gerenciador.possuiErros())
print("Quantidade:", gerenciador.obterQuantidadeErros())


print("\n2 - Registrando erro comum")

gerenciador.registrarErro(
    "literal não finalizado",
    3,
    8
)

print("Possui erros:", gerenciador.possuiErros())
print("Quantidade:", gerenciador.obterQuantidadeErros())


print("\n3 - Registrando caractere inválido")

gerenciador.registrarCaractereInvalido(
    "@",
    5,
    4
)

print("Quantidade:", gerenciador.obterQuantidadeErros())


print("\n4 - Exibindo erros")

gerenciador.exibirErros()


print("\n5 - Limpando erros")

gerenciador.limparErros()

print("Possui erros:", gerenciador.possuiErros())
print("Quantidade:", gerenciador.obterQuantidadeErros())