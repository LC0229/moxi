"""
Pipeline dashboard: for developers only (workflow + collection count).

Separate from the user-facing web UI (gradio_app). Run: make pipeline-dashboard.
Shows architecture diagram (llm-twin style) with implemented parts in bold + real data.
"""

import gradio as gr

from web_ui.pipeline_stats import get_pipeline_stats


def _build_architecture_md(stats: dict) -> str:
    """Build architecture diagram markdown: 4 pipelines, implemented parts in bold with data."""
    n = stats["collection_count"]
    src = stats["collection_source"]
    sft_n = stats["sft_count"]

    return f"""
## End-to-end architecture (production-ready LLM system)

*Bold = implemented in this project, with live data.*

---

### 1. Data Collection Pipeline

| Component | Status |
|-----------|--------|
| Digital data sources | Medium, Substack, LinkedIn, **GitHub** |
| ETL | Medium ETL, Substack ETL, LinkedIn ETL, **GitHub ETL** (awesome-readme → READMEs + file trees) |
| **(1) NoSQL DB** | **MongoDB — {n} readme_samples** ({src}) |
| CDC → Queue (2) | Not implemented |

---

### 2. Feature Pipeline (Streaming Ingestion)

| Component | Status |
|-----------|--------|
| (2) Queue → streaming ingestion | Not implemented (bytewax / Superlinked) |
| Features: Articles, Posts, Code (3) | Not implemented |
| **(4) Vector DB** | Qdrant configured; not populated from README pipeline |
| Vector DB Retrieval Clients | Not implemented |

---

### 3. Training Pipeline

| Component | Status |
|-----------|--------|
| Experiment Tracker (Comet) | Optional; config present |
| **(5) LLM Fine-tuning** | **SFT trainer implemented** (`sft_trainer.py`); LoRA/QLoRA, optional Alpaca merge |
| Data to Prompt Layer | To implement (chunk → instruction + input + content) |
| Qdrant Retrieval Clients (5) | Not used for README task (we use file_tree) |
| LLM Candidate (6) → Model Registry (7) | Not implemented |
| Evaluate LLM Candidate (Opik) | Not implemented |
| Load & Quantize LLM (8) → Twin LLM (10) | Not implemented |
| **SFT dataset** | **{sft_n} samples** (when Phase 3 run) |

---

### 4. Inference Pipeline

| Component | Status |
|-----------|--------|
| Twin LLM (10) | Not implemented |
| Query to Prompt Layer | Not implemented |
| Qdrant Retrieval → Metadata & Text | Not implemented |
| REST API (e.g. AWS) | Not implemented |

---

### Implemented summary (live data)

- **Data Collection:** **{n}** README samples in **MongoDB** `readme_samples` ({src}).
- **Training (foundation):** SFT trainer and data shape ready; SFT dataset count: **{sft_n}**.
- **Feature / Inference:** Not yet implemented.
"""


def _build_pipeline_md(stats: dict) -> str:
    """Build phase table (same structure as llm-twin-course)."""
    lines = [
        "## Phase table (Collect → Chunk → Instructions → Train → Infer)",
        "",
        "| Phase | Name | Description | Output | Status |",
        "|-------|------|--------------|--------|--------|",
    ]
    for p in stats["phases"]:
        name = p["name"]
        desc = p["description"][:50] + "…" if len(p["description"]) > 50 else p["description"]
        out = p["output"][:40] + "…" if len(p["output"]) > 40 else p["output"]
        status = p["status"]
        count_str = f" **{p['count']}**" if p.get("count") is not None and p["count"] > 0 else ""
        lines.append(f"| **{p['id']}** | {name} | {desc} | {out} | {status}{count_str} |")
    return "\n".join(lines)


def refresh_dashboard() -> tuple[str, str, str]:
    """Fetch latest stats; return (architecture_md, phase_table_md, status_summary)."""
    stats = get_pipeline_stats()
    architecture_md = _build_architecture_md(stats)
    phase_table_md = _build_pipeline_md(stats)
    summary = (
        f"**Collection: {stats['collection_count']}** samples | "
        f"**SFT dataset: {stats['sft_count']}** samples"
    )
    return architecture_md, phase_table_md, summary


def create_interface():
    """Create Gradio Blocks for the pipeline dashboard (architecture + phase table)."""
    architecture_md, phase_table_md, summary = refresh_dashboard()

    with gr.Blocks(
        title="Moxi – Pipeline Architecture",
        css="""
        .phase-done { color: #16a34a; }
        .phase-pending { color: #6b7280; }
        """
    ) as app:
        gr.Markdown(
            """
            # Moxi – Production-ready LLM pipeline (llm-twin style)

            Four pipelines: **Data Collection** → **Feature (Streaming)** → **Training** → **Inference**.
            Implemented parts are **bold** with live data from MongoDB / config.
            """
        )

        status_line = gr.Markdown(summary)
        refresh_btn = gr.Button("Refresh", variant="primary")

        gr.Markdown("### Architecture diagram")
        architecture_display = gr.Markdown(architecture_md)

        with gr.Accordion("Phase table (Collect → Chunk → Instructions → Train → Infer)", open=False):
            phase_display = gr.Markdown(phase_table_md)

        refresh_btn.click(
            fn=refresh_dashboard,
            inputs=[],
            outputs=[architecture_display, phase_display, status_line],
        )

        gr.Markdown("---\n**References:** `TRAINING_WORKFLOW.md`, `PROCESS_COMPARISON.md`")

    return app


def main():
    """Run the pipeline dashboard (Gradio)."""
    import socket

    def find_free_port(start: int = 7861, attempts: int = 10):
        for i in range(attempts):
            port = start + i
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("localhost", port)) != 0:
                    return port
        return None

    app = create_interface()
    port = find_free_port(7861) or 0
    app.launch(server_name="0.0.0.0", server_port=port, share=False)


if __name__ == "__main__":
    main()
