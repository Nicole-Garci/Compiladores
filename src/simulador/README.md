# Simulador TAC

O simulador executa código intermediário de três endereços (TAC — *Three-Address Code*) da linguagem C--. Ele foi desenvolvido em Python para o Trabalho 4 de Compiladores e pode ser utilizado independentemente do analisador semântico.

Aceita arquivos TAC nos formatos textual (`.tac`) e JSON (`.json`), apresenta a saída do programa e, ao final de uma execução bem-sucedida, o rastro das instruções efetivamente executadas.

## 1. Requisitos

- Python 3.10 ou superior.
- Nenhuma dependência externa para executar o simulador.

Os comandos deste README devem ser executados na raiz do projeto `Compiladores`, onde estão as pastas `src` e `tests` e o arquivo `main.py`.

## 2. Como executar

Para consultar a ajuda da interface de linha de comando:

```bash
python -B -m src.simulador --help
```

Para executar um arquivo TAC textual:

```bash
python -B -m src.simulador tests/tac/soma.tac
```

Para executar um arquivo TAC em JSON:

```bash
python -B -m src.simulador tests/tac/expressao.json
```

O argumento `-B` evita a gravação de arquivos de bytecode (`.pyc`) e é opcional. O argumento `-m` executa o pacote `src.simulador` por meio de seu arquivo `__main__.py`. O último argumento é o caminho do arquivo de entrada, relativo ao diretório atual ou absoluto.

Se estiver dentro de `src/simulador`, volte à raiz antes de executar os comandos acima:

```bash
cd ../..
```

O `main.py` da raiz é o ponto de entrada do compilador C--; ele não é chamado por esses comandos. O simulador recebe TAC, não código-fonte `.cmm` diretamente.

## 3. Criando um programa para teste manual

O arquivo `tests/tac/teste.tac` é reservado para experimentação. Edite-o, substituindo seu conteúdo pelo programa que deseja testar:

```bash
nano tests/tac/teste.tac
```

Exemplo de soma:

```asm
# Soma de dois valores
.entrada main
.dados 0
.quadro main 0 []

label rotulo[main]
add temporario[t0], constante[7], constante[19]
print temporario[t0]
halt
```

Salve o arquivo e execute:

```bash
python -B -m src.simulador tests/tac/teste.tac
```

Saída esperada:

```text
26

Rastro de execução:
1: PC 0 | label rotulo[main]
2: PC 1 | add temporario[t0], constante[7], constante[19]
3: PC 2 | print temporario[t0]
4: PC 3 | halt
Total de instruções executadas: 4
```

### Diretivas de configuração

| Diretiva | Descrição |
| --- | --- |
| `.entrada main` | Define o rótulo de início da execução. |
| `.dados 0` | Define a quantidade de posições de memória estática (globais). |
| `.quadro main 0 []` | Define o quadro da função `main`, seu tamanho na pilha e os deslocamentos dos parâmetros. |

Por exemplo, `.quadro soma 4 [0, 1]` descreve um quadro de quatro posições, com dois parâmetros armazenados nos deslocamentos 0 e 1. As demais posições podem ser usadas para variáveis locais.

As diretivas configuram o programa e não aparecem no rastro. Comentários começam com `#`, e linhas vazias são permitidas.

### Instruções e operandos

A sintaxe utiliza um opcode seguido dos operandos, separados por vírgulas:

```asm
add temporario[t0], constante[7], constante[19]
```

Nesse caso, `add` soma os operandos de origem e grava o resultado no temporário `t0`.

| Categoria | Exemplo | Significado |
| --- | --- | --- |
| `constante` | `constante[7]` | Valor literal. |
| `temporario` | `temporario[t0]` | Registrador temporário virtual. |
| `global` | `global[0]` | Posição da memória estática. |
| `local` | `local[0]` | Deslocamento relativo ao quadro atual. |
| `rotulo` | `rotulo[laco]` | Referência a uma posição de código. |
| `funcao` | `funcao[soma]` | Referência a uma função. |

Constantes podem representar inteiros, reais, booleanos e caracteres. Use aspas simples para caracteres ambíguos, como `constante['1']`, distinguindo-os de `constante[1]`. O símbolo `_` representa um operando opcional ausente, nos opcodes que o permitem.

O contrato completo, incluindo a sintaxe textual e as regras de cada instrução, está em [ReadMeTAC.md](../tac/ReadMeTAC.md).

### Instruções disponíveis

| Categoria | Opcodes |
| --- | --- |
| Transferência de valores | `move` |
| Aritmética | `add`, `sub`, `mul`, `div`, `mod`, `neg` |
| Negação lógica | `not` |
| Comparações | `eq`, `ne`, `lt`, `le`, `gt`, `ge` |
| Memória | `addr`, `load`, `store` |
| Controle de fluxo | `label`, `goto`, `if_true`, `if_false` |
| Funções | `param`, `call`, `return` |
| Entrada e saída | `read`, `print` |
| Encerramento | `halt` |

São 27 opcodes. `goto` é o salto incondicional do TAC, enquanto `if_true` e `if_false` realizam saltos condicionais. O simulador executa o TAC do projeto, não Assembly MIPS.

## 4. Exemplo com entrada e repetição

Substitua o conteúdo de `tests/tac/teste.tac` pelo programa abaixo para calcular a tabuada de um número:

```asm
# Tabuada de 1 a 10
.entrada main
.dados 0
.quadro main 0 []

label rotulo[main]
read temporario[n]
move temporario[i], constante[1]

label rotulo[laco]
le temporario[cond], temporario[i], constante[10]
if_false temporario[cond], rotulo[fim]
mul temporario[resultado], temporario[n], temporario[i]
print temporario[resultado]
add temporario[i], temporario[i], constante[1]
goto rotulo[laco]

label rotulo[fim]
halt
```

Execute e digite `7` seguido de Enter:

```bash
python -B -m src.simulador tests/tac/teste.tac
```

Também é possível fornecer a entrada diretamente pelo terminal:

```bash
printf '7\n' | python -B -m src.simulador tests/tac/teste.tac
```

A saída esperada do programa é `7`, `14`, `21`, `28`, `35`, `42`, `49`, `56`, `63` e `70`, um valor por linha, seguida pelo rastro.

## 5. Exemplos disponíveis

Os exemplos em `tests/tac/` foram construídos manualmente, sem depender da geração automática de TAC pelo analisador semântico.

| Arquivo textual | Saída esperada (uma por linha) | Instruções executadas |
| --- | --- | ---: |
| `soma.tac` (exemplo original: 2 + 3) | `5` | 4 |
| `expressao.tac` | `-14`, `-3.5` | 12 |
| `matriz.tac` | `36` | 107 |
| `structs.tac` | `42`, `2.5`, `true`, `A`, `15` | 35 |
| `fibonacci.tac` (entrada 8) | `21` | 539 |

```bash
python -B -m src.simulador tests/tac/expressao.tac
python -B -m src.simulador tests/tac/matriz.tac
python -B -m src.simulador tests/tac/structs.tac
printf '8\n' | python -B -m src.simulador tests/tac/fibonacci.tac
```

Os quatro últimos também possuem versões `.json` equivalentes. Os resultados acima correspondem aos exemplos originais; se o conteúdo for editado, as saídas e contagens poderão mudar.

## 6. Rastro de execução

O rastro é apresentado após a saída do programa e informa:

- A ordem cronológica de execução, iniciando em 1.
- O PC (*Program Counter*) correspondente à posição da instrução, iniciando em 0.
- A representação textual da instrução executada.
- O total de instruções concluídas.

Instruções repetidas durante laços e chamadas de funções aparecem novamente no rastro. Por isso, a quantidade executada pode ser maior do que a quantidade de instruções escritas no arquivo. Rótulos também são contabilizados pelo simulador atual.

## 7. Erros e códigos de saída

| Código | Significado |
| --- | --- |
| `0` | Execução bem-sucedida. |
| `1` | TAC inválido segundo o contrato ou erro de execução. |
| `2` | Argumento inválido, erro de carregamento ou erro de sintaxe textual. |

Os diagnósticos são enviados para `stderr`. Em caso de falha, a CLI não apresenta o rastro de conclusão normal.

Para testar uma divisão por zero, substitua temporariamente o conteúdo de `teste.tac` por:

```asm
.entrada main
.dados 0
.quadro main 0 []

label rotulo[main]
div temporario[t0], constante[10], constante[0]
halt
```

Execute e consulte o código de saída imediatamente depois:

```bash
python -B -m src.simulador tests/tac/teste.tac
echo $?
```

O resultado esperado é um diagnóstico de erro de execução e código `1`.

Se ocorrer `ModuleNotFoundError: No module named 'src'`, confira se está na raiz do projeto com `pwd` e `ls`. Caso esteja utilizando um interpretador de outro ambiente virtual, verifique-o com `python --version` e `which python`.

## 8. Testes automatizados

Execute a suíte completa na raiz do projeto:

```bash
python -B -m unittest discover -s tests -p 'test_*.py' -v
```

Para testar apenas a interface do simulador ou o leitor textual:

```bash
python -B -m unittest discover -s tests -p 'test_simulador_cli.py' -v
python -B -m unittest discover -s tests -p 'test_leitor_tac.py' -v
```

Na validação reportada após a implementação do leitor textual, a suíte completa possuía 105 testes aprovados. Os testes incluem operações, memória, registradores, saltos, chamadas, recursividade, entrada e saída, erros, rastro e equivalência entre os formatos textual e JSON.

## 9. Organização do módulo

```text
src/simulador/
├── __init__.py
├── __main__.py
├── README.md
├── Simulador.py
└── core/
    ├── __init__.py
    ├── BancoRegistradores.py
    ├── MemoriaDados.py
    ├── MemoriaInstrucoes.py
    └── UnidadeOperacoes.py
```

O `__main__.py` recebe o arquivo pela linha de comando e coordena o carregamento, a execução e a apresentação do rastro. O leitor textual (`../tac/LeitorTAC.py`) e o carregamento JSON produzem a representação `ProgramaTAC`. A classe `Simulador` controla o ciclo de busca, decodificação e execução e utiliza as quatro classes do core.

Para mais detalhes sobre os modelos e o contrato, consulte [ReadMeTAC.md](../tac/ReadMeTAC.md). A integração direta com o analisador semântico e o gerador de TAC permanece em desenvolvimento.

## 10. Observações

- O tipo de entrada de `read` é inferido pelo formato digitado, pois o contrato TAC atual não informa o tipo esperado. Para operações inteiras, forneça inteiros.
- A memória verifica limites das regiões e dos quadros, mas não oferece proteção individual completa por variável ou vetor nem detecção completa de referências a quadros liberados e reutilizados.
- Não há limite automático de instruções para laços infinitos. Em um teste manual, use `Ctrl+C` para interromper uma execução que não termina.
- O formato textual é uma representação do TAC existente. Não é necessário converter as instruções para MIPS nem modificar o analisador semântico para realizar os testes deste guia.
