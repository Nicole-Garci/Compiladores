
# Soma e multiplicacao

.entrada main
.dados 0
.quadro main 0 []

label rotulo[main]

# Inicializacao dos valores
move temporario[a], constante[10]
move temporario[b], constante[5]

# Operacoes aritmeticas
add temporario[soma], temporario[a], temporario[b]
mul temporario[produto], temporario[a], temporario[b]

# Impressao dos resultados
print temporario[soma]
print temporario[produto]

halt
