# Contrato do código de três endereços

Este documento é, atualmente, temporário. Ele define o formato de TAC usado pelas classes em `src/tac` e
prepara uma interface comum para o gerador semântico e o simulador. A geração
automática a partir da AST ainda pertence ao analisador semântico.

## Operandos

Um operando é o par `categoria, valor`. As categorias planejadas são:

| Categoria | Valor | Uso |
|---|---|---|
| `constante` | `int`, `float`, `bool` ou `str` | Literal imediato |
| `temporario` | nome string, como `t0` | Resultado intermediário |
| `global` | deslocamento inteiro | Endereço de dado global |
| `local` | deslocamento inteiro | Endereço relativo ao quadro corrente |
| `rotulo` | nome string | Destino de salto ou rótulo definido |
| `funcao` | nome string | Função chamada |

`global` e `local` seguem os deslocamentos atribuídos pela análise semântica.
Um temporário não é um identificador da linguagem fonte: ele armazena um
resultado intermediário. Os construtores mantêm `categoria` aberta para que
outras categorias possam ser introduzidas sem quebrar dados já serializados.

## Instruções

Os opcodes são escritos em minúsculas. Resultados vêm primeiro. `None` só é
permitido nos operandos opcionais de `call` e `return`.

| Opcode | Operandos | Comportamento |
|---|---|---|
| `label` | rótulo | Marca uma posição do programa |
| `move` | destino, origem | Copia um valor |
| `add`, `sub`, `mul`, `div`, `mod` | destino, esquerda, direita | Operação aritmética |
| `neg`, `not` | destino, origem | Negação aritmética ou lógica |
| `eq`, `ne`, `lt`, `le`, `gt`, `ge` | destino, esquerda, direita | Comparação; produz booleano |
| `addr` | destino, base, deslocamento | Calcula endereço efetivo a partir da base e deslocamento |
| `load` | destino, endereço | Lê da memória de dados |
| `store` | endereço, valor | Escreve na memória de dados |
| `goto` | rótulo | Salto incondicional |
| `if_true`, `if_false` | condição, rótulo | Salta conforme a condição |
| `param` | valor | Empilha/prepara um argumento para a próxima chamada |
| `call` | destino opcional, função, quantidade de argumentos | Chama uma função |
| `return` | valor opcional | Retorna da função atual |
| `read` | destino | Lê um valor de entrada para o destino |
| `print` | valor | Emite um valor |
| `halt` | nenhum | Encerra a execução |

`if_true` considera verdadeira uma condição diferente de zero; `if_false` faz
o inverso. `param` deve aparecer na ordem dos argumentos imediatamente antes
do `call` correspondente. Uma chamada sem valor de retorno usa `None` no
primeiro operando.

## Exemplo

```text
label rotulo[main]
add temporario[t0], constante[1], constante[2]
if_true temporario[t0], rotulo[tem_valor]
goto rotulo[fim]
label rotulo[tem_valor]
print temporario[t0]
label rotulo[fim]
return
```

Na representação em memória, cada instrução guarda o opcode, uma tupla de
operandos e linha/coluna opcionais da origem. `ProgramaTAC` também guarda o
rótulo de entrada, o tamanho dos dados e os quadros. O salvamento usa JSON
UTF-8 versão 1; `salvar` e `carregar` preservam a ordem e os tipos de valores.

## Validação disponível

`InstrucaoTAC.validar()` verifica se o opcode é conhecido e se a quantidade e
as posições opcionais de operandos estão corretas. `ProgramaTAC.validar()`
também verifica rótulos duplicados e destinos de salto não definidos. A
validação estrutural também exige que o rótulo de entrada exista. Ela não
executa o programa nem substitui a análise semântica.

## O que ainda não está ligado

O MotorSemantico já cria alguns operandos de endereço para variáveis, mas ainda não percorre todas as expressões e comandos para produzir instruções TAC. A geração automática a partir da AST continua pendente, assim como a execução no simulador. Portanto, por enquanto, essas classes permitem montar, conferir, imprimir e salvar programas TAC, mas ainda não completam o fluxo fonte → TAC → execução.