# O que muda nesta versão experimental

`Compiladores/` continua intacta no commit `97caf17`. Para a revisão
compartilhada, a branch experimental usa como base o commit remoto `514f5ae`
(`Finalização do simulador`), que acrescenta a leitura de TAC em texto. Assim,
a proposta inclui também esse trabalho recente do grupo.

Neste repositório, a branch `main` guarda essa base atualizada e a branch
`review/semantico-tac` contém a proposta semântica. A pasta `Compiladores/`
permanece intacta; dentro de `copia experimental/`, as mudanças estão somente
na branch de revisão.

## Em poucas palavras

Antes, o projeto já reconhecia o texto C--, verificava sua estrutura e tinha
um simulador capaz de executar TAC escrito separadamente. Esta mudança liga as
partes: depois de verificar o programa, o compilador gera o TAC e pode pedir ao
simulador para executá-lo.

```text
arquivo .cmm → leitura e análise → verificação de nomes e tipos → TAC → simulador
```

Sem a opção `--executar`, o compilador só analisa e traduz o programa. Com
`--executar`, também roda o resultado. A opção `--tac arquivo.json` guarda a
tradução em um arquivo que pode ser executado depois.

## O que foi alterado e por quê

### Análise semântica e geração do programa

| Arquivo | O que faz agora | Por quê |
|---|---|---|
| `src/semantico/core/MotorSemantico.py` | Percorre a árvore do parser, verifica declarações e tipos e transforma expressões, comandos, funções, vetores e `structs` em instruções TAC. | Completa a passagem do texto C-- para o formato que o simulador já entende. |
| `src/semantico/models/ResultadoExpressao.py` | Guarda o tipo da expressão e distingue seu valor do endereço onde ela pode ser lida ou alterada. Também marca parâmetros agregados que guardam um endereço. | Evita confundir, por exemplo, o endereço de um vetor passado a uma função com o endereço do parâmetro que guarda esse endereço. |
| `src/semantico/models/TipoSemantico.py` | Expõe o tamanho em posições da memória virtual e diferencia `struct` de vetor. | O simulador trabalha com posições numeradas; esses tamanhos não são bytes. |
| `src/semantico/AnalisadorSemantico.py` | Apresenta tamanhos e deslocamentos como posições na tabela exibida ao usuário. | Faz a saída refletir a unidade realmente usada pelo simulador. |
| `main.py` | Aceita `--tac ARQUIVO` e `--executar`. | Permite guardar o resultado ou percorrer o fluxo completo pela linha de comando. |

### Ligação com o TAC e com o simulador

| Arquivo | O que foi ajustado | Por quê |
|---|---|---|
| `src/tac/ContratoTAC.py` | A instrução `read` pode trazer o tipo esperado, além do destino. | A leitura de entrada precisa saber se deve receber `int`, `float`, `bool` ou `char`. |
| `src/simulador/Simulador.py` | Lê e valida a entrada conforme o tipo informado. Também continua aceitando TAC antigo, sem tipo explícito. | Evita interpretar uma entrada pelo conteúdo quando o compilador já sabe o tipo da variável. |
| `src/simulador/core/UnidadeOperacoes.py` | Compara caracteres de um caractere usando `==` e `!=`. | Faz as comparações de `char` aceitas pelo semântico também funcionarem durante a execução. |
| `src/tac/ReadMeTAC.md` | Documenta posições virtuais, leitura com tipo e o fluxo atualizado. | Mantém o contrato do TAC alinhado ao código. |

O lexer, a gramática e o parser não precisaram mudar para esta implementação.

## Regras para `struct`

Os campos são acessados por posição, na ordem em que aparecem na declaração:

```c
typedef struct {
    int codigo;
    float nota;
} Registro;

int main() {
    Registro r;
    r[0] = 12;       // primeiro campo: codigo
    r[1] = 8.5;      // segundo campo: nota
    print(r[0]);
    return 0;
}
```

O índice precisa ser um número inteiro constante e estar dentro dos limites. O
tipo do campo é mantido: por isso `r[0]` é `int` e `r[1]` é `float`.

Para manter a implementação desta etapa pequena, ela não aceita `p.campo`,
vetores de `struct`, campos que sejam vetores ou campos que sejam outras
`structs`. Funções também não podem retornar vetores ou `structs`.

## Comportamento que vale conhecer

- Cada valor simples ocupa uma posição na memória virtual. Vetores e `structs`
  ocupam várias posições consecutivas.
- Variáveis globais começam com `0`, `0.0`, `false` ou caractere nulo. Variáveis
  locais não recebem um valor automaticamente.
- `int` pode ser convertido para `float`. A conversão automática de `float`
  para `int` é recusada.
- Vetores e `structs` passados a funções compartilham os dados originais. Uma
  função pode, portanto, alterar o agregado recebido.
- Atribuir uma `struct` copia seus campos; retornar uma `struct` não é
  suportado.
- Índices constantes de vetor são conferidos durante a análise. Um índice
  calculado durante a execução não recebe verificação do limite daquele vetor.
- A gramática atual exige `else` em `if` e só permite declarações locais no
  começo do corpo da função, não dentro de blocos internos.

O ponto de passagem de `struct` por referência merece confirmação do grupo se
o enunciado exigir cópia por valor.

## Testes e arquivos de apoio

| Arquivo | Mudança | Motivo |
|---|---|---|
| `tests/test_semantico.py` | Adiciona casos que passam do lexer ao simulador, incluindo funções, tipos, entrada, vetores, `structs` e erros esperados. | Cobrir o fluxo completo e as regras semânticas novas. |
| `tests/test_unidade_operacoes.py` | Atualiza as expectativas para permitir igualdade e diferença entre caracteres de um caractere. | Manter o teste da unidade de operações coerente com o simulador. |
| `tests/semantico/valido_declaracoes.cmm` | Substitui um campo vetor de uma `struct` por um campo escalar. | O modelo atual ainda não aceita vetores como campos de `struct`. |
| `tests/semantico/valido_struct_nomeado.cmm` | Simplifica `structs` aninhadas, campos vetoriais e vetores de `struct`. | Deixar este exemplo dentro das limitações desta etapa. |
| `tests/semantico/exemplo_incremento.cmm` | Adiciona um programa curto que altera e imprime variáveis. | Dar um exemplo fácil de executar pela CLI. |
| `README.md` | Explica como analisar, salvar o TAC, executar o programa e ver a árvore. | Dar um ponto de entrada para quem vai usar o compilador. |
| `docs/GuiaSemanticoTAC.md` | Explica como a árvore vira instruções e indica métodos importantes para leitura do código. | Ajudar quem quer entender a implementação por dentro. |
| `README_MUDANCAS.md` | Registra as diferenças, motivos, regras, limites e como desfazer a mudança. | Facilitar a revisão pelo grupo e preservar o caminho de volta. |

## Exemplos para acompanhar a execução

`tests/semantico/exemplo_incremento.cmm` é um exemplo curto: declara duas
variáveis, altera seus valores e imprime o resultado. Execute-o assim:

```sh
python main.py tests/semantico/exemplo_incremento.cmm --executar
```

Os testes automatizados do semântico estão em `tests/test_semantico.py`. Para
executar a suíte completa:

```sh
python -m unittest discover -s tests -v
```

Esta preparação não reexecutou a suíte. Os comandos acima permitem ao grupo
repetir as verificações na cópia compartilhada.

## Como revisar e desfazer

Para voltar à base ou retornar à revisão:

```sh
git switch main
git switch review/semantico-tac
```

Na branch de revisão, estes comandos mostram o commit e os arquivos que ele
altera:

```sh
git show --stat HEAD
git diff 514f5ae..HEAD
```

O remoto do projeto já está configurado como `origin`. Depois de autenticar-se
no GitHub neste computador, publique somente a branch de revisão com:

```sh
git push -u origin review/semantico-tac
```

Isso cria uma branch separada no GitHub; não envia alterações para `main` nem
para `parte-3-semantico`.

Se o grupo decidir não manter a mudança, `git revert HEAD` cria um novo commit
que desfaz o commit experimental e preserva o histórico. Isso é mais seguro
para uma branch compartilhada do que apagar commits já publicados. A branch
`main` continua na base, e a pasta `Compiladores/` permanece intacta.

Para entender o caminho por dentro do compilador, consulte
[`docs/GuiaSemanticoTAC.md`](docs/GuiaSemanticoTAC.md). O formato das instruções
está descrito em [`src/tac/ReadMeTAC.md`](src/tac/ReadMeTAC.md).

## Arquivos principais para uma integração futura

Para levar a geração semântica a outra cópia do projeto, as mudanças principais
estão nestes arquivos:

1. `src/semantico/AnalisadorSemantico.py`
2. `src/semantico/core/MotorSemantico.py`
3. `src/semantico/models/ResultadoExpressao.py`
4. `src/semantico/models/TipoSemantico.py`
5. `src/tac/ContratoTAC.py`
6. `src/simulador/Simulador.py`
7. `src/simulador/core/UnidadeOperacoes.py`

`main.py` inclui as opções para salvar e executar o TAC. Os arquivos de
documentação e os testes ajudam a revisar e explicar a implementação.
