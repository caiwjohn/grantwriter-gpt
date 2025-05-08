# GrantWriter‑GPT

A lightweight retrieval‑augmented language‑model assistant that helps biomedical researchers draft **NIH R01 Specific Aims** pages by learning from past funded grants.

---

## Project Snapshot
| Item | Detail |
|------|--------|
| **Project start date** | **30 April 2025** |
| **Outcome** | Deployable prototype (CLI + minimal web UI) that:<br>1. Ingests/embeds exemplar R01 grants<br>2. Generates draft Specific Aims text on demand<br>3. Cites source grants for every paragraph |
| **Constraints** | ≤ US $100 total compute • 5 h per week • Solo developer • Runs locally on MacBook Pro (M3) |

---

## Condensed Timeline (8‑week view)

| Week | Focus (1‑h work blocks) | Key Deliverables |
|------|------------------------|------------------|
| 0 | **Kick‑off** – scope & success criteria | Decide: R01 + Specific Aims only |
| 1 | **Dataset collection** | 5–10 funded R01 PDFs secured |
| 2 | **Parsing & cleaning** | JSONL with title, aims text, scores |
| 3 | **Embedding & vector store** | FAISS index + retrieval sanity test |
| 4 | **Fine‑tuning GPT‑4o‑mini** | First 100‑epoch run (< $25) |
| 5 | **RAG pipeline integration** | End‑to‑end script with citations |
| 6 | **Minimal UI** | Streamlit demo & Typer CLI |
| 7 | **Evaluation & refinement** | BLEU/ROUGE metrics, human review |
| 8 | **Packaging & docs** | `pip install grantwriter‑gpt` + README |

---

## Tech Stack
| Layer | Tools |
|-------|-------|
| **Programming** | Python 3.11 |
| **LLM** | OpenAI **GPT‑4o‑mini** (fine‑tuned) |
| **Embeddings** | `text‑embedding‑3‑small` |
| **Vector DB** | FAISS (in‑memory, local) |
| **Frameworks** | LangChain · tiktoken · pydantic |
| **PDF / text** | PyPDF2 · pandas · spaCy |
| **Interface** | Typer CLI · Streamlit web demo |
| **Testing** | pytest · coverage |
| **CI/CD** | GitHub Actions |

---

## Quick Start

```bash
# clone & create environment
git clone https://github.com/<your‑org>/grantwriter‑gpt.git
cd grantwriter‑gpt
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# ingest sample grants
python scripts/ingest_grants.py data/raw/*.pdf

# launch demo UI
streamlit run ui/demo.py

