# Compilador C--

Este projeto implementa um compilador para a linguagem C-- a ser desenvolvido de forma incremental em quatro partes:

1. Analisador Léxico
2. Analisador Sintático
3. Analisador Semântico
4. Simulador do Compilador

---

## Autor

- **João Victor Domingos e Souza** - [John5626]
- **NOME** - [GitHub]
- **NOME** - [GitHub]
- **NOME** - [GitHub]

---
## Organização das branches

A branch `main` deve conter sempre a parte mais recente completamente implementada, revisada e finalizada. Ao término das quatro partes, ela representará a versão final do trabalho.

Cada parte deve ser desenvolvida em uma nova branch, começando pelo Analisador Léxico. Nunca implemente diretamente na `main`. Nomes a serem usados:

- `parte-1-lexer`
- `parte-2-sintatico`
- `parte-3-semantico`
- `parte-4-simulador`

Sempre que realizar uma alteração, crie a nova branch a partir da branch que está em implementação. Ao finalizar, abra um PR para a branch e marque os integrantes para revisão. 
O merge para main deve ocorrer sempre ao final de cada entrega do trabalho.

---
## Padrões de implementação

- Uma classe por arquivo, com módulos e classes em `CamelCase`.
- Métodos e variáveis em `lowerCamelCase`.
- `Lexer.py` funciona como fachada do analisador léxico.
- `src/core` concentra leitura, reconhecimento e motor de execução.
- `src/models` contém apenas os modelos de dados compartilhados.
- Cada parte deve preservar o funcionamento das partes anteriores.
- Toda implementação deve incluir testes e passar pela revisão do grupo antes do merge.
---