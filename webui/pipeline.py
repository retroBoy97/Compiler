"""
Compiler-pipeline glue for the web UI.

Each phase runner returns a tuple shaped:
    (status_pill_html, payload_for_ui, internal_object_or_None, error_str_or_None)
"""

import os
import sys
from pathlib import Path

# Make src/ importable regardless of working directory
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from lexer import Lexer, LexerError, TokenType
from parser import Parser, ParseError
from semantic import SemanticAnalyzer, SemanticError


SAMPLES_DIR = _ROOT / "samples"


def load_samples() -> dict[str, str]:
    return {p.stem: p.read_text() for p in sorted(SAMPLES_DIR.glob("*.cl"))}


def badge(kind: str, text: str) -> str:
    """Pill badge styled for the dark theme."""
    palettes = {
        "ok":   ("rgba(0, 114, 245, 0.10)", "#3b9eff", "rgba(59, 158, 255, 0.25)"),
        "err":  ("rgba(255, 91, 79, 0.10)", "#ff7a70", "rgba(255, 122, 112, 0.30)"),
        "skip": ("rgba(255, 255, 255, 0.04)", "#808080", "rgba(255, 255, 255, 0.08)"),
    }
    bg, fg, border = palettes.get(kind, palettes["skip"])
    return (
        f'<span style="display:inline-block;background:{bg};color:{fg};'
        f'padding:4px 12px;border-radius:9999px;font-size:12px;font-weight:500;'
        f'font-family:Geist,sans-serif;letter-spacing:normal;'
        f'border:1px solid {border};margin:0 4px 4px 0;">{text}</span>'
    )


def _phase_lex(source: str):
    try:
        tokens = Lexer(source).tokenize()
        rows = [
            [i, t.type.name, t.value, t.line, t.col]
            for i, t in enumerate(tokens)
            if t.type is not TokenType.EOF
        ]
        return badge("ok", "Lexer · OK"), rows, tokens, None
    except LexerError as e:
        return badge("err", f"Lexer · {e}"), [], None, str(e)


def _phase_parse(tokens):
    try:
        ast = Parser(tokens).parse()
        return badge("ok", "Parser · OK"), ast.pretty(), ast, None
    except ParseError as e:
        return badge("err", f"Parser · {e}"), "", None, str(e)


def _phase_semantic(ast):
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        symbols = [
            [name, info["type"]]
            for name, info in analyzer.global_scope.symbols.items()
        ]
        return badge("ok", "Semantic · OK"), symbols, None
    except SemanticError as e:
        return badge("err", f"Semantic · {e}"), [], str(e)


def compile_all(source: str):
    """Run all three phases and produce outputs for the stacked layout."""
    lex_status, token_rows, tokens, lex_err = _phase_lex(source)
    if lex_err:
        return (
            f"{lex_status} {badge('skip', 'Parser · skipped')} {badge('skip', 'Semantic · skipped')}",
            token_rows,
            "// skipped — lexer failed",
            badge("skip", "skipped — lexer failed"),
            [],
        )

    parse_status, ast_pretty, ast, parse_err = _phase_parse(tokens)
    if parse_err:
        return (
            f"{lex_status} {parse_status} {badge('skip', 'Semantic · skipped')}",
            token_rows,
            ast_pretty or "// parse failed",
            badge("skip", "skipped — parser failed"),
            [],
        )

    sem_status, symbols, _ = _phase_semantic(ast)
    return (
        f"{lex_status} {parse_status} {sem_status}",
        token_rows,
        ast_pretty,
        sem_status,
        symbols,
    )
