"""
tests/test_lexer.py — Unit tests for Milestone 1: Lexer

Run with:
    python -m unittest tests/test_lexer.py -v
    # or from the project root:
    python -m unittest discover tests/ -v
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer, Token, TokenType, LexerError


def tokenize(source: str):
    """Helper: tokenize source and return list WITHOUT the final EOF token."""
    tokens = Lexer(source).tokenize()
    return [t for t in tokens if t.type is not TokenType.EOF]


class TestLexerBasicTokens(unittest.TestCase):

    def test_integer_literal(self):
        tokens = tokenize("42")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.INT_LIT)
        self.assertEqual(tokens[0].value, "42")

    def test_string_literal(self):
        tokens = tokenize('"hello world"')
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.STRING_LIT)
        self.assertEqual(tokens[0].value, '"hello world"')

    def test_identifier(self):
        tokens = tokenize("myVar")
        self.assertEqual(tokens[0].type, TokenType.IDENT)
        self.assertEqual(tokens[0].value, "myVar")

    def test_keywords(self):
        source = "int string if then else"
        types = [t.type for t in tokenize(source)]
        self.assertEqual(types, [
            TokenType.INT,
            TokenType.STRING,
            TokenType.IF,
            TokenType.THEN,
            TokenType.ELSE,
        ])

    def test_operators(self):
        source = "+ - * = >"
        types = [t.type for t in tokenize(source)]
        self.assertEqual(types, [
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.STAR,
            TokenType.EQUALS,
            TokenType.GT,
        ])

    def test_delimiters(self):
        source = "( ) { } ;"
        types = [t.type for t in tokenize(source)]
        self.assertEqual(types, [
            TokenType.LPAREN,
            TokenType.RPAREN,
            TokenType.LBRACE,
            TokenType.RBRACE,
            TokenType.SEMICOLON,
        ])


class TestLexerExpressions(unittest.TestCase):

    def test_assignment(self):
        tokens = tokenize("x = 5;")
        types = [t.type for t in tokens]
        self.assertEqual(types, [
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.INT_LIT,
            TokenType.SEMICOLON,
        ])
        self.assertEqual(tokens[0].value, "x")
        self.assertEqual(tokens[2].value, "5")

    def test_arithmetic(self):
        tokens = tokenize("x = 5 + 2;")
        types = [t.type for t in tokens]
        self.assertEqual(types, [
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.INT_LIT,
            TokenType.PLUS,
            TokenType.INT_LIT,
            TokenType.SEMICOLON,
        ])

    def test_complex_expression(self):
        tokens = tokenize("z = x * (y - 3);")
        types = [t.type for t in tokens]
        self.assertEqual(types, [
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.IDENT,
            TokenType.STAR,
            TokenType.LPAREN,
            TokenType.IDENT,
            TokenType.MINUS,
            TokenType.INT_LIT,
            TokenType.RPAREN,
            TokenType.SEMICOLON,
        ])

    def test_if_statement(self):
        tokens = tokenize("if a > b then { a = 1; }")
        types = [t.type for t in tokens]
        self.assertIn(TokenType.IF, types)
        self.assertIn(TokenType.THEN, types)
        self.assertIn(TokenType.GT, types)
        self.assertIn(TokenType.LBRACE, types)
        self.assertIn(TokenType.RBRACE, types)


class TestLexerLineNumbers(unittest.TestCase):

    def test_line_tracking(self):
        source = "int x;\nx = 5;"
        tokens = tokenize(source)
        # 'int' is on line 1, 'x' (second occurrence) is on line 2
        self.assertEqual(tokens[0].line, 1)   # 'int'
        self.assertEqual(tokens[3].line, 2)   # 'x' in second line

    def test_whitespace_skipped(self):
        tokens = tokenize("   x   ")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.IDENT)

    def test_comments_skipped(self):
        tokens = tokenize("// this is a comment\nx = 5;")
        types = [t.type for t in tokens]
        self.assertNotIn(TokenType.EOF, types)
        self.assertEqual(types[0], TokenType.IDENT)   # 'x', not comment


class TestLexerErrors(unittest.TestCase):

    def test_invalid_character(self):
        with self.assertRaises(LexerError):
            Lexer("x @ 5;").tokenize()

    def test_eof_token_present(self):
        tokens = Lexer("x = 1;").tokenize()
        self.assertEqual(tokens[-1].type, TokenType.EOF)


if __name__ == "__main__":
    unittest.main()
