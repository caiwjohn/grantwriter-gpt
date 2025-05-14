import json, sys, re
from pathlib import Path

path = Path("tmp_json/R01_John_2020.json")
data = json.loads(path.read_text())

missing = []
for i, el in enumerate(data):
    if re.search(r"(?i)^specific\s+aims?$", el["text"].strip()):
        # Look ahead for the first non‑blank paragraph
        for j in range(i + 1, min(i + 6, len(data))):
            if data[j]["type"] not in {"Title", "Section"} and data[j]["text"].strip():
                break
        else:
            missing.append(i)

if missing:
    print(f"⚠️  Heading found but no paragraph after elements {missing}")
else:
    print("✅  Specific Aims heading followed by text ✅")
