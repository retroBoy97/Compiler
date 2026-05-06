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


# Loads mermaid.js once and renders any <pre class="mermaid"> that appears
# in the DOM (including blocks that Gradio injects after a Compile click).
_MERMAID_HEAD = """
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>
(function () {
  var initialized = false;
  var pending = null;

  function init() {
    if (initialized || !window.mermaid) return;
    window.mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        background: '#0a0a0a',
        primaryColor: '#0a0a0a',
        primaryTextColor: '#ededed',
        primaryBorderColor: '#3b9eff',
        lineColor: 'rgba(255,255,255,0.35)',
        textColor: '#ededed',
        mainBkg: '#0a0a0a',
        fontFamily: 'Geist Mono, ui-monospace, monospace',
        fontSize: '13px'
      },
      flowchart: { curve: 'basis', padding: 12, nodeSpacing: 28, rankSpacing: 38 }
    });
    initialized = true;
  }

  function render() {
    if (!window.mermaid) return;
    init();
    var nodes = document.querySelectorAll('pre.mermaid:not([data-processed="true"])');
    if (nodes.length === 0) return;
    try { window.mermaid.run({ nodes: nodes }); }
    catch (e) { console.error('mermaid render failed:', e); }
  }

  function schedule() {
    if (pending) return;
    pending = setTimeout(function () { pending = null; render(); }, 80);
  }

  function setup() {
    if (!window.mermaid) { setTimeout(setup, 100); return; }
    render();
    new MutationObserver(schedule).observe(
      document.body, { childList: true, subtree: true }
    );
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
})();
</script>
"""


def load_css() -> str:
    return (Path(__file__).parent / "styles.css").read_text(encoding="utf-8")


def _load_sample(name: str) -> str:
    return SAMPLES.get(name, "")


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="CL Compiler — Visualizer", head=_MERMAID_HEAD) as demo:
        # --- Header --------------------------------------------------------
        gr.Markdown("# CL Compiler", elem_classes="app-header")
        gr.Markdown(
            "A visual pipeline for the CL language — watch source code flow through "
            "**Lexer → Parser → Semantic Analyzer**.",
            elem_classes="app-subtitle",
        )
        gr.Markdown(
            "Kacem Mathlouthi · Mohamed Amine Haouas · Alaeddine Zaouali · Rami Kaabi · Oussama Kraiem",
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
            ast_view = gr.HTML(
                value='<div class="ast-mermaid-empty">Click Compile to see the syntax tree.</div>',
                elem_classes="ast-view",
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
