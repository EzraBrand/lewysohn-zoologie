"""Second reading of the Hebrew: flag every Hebrew word where two OCR engines differ.

  uv run hebcheck.py 1 63                         # pages 1-63 (p. 1 = scan0015)
  uv run hebcheck.py 64 158 --main "or-claude-sonnet-5.5@low+ital" --crops

The main engine (Opus or Sonnet) reads German and layout well but writes plausible wrong Hebrew
words (נער for עוא, טגרים for טגריס); Gemini 3.8 Flash reads Hebrew letters better but reverses
right-to-left lists. Their errors differ, so a difference marks a word to check against the scan.
Vowel points are removed before comparing; final letters are kept (ם vs ס matters).
A difference where the same words only come in another order is "order" (usually Flash
reversing a list): low priority. Writes logs/hebcheck_{first}-{last}.csv; with --crops, an image
of the area around each flagged line in logs/hebcheck_crops/ for review.
"""

import argparse
import csv
import difflib
import json
import re
import sys
from pathlib import Path

from PIL import Image

import ocr

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
DATA = ROOT / "data"
WORD = re.compile(r"[א-ת][֑-ׇא-ת'\"]*")
POINTS = re.compile(r"[֑-ׇ]")


def key(page: int) -> str:
    return "scan0015" if page == 1 else str(page)  # p. 1 is unnumbered in the Frankfurt manifest


def words(engine: str, page: str) -> tuple[list[tuple[str, int]], list[str]]:
    """-> [(word without points, line index)], lines of the page (furniture left out)."""
    f = DATA / "ocr" / engine / f"{page}.json"
    blocks = json.loads(f.read_text(encoding="utf-8"))["blocks"]
    lines = "\n".join(b["text"] for b in blocks if b["type"] != "furniture").split("\n")
    out = [(POINTS.sub("", m.group(0)).strip("'\""), i) for i, line in enumerate(lines) for m in WORD.finditer(line)]
    return out, lines


def crop(page: str, line: int, n_lines: int, out: Path) -> None:
    """The scan area around a line, estimated from its position among the page's lines."""
    gray = Image.open(DATA / "raw" / f"{page}.jpg").convert("L")
    x0, y0, x1, y1 = ocr.text_box(gray)
    y = y0 + (y1 - y0) * (line + 0.5) / max(n_lines, 1)
    h = (y1 - y0) * 0.09
    gray.crop((x0, max(int(y - h), 0), x1, min(int(y + h), gray.height))).save(out, quality=85)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("first", type=int)
    p.add_argument("last", type=int)
    p.add_argument("--main", default="or-claude-opus-5.5@low+ital")
    p.add_argument("--check", default="or-gemini-3.8-flash@low+ital")
    p.add_argument("--crops", action="store_true")
    a = p.parse_args()
    rows, n_words = [], 0
    crops = ROOT / "logs" / "hebcheck_crops"
    for page in range(a.first, a.last + 1):
        page_rows_from = len(rows)
        k = key(page)
        if not (DATA / "ocr" / a.check / f"{k}.json").exists() or not (DATA / "ocr" / a.main / f"{k}.json").exists():
            print(f"p. {page}: missing OCR, skipped")
            continue
        m, lines = words(a.main, k)
        c, _ = words(a.check, k)
        n_words += len(m)
        sm = difflib.SequenceMatcher(None, [w for w, _ in m], [w for w, _ in c], autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            mw, cw = [w for w, _ in m[i1:i2]], [w for w, _ in c[j1:j2]]
            kind = "order" if len(mw) > 1 and sorted(mw) == sorted(cw) else op
            line = m[i1][1] if i1 < len(m) else (m[-1][1] if m else 0)
            row = {"page": page, "kind": kind, "main": " ".join(mw), "check": " ".join(cw),
                   "line": lines[line].strip() if lines else "", "crop": ""}
            if a.crops and kind != "order":
                crops.mkdir(parents=True, exist_ok=True)
                out = crops / f"p{page:03d}_{len(rows):03d}.jpg"
                crop(k, line, len(lines), out)
                row["crop"] = out.name
            rows.append(row)
        # a reversed list can come out as a deletion plus an insertion of the same words
        dels = [r for r in rows[page_rows_from:] if r["kind"] == "delete"]
        ins = [r for r in rows[page_rows_from:] if r["kind"] == "insert"]
        for d in dels:
            for i in ins:
                if i["kind"] == "insert" and sorted(d["main"].split()) == sorted(i["check"].split()):
                    d["kind"] = i["kind"] = "order"
    out = ROOT / "logs" / f"hebcheck_{a.first}-{a.last}.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["page", "kind", "main", "check", "line", "crop"])
        w.writeheader()
        w.writerows(rows)
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"{n_words} Hebrew words in {a.main}; {len(rows)} differences {kinds}; wrote {out}")


if __name__ == "__main__":
    main()
