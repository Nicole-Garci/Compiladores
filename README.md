# Compilador C-- - Entrega 2

Implementação do analisador léxico e sintático da linguagem C-- descrita nos enunciados em
`docs/Trabalho 1 - Compiladores.pdf` e `docs/Trabalho 2 - Compiladores.pdf`.

## Requisitos e execução

- Python 3.10 ou posterior.
- Nenhuma dependência externa para executar ou testar o analisador.
- Arquivos de entrada devem usar UTF-8 e extensão `.cmm`.

Na raiz do projeto:

```text
python main.py tests/arquivoTexto.cmm
```

Também é possível instalar o projeto e usar o comando `cmm`:

```text
python -m pip install -e .
cmm tests/arquivoTexto.cmm
```

Na execução atual, o parser escreve em `stdout` os não terminais visitados e
os tokens casados (`Match: ...`). Os diagnósticos sintáticos são reunidos e
exibidos em `stderr` ao final. Se o lexer encontrar erros, o parser não é
executado. O código de saída é 0 sem erros, 1 com erros léxicos ou sintáticos
e 2 quando o arquivo não pode ser processado.

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
- `src/parser/core/MotorParser.py`: implementa as produções por funções
  recursivas, casa terminais e recupera erros sintáticos.
- `src/parser/SaidaParser.py`: imprime o rastreamento da análise.
- `src/parser/GerenciadorErrosSintaticos.py`: reúne os diagnósticos sintáticos.
- `tests/gramatica/gramaticaCompleta_4.g`: gramática LL(1) usada na
  implementação; corpos e blocos vazios são aceitos por decisão do grupo.
- `docs/doc_Latex/`: fontes do relatório, incluindo o esboço da seção sintática.

## Verificação gramática

O verificador da gramática está em `tests/gramatica/analiseLl1.py`.

## Autores

- João Victor Domingos e Souza - John5626
- Nicole Garcia Montes Clemente - Nicole-Garci
- Marcelo Americo da Silva
- Davi Marques de Oliveira
