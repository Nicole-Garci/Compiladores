# Core do simulador C--

Documentação técnica de apoio ao grupo e ao relatório acadêmico definitivo.
Estado verificado em 26/11/2026, na branch `parte-3-semantico`.

A referência principal é o [Trabalho 4 — Compiladores](<Trabalho 4 - Compiladores.pdf>).
As páginas citadas são as quatro páginas físicas desse PDF. Esta documentação
não substitui o relatório acadêmico completo nem comprova atendimento às
orientações de sala de aula que não estejam registradas no repositório.

## 1. Objetivo e estado da implementação

O core fornece armazenamento de registradores, memória de dados, memória de
instruções e operações sobre valores para a futura execução do código de três
endereços (TAC) produzido na parte 3. Atende à divisão de módulos descrita no
Trabalho 4, páginas 1–3.

Usamos três classificações ao longo deste documento:

- **Implementado:** comportamento disponível nas quatro classes e verificável no código.
- **Provisório:** comportamento já implementado, mas cuja semântica precisa ser
  confirmada entre os responsáveis pelo gerador TAC e pelo simulador.
- **Pendente:** comportamento ainda não implementado, especialmente coordenação
  da execução, entrada/saída e geração de TAC a partir de expressões.

As quatro classes estão implementadas. A suíte possui 44 testes aprovados.
[Simulador.py](../src/simulador/Simulador.py) ainda contém apenas `pass`.
Portanto, o projeto ainda não executa automaticamente um programa TAC completo.
Os testes de interoperabilidade coordenam chamadas específicas aos componentes;
não constituem um executor alternativo.

## 2. Arquitetura de referência

A organização adotada é a de uma **máquina abstrata para execução direta de TAC**,
com registradores virtuais, armazenamento separado de código e dados e uma
unidade de operações. Ela se baseia na decomposição funcional apresentada no
Trabalho 4, páginas 2–3, e no [diagrama do simulador](simulador.png).

O enunciado permite uma arquitetura modificada para a linguagem intermediária
(página 1). Por isso, não é necessário emular fielmente uma ISA MIPS, gerar código
binário ou acrescentar uma tradução obrigatória para outra linguagem de máquina.
Os exemplos `ADD`, `MUL`, `SW`, `SLT` e `BEQ` da página 3 ilustram mapeamentos;
o contrato executado pelos componentes usa os opcodes TAC em minúsculas.

A separação facilita preservar os contratos entre os integrantes: a memória de
instruções conhece os modelos TAC; o banco, a memória de dados e a ULA trabalham
com valores e não dependem do analisador semântico ou do Simulador.

### Organização

| Componente | Responsabilidade implementada | Responsabilidade que não assume |
|---|---|---|
| `BancoRegistradores` | Especiais e temporários; troca do conjunto ativo | Decodificar nomes TAC, controlar chamadas ou PC |
| `MemoriaDados` | Globais, pilha, reservas e liberações LIFO | Somar FP a deslocamentos ou atualizar registradores |
| `MemoriaInstrucoes` | Validar/carregar TAC, buscar instruções e resolver rótulos | Executar instruções ou avançar PC |
| `UnidadeOperacoes` | Calcular operações sobre valores já resolvidos | Ler/escrever memória, registradores ou entrada/saída |
| `Simulador` — pendente | Coordenará os quatro componentes, PC, IR e rastro | Sua implementação não faz parte do core já concluído |

### Pipeline, ULAs e quantidade de registradores

- **Implementado:** uma classe de ULA sem estado de execução interno; cinco
  registradores especiais no banco e quantidade dinâmica de temporários ativos.
- **Decisão arquitetural para integração:** execução sequencial, sem pipeline,
  coordenada por uma instância da ULA. Ainda não há ciclo de execução implementado.
- Não há mecanismos de hazards, escalonamento, múltiplas ULAs, alocação de
  registradores físicos ou spilling. O Trabalho 4, página 1, pede explicar se
  pipeline e múltiplas ULAs existem; não obriga implementá-los.
- PC e IR serão estados da unidade de controle, separados dos cinco especiais
  armazenados no banco. Não há requisito de 32 registradores no enunciado.

## 3. BancoRegistradores

Fonte: [BancoRegistradores.py](../src/simulador/core/BancoRegistradores.py).

### Atributos

| Atributo interno | Tipo | Conteúdo |
|---|---|---|
| `_especiais` | `dict[str, object]` | Cinco nomes conhecidos |
| `_temporarios` | `dict[int, object]` | Temporários ativos, inicialmente vazio |

| Especial | Valor inicial | Papel na execução futura |
|---|---|---|
| `$zero` | `0` | Constante somente leitura |
| `$sp` | `0` | Ponteiro da pilha |
| `$fp` | `0` | Base do quadro corrente |
| `$ra` | `None` | Endereço de retorno |
| `$v0` | `None` | Valor de retorno |

Somente esses nomes são aceitos. `$pc`, `r0` e `$r0` não são aliases disponíveis.
A página 3 do enunciado descreve os papéis dos registradores; o diagrama coloca o
PC na fachada. Manter um único PC evita duplicação de estado.

### Contratos públicos

| Método | Contrato |
|---|---|
| `__init__(self) -> None` | Cria dicionários independentes por instância e o estado inicial acima |
| `ler(self, chave: str \| int) -> object` | Retorna especial conhecido ou temporário existente; não cria entradas |
| `escrever(self, chave: str \| int, valor: object) -> None` | Atualiza especial gravável ou cria/substitui temporário |
| `trocarTemporarios(self, novos: dict[int, object]) -> dict[int, object]` | Valida todo o novo conjunto, instala cópia superficial e devolve o dicionário anteriormente ativo |

Chaves inteiras devem ser não negativas; booleanos são rejeitados mesmo sendo
subclasse de `int` em Python. Strings identificam apenas especiais. A conversão
de nomes como `t0` para índices pertence ao Simulador e ainda não existe.
O contrato TAC documenta nomes string, mas não fecha formalmente sua sintaxe.

Escrever em `$zero`, inclusive escrever `0`, gera `ValueError`. Ler temporário
inexistente ou usar especial desconhecido gera `KeyError`. Tipo de chave inválido
gera `TypeError`; índice negativo gera `ValueError`.

A troca inválida não modifica o conjunto ativo. O dicionário recebido não é
compartilhado como coleção, mas seus valores permanecem por referência. O conjunto
anterior devolvido deixa de ser ativo. A troca não altera nenhum especial.

O auxiliar `_validarChave` centraliza a validação. O banco não verifica se um
valor escrito em SP, FP ou RA representa um endereço válido; esse é um invariante
a ser mantido pela coordenação. A proteção dos atributos internos é convencional
em Python: a garantia de `$zero` vale para o acesso pela API pública.

## 4. MemoriaDados

Fonte: [MemoriaDados.py](../src/simulador/core/MemoriaDados.py).

### Atributos

| Atributo interno | Tipo | Conteúdo |
|---|---|---|
| `_dadosEstaticos` | `dict[int, object]` | Posições globais de zero a `tamanhoDados - 1` |
| `_pilha` | `list[object]` | Posições locais reservadas |
| `_basesQuadros` | `list[int]` | Bases das reservas, na ordem de criação, inclusive vazias |

### Contratos públicos

| Método | Contrato |
|---|---|
| `__init__(self, tamanhoDados: int = 0) -> None` | Reserva a área global com valores `None`; pilha e registros de quadros começam vazios |
| `reservarQuadro(self, tamanho: int) -> int` | Acrescenta `tamanho` posições `None`, registra a reserva e devolve a base anterior ao crescimento |
| `liberarQuadro(self, base: int) -> None` | Exige coincidência com a base do quadro do topo; remove suas posições e um registro de reserva |
| `ler(self, regiao: str, endereco: int) -> object` | Retorna o valor da posição reservada; posição ainda não escrita retorna `None` |
| `escrever(self, regiao: str, endereco: int, valor: object) -> None` | Substitui o valor de uma posição já reservada; não expande a região |

Os auxiliares `_validarInteiro` e `_validarAcesso` verificam tipos, sinal,
identificador da região e limites.

### Organização e endereçamento

As regiões válidas são exatamente `global` e `local`. Os espaços são separados:
`global[0]` e `local[0]` não são a mesma posição.

O endereço recebido em `local` é **índice absoluto da pilha**. O Simulador deverá
calcular `FP + deslocamentoLocal` antes do acesso. A pilha cresce a partir de zero.
Endereços, tamanhos e bases devem ser inteiros não negativos e não booleanos.

O modelo usa posições, não bytes físicos de MIPS. Em
[TipoSemantico.py](../src/semantico/models/TipoSemantico.py), `TAMANHO_POSICAO = 1`
para `int`, `float`, `char` e `bool`, apesar do nome do atributo `tamanhoBytes`.
Vetores multiplicam o tamanho do elemento pelo comprimento; structs acumulam
campos. Não se deve aplicar uma escala de quatro bytes sem mudar o contrato do
produtor de endereços.

Valores são armazenados por referência. A memória pode transportar strings,
booleanos e outros objetos; isso não significa que a ULA aceite operar sobre todos
eles. `None` é estado interno inicial, não um novo literal da linguagem C--.
A política de uso de valores não inicializados durante execução ainda precisa
ser definida na coordenação.

### Quadros de ativação

`ProgramaTAC.quadros` fornece `nomeFuncao -> (tamanho, deslocamentosParametros)`.
O motor semântico atual atribui posições a parâmetros e locais; não reserva
explicitamente posições para RA, FP ou temporários.

A lista `_basesQuadros` permite distinguir a quantidade de reservas mesmo quando
elas têm tamanho zero. Cada liberação remove somente o quadro mais recente.
Bases repetidas não identificam unicamente uma ativação: se dois quadros têm a
mesma base, `liberarQuadro(base)` sempre remove o do topo, sem poder inferir qual
deles o chamador pretendia liberar.

Acessos são limitados à região reservada inteira. Não há proteção individual de
variáveis, vetores ou quadros contra acessos a outras posições ainda reservadas.
Ao liberar e reservar novamente, as posições novas recebem `None`, sem reaproveitar
os valores antigos.

A memória não mantém SP/FP nem uma pilha de endereços de retorno. O Simulador deverá
salvar/restaurar o estado de controle e chamar as APIs em ordem LIFO. O significado
exato de SP ainda precisa ser consolidado; os exemplos e testes usam a próxima
posição livre.

## 5. MemoriaInstrucoes

Fonte: [MemoriaInstrucoes.py](../src/simulador/core/MemoriaInstrucoes.py).

| Atributo interno | Tipo | Conteúdo |
|---|---|---|
| `_instrucoes` | `list[InstrucaoTAC]` | Sequência carregada, inicialmente vazia |
| `_rotulos` | `dict[str, int]` | Nome do rótulo para índice da própria instrução `label` |

| Método | Contrato |
|---|---|
| `__init__(self) -> None` | Cria memória vazia |
| `carregar(self, programa: ProgramaTAC) -> None` | Exige `ProgramaTAC`, chama `validar()`, prepara lista e mapa novos e então substitui ambos |
| `buscar(self, pc: int) -> InstrucaoTAC` | Retorna a instrução no índice informado; não altera PC nem executa código |
| `resolverRotulo(self, nome: str) -> int` | Retorna o índice do rótulo conhecido |

O carregamento preserva a ordem e as instruções `label`. A lista é copiada
superficialmente; os objetos `InstrucaoTAC`, dataclasses congeladas, são compartilhados.
Modificar posteriormente a lista do programa não modifica a coleção carregada.

Os diagnósticos de `ProgramaTAC.validar()` são reunidos em `ValueError`. Um
carregamento rejeitado preserva o conteúdo anterior; um carregamento válido o
substitui completamente, inclusive os rótulos antigos.

A validação existente verifica opcodes, aridade, posições opcionais, rótulos,
entrada e destinos dos saltos. Não valida integralmente tipos de valores,
metadados de quadros ou funções de `call`. Objetos construídos manualmente fora
dos tipos anotados de `ProgramaTAC` também não recebem garantia de diagnóstico
uniforme. A memória não substitui o analisador semântico.

PC negativo gera `ValueError`; booleano ou tipo não inteiro gera `TypeError`;
PC fora da lista gera `IndexError`. Nome não string gera `TypeError`; rótulo
inexistente, inclusive string vazia, gera `KeyError`.

## 6. UnidadeOperacoes

Fonte: [UnidadeOperacoes.py](../src/simulador/core/UnidadeOperacoes.py).
Não possui atributos de estado ou construtor próprio.

```python
executar(self, opcode: str, a: object, b: object = None) -> object
```

Recebe valores já resolvidos e devolve um resultado. Não recebe destino TAC,
memória, registradores ou PC. O auxiliar `_validarNumero` aceita somente os tipos
exatos `int` e `float`, excluindo `bool` e subclasses numéricas personalizadas.

### Os 13 opcodes implementados

A aridade abaixo é a quantidade de valores recebidos pela ULA, sem o destino TAC.

| Opcode | Aridade | Tipos aceitos | Resultado |
|---|---:|---|---|
| `add` | 2 | `int`/`float` | Soma |
| `sub` | 2 | `int`/`float` | Subtração |
| `mul` | 2 | `int`/`float` | Multiplicação |
| `div` | 2 | `int`/`float` | Inteiro truncado para zero se ambos inteiros; real caso contrário |
| `mod` | 2 | Dois `int` | Resto coerente com divisão truncada |
| `neg` | 1 | `int`/`float` | Negação aritmética |
| `not` | 1 | `bool`, `int` ou `float` | `bool`: verdadeiro para falso/zero |
| `eq` | 2 | Números ou dois `bool` | `bool`: igualdade |
| `ne` | 2 | Números ou dois `bool` | `bool`: desigualdade |
| `lt` | 2 | `int`/`float` | `bool`: menor |
| `le` | 2 | `int`/`float` | `bool`: menor ou igual |
| `gt` | 2 | `int`/`float` | `bool`: maior |
| `ge` | 2 | `int`/`float` | `bool`: maior ou igual |

### Políticas implementadas, provisórias para integração

O Trabalho 3, página 3, descreve aritmética e relações sobre `int`/`float`, mas
os documentos não fecham divisão inteira, resto, promoções e operações com `char`.
As seguintes políticas estão no código e precisam ser mantidas coerentes com o
semântico e com o gerador:

- Mistura de `int` e `float` é permitida; não se convertem strings ou booleanos
  implicitamente para números. Comparações numéricas seguem Python sem conversão
  explícita prévia de todos os valores para `float`.
- Para divisão inteira, calcula-se `abs(a) // abs(b)` e aplica-se o sinal.
  Não há conversão intermediária para `float`, inclusive para inteiros muito grandes.
- O resto é `a - quociente * b`: `div(-7, 3) == -2` e `mod(-7, 3) == -1`.
- `mod` não aceita floats. Divisor zero numérico válido gera `ZeroDivisionError`.
- `eq`/`ne` aceitam dois booleanos; não permitem misturar booleano e número.
- `not` testa zero para números e nega booleanos. Não usa a verdade genérica de
  strings, listas ou objetos.
- Strings, inclusive caracteres representados como string, não são operandos
  aceitos pela ULA. Armazenar/transportar um `char` continua possível no banco e memória.
- Não há overflow artificial de inteiros. Floats mantêm precisão, valores especiais
  e limites do Python; não há emulação de formato numérico MIPS.

`None` representa ausência de `b`. Operações binárias o rejeitam; unárias aceitam
`b` omitido ou explicitamente `None`, sem distinguir essas duas chamadas. Operando
`a=None` é rejeitado. Um segundo operando não nulo em operação unária é rejeitado.
A contagem de operandos TAC, incluindo destino, é validada separadamente.

## 7. Os 27 opcodes TAC e a futura execução

Fontes: [ContratoTAC.py](../src/tac/ContratoTAC.py) e
[ReadMeTAC.md](../src/tac/ReadMeTAC.md). A memória de instruções já armazena esses
opcodes quando estruturalmente válidos. **O despacho de todos eles no Simulador
está pendente**, mesmo quando a operação isolada da ULA já existe.

Na tabela, BR = banco, MD = memória de dados, MI = memória de instruções e ULA =
unidade de operações. As colunas de execução descrevem responsabilidades futuras,
não um executor disponível.

| Opcode | Operandos TAC, na ordem | Componentes e coordenação futura |
|---|---|---|
| `label` | rótulo | MI já indexa; Simulador tratará marcador e avanço |
| `move` | destino, origem | Simulador resolverá origem e escreverá destino em BR/MD |
| `add` | destino, esquerda, direita | Simulador resolverá valores; ULA já soma; escrever resultado |
| `sub` | destino, esquerda, direita | ULA já subtrai; leitura/escrita pelo Simulador |
| `mul` | destino, esquerda, direita | ULA já multiplica; leitura/escrita pelo Simulador |
| `div` | destino, dividendo, divisor | ULA já divide; leitura/escrita pelo Simulador |
| `mod` | destino, dividendo, divisor | ULA já calcula resto; leitura/escrita pelo Simulador |
| `neg` | destino, origem | ULA já nega aritmeticamente; escrita pelo Simulador |
| `not` | destino, origem | ULA já nega logicamente; escrita pelo Simulador |
| `eq` | destino, esquerda, direita | ULA já compara igualdade; escrita pelo Simulador |
| `ne` | destino, esquerda, direita | ULA já compara desigualdade; escrita pelo Simulador |
| `lt` | destino, esquerda, direita | ULA já compara menor; escrita pelo Simulador |
| `le` | destino, esquerda, direita | ULA já compara menor/igual; escrita pelo Simulador |
| `gt` | destino, esquerda, direita | ULA já compara maior; escrita pelo Simulador |
| `ge` | destino, esquerda, direita | ULA já compara maior/igual; escrita pelo Simulador |
| `addr` | destino, base, deslocamento | Simulador calculará endereço preservando região; formato pendente |
| `load` | destino, endereço | Simulador resolverá endereço, lerá MD e escreverá destino |
| `store` | endereço, valor | Simulador resolverá ambos e escreverá MD |
| `goto` | rótulo | MI resolve alvo; Simulador alterará PC |
| `if_true` | condição, rótulo | Simulador saltará se condição diferente de zero; MI resolve alvo |
| `if_false` | condição, rótulo | Simulador saltará se condição igual a zero; MI resolve alvo |
| `param` | valor | Simulador preparará argumentos em ordem |
| `call` | destino opcional, função, quantidade | Simulador coordenará MI, MD e BR e salvará estado |
| `return` | valor opcional | Simulador restaurará ativação e entregará retorno |
| `read` | destino | Simulador/entrada: ler e converter valor; escrever destino |
| `print` | valor | Simulador/saída: apresentar valor resolvido |
| `halt` | nenhum | Simulador encerrará a execução |

`call` tem sempre três posições; o destino pode ser `None`. `return` aceita zero
ou um operando, inclusive `None`. `param` deve aparecer na ordem dos argumentos
imediatamente antes do `call`, conforme o README TAC.

Não existem opcodes TAC `and`, `or`, `SW` ou `BEQ`. Os operadores da gramática
`&&`, `||`, `++` e `--` precisam ser traduzidos pelo gerador usando o contrato
acordado. A ausência de opcodes específicos não exige ampliar a ULA.

## 8. Tratamento de erros

São usadas exceções nativas; não existe gerenciador de erros de execução no core.

| Exceção | Situações representativas |
|---|---|
| `TypeError` | Chaves/endereços/PC com tipo inválido ou booleano; região/nome/opcode não string; operandos incompatíveis; aridade da ULA inválida |
| `ValueError` | Índice/tamanho/base negativo; escrita em zero; região desconhecida; liberação fora do topo; TAC inválido; opcode fora da ULA |
| `KeyError` | Temporário não inicializado, especial ou rótulo desconhecido |
| `IndexError` | Endereço fora da área reservada ou PC fora da lista |
| `ZeroDivisionError` | Divisão ou módulo com divisor zero de tipo aceito |

A validação ocorre antes das mutações normais: troca inválida de temporários,
carregamento rejeitado e liberação com base incompatível preservam o estado.
Não se promete recuperação de falhas de recursos, como esgotamento da memória do
processo Python.

O Simulador deverá acrescentar contexto de PC, opcode e, quando disponíveis,
linha/coluna de origem ao apresentar falhas. A orientação do Trabalho 3 de
continuar após diagnósticos semânticos não define uma obrigação de continuar uma
execução após falha de memória ou divisão por zero.

## 9. Exemplos práticos

Execute os exemplos em Python a partir da raiz do projeto. Eles usam apenas as
APIs existentes e não implementam um laço de execução.

### 9.1 Carregar TAC, calcular e guardar em memória global

```python
from src.tac.ProgramaTAC import ProgramaTAC
from src.tac.InstrucaoTAC import InstrucaoTAC
from src.tac.OperandoTAC import OperandoTAC
from src.simulador.core.BancoRegistradores import BancoRegistradores
from src.simulador.core.MemoriaDados import MemoriaDados
from src.simulador.core.MemoriaInstrucoes import MemoriaInstrucoes
from src.simulador.core.UnidadeOperacoes import UnidadeOperacoes

programa = ProgramaTAC(tamanhoDados=1, instrucoes=[
    InstrucaoTAC("label", (OperandoTAC("rotulo", "main"),)),
    InstrucaoTAC("add", (
        OperandoTAC("temporario", "t0"),
        OperandoTAC("constante", 7),
        OperandoTAC("constante", 5),
    )),
    InstrucaoTAC("halt"),
])
instrucoes = MemoriaInstrucoes()
instrucoes.carregar(programa)
banco = BancoRegistradores()
dados = MemoriaDados(programa.tamanhoDados)
ula = UnidadeOperacoes()

pc = instrucoes.resolverRotulo(programa.entrada)
soma = instrucoes.buscar(pc + 1)
resultado = ula.executar(soma.opcode, soma.operandos[1].valor,
                        soma.operandos[2].valor)
banco.escrever(0, resultado)  # Neste exemplo, t0 corresponde ao índice 0.
dados.escrever("global", 0, banco.ler(0))
assert dados.ler("global", 0) == 12
assert instrucoes.buscar(pc).opcode == "label"
assert instrucoes.buscar(pc + 2).opcode == "halt"
```

A escrita global é uma chamada explícita da demonstração; nenhuma instrução foi
automaticamente despachada. A tradução de `t0` não é feita pelo banco.

### 9.2 Reserva local e restauração de estado

Exemplo independente. Adota SP como próxima posição livre para demonstrar uma
convenção possível; essa convenção ainda precisa ser consolidada na fachada.

```python
from src.simulador.core.BancoRegistradores import BancoRegistradores
from src.simulador.core.MemoriaDados import MemoriaDados

banco = BancoRegistradores()
dados = MemoriaDados()
basePrincipal = dados.reservarQuadro(1)
banco.escrever("$fp", basePrincipal)
banco.escrever("$sp", basePrincipal + 1)
banco.escrever(0, 10)
dados.escrever("local", basePrincipal, 10)

estadoAnterior = tuple(banco.ler(n) for n in ("$fp", "$sp", "$ra"))
temporariosAnteriores = banco.trocarTemporarios({})
baseFilho = dados.reservarQuadro(2)
banco.escrever("$fp", baseFilho)
banco.escrever("$sp", baseFilho + 2)
banco.escrever("$ra", 8)  # Endereço ilustrativo; o banco não valida o código.
banco.escrever(0, 20)
dados.escrever("local", banco.ler("$fp") + 1, banco.ler(0))
assert dados.ler("local", baseFilho + 1) == 20
banco.escrever("$v0", banco.ler(0))

dados.liberarQuadro(baseFilho)
banco.trocarTemporarios(temporariosAnteriores)
for nome, valor in zip(("$fp", "$sp", "$ra"), estadoAnterior):
    banco.escrever(nome, valor)
banco.escrever(1, banco.ler("$v0"))  # Destino pertence ao chamador restaurado.
assert banco.ler(0) == 10
assert banco.ler(1) == 20
assert dados.ler("local", basePrincipal) == 10
dados.liberarQuadro(basePrincipal)
```

Chamadas aninhadas exigem guardar um estado por ativação, em ordem LIFO. A simples
existência de RA e de troca de temporários não implementa recursão automaticamente.

### 9.3 Semântica numérica e quadro vazio

```python
from src.simulador.core.UnidadeOperacoes import UnidadeOperacoes
from src.simulador.core.MemoriaDados import MemoriaDados

ula = UnidadeOperacoes()
assert ula.executar("div", -7, 3) == -2
assert ula.executar("mod", -7, 3) == -1
assert ula.executar("div", 7, 2.0) == 3.5
assert ula.executar("not", 0) is True
assert ula.executar("eq", 2, 2.0) is True

memoria = MemoriaDados()
assert memoria.reservarQuadro(0) == 0
assert memoria.reservarQuadro(0) == 0
memoria.liberarQuadro(0)
memoria.liberarQuadro(0)
# Uma terceira liberação geraria ValueError: já não há quadro reservado.
```

## 10. Resultados reais dos testes

Execução confirmada em 26/11/2026, na raiz do projeto:

```text
python -B -m unittest discover -s tests -p 'test_*.py' -v

Ran 44 tests in 0.005s

OK
```

O tempo corresponde a esta execução local e não constitui benchmark. A opção
`-B` evita a geração de bytecode. A contagem é de métodos de teste; vários usam
subtestes para múltiplos valores.

| Arquivo | Quantidade | Cobertura principal |
|---|---:|---|
| [test_banco_registradores.py](../tests/test_banco_registradores.py) | 8 | Inicialização, leitura/escrita, zero, chaves, troca, isolamento e restauração aninhada |
| [test_memoria_dados.py](../tests/test_memoria_dados.py) | 10 | Regiões, limites, tipos, posições iniciais, LIFO, quadros vazios e isolamento |
| [test_memoria_instrucoes.py](../tests/test_memoria_instrucoes.py) | 9 | Carga, identidade/ordem, cópia, diagnósticos, preservação após erro, PC, rótulos, recarga e isolamento |
| [test_unidade_operacoes.py](../tests/test_unidade_operacoes.py) | 10 | Todos os opcodes da ULA, sinais, divisão real/inteira, resto, booleanos, tipos, aridade e zero |
| [test_simulador_core.py](../tests/test_simulador_core.py) | 2 | Interoperabilidade por chamadas explícitas aos componentes |
| [test_tac_contract.py](../tests/test_tac_contract.py) | 5 | Contratos estruturais das instruções e rótulos |
| **Total** | **44** | **Todos aprovados** |

A ULA foi testada com inteiros da ordem de `10 ** 400`, incluindo divisão sem
conversão para float. Os testes negativos verificam rejeições esperadas, não falhas
da suíte.

Os dois testes de interoperabilidade cobrem:

1. TAC manual, carregamento, busca, cálculo, temporários, memória global e resolução
   de destino de salto.
2. Quadros aninhados, uso de operação carregada, memória local, preservação de
   temporários e restauração de FP, SP e RA, com transferência de retorno por V0.

Esses testes não comprovam execução de `call`, saltos ou `halt` por um Simulador,
nem o fluxo fonte → TAC gerado → execução. Tampouco transformam decisões
provisórias de tipos em requisitos acadêmicos definitivos.

## 11. Contratos para a futura classe Simulador

O [diagrama](simulador.png) prevê `executar(programa)`, `obterRastro()` e um método
interno `executarInstrucao`, com referências aos quatro componentes, `pc`, `ir` e
`rastro: list[tuple[int, InstrucaoTAC]]`. Isso é **planejado, não implementado**.

A integração deverá respeitar:

1. Carregar instruções por `MemoriaInstrucoes.carregar` e reservar globais com
   `MemoriaDados(programa.tamanhoDados)`.
2. Resolver a entrada pelo rótulo, manter PC/IR na fachada e definir o instante de
   avanço do PC. A página 3 descreve o PC como endereço da próxima instrução.
3. Preservar os índices de `label`; não removê-los sem reconstruir coerentemente
   todos os endereços. Definir se marcadores entram no rastro apresentado.
4. Resolver categorias `constante`, `temporario`, `global`, `local`, `rotulo` e
   `funcao`; não passar `OperandoTAC` diretamente à ULA esperando decodificação.
5. Traduzir nomes de temporários para índices de maneira estável e sem colisões;
   não assumir uma sintaxe mais restrita que a acordada com o gerador.
6. Somar FP ao deslocamento local e preservar a região ao representar endereços
   calculados. O formato do resultado de `addr` ainda está pendente.
7. Manter a unidade de deslocamento do semântico; definir se o argumento de `addr`
   já está escalado pelo tamanho do elemento. O contrato usa as palavras índice e
   deslocamento em fontes diferentes.
8. Preparar argumentos na ordem documentada, usar os deslocamentos de parâmetros
   de `quadros` e validar a função/quantidade conforme o contrato final.
9. Salvar estado por chamada, reservar quadro, trocar temporários e restaurar em
   ordem LIFO. Salvar RA é necessário antes que outra chamada o sobrescreva.
10. Entregar o resultado ao destino do chamador depois de restaurar seus temporários.
11. Definir término por `halt`, retorno da entrada e comportamento ao ultrapassar
    a lista; a memória sempre rejeita PC fora da faixa.
12. Definir conversões de `read`, apresentação de `print`, uso de `None` e contexto
    de erros; produzir a lista real de instruções tomadas exigida na página 1.
13. Reinicializar estado para execuções independentes; o core não oferece método
    global de reset. Novas instâncias são uma opção compatível.

## 12. Limitações e decisões pendentes

- O gerador ainda não produz toda a sequência executável a partir da AST.
  [MotorSemantico.visitarExpressao](../src/semantico/core/MotorSemantico.py) contém
  `NotImplementedError`; os metadados de endereços e quadros já são calculados.
- A CLI atual recebe fonte C-- e executa análises; não há caminho integrado para
  carregar e executar arquivo TAC no simulador.
- É necessário consolidar uma tabela de operações válidas por tipo, especialmente
  `char`, igualdade booleana, promoções e módulo. A gramática define sintaxe, não
  resolve sozinha todas essas regras.
- O Trabalho 3 exige condições booleanas na fonte (página 3), enquanto o README
  TAC define desvios por zero/não zero. São camadas distintas; o semântico deve
  garantir a regra da fonte, mesmo que a máquina intermediária seja mais permissiva.
- Formato de endereço calculado, passagem de agregados, armazenamento do estado de
  retorno e significado de SP permanecem decisões de integração.
- Não há largura fixa de inteiro, controle de recursos da máquina virtual,
  proteção por objeto de memória, heap, cache ou temporização de instruções.
  Essas funcionalidades não são exigidas explicitamente pelo Trabalho 4.
- O exemplo `SLT` seguido de `BEQ ... $zero` na página 3 aparenta inverter a condição
  de `if a < b`. Deve ser tratado como ilustração; não substitui a semântica explícita
  do contrato `if_true`.

Não há justificativa, apenas pelo enunciado, para introduzir uma arquitetura mais
sofisticada ou ampliar os opcodes. Ajustes de tipos devem decorrer de contrato
conjunto com o semântico, não de permissividade acidental do Python.

## 13. Matriz de conformidade com o Trabalho 4

A situação distingue atendimento do core de conclusão da entrega. As evidências
referem-se às classes e métodos documentados acima.

| Requisito | Página | Responsável e evidência | Situação | Ação restante |
|---|---:|---|---|---|
| Simulador para o intermediário da parte 3 | 1–2 | Core usa modelos TAC; fachada ainda vazia | Parcialmente atendido | Integrar geração e execução |
| C++ ou Python; modularidade | 1 | Quatro classes Python independentes | Atendido no core | Fundamentar decisões com bibliografia |
| Listar instruções e explicar geração | 1–2 | Contrato com 27 opcodes; tabelas deste documento | Parcialmente atendido | Documentar geração e execução reais |
| Implementar memória de instruções | 1–2 | MI: carregar, buscar, resolverRotulo | Atendido no core | Coordenar pelo Simulador |
| Implementar memória de dados | 1–2 | MD: regiões, reserva, leitura/escrita | Atendido no core | Coordenar endereços e quadros |
| Implementar unidade de operações | 1–2 | ULA com 13 opcodes | Atendido no subconjunto acordado | Consolidar tipos com o semântico |
| Separar código, dados estáticos e pilha | 2 | MI e MD separados; duas estruturas em MD | Atendido | Nenhuma correção estrutural |
| Banco de gerais e especiais | 2–3 | BR: cinco especiais e temporários virtuais | Atendido como armazenamento | Explicar natureza dinâmica no relatório |
| Zero somente leitura | 3 | BR.escrever rejeita alteração | Atendido pela API | Nenhuma |
| SP, FP, RA e valor de retorno | 3 | BR armazena; MD fornece reservas | Parcialmente atendido | Implementar atualização e restauração |
| PC, IR, saltos e chamadas | 3 | MI fornece busca/alvos; controle previsto no diagrama | Fora do escopo executável do core | Implementar no Simulador |
| Receber arquivo TAC | 2 | ProgramaTAC.carregar existe | Parcialmente atendido | Ligar carregador à fachada/CLI |
| Ciclo busca–decodificação–execução | 2 | Busca implementada; despacho ausente | Parcialmente atendido | Implementar ciclo sequencial |
| Lista final das instruções tomadas | 1 | Rastro apenas previsto no diagrama | Fora do escopo do core; pendente | Registrar e apresentar execução real |
| Arquivo de entrada por CLI | 3 | main.py ainda não executa TAC | Fora do escopo do core; pendente | Integrar modo de execução |
| Gramática C-- da parte 1 | 3–4 | Modelos compatíveis; geração/operações por tipo incompletas | Parcialmente atendido | Concluir semântico e integração |
| Título, visão geral, módulos e decisões | 1 | Este material oferece documentação técnica | Parcialmente atendido na entrega | Incorporar ao relatório definitivo |
| Arquitetura, quantidade/comportamento dos registradores | 1 | Seções 2–3 | Atendido neste material técnico | Acrescentar fundamentação acadêmica |
| Informar pipeline e múltiplas ULAs | 1 | Seção 2: ausência de pipeline; uma ULA planejada | Atendido como decisão documentada | Confirmar na execução integrada |
| Testes, resultados e casos com erros | 2 | 44 testes; resultados na seção 10 | Parcialmente atendido | Casos fonte → TAC → execução e análise por etapa |
| Conclusão | 2 | Avaliação técnica na seção 15 | Parcialmente atendido | Conclusão experimental após integração |
| Referências e seções específicas de livros | 1–2 | Fontes locais consultadas listadas abaixo | Parcialmente atendido | Incluir literatura efetivamente utilizada |
| Ao menos três referências por seção | 2 | Não demonstrado por esta documentação | Não atendido | Cumprir no relatório acadêmico definitivo |
| Utilizar bibliografia disponibilizada | 3 | Lista externa da disciplina não identificada aqui | Comprovação pendente | Identificar e consultar os materiais indicados |

O enunciado não obriga pipeline, múltiplas ULAs, 32 registradores, overflow de
32 bits ou os mnemônicos dos exemplos como ISA obrigatória. Também não informa,
nesse PDF, prazo, nome de arquivo ou quantidade mínima de testes.

## 14. Referências efetivamente consultadas e pendências bibliográficas

### Fontes acadêmicas locais

- [Trabalho 4 — Compiladores](<Trabalho 4 - Compiladores.pdf>): referência principal,
  lida integralmente. Páginas 1–2: requisitos e documentação; páginas 2–3:
  funcionamento e componentes; página 3: registradores, exemplos e CLI;
  página 4: remissão à gramática da parte 1.
- [Trabalho 3 — Compiladores](<Trabalho 3 - Compiladores.pdf>): contexto da geração
  TAC. Página 3: regras de expressões e condições; páginas 4–5: TAC, temporários,
  vetores e saltos; páginas 6–7: erros e saída para a parte 4.
- [Trabalho 1 — Compiladores](<Trabalho 1 - Compiladores.pdf>): consultado quanto à
  gramática C--, também reproduzida em [gramaticaInicial.md](gramatica/gramaticaInicial.md).

### Fontes internas de projeto

- [Diagrama do simulador](simulador.png) e [diagrama semântico](semantico.png).
- [README TAC](../src/tac/ReadMeTAC.md) e [ContratoTAC.py](../src/tac/ContratoTAC.py).
- [ProgramaTAC.py](../src/tac/ProgramaTAC.py),
  [InstrucaoTAC.py](../src/tac/InstrucaoTAC.py) e
  [OperandoTAC.py](../src/tac/OperandoTAC.py).
- As quatro classes do core e os seis arquivos de testes vinculados neste documento.
- [TipoSemantico.py](../src/semantico/models/TipoSemantico.py),
  [MotorSemantico.py](../src/semantico/core/MotorSemantico.py),
  [Simulador.py](../src/simulador/Simulador.py) e [main.py](../main.py).

Essas fontes registram requisitos e evidências; não substituem automaticamente
as referências de artigos e livros exigidas pelo enunciado. Não foram acrescentados
autores, edições ou capítulos de obras que não tenham sido consultadas.

**Pendente para o relatório definitivo:** identificar a bibliografia disponibilizada
na disciplina; consultar e citar as fontes que fundamentam arquitetura, TAC,
registradores, quadros e operações; informar as seções dos livros utilizadas e
atender à exigência literal de pelo menos três referências em cada seção
(Trabalho 4, página 2). Não se declara essa exigência cumprida com os links internos.

## 15. Avaliação técnica

O core está implementado e testado nas responsabilidades documentadas. A estrutura
é compatível com a arquitetura modificada permitida pelo Trabalho 4, sem necessidade
de acrescentar mecanismos de hardware não solicitados.

A conclusão acadêmica da parte 4 depende do Simulador, da geração TAC, da CLI,
do rastro e dos resultados completos. A confirmação das políticas provisórias
de tipos e endereços deve preceder a afirmação de compatibilidade integral com
programas C--. Esta documentação serve como contrato de integração e material
de apoio, não como declaração de entrega acadêmica concluída.
