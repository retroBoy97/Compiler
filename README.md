# Mini Compiler — CL Language (Python)

A three-milestone compiler for the **CL** (Custom Language) programming language,
built entirely in Python with no runtime dependencies. Project metadata and the
optional dev toolchain (pytest) are managed with [uv](https://docs.astral.sh/uv/).

## Language Features

- Integer and string variable declarations (`int x;`, `string name;`)
- Arithmetic expressions: `+`, `-`, `*`
- Comparison operator: `>`
- Assignment statements: `x = expr;`
- `if / then / else` control flow with brace-delimited blocks
- Block scoping with `{ }`

## Sample Program

```cl
int x;
x = 5;
x = x + 2;

if x > 3 then {
    x = x - 1;
}

string name;
name = "Alice";
```

## Setup

```bash
# Install uv (one-time): https://docs.astral.sh/uv/getting-started/installation/
# Then sync the project (creates .venv and installs dev deps):
uv sync
```

## Running the Compiler

```bash
# Full pipeline (lex + parse + semantic) on a source file
uv run python compiler.py samples/hello.cl

# Run only the lexer (Milestone 1)
uv run python compiler.py samples/hello.cl --phase lex

# Run only the parser (Milestone 2)
uv run python compiler.py samples/hello.cl --phase parse

# Run only semantic analysis (Milestone 3)
uv run python compiler.py samples/hello.cl --phase semantic

# Test error detection
uv run python compiler.py samples/errors.cl --phase semantic

# Run all unit tests (stdlib unittest, no dev deps needed)
uv run python -m unittest discover tests/ -v

# Run all unit tests with pytest
uv run pytest tests/ -v
```

## Web UI (Gradio)

Launch the visual pipeline explorer:

```bash
uv run python ui.py
# Opens http://127.0.0.1:7860
```

The UI lets you load a sample (or write your own CL code), then click **Compile**
to step through Lexer → Parser → Semantic Analyzer in three tabs:
token table, AST tree view, and symbol table with type/scope diagnostics.

## Project Structure

```
Compiler/
├── compiler.py          # CLI entry point — runs all phases
├── ui.py                # Gradio web UI — visual pipeline explorer
├── pyproject.toml       # uv-managed project metadata + dev deps
├── uv.lock              # locked dependency versions (committed)
│
├── src/
│   ├── lexer.py         # Milestone 1 — Tokenizer
│   ├── ast_nodes.py     # AST node class definitions
│   ├── parser.py        # Milestone 2 — Recursive descent parser
│   └── semantic.py      # Milestone 3 — Type & scope checker
│
├── tests/
│   ├── test_lexer.py    # Unit tests for Milestone 1
│   ├── test_parser.py   # Unit tests for Milestone 2
│   └── test_semantic.py # Unit tests for Milestone 3
│
└── samples/
    ├── hello.cl         # Basic program
    ├── arithmetic.cl    # Arithmetic expressions
    ├── conditionals.cl  # if/then/else
    └── errors.cl        # Intentional semantic errors
```

## Milestone Overview

| Milestone | File              | Input        | Output              |
|-----------|-------------------|--------------|---------------------|
| 1 — Lexer | `src/lexer.py`    | Source text  | Token stream        |
| 2 — Parser| `src/parser.py`   | Token stream | Abstract Syntax Tree|
| 3 — Semantic | `src/semantic.py` | AST       | Validated / Errors  |

## Language Grammar (BNF)

```
<program>   ::= <stmt>* EOF
<stmt>      ::= <decl> | <assign> | <if_stmt> | <block>
<decl>      ::= ('int' | 'string') IDENT ';'
<assign>    ::= IDENT '=' <expr> ';'
<if_stmt>   ::= 'if' <cmp_expr> 'then' <block> ( 'else' <block> )?
<block>     ::= '{' <stmt>* '}'
<cmp_expr>  ::= <expr> '>' <expr>
<expr>      ::= <term> ( ('+' | '-') <term> )*
<term>      ::= <factor> ( '*' <factor> )*
<factor>    ::= IDENT | INT_LIT | STRING_LIT | '(' <expr> ')'
```

## Semantic Rules

- Variables must be declared before use.
- No duplicate declarations in the same scope.
- Assignment RHS type must match the declared variable type.
- Arithmetic operators (`-`, `*`) require both operands to be `int`.
- Operator `+` allows `int + int` or `string + string` (concatenation).
- Comparison operator `>` requires both operands to be `int`.

## Team

GL4 — Academic Year 2025/2026
Submission: May 3rd, 2026 | Defense: May 6th, 2026
