"""
Compiler-pipeline glue for the web UI.

Each phase runner returns a tuple shaped:
    (status_pill_html, payload_for_ui, internal_object_or_None, error_str_or_None)
"""

import html
import os
import sys
from pathlib import Path

# Make src/ importable regardless of working directory
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from lexer import Lexer, LexerError, TokenType
from parser import Parser, ParseError
from semantic import SemanticAnalyzer, SemanticError
from ast_nodes import (
    ProgramNode, DeclNode, AssignNode, IfNode, WhileNode, ForNode,
    BlockNode, BinOpNode, UnaryOpNode, IdentNode, NumNode, StringNode,
)


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


# --- AST → Mermaid flowchart ---------------------------------------------

# Maps node class → mermaid classDef name (defined in _MERMAID_CLASSDEFS).
_NODE_STYLES = {
    "ProgramNode": "stmt",
    "DeclNode":    "decl",
    "AssignNode":  "stmt",
    "IfNode":      "ctrl",
    "WhileNode":   "ctrl",
    "ForNode":     "ctrl",
    "BlockNode":   "block",
    "BinOpNode":   "op",
    "UnaryOpNode": "op",
    "IdentNode":   "ident",
    "NumNode":     "lit",
    "StringNode":  "lit",
}


def _node_summary(node):
    """
    Return (label_text, [(child_role_or_None, child_node), ...]) for a node.
    Driven by isinstance checks so the renderer stays decoupled from the AST.
    """
    if isinstance(node, ProgramNode):
        return "Program", [(None, s) for s in node.statements]
    if isinstance(node, DeclNode):
        return f"Decl({node.var_type} {node.name})", []
    if isinstance(node, AssignNode):
        return f"Assign({node.name})", [(None, node.expr)]
    if isinstance(node, IfNode):
        kids = [("condition", node.condition), ("then", node.then_block)]
        if node.else_block:
            kids.append(("else", node.else_block))
        return "If", kids
    if isinstance(node, WhileNode):
        return "While", [("condition", node.condition), ("body", node.body)]
    if isinstance(node, ForNode):
        return f"For({node.var_name})", [
            ("init", node.init), ("limit", node.limit), ("body", node.body),
        ]
    if isinstance(node, BlockNode):
        return "Block", [(None, s) for s in node.statements]
    if isinstance(node, BinOpNode):
        return f"BinOp({node.op!r})", [(None, node.left), (None, node.right)]
    if isinstance(node, UnaryOpNode):
        return f"UnaryOp({node.op!r})", [(None, node.operand)]
    if isinstance(node, IdentNode):
        return f"Ident({node.name})", []
    if isinstance(node, NumNode):
        return f"Num({node.value})", []
    if isinstance(node, StringNode):
        return f"String({node.value!r})", []
    return type(node).__name__, []


# Colors per node category, applied as mermaid classDefs.
_MERMAID_CLASSDEFS = """
    classDef stmt  fill:#0c1f3a,stroke:#3b9eff,color:#cfe5ff,stroke-width:1.5px
    classDef decl  fill:#0c2418,stroke:#4ade80,color:#c5f0d6,stroke-width:1.5px
    classDef ctrl  fill:#2a1a08,stroke:#f5a35e,color:#ffd9b8,stroke-width:1.5px
    classDef block fill:#1a1a1a,stroke:#888,color:#ddd,stroke-width:1.5px
    classDef op    fill:#1a0e2e,stroke:#c4a8ff,color:#e0cdff,stroke-width:1.5px
    classDef ident fill:#2a2208,stroke:#ffe28a,color:#fff0b8,stroke-width:1.5px
    classDef lit   fill:#08251f,stroke:#7ee2c4,color:#bdf0e1,stroke-width:1.5px
"""


def _mermaid_escape(s: str) -> str:
    """Escape a label for inclusion inside mermaid `"..."` quoted form."""
    # mermaid quoted labels accept HTML entities for special characters.
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def render_ast_mermaid(ast) -> str:
    """
    Render the AST as an HTML block containing a mermaid flowchart.
    The actual mermaid → SVG rendering happens in the browser; this just
    produces the source.
    """
    counter = [0]
    nodes: list[str] = []
    edges: list[str] = []

    def fresh_id() -> str:
        counter[0] += 1
        return f"n{counter[0]}"

    def visit(node) -> str:
        my_id = fresh_id()
        label, children = _node_summary(node)
        css = _NODE_STYLES.get(type(node).__name__, "stmt")
        nodes.append(f'    {my_id}["{_mermaid_escape(label)}"]:::{css}')
        for role, child in children:
            child_id = visit(child)
            if role:
                edges.append(
                    f'    {my_id} -- "{_mermaid_escape(role)}" --> {child_id}'
                )
            else:
                edges.append(f"    {my_id} --> {child_id}")
        return my_id

    visit(ast)

    diagram = (
        "flowchart TD\n"
        + "\n".join(nodes)
        + ("\n" if edges else "")
        + "\n".join(edges)
        + "\n"
        + _MERMAID_CLASSDEFS
    )
    return f'<div class="ast-mermaid"><pre class="mermaid">{diagram}</pre></div>'


# --- Phase runners --------------------------------------------------------

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
        return badge("ok", "Parser · OK"), render_ast_mermaid(ast), ast, None
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
            '<div class="ast-mermaid-empty">skipped — lexer failed</div>',
            badge("skip", "skipped — lexer failed"),
            [],
        )

    parse_status, ast_html, ast, parse_err = _phase_parse(tokens)
    if parse_err:
        return (
            f"{lex_status} {parse_status} {badge('skip', 'Semantic · skipped')}",
            token_rows,
            ast_html or '<div class="ast-mermaid-empty">parse failed</div>',
            badge("skip", "skipped — parser failed"),
            [],
        )

    sem_status, symbols, _ = _phase_semantic(ast)
    return (
        f"{lex_status} {parse_status} {sem_status}",
        token_rows,
        ast_html,
        sem_status,
        symbols,
    )
