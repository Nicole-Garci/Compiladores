Program -> TypeDeclOne Program | Type ID RestoDecl

TypeDeclOne -> typedef struct { Type idList ; VarDecl } ;

RestoDecl -> ( FormalList ) { Body } Program' | Array idList' ; Program

Program' -> Program | ε

VarDecl -> Type idList ; VarDecl | ε

Body -> PrimType idList ; Body | ID BodyId | StmtNoId StmtList | ε

BodyId -> idList ; Body | IdExprRest ; StmtList

IdExprRest -> CallOpt Index' Mul' Add' Rel' Equality' And' Or' Assign'

PrimType -> int | float | bool | char

StmtNoId -> if ( Expr ) Stmt else Stmt | while ( Expr ) Stmt | break ; | print ( ExprList ) ; | readln ( Expr ) ; | return Expr ; | { StmtList } | ExprNoId ;

ExprNoId -> UnaryOp UnaryExpr Mul' Add' Rel' Equality' And' Or' Assign' | AtomNoId Index' Mul' Add' Rel' Equality' And' Or' Assign'

AtomNoId -> NUM_INT | NUM_FLOAT | LITERAL | ASCII | ( Expr ) | true | false

idList -> ID Array idList'

idList' -> , ID Array idList' | ε

Array -> [ NUM_INT ] | ε

FormalList -> Type ID Array FormalRest | ε

FormalRest -> , Type ID Array FormalRest | ε

Type -> int | float | bool | ID | char

StmtList -> Stmt StmtList | ε

Stmt -> if ( Expr ) Stmt else Stmt | while ( Expr ) Stmt | break ; | print ( ExprList ) ; | readln ( Expr ) ; | return Expr ; | { StmtList } | Expr ;

ExprList -> ε | ExprList'

ExprList' -> Expr RestoExprList

RestoExprList -> , ExprList' | ε

Expr -> AssignExpr

AssignExpr -> OrExpr Assign'

Assign' -> = AssignExpr | ε

OrExpr -> AndExpr Or'

Or' -> || AndExpr Or' | ε

AndExpr -> EqualityExpr And'

And' -> && EqualityExpr And' | ε

EqualityExpr -> RelExpr Equality'

Equality' -> == RelExpr Equality' | != RelExpr Equality' | ε

RelExpr -> AddExpr Rel'

Rel' -> < AddExpr Rel' | <= AddExpr Rel' | > AddExpr Rel' | >= AddExpr Rel' | ε

AddExpr -> MulExpr Add'

Add' -> + MulExpr Add' | - MulExpr Add' | ε

MulExpr -> UnaryExpr Mul'

Mul' -> * UnaryExpr Mul' | / UnaryExpr Mul' | % UnaryExpr Mul' | ε

UnaryExpr -> UnaryOp UnaryExpr | Primary

Primary -> Atom Index'

Index' -> [ Expr ] Index' | ε

Atom -> ID CallOpt | NUM_INT | NUM_FLOAT | LITERAL | ASCII | ( Expr ) | true | false

CallOpt -> ( ExprList ) | ε

UnaryOp -> -- | ++ | !