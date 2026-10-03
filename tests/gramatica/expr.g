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

Stmt -> if ( Expr ) Stmt else Stmt | while ( Expr ) Stmt | break ; | print ( ExprList ) ; |	readln ( Expr ) ; |	return Expr ; |	{ StmtList } | ID ( ExprList ) ; | Expr ;

ExprList -> ε | ExprList'

ExprList' -> Expr | Expr , ExprList'

