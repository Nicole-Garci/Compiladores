# Compilador C-- e simulador TAC

Implementação das análises léxica, sintática e semântica de C--, com geração
de código de três endereços e execução no simulador. Os enunciados das
quatro partes estão em `docs/`.

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

O parser escreve em `stdout` os não terminais visitados e os tokens casados
(`Match: ...`). Os diagnósticos são exibidos em `stderr`. O código de saída
é 0 sem erros, 1 com erros de análise ou de validação, e 2 quando um arquivo
ou a visualização da árvore não puder ser processado.

## Compilação, execução e testes

`cmm arquivo.cmm` gera `arquivo.tac.json` na pasta do fonte. Para escolher
o nome ou o caminho da saída, use `cmm arquivo.cmm -o programa.json`.
`--tac-saida` é um alias de `-o`. Os mesmos argumentos funcionam com
`python main.py`.

Use `cmm arquivo.cmm --executar` para compilar e executar em um só comando.
O terminal exibe os valores de `print` e os diagnósticos em caso de erro.
Use `-o` junto com `--executar` para escolher onde salvar o TAC. Para ver
o rastro de instruções, abra o TAC com `python -m src.simulador`.

```text
python -B main.py tests/semantico/valido_declaracoes.cmm
python -B -m src.simulador tests/semantico/valido_declaracoes.tac.json
python -B -m unittest discover -s tests
```

O exemplo imprime `0`, seguido do rastro com os PCs e as instruções
executadas. Para rodar a suíte no PowerShell em UTF-8, defina
`$env:PYTHONUTF8 = '1'` e `$env:PYTHONIOENCODING = 'utf-8'` antes dos comandos.

O semântico cadastra globais e assinaturas antes de percorrer os corpos.
Na segunda passagem, cada expressão devolve tipo e operando. Os comandos
recebem o escopo e o contexto de função, emitem TAC e informam quais caminhos
podem continuar, retornar ou terminar com `break`. A recuperação usa um
tipo de erro e mantém a análise dos outros nós. Só há exportação depois de
validar os diagnósticos e o programa TAC. A execução começa em `main()`,
que recebe zero parâmetros e retorna um tipo escalar.

As condições e os operadores lógicos exigem `bool`. Aritmética combina
`int` e `float`, enquanto atribuições, chamadas e retornos exigem tipos
compatíveis por igualdade. Em `struct`, os campos são indexados com um
literal inteiro a partir de zero, pela ordem de declaração. Vetores aceitam
expressões de índice inteiro com verificação de limites. Atribuição e
passagem de agregados usam cópia por valor.

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
- `tests/gramatica/gramaticaCompleta_5.g`: gramática LL(1) usada na
  implementação; corpos e blocos vazios são aceitos por decisão do grupo.

## Verificação gramática

O verificador da gramática está em `tests/gramatica/analiseLl1.py`.

## Autores

- João Victor Domingos e Souza - John5626
- Nicole Garcia Montes Clemente - Nicole-Garci
- Marcelo Americo da Silva
- Davi Marques de Oliveira
