"""Vote on the flagged Hebrew words: Flash's reading, the image judge, the text judge.

  uv run hebvote.py 1 63        # reads logs/hebcheck_1-63.csv, data/hebfix/1-63.json and 1-63.image.json

The main OCR is changed only where at least two of the three checks agree on a reading that differs
from it. On the known cases (pp. 68-71) each check alone was wrong once or twice, the majority was
right in all three. Writes data/hebfix/{range}.decisions.json (applied by entry.py to pages
without gold text) and logs/hebvote_{range}.csv for review.
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from rapidfuzz.distance import Levenshtein

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
FIX = ROOT / "data" / "hebfix"


def similar(old: str, new: str) -> bool:
    """A misread word differs in a letter or two; a pair of different words of a list (an alignment
    error of hebcheck, e.g. יוכני / אוזא) is not changed but listed for review."""
    o, n = old.split(), new.split()
    if len(o) != len(n):
        return False
    return all(Levenshtein.distance(a, b) <= min(2, max(1, len(a) // 2)) for a, b in zip(o, n))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("first", type=int)
    p.add_argument("last", type=int)
    a = p.parse_args()
    rng = f"{a.first}-{a.last}"
    flags = [r for r in csv.DictReader((ROOT / "logs" / f"hebcheck_{rng}.csv").open(encoding="utf-8-sig"))
             if r["kind"] != "order" and r["main"] and r["check"]]
    judge = {}
    files = ([("text", FIX / f"{rng}.json")] + [("text", f) for f in sorted(FIX.glob(f"{rng}_w*.json"))]
             + [("image", f) for f in sorted(FIX.glob(f"{rng}.image*.json"))])
    for name, f in files:  # several files when a judge ran as parallel workers (text: suffix _wN)
        for d in json.loads(f.read_text(encoding="utf-8"))["items"]:
            judge.setdefault((name, d["page"], d["line"], d["main"]), d["printed"])
    missing = [r for r in flags if ("image", int(r["page"]), r["line"], r["main"]) not in judge
               or ("text", int(r["page"]), r["line"], r["main"]) not in judge]
    if missing:
        print(f"{len(missing)} flags not yet decided by both judges; they get no majority unless Flash and one judge agree")
    decisions, rows, tally = [], [], Counter()
    for r in flags:
        k = (int(r["page"]), r["line"], r["main"])
        votes = {"flash": r["check"], "image": judge.get(("image", *k)), "text": judge.get(("text", *k))}
        counts = Counter(v for v in votes.values() if v)
        best, n = counts.most_common(1)[0] if counts else ("", 0)
        if n >= 2 and best != r["main"] and not similar(r["main"], best):
            outcome = "review (words not similar: alignment?)"
        elif n >= 2 and best != r["main"]:
            outcome = "change"
            decisions.append({"page": k[0], "line": k[1], "old": r["main"], "new": best, "votes": votes})
        elif n >= 2:
            outcome = "keep"
        else:
            outcome = "no majority"
        tally[outcome] += 1
        rows.append({"page": k[0], "main (Opus/Sonnet)": r["main"], **votes, "outcome": outcome,
                     "new": best if outcome == "change" else "", "line": k[1]})
    (FIX / f"{rng}.decisions.json").write_text(json.dumps(
        {"rule": "change where at least 2 of flash, image, text agree against the main OCR",
         "items": decisions}, ensure_ascii=False, indent=1), encoding="utf-8")
    out = ROOT / "logs" / f"hebvote_{rng}.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(flags)} flags: {dict(tally)}; wrote {FIX / f'{rng}.decisions.json'} and {out}")


if __name__ == "__main__":
    main()
