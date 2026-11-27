# Compilador C--

Este projeto lê programas escritos em C--, verifica se estão bem formados e,
quando não encontra erros, traduz o programa para uma lista de instruções que o
simulador consegue executar.

## Requisitos e primeira execução

- Python 3.10 ou posterior.
- Nenhuma biblioteca externa para compilar ou executar o simulador.
- Graphviz é necessário somente para salvar a árvore como imagem.
- Os arquivos de entrada usam a extensão `.cmm`.

Na raiz do projeto:

```sh
python main.py tests/exemplo.cmm
```

Opcionalmente, instale o projeto para usar o comando `cmm`:

```sh
python -m pip install -e .
cmm tests/exemplo.cmm
```

O compilador trabalha em etapas: o **lexer** reconhece as palavras e símbolos;
o **parser** verifica se eles estão na ordem permitida pela gramática; o
**analisador semântico** verifica nomes, escopos e tipos. Se essas etapas
terminarem sem erro, o compilador já produziu o TAC, uma lista de instruções
simples usada pelo simulador.

Por padrão, o programa-fonte é analisado, mas não executado. Para executá-lo:

```sh
python main.py tests/semantico/exemplo_incremento.cmm --executar
```

O simulador mostra os valores impressos pelo programa e, ao final, o rastro das
instruções executadas. Se o programa usar `readln`, o simulador espera a entrada
no terminal.

## Opções da linha de comando

- `--executar`: executa o TAC produzido e mostra o rastro da execução.
- `--tac ARQUIVO.json`: salva o TAC em um arquivo JSON. Pode ser combinado com
  `--executar`.
- `--tabela`: mostra os tipos e as posições reservadas para variáveis e
  funções.
- `--arvore`: imprime a árvore criada pelo parser.
- `--imagem ARQUIVO.png`: salva a árvore como imagem (requer Graphviz).

Se houver um erro de sintaxe, `--arvore` ainda pode mostrar a parte da árvore
que o parser conseguiu construir.

Exemplos:

```sh
python main.py tests/semantico/exemplo_incremento.cmm --tac programa.json
python main.py tests/semantico/exemplo_incremento.cmm --tac programa.json --executar
python main.py tests/exemplo.cmm --arvore
python main.py tests/exemplo.cmm --imagem arvore.png
```

O simulador também executa arquivos TAC em texto (`.tac`) ou JSON:

```sh
python -m src.simulador programa.json
python -m src.simulador tests/tac/soma.tac
```

## Comportamento e limites desta versão

- Sem erros, o comando termina com código `0`; erros léxicos, sintáticos ou
  semânticos terminam com código `1`; problemas ao abrir arquivos ou criar
  imagens terminam com código `2`.
- O parser mostra seu rastreamento durante a análise. Diagnósticos de erro são
  enviados ao `stderr`.
- Variáveis globais começam com valor padrão (`0`, `0.0`, `false` ou caractere
  nulo). Variáveis locais precisam receber um valor antes de serem lidas.
- `int` pode ser convertido para `float`; conversão automática de `float` para
  `int` é recusada.
- Campos de `struct` são acessados pela posição declarada, como `p[0]` e
  `p[1]`. Campos chamados por nome, como `p.x`, ainda não são aceitos.
- Há limites adicionais para vetores e `structs`; eles estão explicados em
  [`README_MUDANCAS.md`](README_MUDANCAS.md).

Para uma explicação do caminho da árvore até o simulador, consulte
[`docs/GuiaSemanticoTAC.md`](docs/GuiaSemanticoTAC.md). O formato das instruções
está em [`src/tac/ReadMeTAC.md`](src/tac/ReadMeTAC.md).

## Testes

Para executar os testes automatizados:

```sh
python -m unittest discover -s tests -v
```

O verificador da gramática LL(1) fica em `tests/gramatica/analiseLl1.py`.

## Autores

- João Victor Domingos e Souza - John5626
- Nicole Garcia Montes Clemente - Nicole-Garci
- Marcelo Americo da Silva
- Davi Marques de Oliveira
