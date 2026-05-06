"""
Converts raw source text into a flat list of Token objects.

Algorithm: single-pass regex-based scanner.
  1. Build one combined regex from ordered token patterns.
  2. Walk through the source string left-to-right.
  3. Each match produces a Token; whitespace/comments are skipped.
  4. Unrecognised characters raise LexerError with line/column info.

Token types are defined in the TokenType enum so the parser can
reference them by name (e.g. TokenType.INT) rather than magic strings.
"""

import re
from enum import Enum, auto
from typing import List, NamedTuple


# Token type enumeration
class TokenType(Enum):
    # --- Literals ---
    INT_LIT    = auto()   # e.g. 42
    STRING_LIT = auto()   # e.g. "hello"

    # --- Keywords ---
    INT        = auto()   # 'int'    (type keyword)
    STRING     = auto()   # 'string' (type keyword)
    IF         = auto()   # 'if'
    THEN       = auto()   # 'then'
    ELSE       = auto()   # 'else'
    WHILE      = auto()   # 'while'
    FOR        = auto()   # 'for'
    TO         = auto()   # 'to' (used by the for-loop range)

    # --- Identifier ---
    IDENT      = auto()   # variable names: [a-zA-Z_][a-zA-Z0-9_]*

    # --- Operators ---
    PLUS       = auto()   # +
    MINUS      = auto()   # -
    STAR       = auto()   # *
    EQUALS     = auto()   # =   (assignment)
    EQ         = auto()   # ==  (equality test)
    GT         = auto()   # >
    LT         = auto()   # <

    # --- Delimiters ---
    LPAREN     = auto()   # (
    RPAREN     = auto()   # )
    LBRACE     = auto()   # {
    RBRACE     = auto()   # }
    SEMICOLON  = auto()   # ;

    # --- Special ---
    EOF        = auto()   # end of token stream


# Token data class
class Token(NamedTuple):
    """
    A single token produced by the lexer.

    Attributes:
        type  : one of the TokenType enum values
        value : the exact substring from the source
        line  : 1-based line number in the source file
        col   : 1-based column number of the first character
    """
    type: TokenType
    value: str
    line: int
    col: int

    def __str__(self) -> str:
        return f"Token({self.type.name:12s}, {self.value!r:15s}, line={self.line}, col={self.col})"


# Lexer error
class LexerError(Exception):
    """Raised when the lexer encounters an unrecognised character."""
    pass


# Token patterns

# Keyword lookup table. Any IDENT that appears here is re-classified.
KEYWORDS: dict = {
    "int":    TokenType.INT,
    "string": TokenType.STRING,
    "if":     TokenType.IF,
    "then":   TokenType.THEN,
    "else":   TokenType.ELSE,
    "while":  TokenType.WHILE,
    "for":    TokenType.FOR,
    "to":     TokenType.TO,
}

# Token patterns are tried in order; put longer/more specific patterns first.
# Each tuple is (regex_pattern, TokenType_or_None).
# None means "skip this match" (used for whitespace and comments).
TOKEN_PATTERNS: list = [
    # Whitespace — skip
    (r"[ \t\r\n]+",        None),

    # Single-line comments — skip
    (r"//[^\n]*",          None),

    # String literal (handles \" escape inside the string)
    (r'"(?:[^"\\]|\\.)*"', TokenType.STRING_LIT),

    # Integer literal
    (r"\d+",               TokenType.INT_LIT),

    # Identifiers and keywords (keywords are re-classified after match)
    (r"[a-zA-Z_]\w*",      TokenType.IDENT),

    # Multi-character operators (must come before single-character ones
    # so the longest match wins — '==' before '=').
    (r"==",   TokenType.EQ),

    # Single-character tokens
    (r"\+",   TokenType.PLUS),
    (r"-",    TokenType.MINUS),
    (r"\*",   TokenType.STAR),
    (r"=",    TokenType.EQUALS),
    (r">",    TokenType.GT),
    (r"<",    TokenType.LT),
    (r"\(",   TokenType.LPAREN),
    (r"\)",   TokenType.RPAREN),
    (r"\{",   TokenType.LBRACE),
    (r"\}",   TokenType.RBRACE),
    (r";",    TokenType.SEMICOLON),
]

# Compile all patterns into a single master regex.
_MASTER_PATTERN = re.compile(
    "|".join(f"({pat})" for pat, _ in TOKEN_PATTERNS)
)


# Lexer class
class Lexer:
    """
    Tokenizes a source string into a list of Token objects.

    Usage:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()   # returns List[Token], last item is EOF
    """

    def __init__(self, source: str) -> None:
        self.source = source

    def tokenize(self) -> List[Token]:
        """
        Scan the entire source string and return a token list.
        The final element is always Token(EOF, '', ...).
        Raises LexerError for unrecognised characters.
        """
        tokens: List[Token] = []
        pos = 0
        line = 1
        line_start = 0  # character index where the current line started

        while pos < len(self.source):
            match = _MASTER_PATTERN.match(self.source, pos)

            if not match:
                bad_char = self.source[pos]
                col = pos - line_start + 1
                raise LexerError(
                    f"Unexpected character {bad_char!r} at line {line}, col {col}"
                )

            # Which pattern index matched?
            group_index = next(
                i for i, g in enumerate(match.groups()) if g is not None
            )
            token_type = TOKEN_PATTERNS[group_index][1]
            matched_text = match.group(0)
            col = pos - line_start + 1

            if token_type is not None:
                # Re-classify identifiers that are actually keywords
                if token_type is TokenType.IDENT and matched_text in KEYWORDS:
                    token_type = KEYWORDS[matched_text]

                tokens.append(Token(token_type, matched_text, line, col))

            # Advance position; update line counter for newlines in the match
            newlines = matched_text.count("\n")
            if newlines:
                line += newlines
                line_start = pos + matched_text.rfind("\n") + 1

            pos = match.end()

        # Append synthetic EOF token
        eof_col = pos - line_start + 1
        tokens.append(Token(TokenType.EOF, "", line, eof_col))
        return tokens
