# Compilador C-- - Entrega 2

Implementação do analisador léxico e sintático da linguagem C-- descrita nos enunciados em
`docs/Trabalho 1 - Compiladores.pdf` e `docs/Trabalho 2 - Compiladores.pdf`.

## Requisitos e execução

- Python 3.10 ou posterior.
- Nenhuma dependência externa para executar o analisador.
- `--arvore` não requer dependências externas. Para `--imagem`, instale
  [Graphviz](https://graphviz.org/download/).
- Arquivos de entrada devem usar extensão `.cmm`.

Na raiz do projeto:

```text
python main.py tests/exemplo.cmm
```

Também é possível instalar o projeto e usar o comando `cmm`:

```text
python -m pip install -e .
cmm tests/exemplo.cmm
```

Na execução atual, o parser escreve em `stdout` os não terminais visitados e
os tokens casados (`Match: ...`). Os diagnósticos são exibidos em `stderr`.
Se o lexer encontrar erros, a análise termina antes de executar o parser.
O código de saída é 0 sem erros, 1 com erros léxicos ou sintáticos e 2 quando
o arquivo ou a visualização da árvore não pode ser processado.

## Árvore de sintaxe abstrata

`Parser.analisar(tokens)` devolve a raiz `Programa` da árvore de sintaxe
abstrata, construída em memória durante o parsing. Os nós ficam em
`src/parser/ast/Nos.py`. Para visualizá-la:

```text
python main.py tests/exemplo.cmm --arvore
python main.py tests/exemplo.cmm --imagem arvore.png
```

`--arvore` imprime a árvore no fim da saída. Se houver erros sintáticos, a
árvore exibida é parcial e marca com `<erro>` as partes perdidas na
recuperação. A imagem é gerada pelo Graphviz diretamente a partir da árvore,
sem criar um arquivo temporário intermediário.

Exemplo mínimo de entrada:

```c
int main() {
    print(1);
    return 0;
}
```

O rastreamento mostra a entrada nas produções da gramática e cada token
efetivamente consumido. Os tokens inseridos durante a recuperação são
registrados no diagnóstico, sem aparecer como `Match`.

## Organização

- `main.py`: interface de linha de comando.
- `src/lexer/Lexer.py`: fachada que valida a entrada e inicia uma análise isolada.
- `src/lexer/AFD.py` e `src/lexer/AFD.json`: execução e configuração do autômato.
- `src/lexer/core`: leitura, reconhecimento por maior lexema e orquestração.
- `src/lexer/TabelaSimbolos.py`: tabela única de reservadas, símbolos fixos,
  identificadores e literais.
- `src/lexer/GerenciadorErros.py`: coleta de diagnósticos sem interromper a análise.
- `src/parser/core/FluxoTokens.py`: mantém o token corrente e avança na entrada.
- `src/parser/Parser.py`: fachada que recebe os tokens, inicia uma análise
  isolada e disponibiliza os erros sintáticos.
- `src/parser/core/ConjuntosLL1.py`: reúne os conjuntos de previsão e
  recuperação utilizados pelo motor.
- `src/parser/core/MotorParser.py`: implementa as produções por funções
  recursivas, casa terminais e recupera erros sintáticos.
- `src/parser/SaidaParser.py`: imprime o rastreamento da análise.
- `src/parser/ast/Nos.py`: nós da árvore de sintaxe abstrata.
- `src/parser/VisualizadorArvore.py`: imprime a árvore e gera imagens com Graphviz.
- `src/parser/GerenciadorErrosSintaticos.py`: reúne os diagnósticos sintáticos.
- `tests/gramatica/gramaticaCompleta_4.g`: gramática LL(1) usada na
  implementação; corpos e blocos vazios são aceitos por decisão do grupo.

## Verificação gramática

O verificador da gramática está em `tests/gramatica/analiseLl1.py`.

## Autores

- João Victor Domingos e Souza - John5626
- Nicole Garcia Montes Clemente - Nicole-Garci
- Marcelo Americo da Silva
- Davi Marques de Oliveira
