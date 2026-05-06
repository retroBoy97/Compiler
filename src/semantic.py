"""
Walks the AST produced by the Parser and performs:
  1. Scope checking  — variables must be declared before use;
                       no duplicate declarations in the same scope.
  2. Type checking   — only compatible types in expressions;
                       assignment RHS must match the declared LHS type.

Design:
  - SymbolTable  : stack of scopes (dicts mapping name → {'type': str}).
                   push_scope() / pop_scope() for blocks.
  - SemanticAnalyzer : visitor that calls _visit_<NodeClass>(node).
                       Returns a type string ('int' or 'string') for
                       expression nodes; returns None for statement nodes.

Usage:
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)          # raises SemanticError on failure
    # On success, inspect analyzer.global_scope for the symbol table
"""

from ast_nodes import (
    ASTNode, ProgramNode, DeclNode, AssignNode, IfNode,
    WhileNode, ForNode, BlockNode, BinOpNode, UnaryOpNode,
    IdentNode, NumNode, StringNode,
)


# Operators that produce a boolean-style result usable as a condition.
_COMPARISON_OPS = frozenset({">", "<", "=="})


class SemanticError(Exception):
    """Raised when a semantic rule is violated."""
    pass


# Symbol table
class SymbolTable:
    """
    A scoped symbol table implemented as a stack of dicts.

    Each scope is a dict mapping variable name → {'type': str}.
    The bottom of the stack is the global scope.
    """

    def __init__(self) -> None:
        self._scopes: list = [{}]   # start with global scope

    # Scope management
    def push_scope(self) -> None:
        """Enter a new inner scope (e.g., a block)."""
        self._scopes.append({})

    def pop_scope(self) -> None:
        """Leave the current inner scope."""
        if len(self._scopes) > 1:
            self._scopes.pop()

    @property
    def symbols(self) -> dict:
        """Return the symbols of the current (innermost) scope."""
        return self._scopes[-1]

    # Symbol operations
    def define(self, name: str, var_type: str, line: int = 0) -> None:
        """
        Declare a new variable in the current scope.
        Raises SemanticError if it was already declared in this scope.
        """
        if name in self._scopes[-1]:
            raise SemanticError(
                f"Variable '{name}' is already declared in this scope "
                f"(line {line})"
            )
        self._scopes[-1][name] = {"type": var_type}

    def lookup(self, name: str, line: int = 0) -> str:
        """
        Look up a variable name across all scopes (inner → outer).
        Returns the type string ('int' or 'string').
        Raises SemanticError if not found.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]["type"]
        raise SemanticError(
            f"Variable '{name}' used before declaration (line {line})"
        )


# Semantic analyzer
class SemanticAnalyzer:
    """
    Walks the AST and enforces semantic rules.

    After a successful analyze() call:
        self.global_scope  — the SymbolTable (global scope contains top-level vars)
    """

    def __init__(self) -> None:
        self.global_scope = SymbolTable()

    def analyze(self, node: ProgramNode) -> None:
        """Entry point. Analyzes the whole program."""
        self._visit(node)

    # Visitor dispatch
    def _visit(self, node: ASTNode):
        """Dispatch to the appropriate _visit_<Class> method."""
        method_name = f"_visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self._visit_unknown)
        return visitor(node)

    def _visit_unknown(self, node: ASTNode):
        raise SemanticError(f"No visitor defined for node type {type(node).__name__}")

    # Statement visitors (return None)
    def _visit_ProgramNode(self, node: ProgramNode) -> None:
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_DeclNode(self, node: DeclNode) -> None:
        """Register the variable in the current scope."""
        self.global_scope.define(node.name, node.var_type, line=node.line)

    def _visit_AssignNode(self, node: AssignNode) -> None:
        """
        Check:
          1. The variable is declared.
          2. The RHS expression type is compatible with the declared type.
        """
        declared_type = self.global_scope.lookup(node.name, line=node.line)
        rhs_type = self._visit(node.expr)

        if rhs_type is not None and rhs_type != declared_type:
            raise SemanticError(
                f"Type mismatch: variable '{node.name}' is declared as "
                f"'{declared_type}' but assigned a '{rhs_type}' value "
                f"(line {node.line})"
            )

    def _visit_IfNode(self, node: IfNode) -> None:
        """
        Enforce that the condition is a comparison expression, then
        type-check the comparison and analyse both branches.
        """
        self._check_condition(node.condition, "if", node.line)
        self._visit(node.condition)
        self._visit(node.then_block)
        if node.else_block:
            self._visit(node.else_block)

    def _visit_WhileNode(self, node: WhileNode) -> None:
        """Same condition rules as 'if', plus the body."""
        self._check_condition(node.condition, "while", node.line)
        self._visit(node.condition)
        self._visit(node.body)

    def _visit_ForNode(self, node: ForNode) -> None:
        """
        For-loop checks:
          - The loop variable must be already declared as 'int'.
          - The init and limit expressions must be 'int'.
          - The body is analysed in its own (block) scope.
        """
        var_type = self.global_scope.lookup(node.var_name, line=node.line)
        if var_type != "int":
            raise SemanticError(
                f"For-loop variable '{node.var_name}' must be 'int', "
                f"got '{var_type}' (line {node.line})"
            )

        init_type = self._visit(node.init)
        if init_type != "int":
            raise SemanticError(
                f"For-loop init expression must be 'int', "
                f"got '{init_type}' (line {node.line})"
            )

        limit_type = self._visit(node.limit)
        if limit_type != "int":
            raise SemanticError(
                f"For-loop limit expression must be 'int', "
                f"got '{limit_type}' (line {node.line})"
            )

        self._visit(node.body)

    def _check_condition(self, cond: ASTNode, context: str, line: int) -> None:
        """
        Enforce that 'if' / 'while' conditions are real comparisons.
        Without this check, code like  if "hello" then { ... }  would
        silently pass semantic analysis.
        """
        if not (isinstance(cond, BinOpNode) and cond.op in _COMPARISON_OPS):
            raise SemanticError(
                f"'{context}' condition must be a comparison "
                f"('>', '<', or '=='), got non-comparison expression "
                f"(line {line})"
            )

    def _visit_BlockNode(self, node: BlockNode) -> None:
        """Push a new scope for the block, then visit all statements."""
        self.global_scope.push_scope()
        for stmt in node.statements:
            self._visit(stmt)
        self.global_scope.pop_scope()

    # Expression visitors (return type string: 'int' or 'string')
    def _visit_NumNode(self, node: NumNode) -> str:
        return "int"

    def _visit_StringNode(self, node: StringNode) -> str:
        return "string"

    def _visit_IdentNode(self, node: IdentNode) -> str:
        """Look up the variable and return its declared type."""
        return self.global_scope.lookup(node.name, line=node.line)

    def _visit_BinOpNode(self, node: BinOpNode) -> str:
        """
        Check that operand types are compatible for the operator.

        Rules:
          - Arithmetic (+, -, *): both operands must be 'int'.
          - String concatenation (+): both operands must be 'string'.
          - Ordered comparison (>, <): both operands must be 'int'.
          - Equality (==): both operands must be the same type
            (int == int  or  string == string).
          - All comparisons return 'int' (treating boolean as int).
        """
        left_type = self._visit(node.left)
        right_type = self._visit(node.right)

        if node.op == "+":
            # Allow int + int  OR  string + string
            if left_type == right_type:
                return left_type
            raise SemanticError(
                f"Operator '+' requires both operands to be the same type, "
                f"but got '{left_type}' and '{right_type}' (line {node.line})"
            )

        if node.op in ("-", "*"):
            if left_type != "int" or right_type != "int":
                raise SemanticError(
                    f"Operator '{node.op}' requires both operands to be 'int', "
                    f"but got '{left_type}' and '{right_type}' (line {node.line})"
                )
            return "int"

        if node.op in (">", "<"):
            if left_type != "int" or right_type != "int":
                raise SemanticError(
                    f"Operator '{node.op}' requires both operands to be 'int', "
                    f"but got '{left_type}' and '{right_type}' (line {node.line})"
                )
            return "int"

        if node.op == "==":
            if left_type != right_type:
                raise SemanticError(
                    f"Operator '==' requires both operands to be the same type, "
                    f"but got '{left_type}' and '{right_type}' (line {node.line})"
                )
            return "int"

        raise SemanticError(f"Unknown operator '{node.op}' (line {node.line})")

    def _visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        """Unary minus requires an 'int' operand and returns 'int'."""
        operand_type = self._visit(node.operand)

        if node.op == "-":
            if operand_type != "int":
                raise SemanticError(
                    f"Unary '-' requires an 'int' operand, "
                    f"got '{operand_type}' (line {node.line})"
                )
            return "int"

        raise SemanticError(
            f"Unknown unary operator '{node.op}' (line {node.line})"
        )
