# Guia para ler o semântico e o TAC

Este guia acompanha a implementação em
[`MotorSemantico.py`](../src/semantico/core/MotorSemantico.py). A ideia é explicar
como a árvore do parser vira instruções que o simulador executa diretamente.

## Caminho do programa

```text
arquivo .cmm → lexer → parser/AST → analisador semântico → ProgramaTAC → simulador
```

O [`AnalisadorSemantico`](../src/semantico/AnalisadorSemantico.py) é a fachada:
recebe a AST, inicia um `MotorSemantico` e devolve um `ProgramaTAC` se não houver
erros. O motor faz duas passagens:

1. `cadastrarGlobais` registra os tipos struct, variáveis globais e assinaturas
   de todas as funções. Assim, uma função pode chamar outra que aparece depois
   no arquivo.
2. `visitarFuncao` percorre cada corpo, verifica os comandos e expressões e
   acrescenta as instruções TAC.

Se encontrar erro de tipo ou de escopo, o analisador guarda a mensagem com a
linha e a coluna e não entrega o TAC para execução.

## Endereços e valores

Cada `int`, `float`, `char` e `bool` ocupa uma posição de dados. Um endereço
`global[3]` aponta para a quarta posição global; `local[2]` aponta para uma
posição no quadro da função atual. Vetores ocupam posições consecutivas. Os
deslocamentos são contados em posições, nunca em bytes.

Ao visitar uma expressão, o motor devolve um
[`ResultadoExpressao`](../src/semantico/models/ResultadoExpressao.py):

- `tipo` diz que tipo a expressão tem;
- `operando` guarda um valor TAC já calculado, quando existe;
- `deslocamento` guarda o endereço onde um valor pode ser lido ou escrito;
- `atribuivel` indica se a expressão pode ficar do lado esquerdo de uma
  atribuição;
- `indireto` marca parâmetros agregados cujo endereço está guardado numa
  posição local.

Essa diferença entre valor e endereço é importante. Para `x = a + b`, `a` e `b`
são lidos, a soma é calculada num temporário e o resultado é escrito no endereço
de `x`:

```text
add temporario[t0], global[0], global[1]
move global[2], temporario[t0]
```

Para `v[i]`, o motor calcula o endereço da posição do vetor. Se `i` for uma
constante e o vetor tiver endereço direto, pode somar o deslocamento durante a
compilação. Caso contrário, emite `addr`; para ler esse elemento, emite `load`,
e para escrevê-lo, `store`.

Para uma struct individual, `p[i]` escolhe o campo de índice `i` na ordem em
que foi declarado. O índice precisa ser um literal inteiro constante. O tipo
do campo selecionado continua sendo verificado: por exemplo, se `x` é `int` e
`y` é `float`, `p[0]` é `int` e `p[1]` é `float`.

## Como os comandos viram TAC

| Código C-- | Instruções principais |
|---|---|
| `x = a + b` | `add` e `move` (ou `store` para endereço calculado) |
| `print(x)` | `move` para preservar o valor e `print` |
| `readln(x)` | `read` com o tipo esperado |
| `if` / `else` | `if_false`, `goto` e rótulos `label` |
| `while` | rótulo de início, teste, salto ao fim e retorno ao início |
| `break` | `goto` para o rótulo de fim do laço mais próximo |
| chamada de função | temporários dos argumentos, `param` consecutivos e `call` |
| `return x` | `return` com o valor convertido para o tipo da função |

Os temporários guardam resultados de expressões. Os rótulos identificam lugares
do programa para onde os saltos podem ir. O simulador não transforma esses
nomes em registradores físicos: os temporários ficam no banco virtual do
simulador.

Para cada função, `ProgramaTAC.quadros` registra o tamanho do quadro local e os
endereços dos parâmetros. Parâmetros simples ocupam uma posição. Vetores e
structs são passados por referência: o parâmetro guarda o endereço inicial do
agregado. As chamadas emitem todos os `param` em sequência logo antes de
`call`, que é o formato exigido pelo simulador.

## Por onde começar no código

Em `MotorSemantico.py`, leia estes métodos nesta ordem:

1. `executar`: coordena o cadastro, a validação de `main` e a geração.
2. `cadastrarGlobais` e `resolverTipo`: montam a tabela de nomes e resolvem os
   tipos das declarações.
3. `visitarFuncao`, `visitarBloco` e `visitarComando`: alocam posições locais e
   geram TAC para comandos.
4. `visitarExpressao` e os métodos `_visitar...`: verificam e geram as
   expressões.
5. `_comoValor`, `_ponteiro`, `_armazenar` e `_enderecoComOffset`: convertem
   entre valores e endereços de memória.
6. `_tiposAtribuiveis`, `_mesmoTipo` e `_tipoOperacao`: concentram as regras de
   compatibilidade de tipos.

O contrato dos opcodes está em [`ReadMeTAC.md`](../src/tac/ReadMeTAC.md); o
simulador executa essas mesmas instruções em
[`Simulador.py`](../src/simulador/Simulador.py).

## Limites atuais

- `p.campo` não é aceito; os campos são acessados como `p[i]`, por índice
  constante na ordem de declaração.
- Vetores de structs e campos que sejam vetores ou outras structs são rejeitados
  para não adicionar mais dimensões de indexação nesta versão.
- Funções não retornam vetores ou structs. A atribuição de struct copia suas
  posições; vetores são passados por referência e não podem ser atribuídos
  inteiros.
- Índices constantes são verificados contra o comprimento do vetor. Um índice
  calculado em execução não recebe uma verificação do limite daquele vetor.
- A gramática atual exige `else` em `if` e só permite declarações locais no
  começo do corpo da função, não dentro de blocos aninhados.

## Rodar as verificações

Na raiz de `copia experimental`:

```sh
python3 -m unittest discover -s tests -v
python3 main.py tests/semantico/valido_declaracoes.cmm --executar
```

O primeiro comando roda a suíte automatizada, incluindo os testes de integração
do semântico em `tests/test_semantico.py`. O segundo compila um exemplo e executa
o TAC gerado.
