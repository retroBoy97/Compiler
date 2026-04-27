"""
tests/test_parser.py — Unit tests for Milestone 2: Parser

Run with:
    python -m unittest tests/test_parser.py -v
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer
from parser import Parser, ParseError
from ast_nodes import (
    ProgramNode, DeclNode, AssignNode, IfNode, BlockNode,
    BinOpNode, IdentNode, NumNode, StringNode,
)


def parse(source: str) -> ProgramNode:
    """Helper: lex + parse source and return the AST root."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class TestParserDeclarations(unittest.TestCase):

    def test_int_declaration(self):
        ast = parse("int x;")
        self.assertEqual(len(ast.statements), 1)
        decl = ast.statements[0]
        self.assertIsInstance(decl, DeclNode)
        self.assertEqual(decl.var_type, "int")
        self.assertEqual(decl.name, "x")

    def test_string_declaration(self):
        ast = parse("string name;")
        decl = ast.statements[0]
        self.assertIsInstance(decl, DeclNode)
        self.assertEqual(decl.var_type, "string")
        self.assertEqual(decl.name, "name")

    def test_multiple_declarations(self):
        ast = parse("int a;\nint b;\nstring c;")
        self.assertEqual(len(ast.statements), 3)
        self.assertIsInstance(ast.statements[0], DeclNode)
        self.assertIsInstance(ast.statements[1], DeclNode)
        self.assertIsInstance(ast.statements[2], DeclNode)


class TestParserAssignments(unittest.TestCase):

    def test_assign_integer(self):
        ast = parse("x = 5;")
        assign = ast.statements[0]
        self.assertIsInstance(assign, AssignNode)
        self.assertEqual(assign.name, "x")
        self.assertIsInstance(assign.expr, NumNode)
        self.assertEqual(assign.expr.value, 5)

    def test_assign_string(self):
        ast = parse('name = "Alice";')
        assign = ast.statements[0]
        self.assertIsInstance(assign, AssignNode)
        self.assertIsInstance(assign.expr, StringNode)
        self.assertEqual(assign.expr.value, "Alice")

    def test_assign_addition(self):
        ast = parse("x = a + 2;")
        assign = ast.statements[0]
        self.assertIsInstance(assign.expr, BinOpNode)
        self.assertEqual(assign.expr.op, "+")
        self.assertIsInstance(assign.expr.left, IdentNode)
        self.assertIsInstance(assign.expr.right, NumNode)

    def test_assign_complex_expr(self):
        ast = parse("z = x * (y - 3);")
        assign = ast.statements[0]
        binop = assign.expr
        self.assertIsInstance(binop, BinOpNode)
        self.assertEqual(binop.op, "*")
        self.assertIsInstance(binop.right, BinOpNode)
        self.assertEqual(binop.right.op, "-")


class TestParserIfStatement(unittest.TestCase):

    def test_if_then(self):
        ast = parse("if x > 10 then { x = 1; }")
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, IfNode)
        self.assertIsInstance(stmt.condition, BinOpNode)
        self.assertEqual(stmt.condition.op, ">")
        self.assertIsInstance(stmt.then_block, BlockNode)
        self.assertIsNone(stmt.else_block)

    def test_if_then_else(self):
        ast = parse("if x > 0 then { x = 1; } else { x = 0; }")
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, IfNode)
        self.assertIsNotNone(stmt.else_block)
        self.assertIsInstance(stmt.else_block, BlockNode)

    def test_block_contains_statements(self):
        ast = parse("if x > 0 then { int y;\ny = x + 1; }")
        block = ast.statements[0].then_block
        self.assertEqual(len(block.statements), 2)
        self.assertIsInstance(block.statements[0], DeclNode)
        self.assertIsInstance(block.statements[1], AssignNode)


class TestParserErrors(unittest.TestCase):

    def test_missing_semicolon(self):
        with self.assertRaises(ParseError):
            parse("int x")   # missing ;

    def test_missing_then(self):
        with self.assertRaises(ParseError):
            parse("if x > 0 { x = 1; }")  # missing 'then'

    def test_unmatched_brace(self):
        with self.assertRaises(ParseError):
            parse("if x > 0 then { x = 1;")  # missing }

    def test_bad_expression(self):
        with self.assertRaises(ParseError):
            parse("x = ;")   # missing expression after =


class TestParserPrettyPrint(unittest.TestCase):

    def test_pretty_runs(self):
        ast = parse("int x;\nx = 5 + 2;")
        output = ast.pretty()
        self.assertIn("Program", output)
        self.assertIn("Decl", output)
        self.assertIn("Assign", output)
        self.assertIn("BinOp", output)


if __name__ == "__main__":
    unittest.main()
