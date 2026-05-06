"""
Every grammar rule that produces a tree node has its own class here.
All nodes inherit from ASTNode which provides:
  - a .pretty(indent) method for human-readable printing
  - a .__repr__ for debugging

Design note: nodes are intentionally simple data containers.
No logic lives here — the parser builds them; the semantic
analyzer walks them. This clean separation makes each milestone
independently testable.

Node hierarchy:
    ASTNode
    ├── ProgramNode   — root; holds a list of statements
    ├── DeclNode      — type declaration:  int x;
    ├── AssignNode    — assignment:        x = expr;
    ├── IfNode        — if/then/else
    ├── WhileNode     — while cond { body }
    ├── ForNode       — for i = init to limit { body }
    ├── BlockNode     — { stmt* }
    ├── BinOpNode     — expr op expr
    ├── UnaryOpNode   — op expr  (currently: '-')
    ├── IdentNode     — variable reference
    ├── NumNode       — integer literal
    └── StringNode    — string literal
"""

from __future__ import annotations
from typing import List, Optional


class ASTNode:
    """Base class for all AST nodes."""

    def pretty(self, indent: int = 0) -> str:
        """Return an indented string representation of this subtree."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.pretty()


# Statement nodes
class ProgramNode(ASTNode):
    """Root node. Contains the list of top-level statements."""

    def __init__(self, statements: List[ASTNode]) -> None:
        self.statements = statements

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Program"]
        for stmt in self.statements:
            lines.append(stmt.pretty(indent + 1))
        return "\n".join(lines)


class DeclNode(ASTNode):
    """
    Variable declaration node.
    Example:  int x;   →  DeclNode(var_type='int', name='x')
    """

    def __init__(self, var_type: str, name: str, line: int = 0) -> None:
        self.var_type = var_type   # 'int' or 'string'
        self.name = name
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Decl({self.var_type} {self.name})"


class AssignNode(ASTNode):
    """
    Assignment node.
    Example:  x = 5;   →  AssignNode(name='x', expr=NumNode(5))
    """

    def __init__(self, name: str, expr: ASTNode, line: int = 0) -> None:
        self.name = name
        self.expr = expr
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Assign({self.name})"]
        lines.append(self.expr.pretty(indent + 1))
        return "\n".join(lines)


class IfNode(ASTNode):
    """
    If/then/else node.
    The else_block is None if there is no else branch.
    """

    def __init__(
        self,
        condition: ASTNode,
        then_block: BlockNode,
        else_block: Optional[BlockNode] = None,
        line: int = 0,
    ) -> None:
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}If"]
        lines.append(f"{pad}  condition:")
        lines.append(self.condition.pretty(indent + 2))
        lines.append(f"{pad}  then:")
        lines.append(self.then_block.pretty(indent + 2))
        if self.else_block:
            lines.append(f"{pad}  else:")
            lines.append(self.else_block.pretty(indent + 2))
        return "\n".join(lines)


class WhileNode(ASTNode):
    """
    While loop:  while cond { body }
    The condition must be a comparison (semantic analyzer enforces this).
    """

    def __init__(self, condition: ASTNode, body: BlockNode, line: int = 0) -> None:
        self.condition = condition
        self.body = body
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}While"]
        lines.append(f"{pad}  condition:")
        lines.append(self.condition.pretty(indent + 2))
        lines.append(f"{pad}  body:")
        lines.append(self.body.pretty(indent + 2))
        return "\n".join(lines)


class ForNode(ASTNode):
    """
    For loop:  for IDENT = init to limit { body }
    The loop variable must be a previously declared 'int'.
    """

    def __init__(
        self,
        var_name: str,
        init: ASTNode,
        limit: ASTNode,
        body: BlockNode,
        line: int = 0,
    ) -> None:
        self.var_name = var_name
        self.init = init
        self.limit = limit
        self.body = body
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}For({self.var_name})"]
        lines.append(f"{pad}  init:")
        lines.append(self.init.pretty(indent + 2))
        lines.append(f"{pad}  limit:")
        lines.append(self.limit.pretty(indent + 2))
        lines.append(f"{pad}  body:")
        lines.append(self.body.pretty(indent + 2))
        return "\n".join(lines)


class BlockNode(ASTNode):
    """A brace-delimited block: { stmt* }"""

    def __init__(self, statements: List[ASTNode], line: int = 0) -> None:
        self.statements = statements
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Block"]
        for stmt in self.statements:
            lines.append(stmt.pretty(indent + 1))
        return "\n".join(lines)


# Expression nodes
class BinOpNode(ASTNode):
    """
    Binary operation node.
    op is one of: '+', '-', '*', '>'
    """

    def __init__(self, op: str, left: ASTNode, right: ASTNode, line: int = 0) -> None:
        self.op = op
        self.left = left
        self.right = right
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}BinOp({self.op!r})"]
        lines.append(self.left.pretty(indent + 1))
        lines.append(self.right.pretty(indent + 1))
        return "\n".join(lines)


class UnaryOpNode(ASTNode):
    """
    Unary operation node.
    op is currently always '-'.
    """

    def __init__(self, op: str, operand: ASTNode, line: int = 0) -> None:
        self.op = op
        self.operand = operand
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}UnaryOp({self.op!r})"]
        lines.append(self.operand.pretty(indent + 1))
        return "\n".join(lines)


class IdentNode(ASTNode):
    """A variable reference (identifier used as an expression)."""

    def __init__(self, name: str, line: int = 0) -> None:
        self.name = name
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Ident({self.name})"


class NumNode(ASTNode):
    """An integer literal."""

    def __init__(self, value: int, line: int = 0) -> None:
        self.value = value
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Num({self.value})"


class StringNode(ASTNode):
    """A string literal (value has surrounding quotes stripped)."""

    def __init__(self, value: str, line: int = 0) -> None:
        self.value = value   # raw content, quotes stripped
        self.line = line

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}String({self.value!r})"
