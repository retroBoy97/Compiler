"""
Main entry point for the Mini Compiler.

Usage:
    python compiler.py <source_file> [--phase lex|parse|semantic|all]

Runs the full compilation pipeline (or a single phase) on a .cl source file
and prints the result to stdout.
"""

import argparse
import sys
import os

# Make the src/ package importable regardless of working directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyzer, SemanticError


def read_source(path: str) -> str:
    """Read source code from a file, with a friendly error on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found: '{path}'", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def run_lexer(source: str) -> list:
    """Milestone 1: Tokenize source and return token list."""
    lexer = Lexer(source)
    try:
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[Lexer Error] {e}", file=sys.stderr)
        sys.exit(1)

    print("=== TOKEN STREAM ===")
    for tok in tokens:
        print(f"  {tok}")
    return tokens


def run_parser(source: str):
    """Milestone 2: Parse source into an AST and return the root node."""
    lexer = Lexer(source)
    try:
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[Lexer Error] {e}", file=sys.stderr)
        sys.exit(1)

    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except ParseError as e:
        print(f"[Parse Error] {e}", file=sys.stderr)
        sys.exit(1)

    print("=== ABSTRACT SYNTAX TREE ===")
    print(ast.pretty())
    return ast


def run_semantic(source: str):
    """Milestone 3: Run semantic analysis and report errors or success."""
    lexer = Lexer(source)
    try:
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[Lexer Error] {e}", file=sys.stderr)
        sys.exit(1)

    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except ParseError as e:
        print(f"[Parse Error] {e}", file=sys.stderr)
        sys.exit(1)

    analyzer = SemanticAnalyzer()
    try:
        analyzer.analyze(ast)
    except SemanticError as e:
        print(f"[Semantic Error] {e}", file=sys.stderr)
        sys.exit(1)

    print("=== SEMANTIC ANALYSIS ===")
    print("  No errors found.")
    print()
    print("  Symbol Table (global scope):")
    for name, info in analyzer.global_scope.symbols.items():
        print(f"    {name:20s} : {info['type']}")
    return ast


def main():
    arg_parser = argparse.ArgumentParser(
        description="Mini Compiler — CL Language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compiler.py samples/hello.cl
  python compiler.py samples/hello.cl --phase lex
  python compiler.py samples/hello.cl --phase parse
  python compiler.py samples/hello.cl --phase semantic
        """
    )
    arg_parser.add_argument("source", help="Path to the .cl source file")
    arg_parser.add_argument(
        "--phase",
        choices=["lex", "parse", "semantic", "all"],
        default="all",
        help="Which compilation phase to run (default: all)"
    )
    args = arg_parser.parse_args()

    source = read_source(args.source)

    if args.phase == "lex":
        run_lexer(source)
    elif args.phase == "parse":
        run_parser(source)
    elif args.phase == "semantic":
        run_semantic(source)
    else:  # "all"
        print(f"Compiling: {args.source}\n")
        run_lexer(source)
        print()
        run_parser(source)
        print()
        run_semantic(source)
        print()
        print("Compilation successful.")


if __name__ == "__main__":
    main()
