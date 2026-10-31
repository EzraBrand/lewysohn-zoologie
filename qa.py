"""Checks on the OCR of a range of pages, before joining and translating them.

  uv run qa.py 1 63              # pages 1-63 (page 1 = scan0015); writes logs/qa_{from}-{to}.csv
  uv run qa.py 64 158 --main "or-claude-sonnet-5.5@low+ital"

Per page: blocks, characters, Hebrew characters, the ratio to archive.org's OCR of the same page
(its text is garbage, but its length is about right: a low ratio means dropped text), footnote
marks in the text vs. footnotes found, and the last and first words at each page break (for the
join check by eye), and footnote blocks that come before the body text (the OCR typed body
text as a footnote on p. 16). Prints the pages that need a look.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import ia_ocr

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
MARK = re.compile(r"(?<![*†])(\*{1,3}|†{1,2})\)")
SENTENCE_END = re.compile(r"[.!?:;)\]]\s*$")


def key(page: int) -> str:
    return "scan0015" if page == 1 else str(page)  # p. 1 is unnumbered in the Frankfurt manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("first", type=int)
    p.add_argument("last", type=int)
    p.add_argument("--main", default="or-claude-opus-5.5@low+ital", help="OCR folder in data/ocr/")
    a = p.parse_args()
    source = ROOT / "data" / "ocr" / a.main
    root = ia_ocr.ET.parse(ia_ocr.CACHE).getroot() if ia_ocr.CACHE.exists() else None
    rows, prev_end = [], None
    for page in range(a.first, a.last + 1):
        f = source / f"{key(page)}.json"
        if not f.exists():
            rows.append({"page": page, "problem": "no OCR"})
            continue
        blocks = json.loads(f.read_text(encoding="utf-8"))["blocks"]
        main = [b for b in blocks if b["type"] not in ("furniture", "footnote")]
        notes = [b for b in blocks if b["type"] == "footnote"]
        text = "".join(b["text"] for b in blocks if b["type"] != "furniture")
        ia = len(re.sub(r"\s+", "", ia_ocr.leaf_text(root, page + ia_ocr.LEAF_OFFSET))) if root is not None else 0
        ratio = round(len(re.sub(r"\s+", "", text)) / ia, 2) if ia else ""
        marks = MARK.findall("".join(b["text"] for b in main))
        start = main[0]["text"].strip().split("\n")[0][:50] if main else ""
        end = main[-1]["text"].strip().split("\n")[-1][-50:] if main else ""
        problems = []
        body = [b for b in blocks if b["type"] != "furniture"]
        first = next((i for i, b in enumerate(body) if b["type"] in ("body", "heading")), len(body))
        if any(b["type"] == "footnote" for b in body[:first]):
            problems.append("footnote before the body text (body typed as footnote?)")
        if ratio and not 0.8 <= ratio <= 1.25:
            problems.append(f"length {ratio}× archive.org")
        if len(marks) != len(notes):
            problems.append(f"{len(marks)} marks, {len(notes)} notes")
        rows.append({"page": page, "blocks": len(blocks), "chars": len(text),
                     "hebrew": len(re.findall(r"[א-ת]", text)), "ratio_ia": ratio,
                     "marks": len(marks), "notes": len(notes),
                     "join": "" if prev_end is None else
                     ("break" if SENTENCE_END.search(prev_end) else "continue"),
                     "prev_end": prev_end or "", "start": start, "problem": "; ".join(problems)})
        prev_end = end
    out = ROOT / "logs" / f"qa_{a.first}-{a.last}.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(max(rows, key=len).keys()))
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r.get("problem")]
    print(f"{len(rows)} pages, {sum(r.get('chars', 0) for r in rows)} characters, "
          f"{sum(r.get('hebrew', 0) for r in rows)} Hebrew letters; {len(bad)} to look at; wrote {out}")
    for r in bad:
        print(f"  p. {r['page']}: {r['problem']}")


if __name__ == "__main__":
    main()
