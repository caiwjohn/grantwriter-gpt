#!/usr/bin/env python3
"""
ingest_reviewed_aims.py
=======================
Collect reviewed Specific Aims markdown files, build a JSONL with schema:

{
  "grant_id": "<file‑stem>",
  "section" : "Specific Aims",
  "heading" : "<markdown headings>",
  "text"    : "<body narrative, single newlines removed>",
  "raw_md"  : "<full markdown text>"
}

Usage:
  python scripts/ingest_reviewed_aims.py <data_root_dir>
"""

import json
import pathlib
import re
import sys

SECTION_NAME = "Specific Aims"
HEAD_RE = re.compile(r"^\s*#+\s")  # markdown header lines


def squash_single_newlines(lines: list[str]) -> str:
    """Join lines into paragraphs: single newlines -> space, blank lines kept."""
    paragraphs, buf = [], []
    for line in lines + [""]:  # sentinel blank to flush
        if line.strip() == "":
            if buf:
                paragraphs.append(" ".join(buf).strip())
                buf = []
            else:
                paragraphs.append("")  # preserve existing blank line
        else:
            buf.append(line.strip())
    # remove leading/trailing blank paragraphs
    while paragraphs and paragraphs[0] == "":
        paragraphs.pop(0)
    while paragraphs and paragraphs[-1] == "":
        paragraphs.pop()
    return "\n\n".join(paragraphs)


def parse_markdown(path: pathlib.Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8").rstrip()
    headings, body_lines = [], []

    for line in raw.splitlines():
        if HEAD_RE.match(line):
            headings.append(line.rstrip())
        else:
            body_lines.append(line.rstrip())

    return {
        "heading": "\n".join(headings).strip(),
        "text": squash_single_newlines(body_lines),
        "raw_md": raw,
    }


def main(data_root: pathlib.Path) -> None:
    reviewed_dir = data_root / "04_reviewed_aims_md"
    out_dir = data_root / "05_clean_jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "reviewed_specific_aims.jsonl"

    md_files = sorted(reviewed_dir.glob("*.md"))
    if not md_files:
        sys.exit(f"No markdown files found in {reviewed_dir}")

    with out_path.open("w", encoding="utf-8") as fout:
        for md in md_files:
            parts = parse_markdown(md)
            if not parts["text"]:
                print(f"⚠️  {md.name} has no body text — skipped")
                continue

            grant_id = (
                md.stem.replace("_specific_aims", "")
                .replace("_reviewed", "")
                .replace("_aims", "")
            )

            row = {
                "grant_id": grant_id,
                "section": SECTION_NAME,
                **parts,
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"✓ Ingested {len(md_files)} file(s) → {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("USAGE:\n  python scripts/ingest_reviewed_aims.py <data_root_dir>")
    main(pathlib.Path(sys.argv[1]).expanduser())
