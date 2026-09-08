"""
Testando a classe GerenciadorErros.
Para executar este teste, utilize o seguinte comando:
python3 -m tests.teste_gerenciador_erros"""
from src.GerenciadorErros import GerenciadorErros

gerenciador = GerenciadorErros()

print("1 - Estado inicial")
print("Possui erros:", gerenciador.possuiErros())
print("Quantidade:", gerenciador.quantidade())


print("\n2 - Registrando erro comum")

gerenciador.registrarErro(
    mensagem="literal não finalizado",
    linha=3,
    coluna=8,
    lexema='"texto'
)

print("Possui erros:", gerenciador.possuiErros())
print("Quantidade:", gerenciador.quantidade())


print("\n3 - Registrando caractere inválido")

gerenciador.registrarCaractereInvalido(
    "@",
    5,
    4
)

print("Quantidade:", gerenciador.quantidade())


print("\n4 - Exibindo erros")

for erro in gerenciador.obterErros():
    print(erro.paraString())


print("\n5 - Limpando erros")

gerenciador.limpar()

print("Possui erros:", gerenciador.possuiErros())
print("Quantidade:", gerenciador.quantidade())