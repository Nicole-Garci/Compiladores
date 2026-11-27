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

## Leitura textual independente (Trabalho 4)

A CLI `python -B -m src.simulador arquivo.tac` agora aceita TAC textual UTF-8.
Arquivos com extensão `.tac` (sem distinção de maiúsculas) usam
`src/tac/LeitorTAC.py`; os demais continuam usando o carregador JSON existente.
Não há tradução para MIPS nem dependência do analisador semântico. O leitor
constrói os mesmos objetos `ProgramaTAC`, `InstrucaoTAC` e `OperandoTAC`.
Esta extensão não altera os contratos nem a geração de TAC.

A sintaxe das instruções é a de `InstrucaoTAC.paraString()`: uma instrução
por linha, opcode em minúsculas, operandos `categoria[valor]` separados por
vírgula. Todos os 27 opcodes da tabela acima são aceitos. `_` representa
`None`: `call _, funcao[f], constante[0]`, `return _` ou simplesmente
`return`. Os índices `0:`, `1:`, etc. produzidos por `ProgramaTAC.paraString()`
são opcionais e ignorados; saltos continuam usando rótulos, nunca esses índices.
Linhas vazias e comentários iniciados por `#` fora de aspas são ignorados.

Valores: inteiros com sinal opcional, reais (inclusive `.5` e `1e2`), booleanos
`true`/`false` ou `True`/`False`, e texto entre aspas simples ou duplas.
Escapes de literais Python, como `\n`, `\t`, `\\` e `\'`, são aceitos via
`ast.literal_eval`, sem executar expressões. Caracteres Unicode são permitidos.
Uma palavra simples como `constante[A]` é compatível com `paraString()`;
use aspas para valores ambíguos (`constante['1']`, `constante['true']`),
espaços, vírgulas, colchetes e `#`. Nomes de temporários, funções e rótulos
permanecem strings. Endereços usuais são `global[0]` e `local[0]`.

Os metadados, ausentes em `paraString()`, usam três diretivas:

```text
.entrada main
.dados 8
.quadro main 0 []
.quadro soma 2 [0, 1]
```

`.entrada` define o nome do rótulo inicial (padrão `main`); `.dados` define
um tamanho inteiro não negativo (padrão zero); `.quadro nome tamanho [offsets]`
define o quadro e os deslocamentos inteiros dos parâmetros, na ordem dos
argumentos. Sem diretivas de quadros, o dicionário é vazio, como no modelo.
As diretivas podem aparecer em qualquer linha; entrada, dados e cada nome
de quadro só podem ser declarados uma vez. Nomes nas diretivas não usam aspas
nem espaços. Limites e uso dos quadros continuam a cargo do simulador.

Exemplo completo (`tests/tac/soma.tac`):

```text
# Soma independente do analisador semântico
.entrada main
.dados 0
.quadro main 0 []

label rotulo[main]
add temporario[t0], constante[2], constante[3]
print temporario[t0]
halt
```

Os exemplos completos equivalentes aos JSON estão em
[expressao.tac](../../tests/tac/expressao.tac),
[matriz.tac](../../tests/tac/matriz.tac),
[structs.tac](../../tests/tac/structs.tac) e
[fibonacci.tac](../../tests/tac/fibonacci.tac).
Execute a partir da raiz:

```sh
python -B -m src.simulador tests/tac/soma.tac
python -B -m src.simulador tests/tac/expressao.tac
python -B -m src.simulador tests/tac/matriz.tac
python -B -m src.simulador tests/tac/structs.tac
printf '8\n' | python -B -m src.simulador tests/tac/fibonacci.tac
```

Resultados esperados: soma imprime 5 (4 instruções); expressão imprime -14 e
-3.5 (12); matriz imprime 36 (107); structs imprime 42, 2.5, true, A e 15 (35);
Fibonacci com entrada 8 imprime 21 (539). Os testes comparam os tipos e os
metadados dos modelos, além de toda a saída da CLI, incluindo cada PC e
instrução do rastro, entre JSON e texto.

`lerTAC(texto)` e `carregarTAC(caminho)` fazem a leitura, como o carregador
JSON. `diagnosticosTAC(programa)` reutiliza `ProgramaTAC.validar()` e adiciona
localizações; a CLI faz essa verificação antes de executar. Não há outra
implementação dos contratos de opcode, aridade ou execução. Erros sintáticos
interrompem a leitura com linha e coluna (base 1), código de saída 2. Erros de
contrato ou execução retornam 1; sucesso retorna 0. Diagnósticos globais sem
instrução associada, como entrada inexistente, usam linha 1, coluna 1.

Limitações: `paraString()` é uma apresentação legível, não uma serialização
completa: não inclui metadados nem distingue o caractere `'1'` do inteiro 1.
Esses casos exigem diretivas e aspas explícitas. O leitor não infere layout,
não verifica tipos da linguagem fonte e não substitui a validação dinâmica de
endereços, chamadas e quadros. A geração automática de arquivos textuais pelo
analisador semântico permanece fora deste incremento. O Trabalho 4 permite
um simulador da representação intermediária; por isso a leitura preserva o
TAC do grupo e seu rastro, sem introduzir instruções MIPS.
