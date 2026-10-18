Gramática C--

Program –>  FunctionDecl Program |
		TypeDecl Program     |
		VarDecl Program   |
		FunctionDecl

TypeDecl --> typdedef struct {Type IdList ; VarDecl} ; TypeDecl | epsilon

VarDecl –>  Type idList ; VarDecl | epsilon

IdList –> ID Array |
	IdList, ID Array

Array –>  [ NUM ] | epsilon

FunctionDecl –> Type ID ( FormalList ) { VarDecl StmList }

FormalList –> Type ID Array FormalRest | epsilon

FormalRest –> , Type ID Array FormalRest | epsilon

Type –> int | float | bool | ID | char

StmtList –> Stmt | Stmt StmtList

Stmt –> if ( Expr ) Stmt else Stmt |
		while ( Expr ) Stmt |
		break ; |
		print ( ExprList ) ; |
		readln ( Expr ) ; |
		return Expr ;|
		{ StmtList } |
		ID ( ExprList ) ; |
		Expr ;

ExprList –> epsilon | ExprListTail

ExprListTail –> Expr | Expr , ExprListTail

Expr –> Primary |
		UnaryOp Expr |
		Expr BinOp Expr |
		Expr = Expr

Primary –> ID | NUM | LITERAL |
		‘ ASCII ‘ |
		( Expr ) |
		ID ( ExpreList ) |
		Expr [ Expr ] |
		true | false

UnaryOp –> -- | ++ | !

BinOp –>  	== | < | <= | 
			>= | > | != | + | - |
			|| | * | / | % | &&
