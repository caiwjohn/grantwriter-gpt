#!/usr/bin/env python3
"""
pdf_to_text.py  –  Convert a grant PDF to clean Markdown using GROBID

Example
-------
python scripts/pdf_to_text.py \
    --input  data/00_raw_pdfs/R01_smith_2023.pdf \
    --output data/01_clean_text/R01_smith_2023.md \
    --parser grobid
"""
import argparse
import pathlib
import requests
import sys
from io import BytesIO
from lxml import etree
from tqdm import tqdm
import re


# --------------------------- GROBID helpers --------------------------- #
def call_grobid(pdf_path: pathlib.Path, grobid_url: str) -> bytes:
    """
    POST the PDF to GROBID and return the raw TEI‑XML bytes.
    """
    endpoint = f"{grobid_url.rstrip('/')}/api/processFulltextDocument"
    with pdf_path.open("rb") as f:
        files = {"input": (pdf_path.name, f, "application/pdf")}
        resp = requests.post(endpoint, files=files)
    if resp.status_code != 200:
        raise RuntimeError(
            f"GROBID error {resp.status_code}: {resp.text[:400]}"
        )
    return resp.content


def tei_to_markdown(tei: bytes) -> str:
    """
    TEI‑XML ➜ Markdown converter that keeps headings & paragraphs
    from *any* part of the document (front, body, back).
    """
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    root = etree.parse(BytesIO(tei))

    # Grab heads & paragraphs everywhere, in document order
    nodes = root.xpath(".//tei:head | .//tei:p", namespaces=ns)

    lines = []
    for node in nodes:
        text = "".join(node.itertext()).strip()
        if not text:
            continue

        if node.tag.endswith("head"):
            # Heuristic: promote heads that look like grant sections to top‑level
            if re.match(r"(?i)specific\s+aims?", text):
                depth = 1      # force to '# '
            else:
                # depth = nesting of ancestor <div> elements
                depth = 1
                parent = node.getparent()
                while parent is not None and parent.tag.endswith("div"):
                    depth += 1
                    parent = parent.getparent()
                depth = min(depth, 4)
            lines.append("#" * depth + " " + text)
        else:                          # paragraph
            lines.append(text)

        lines.append("")               # blank line spacer

    return "\n".join(lines).rstrip() + "\n"


# --------------------------- Main CLI --------------------------- #
def parse_args():
    p = argparse.ArgumentParser(description="Convert PDF to Markdown via GROBID")
    p.add_argument("--input", "-i", required=True, type=pathlib.Path)
    p.add_argument("--output", "-o", required=True, type=pathlib.Path)
    p.add_argument(
        "--parser", default="grobid",
        help="Unused placeholder to mirror earlier CLI; must be 'grobid'"
    )
    p.add_argument(
        "--grobid_url", default="http://localhost:8070",
        help="Base URL of the GROBID server"
    )
    return p.parse_args()


def main():
    args = parse_args()

    if args.parser.lower() != "grobid":
        sys.exit("Error: --parser must be 'grobid' for this script.")

    if not args.input.exists():
        sys.exit(f"Input PDF not found: {args.input}")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    print(f"→ Sending {args.input.name} to GROBID at {args.grobid_url}")
    tei = call_grobid(args.input, args.grobid_url)

    print("→ Converting TEI‑XML to Markdown")
    md = tei_to_markdown(tei)

    args.output.write_text(md, encoding="utf‑8")
    print(f"✓ Wrote clean text to {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.exit(f"Failed: {e}")

