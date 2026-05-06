"""
Takes the flat token list produced by the Lexer and builds an AST.

Every grammar rule is a method. The method either:
  - Returns an ASTNode on success, OR
  - Raises ParseError with a message and line number.

Grammar implemented:
    program    ::= stmt* EOF
    stmt       ::= decl | assign | if_stmt | while_stmt | for_stmt | block
    decl       ::= ('int' | 'string') IDENT ';'
    assign     ::= IDENT '=' expr ';'
    if_stmt    ::= 'if' cmp_expr 'then' block ( 'else' block )?
    while_stmt ::= 'while' cmp_expr block
    for_stmt   ::= 'for' IDENT '=' expr 'to' expr block
    block      ::= '{' stmt* '}'
    cmp_expr   ::= expr ('>' | '<' | '==') expr     (operator is mandatory)
    expr       ::= term ( ('+' | '-') term )*
    term       ::= factor ( '*' factor )*
    factor     ::= '-' factor | atom
    atom       ::= IDENT | INT_LIT | STRING_LIT | '(' expr ')'

Operator precedence (lowest to highest):
    > < ==  (comparison)
    + -     (additive)
    *       (multiplicative)
    unary - (negation)
    atoms (identifiers, literals, parenthesised expressions)
"""

from typing import List, Optional

from lexer import Token, TokenType
from ast_nodes import (
    ASTNode, ProgramNode, DeclNode, AssignNode, IfNode,
    WhileNode, ForNode, BlockNode, BinOpNode, UnaryOpNode,
    IdentNode, NumNode, StringNode,
)


class ParseError(Exception):
    """Raised on any syntax error found by the parser."""
    pass


class Parser:
    """
    Recursive descent parser.

    Usage:
        parser = Parser(tokens)   # tokens from Lexer.tokenize()
        ast    = parser.parse()   # returns ProgramNode
    """

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0   # index of the current (not yet consumed) token

    # Helper utilities
    def _current(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        """Return the token at pos+offset without consuming anything."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def _advance(self) -> Token:
        """Consume and return the current token, then move forward."""
        tok = self.tokens[self.pos]
        if tok.type is not TokenType.EOF:
            self.pos += 1
        return tok

    def _expect(self, ttype: TokenType) -> Token:
        """
        Consume the current token if it matches ttype.
        Raises ParseError otherwise.
        """
        tok = self._current()
        if tok.type is not ttype:
            raise ParseError(
                f"Expected {ttype.name} but found {tok.type.name} "
                f"({tok.value!r}) at line {tok.line}, col {tok.col}"
            )
        return self._advance()

    def _match(self, *types: TokenType) -> bool:
        """Return True if the current token's type is in types (no consume)."""
        return self._current().type in types

    # Entry point
    def parse(self) -> ProgramNode:
        """Parse the entire token stream and return the program AST root."""
        statements: List[ASTNode] = []

        while not self._match(TokenType.EOF):
            stmt = self._parse_stmt()
            statements.append(stmt)

        self._expect(TokenType.EOF)
        return ProgramNode(statements)

    # Statement rules
    def _parse_stmt(self) -> ASTNode:
        """
        stmt ::= decl | assign | if_stmt | while_stmt | for_stmt | block

        Dispatch using one token of lookahead:
          - INT / STRING keyword  →  declaration
          - IF keyword            →  if statement
          - WHILE keyword         →  while statement
          - FOR keyword           →  for statement
          - LBRACE                →  block
          - IDENT followed by '=' →  assignment
        """
        tok = self._current()

        if tok.type in (TokenType.INT, TokenType.STRING):
            return self._parse_decl()

        if tok.type is TokenType.IF:
            return self._parse_if()

        if tok.type is TokenType.WHILE:
            return self._parse_while()

        if tok.type is TokenType.FOR:
            return self._parse_for()

        if tok.type is TokenType.LBRACE:
            return self._parse_block()

        if tok.type is TokenType.IDENT and self._peek().type is TokenType.EQUALS:
            return self._parse_assign()

        raise ParseError(
            f"Unexpected token {tok.type.name} ({tok.value!r}) "
            f"at line {tok.line}, col {tok.col}"
        )

    def _parse_decl(self) -> DeclNode:
        """decl ::= ('int' | 'string') IDENT ';'"""
        type_tok = self._advance()          # consume 'int' or 'string'
        var_type = type_tok.value           # 'int' or 'string'
        name_tok = self._expect(TokenType.IDENT)
        self._expect(TokenType.SEMICOLON)
        return DeclNode(var_type, name_tok.value, line=type_tok.line)

    def _parse_assign(self) -> AssignNode:
        """assign ::= IDENT '=' expr ';'"""
        name_tok = self._expect(TokenType.IDENT)
        self._expect(TokenType.EQUALS)
        expr = self._parse_expr()
        self._expect(TokenType.SEMICOLON)
        return AssignNode(name_tok.value, expr, line=name_tok.line)

    def _parse_if(self) -> IfNode:
        """if_stmt ::= 'if' cmp_expr 'then' block ( 'else' block )?"""
        if_tok = self._expect(TokenType.IF)
        condition = self._parse_cmp_expr()
        self._expect(TokenType.THEN)
        then_block = self._parse_block()

        else_block: Optional[BlockNode] = None
        if self._match(TokenType.ELSE):
            self._advance()  # consume 'else'
            else_block = self._parse_block()

        return IfNode(condition, then_block, else_block, line=if_tok.line)

    def _parse_while(self) -> WhileNode:
        """while_stmt ::= 'while' cmp_expr block"""
        while_tok = self._expect(TokenType.WHILE)
        condition = self._parse_cmp_expr()
        body = self._parse_block()
        return WhileNode(condition, body, line=while_tok.line)

    def _parse_for(self) -> ForNode:
        """
        for_stmt ::= 'for' IDENT '=' expr 'to' expr block

        The loop variable must already be declared as an int (checked by
        the semantic analyzer). The body executes with the variable
        ranging inclusively from init to limit.
        """
        for_tok = self._expect(TokenType.FOR)
        var_tok = self._expect(TokenType.IDENT)
        self._expect(TokenType.EQUALS)
        init_expr = self._parse_expr()
        self._expect(TokenType.TO)
        limit_expr = self._parse_expr()
        body = self._parse_block()
        return ForNode(
            var_tok.value, init_expr, limit_expr, body, line=for_tok.line
        )

    def _parse_block(self) -> BlockNode:
        """block ::= '{' stmt* '}'"""
        lbrace = self._expect(TokenType.LBRACE)
        statements: List[ASTNode] = []

        while not self._match(TokenType.RBRACE, TokenType.EOF):
            statements.append(self._parse_stmt())

        self._expect(TokenType.RBRACE)
        return BlockNode(statements, line=lbrace.line)

    # Expression rules (handle operator precedence)
    def _parse_cmp_expr(self) -> ASTNode:
        """
        cmp_expr ::= expr ('>' | '<' | '==') expr

        The comparison operator is mandatory: 'if'/'while' conditions
        must be a real comparison, not a bare expression.
        """
        left = self._parse_expr()

        if self._match(TokenType.GT, TokenType.LT, TokenType.EQ):
            op_tok = self._advance()
            right = self._parse_expr()
            return BinOpNode(op_tok.value, left, right, line=op_tok.line)

        tok = self._current()
        raise ParseError(
            f"Expected comparison operator ('>', '<', or '==') but found "
            f"{tok.type.name} ({tok.value!r}) at line {tok.line}, col {tok.col}"
        )

    def _parse_expr(self) -> ASTNode:
        """expr ::= term ( ('+' | '-') term )*"""
        node = self._parse_term()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._parse_term()
            node = BinOpNode(op_tok.value, node, right, line=op_tok.line)

        return node

    def _parse_term(self) -> ASTNode:
        """term ::= factor ( '*' factor )*"""
        node = self._parse_factor()

        while self._match(TokenType.STAR):
            op_tok = self._advance()
            right = self._parse_factor()
            node = BinOpNode("*", node, right, line=op_tok.line)

        return node

    def _parse_factor(self) -> ASTNode:
        """
        factor ::= '-' factor | atom
        atom   ::= IDENT | INT_LIT | STRING_LIT | '(' expr ')'

        Unary minus is right-associative, so '--x' parses as '-(-x)'.
        """
        tok = self._current()

        # Unary minus (highest precedence except for atoms themselves).
        if tok.type is TokenType.MINUS:
            self._advance()
            operand = self._parse_factor()
            return UnaryOpNode("-", operand, line=tok.line)

        if tok.type is TokenType.IDENT:
            self._advance()
            return IdentNode(tok.value, line=tok.line)

        if tok.type is TokenType.INT_LIT:
            self._advance()
            return NumNode(int(tok.value), line=tok.line)

        if tok.type is TokenType.STRING_LIT:
            self._advance()
            # Strip surrounding quotes
            raw = tok.value[1:-1]
            return StringNode(raw, line=tok.line)

        if tok.type is TokenType.LPAREN:
            self._advance()          # consume '('
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr

        raise ParseError(
            f"Expected expression but found {tok.type.name} ({tok.value!r}) "
            f"at line {tok.line}, col {tok.col}"
        )
