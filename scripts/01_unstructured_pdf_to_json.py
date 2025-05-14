#!/usr/bin/env python3
"""
unstructured_pdf_to_json.py
===========================
Parse an NIH R‑series grant PDF with `unstructured`, then emit:

1. data/00_full_json/<grant_id>.json            – raw element list
2. data/01_clean_text/<grant_id>.md             – whole grant as Markdown
3. data/02_sections_jsonl/<grant_id>.jsonl      – one JSON line per section
4. data/03_specific_aims_md/<grant_id>_specific_aims.md
5. data/metadata/<grant_id>.yml                 – PI / institution / etc.

USAGE
-----
python scripts/unstructured_pdf_to_json.py \
       path/to/input.pdf \
       path/to/data      # repository “data/” folder root
"""

import hashlib
import json
import pathlib
import re
import sys
import textwrap
from datetime import datetime
import yaml             
from unstructured.partition.pdf import partition_pdf

# --------------------------- regex helpers --------------------------- #
AIMS_HEAD   = re.compile(r"(?i)\bspecific\s+aims?\b")
AIM_SUBHEAD = re.compile(r"(?i)\b(?:specific\s+)?aim\s*\d+\b|\baim\s*\d+\b")

STOP_HEAD   = re.compile(
    r"(?i)^(significance|innovation|approach|research\s+strategy|"
    r"project\s+summary|abstract|bibliography|references)\b"
)

# crude patterns for metadata
META_PATTERNS = {
    "pi": re.compile(r"(?i)principal investigator[:\s]*([\w ,.-]+)"),
    "institution": re.compile(r"(?i)(?:applicant|performance) organization[:\s]*([\w ,.-]+)"),
    "project_title": re.compile(r"(?i)project title[:\s]*(.+)"),
    "project_number": re.compile(r"(?i)project number[:\s]*(\w{2,}-\w{2,}-\w{6,})"),
    "ic": re.compile(r"(?i)\b(?:issuing)?\s?ic[:\s]*([A-Z]{2,4})\b"),
    "fy": re.compile(r"(?i)fiscal year[:\s]*(\d{4})"),
}

# --------------------------- utilities ------------------------------- #
def is_title(el) -> bool:
    """Return True for heading‑like elements."""
    return getattr(el, "category", "").lower() in {"title", "header"}

def page_num(el):
    return getattr(el.metadata, "page_number", None)

def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# --------------------------- main ------------------------------------ #
def extract_pdf(src_pdf: pathlib.Path, data_root: pathlib.Path):
    grant_id = src_pdf.stem

    # ------------------------------------------------------------------ #
    # 0) partition with unstructured
    elements = partition_pdf(
        filename=str(src_pdf),
        strategy="auto",
        infer_table_structure=True,
    )

    # prepare output dirs
    json_dir      = data_root / "01_full_json"
    clean_dir     = data_root / "02_full_md"
    aims_dir      = data_root / "03_specific_aims_md"
    meta_dir      = data_root / "metadata"
    for d in (json_dir, clean_dir, aims_dir, meta_dir):
        d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 1) raw JSON dump
    json_path = json_dir / f"{grant_id}.json"
    json_path.write_text(json.dumps([e.to_dict() for e in elements], indent=2), "utf-8")
    print(f"✓ full JSON  → {json_path.relative_to(data_root)}")

    # ------------------------------------------------------------------ #
    # 2) whole‑grant Markdown
    md_lines = []
    for el in elements:
        txt = (el.text or "").strip()
        if not txt:
            continue
        if is_title(el):
            depth = min(4, getattr(el.metadata, "section_depth", 1) or 1)
            md_lines.append("#" * depth + " " + txt)
        else:
            md_lines.append(textwrap.fill(txt, width=100))
        md_lines.append("")          # blank line
    clean_path = clean_dir / f"{grant_id}.md"
    clean_path.write_text("\n".join(md_lines).rstrip() + "\n", "utf-8")
    print(f"✓ whole MD   → {clean_path.relative_to(data_root)}")

    # ------------------------------------------------------------------ #
    # 3) Specific Aims page Markdown
    aims_md = []
    start_idx, aims_page = None, None
    for i, el in enumerate(elements):
        if is_title(el) and AIMS_HEAD.search(el.text or ""):
            start_idx, aims_page = i, page_num(el)
            break
    if start_idx is not None:
        for el in elements[start_idx:]:
            txt = (el.text or "").strip()
            if not txt:
                continue
            if is_title(el) and STOP_HEAD.match(txt):
                break
            if aims_page is not None and page_num(el) != aims_page:
                break
            if is_title(el):
                if AIMS_HEAD.search(txt) or AIM_SUBHEAD.search(txt):
                    aims_md.append("## " + txt)
                else:
                    aims_md.append("### " + txt)
            else:
                aims_md.append(textwrap.fill(txt, 100))
            aims_md.append("")
        aims_path = aims_dir / f"{grant_id}_specific_aims.md"
        aims_path.write_text("\n".join(aims_md).rstrip() + "\n", "utf-8")
        print(f"✓ aims MD    → {aims_path.relative_to(data_root)}")
    else:
        print("⚠️  Specific Aims heading not found; skipped aims MD")

    # ------------------------------------------------------------------ #
    # 4) lightweight metadata YAML
    meta = {
        "grant_id": grant_id,
        "source_pdf": str(src_pdf),
        "sha256": sha256_of(src_pdf),
        "extracted_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    # scrape cover‑page elements
    cover_text = "\n".join(e.text or "" for e in elements[:40])
    for k, pat in META_PATTERNS.items():
        m = pat.search(cover_text)
        if m:
            meta[k] = m.group(1).strip()
    meta_path = meta_dir / f"{grant_id}.yml"
    meta_path.write_text(yaml.safe_dump(meta, sort_keys=False), "utf-8")
    print(f"✓ metadata   → {meta_path.relative_to(data_root)}")

# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(
            "USAGE:\n  python scripts/unstructured_pdf_to_json.py "
            "<input.pdf> <data_root_dir>"
        )
    extract_pdf(pathlib.Path(sys.argv[1]).expanduser(),
                pathlib.Path(sys.argv[2]).expanduser())
