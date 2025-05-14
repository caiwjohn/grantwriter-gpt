#!/usr/bin/env python3
"""
Extract only the Specific Aims section from an unstructured JSON and
save it as Markdown.
"""
import json, re, textwrap, pathlib, sys

SRC_JSON = "tmp_json/R01_John_2020.json"
DST_MD   = "review/R01_John_2020_specific_aims.md"

# --- load elements ----------------------------------------------------------
elts = json.loads(pathlib.Path(SRC_JSON).read_text())

# --- find the Specific Aims heading ----------------------------------------
aims_start = None
heading_pattern = re.compile(r"(?i)\bspecific\s+aims?\b")  # case‑insensitive and leading characters

for idx, e in enumerate(elts):
    if e["type"].startswith("Title") and heading_pattern.search(e["text"]):
        aims_start = idx
        break

if aims_start is None:
    sys.exit("❌  No 'Specific Aims' heading found in JSON")

# --- collect until next top‑level heading ----------------------------------
lines = []
for e in elts[aims_start:]:
    # stop when we hit a *different* Title element at the same level
    if e["type"].startswith("Title") and not heading_pattern.search(e["text"]) \
       and lines:
        break

    if e["type"].startswith("Title"):
        # Promote to level‑1 heading
        lines.append("# " + e["text"].strip())
    else:
        lines.append(textwrap.fill(e["text"].strip(), width=100))
    lines.append("")         # blank line spacer

# --- write out --------------------------------------------------------------
out_path = pathlib.Path(DST_MD)
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf‑8")
print(f"✅  Wrote Specific Aims ➜ {out_path}")
