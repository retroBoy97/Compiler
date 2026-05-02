"""
CL Compiler — web UI entry point.

Run:
    uv run python ui.py
"""

import gradio as gr

from webui import build_demo, load_css


if __name__ == "__main__":
    demo = build_demo()
    demo.launch(theme=gr.themes.Base(), css=load_css())
