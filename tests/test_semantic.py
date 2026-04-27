"""
tests/test_semantic.py — Unit tests for Milestone 3: Semantic Analyzer

Run with:
    python -m unittest tests/test_semantic.py -v
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer, SemanticError


def analyze(source: str) -> SemanticAnalyzer:
    """Helper: lex + parse + semantic-check source. Returns analyzer on success."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return analyzer


def should_fail(source: str):
    """Helper: assert that semantic analysis raises SemanticError."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    with unittest.TestCase().assertRaises(SemanticError):
        analyzer.analyze(ast)


class TestSemanticValidPrograms(unittest.TestCase):

    def test_declare_and_assign_int(self):
        # Should not raise
        analyze("int x;\nx = 5;")

    def test_declare_and_assign_string(self):
        analyze('string s;\ns = "hello";')

    def test_arithmetic_with_declared_vars(self):
        analyze("int a;\nint b;\na = 3;\nb = a + 2;")

    def test_string_concatenation(self):
        analyze('string a;\nstring b;\na = "hello";\nb = a + " world";')

    def test_if_statement(self):
        analyze("int x;\nx = 10;\nif x > 5 then { x = x - 1; }")

    def test_if_else_statement(self):
        analyze("int x;\nx = 10;\nif x > 5 then { x = 1; } else { x = 0; }")

    def test_symbol_table_populated(self):
        analyzer = analyze("int x;\nstring name;")
        symbols = analyzer.global_scope.symbols
        self.assertIn("x", symbols)
        self.assertIn("name", symbols)
        self.assertEqual(symbols["x"]["type"], "int")
        self.assertEqual(symbols["name"]["type"], "string")


class TestSemanticUndeclaredVariable(unittest.TestCase):

    def test_use_before_declare(self):
        with self.assertRaises(SemanticError):
            analyze("x = 5;")   # x not declared

    def test_undeclared_in_expression(self):
        with self.assertRaises(SemanticError):
            analyze("int x;\nx = y + 1;")  # y not declared

    def test_undeclared_in_condition(self):
        with self.assertRaises(SemanticError):
            analyze("if z > 0 then { int x;\nx = 1; }")  # z not declared


class TestSemanticTypeMismatch(unittest.TestCase):

    def test_assign_string_to_int(self):
        with self.assertRaises(SemanticError):
            analyze('int x;\nx = "hello";')

    def test_assign_int_to_string(self):
        with self.assertRaises(SemanticError):
            analyze("string s;\ns = 42;")

    def test_mixed_arithmetic(self):
        with self.assertRaises(SemanticError):
            analyze('int x;\nstring s;\ns = "a";\nx = x + s;')

    def test_subtract_strings(self):
        with self.assertRaises(SemanticError):
            analyze('string a;\nstring b;\na = "x";\nb = a - "y";')


class TestSemanticDuplicateDeclaration(unittest.TestCase):

    def test_double_declaration(self):
        with self.assertRaises(SemanticError):
            analyze("int x;\nint x;")   # x declared twice in same scope

    def test_different_type_redeclaration(self):
        with self.assertRaises(SemanticError):
            analyze("int x;\nstring x;")


class TestSemanticBlockScoping(unittest.TestCase):

    def test_variable_in_outer_scope_visible_in_block(self):
        # x is declared outside, used inside the block — should be fine
        analyze("int x;\nx = 5;\nif x > 0 then { x = x - 1; }")

    def test_variable_declared_inside_block(self):
        # y is declared inside the block
        analyze("int x;\nx = 1;\nif x > 0 then { int y;\ny = x + 1; }")


if __name__ == "__main__":
    unittest.main()
