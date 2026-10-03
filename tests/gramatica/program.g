Program -> TypeDeclOne Program | Type ID RestoDecl

TypeDeclOne -> typedef struct { Type idList ; VarDecl } ;

RestoDecl -> ( FormalList ) { VarDecl StmtList } Program' | Array idList' ; Program

Program' -> Program | ε

VarDecl -> Type idList ; VarDecl | ε