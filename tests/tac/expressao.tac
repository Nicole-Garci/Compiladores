.entrada main
.dados 2
.quadro main 0 []
label rotulo[main]
sub temporario[a], constante[17], constante[5]
neg temporario[b], constante[7]
add temporario[b], temporario[b], constante[2]
mul temporario[produto], temporario[a], temporario[b]
div temporario[q], temporario[produto], constante[5]
mod temporario[r], constante[-17], constante[5]
add global[0], temporario[q], temporario[r]
div global[1], global[0], constante[4.0]
print global[0]
print global[1]
halt
