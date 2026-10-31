"""archive.org's own OCR of the Toronto copy, as a baseline engine for eval.py.

  uv run ia_ocr.py 68 70        # writes data/ocr/archive.org/{page}.json

Source: the item's DjVu XML (one OBJECT per leaf, LINE/WORD inside), downloaded once and cached.
Leaf = printed page + 18 for the main text (archive.org leaf 21 is p. 3; checked against the
item's page_numbers.json). The OCR read the Fraktur as roman type, so it is a floor, not a source.
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import fetch

sys.stdout.reconfigure(encoding="utf-8")

ID = "diezoologiedesta00lewyuoft"
URL = f"https://archive.org/download/{ID}/{ID}_djvu.xml"
CACHE = fetch.DATA / "cache" / "archive.org" / f"{ID}_djvu.xml"
OUT = fetch.DATA / "ocr" / "archive.org"
LEAF_OFFSET = 18


def leaf_text(root: ET.Element, leaf: int) -> str:
    for obj in root.iter("OBJECT"):
        usemap = obj.get("usemap", "")
        if re.search(rf"_{leaf:04d}\.djvu$", usemap):
            return "\n".join(" ".join(w.text or "" for w in line.iter("WORD")) for line in obj.iter("LINE"))
    raise KeyError(f"leaf {leaf} not in {CACHE.name}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pages", nargs="+", type=int)
    a = p.parse_args()
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_bytes(fetch.get(URL).content)
    root = ET.parse(CACHE).getroot()
    OUT.mkdir(parents=True, exist_ok=True)
    for page in a.pages:
        text = leaf_text(root, page + LEAF_OFFSET)
        res = {"blocks": [{"type": "body", "lang": "other", "text": text, "marker": ""}],
               "meta": {"engine": "archive.org", "source": URL, "leaf": page + LEAF_OFFSET, "cost_usd": 0}}
        (OUT / f"{page}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"p. {page} (leaf {page + LEAF_OFFSET}): {len(text)} characters; first line: {text.splitlines()[0][:70]!r}")


if __name__ == "__main__":
    main()
