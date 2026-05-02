"""
Gradio Blocks layout for the CL compiler.

Single-column stacked layout: header → input → compile button → status, then
three phase sections (Tokens, AST, Semantic).
"""

from pathlib import Path

import gradio as gr

from .pipeline import badge, compile_all, load_samples


SAMPLES = load_samples()
DEFAULT_SAMPLE = "hello" if "hello" in SAMPLES else next(iter(SAMPLES), "")
DEFAULT_CODE = SAMPLES.get(DEFAULT_SAMPLE, "int x;\nx = 5;\nx = x + 2;\n")


def load_css() -> str:
    return (Path(__file__).parent / "styles.css").read_text(encoding="utf-8")


def _load_sample(name: str) -> str:
    return SAMPLES.get(name, "")


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="CL Compiler — Visualizer") as demo:
        # --- Header --------------------------------------------------------
        gr.Markdown("# CL Compiler", elem_classes="app-header")
        gr.Markdown(
            "A visual pipeline for the CL language — watch source code flow through "
            "**Lexer → Parser → Semantic Analyzer**.",
            elem_classes="app-subtitle",
        )
        gr.Markdown(
            "Kacem Mathlouthi · Mohamed Amine Haouas · Alaeddine Zaouali · Rami Kaabi",
            elem_classes="app-authors",
        )

        # --- Input ---------------------------------------------------------
        sample_dropdown = gr.Dropdown(
            choices=list(SAMPLES.keys()),
            value=DEFAULT_SAMPLE,
            label="Sample",
            interactive=True,
        )
        code_input = gr.Code(
            value=DEFAULT_CODE,
            label="Source",
            lines=14,
            interactive=True,
        )
        compile_btn = gr.Button("Compile", variant="primary", size="lg")
        status = gr.Markdown(
            badge("skip", "Idle — click Compile to run."),
            elem_classes="status-row",
        )

        # --- Phase 1: Tokens ----------------------------------------------
        with gr.Column(elem_classes="phase-section"):
            gr.Markdown("Phase 1", elem_classes="phase-marker")
            gr.Markdown("## Tokens", elem_classes="phase-title")
            gr.Markdown(
                "Source text is scanned left-to-right and emitted as a flat token "
                "stream. Whitespace and `//` comments are skipped.",
                elem_classes="phase-desc",
            )
            tokens_table = gr.Dataframe(
                headers=["#", "Type", "Value", "Line", "Col"],
                datatype=["number", "str", "str", "number", "number"],
                interactive=False,
                wrap=True,
                show_label=False,
            )

        # --- Phase 2: AST -------------------------------------------------
        with gr.Column(elem_classes="phase-section"):
            gr.Markdown("Phase 2", elem_classes="phase-marker")
            gr.Markdown("## Abstract Syntax Tree", elem_classes="phase-title")
            gr.Markdown(
                "Tokens are consumed by a recursive-descent parser that builds a "
                "tree of nodes. Indentation reflects parent → child relationships.",
                elem_classes="phase-desc",
            )
            ast_view = gr.Code(
                label="AST",
                lines=20,
                interactive=False,
                show_label=False,
            )

        # --- Phase 3: Semantic --------------------------------------------
        with gr.Column(elem_classes="phase-section"):
            gr.Markdown("Phase 3", elem_classes="phase-marker")
            gr.Markdown("## Semantic Analysis", elem_classes="phase-title")
            gr.Markdown(
                "The AST is walked with a scoped symbol table. Variables must be "
                "declared before use; assignment and operator types must agree.",
                elem_classes="phase-desc",
            )
            semantic_status = gr.Markdown(elem_classes="status-row")
            symbol_table = gr.Dataframe(
                headers=["Name", "Type"],
                datatype=["str", "str"],
                label="Symbol Table (global scope)",
                interactive=False,
            )

        gr.Markdown(
            "Try the `errors` sample to see how type and scope errors are reported.",
            elem_classes="footer-note",
        )

        # --- Wiring --------------------------------------------------------
        sample_dropdown.change(_load_sample, inputs=sample_dropdown, outputs=code_input)
        compile_btn.click(
            compile_all,
            inputs=code_input,
            outputs=[status, tokens_table, ast_view, semantic_status, symbol_table],
        )

    return demo
