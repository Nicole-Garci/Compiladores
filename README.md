# Compilador C-- - Entrega 1

Implementação do analisador léxico da linguagem C-- descrita no enunciado em
`docs/Trabalho 1 - Compiladores.pdf`. O programa reconhece o maior lexema,
descarta comentários `/* ... */`, consulta todos os lexemas válidos em uma
tabela de símbolos e acumula erros com linha e coluna até emitir `EOF`.

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

Os tokens válidos são escritos em `stdout`, um por linha. Os diagnósticos são
escritos em `stderr`. O código de saída é 0 em uma análise sem erros, 1 quando
há erros léxicos e 2 quando o arquivo não pode ser processado.

Exemplo para `if(x1 <= 32) b = 10;`:

```text
IF
LPARENT
ID.x1
LEQ
NUMINT.32
RPARENT
ID.b
ASSIGN
NUMINT.10
SEMICOLON
EOF
```

## Organização

- `main.py`: interface de linha de comando.
- `src/Lexer.py`: fachada que valida a entrada e inicia uma análise isolada.
- `src/AFD.py` e `src/AFD.json`: execução e configuração do autômato.
- `src/core/`: leitura, reconhecimento por maior lexema e orquestração.
- `src/TabelaSimbolos.py`: tabela única de reservadas, símbolos fixos,
  identificadores e literais.
- `src/GerenciadorErros.py`: coleta de diagnósticos sem interromper a análise.
- `tests/test_lexer.py`: testes automatizados de regressão.
- `docs/doc_Latex/`: fontes, evidências e instruções do relatório.

## Testes

```text
python -m unittest discover -s tests -p "test_*.py" -v
python docs/doc_Latex/scripts/verificar_implementacao.py
```

A suíte cobre todas as classes de operadores e delimitadores, palavras
reservadas, identificadores, números, strings, caracteres, maior lexema,
comentários completos e incompletos, recuperação de erros, CRLF, tabela de
símbolos, reinicialização entre arquivos, CLI e entradas extensas.

## Documentação da entrega

O relatório final atualizado está em
`output/pdf/Compilador_C--_Entrega_1.pdf`. As instruções de reprodução e
compilação ficam em `docs/doc_Latex/README.md`.

## Autores

- João Victor Domingos e Souza - John5626
- Nicole Garcia Montes Clemente - Nicole-Garci
- Marcelo Americo da Silva
- Davi Marques de Oliveira

## Continuidade do projeto

As próximas etapas são análise sintática, análise semântica e simulação. Os
tokens mantêm tipo, lexema, posição e índice de símbolo para que essas fases
possam reutilizar a saída desta entrega sem refazer a análise léxica.
