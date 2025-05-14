#!/usr/bin/env python3
"""
unstructured_pdf_to_json.py  ─  Extract a PDF with unstructured
                                + capture the Specific Aims section.

Outputs
-------
1. <output‑base>.json   – full list[dict]  (all elements)
2. <output‑base>_specific_aims.md          (Markdown page)

Example
-------
python scripts/unstructured_pdf_to_json.py \
       data/00_raw_pdfs/R01_Smith_2023.pdf \
       data/01_parsed/R01_Smith_2023
"""

import json, re, textwrap, pathlib, sys
from unstructured.partition.pdf import partition_pdf

# --- helper ----------------------------------------------------------- #
def is_title(el):
    """Return True for any element that behaves like a heading."""
    return getattr(el, "category", "").lower() in {"title", "header"}

# --------------------------------------------------------------------- #

# --------------------------- regex helpers --------------------------- #
AIMS_HEAD   = re.compile(r"(?i)\bspecific\s+aims?\b")
AIM_SUBHEAD = re.compile(r"(?i)\b(?:specific\s+)?aims?\s*\d+\b|\baim\s*\d+\b")

STOP_HEAD   = re.compile(
    r"(?i)^(significance|innovation|approach|research\s+strategy|"
    r"project\s+summary|introduction|bibliography|references)\b"
)


# --------------------------- main routine --------------------------- #
def extract_pdf(src_pdf: pathlib.Path, out_base: pathlib.Path):
    # --- run unstructured ---------------------------------------------------
    elements = partition_pdf(
        filename=str(src_pdf),
        strategy="auto",            # "hi_res" when needed
        infer_table_structure=True,
    )

    # --- write full JSON ----------------------------------------------------
    json_path = out_base.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps([e.to_dict() for e in elements], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"✓ wrote full JSON ➜ {json_path}")

    # --- carve out Specific Aims -------------------------------------------
    start, aims_page = None, None
    for i, el in enumerate(elements):
        if is_title(el) and AIMS_HEAD.search(el.text or ""):
            start = i
            aims_page = el.metadata.page_number
            break
    if start is None:
        print("⚠️  no 'Specific Aims' heading found – skipping Markdown page")
        return

    lines = []
    for el in elements[start:]:
        txt = (el.text or "").strip()
        if not txt:
            continue

        if is_title(el) and STOP_HEAD.match(txt):          # <-- use helper
            break
        if aims_page is not None and el.metadata.page_number != aims_page:
            break

        # heading vs paragraph formatting
        if is_title(el):                                   # <-- use helper
            if AIMS_HEAD.search(txt) or AIM_SUBHEAD.search(txt):
                lines.append("## " + txt)
            else:
                lines.append("### " + txt)
        else:
            lines.append(textwrap.fill(txt, 100))
        lines.append("")

    md_path = out_base.with_name(out_base.name + "_specific_aims.md")
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"✓ wrote Specific Aims MD ➜ {md_path}")


# --------------------------- CLI ------------------------------------- #
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(
            "usage:\n  python scripts/unstructured_pdf_to_json.py "
            "<input.pdf> <output_base_without_extension>"
        )
    extract_pdf(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
