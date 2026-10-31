"""Decide the flagged Hebrew words of hebcheck.py from a close crop of the scan.

  uv run hebjudge.py 68 71                 # reads logs/hebcheck_68-71.csv, writes data/hebfix/68-71.json
  uv run hebjudge.py 1 63 --main "or-claude-opus-5.5@low+ital"

For each difference that is not "order", a strip of about five lines around the flagged line is
cut from the scan at full resolution and sent to a model with the OCR line and the two readings.
The model writes the Hebrew letters printed there. entry.py applies an answer where it differs
from the main OCR and the model says it is confident. Answers are kept (one JSON per range) and
the run can be resumed: rows already decided are skipped.
"""

import argparse
import base64
import csv
import io
import json
import os
import sys
import time
from pathlib import Path

import requests
from PIL import Image

import hebcheck
import ocr

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
DATA = ROOT / "data"
KEY_FILE = Path(os.environ.get("OPENROUTER_KEY_FILE", Path.home() / "Desktop/Misc/key.txt"))
MODEL, EFFORT = "anthropic/claude-opus-5.5", "medium"

PROMPT = """\
The image shows a few printed lines of a German book of 1858 (Lewysohn, Die Zoologie des Talmuds), \
with Hebrew and Aramaic words in square Hebrew letters (unpointed). One of the lines was read by \
OCR as:

{line}

Two OCR engines disagree about the Hebrew word(s) in it: one read {a}, the other read {b}.

Find that place in the image and write exactly the Hebrew letters that are PRINTED there, letter \
by letter, as many words as the two readings cover. Do not correct the print to a word you know: \
if the print has an unusual spelling or a misprint, write what is printed. Look closely at the \
letters that are easy to confuse in this type: final ם vs. ס, ו vs. ז vs. י, ח vs. ת vs. ה, \
ד vs. ר, ב vs. כ, ג vs. נ, ע vs. צ, and one letter vs. two (וו vs. ו). It may be that neither \
reading is right.

Answer with JSON only: {{"printed": "...", "confident": true or false, "note": "short reason"}}"""

TEXT_PROMPT = """\
Below is a passage from Ludwig Lewysohn, Die Zoologie des Talmuds (1858), as read by OCR. Two OCR \
engines read the same printed Hebrew/Aramaic word(s) differently: reading A is {a}, reading B is {b}. \
One of them is usually what is printed; the errors are in letters that look alike in Hebrew type \
(final ם / ס, ו / ז / י, ח / ת / ה, ד / ר, ב / כ, ג / נ).

Passage (the word is in the line marked >>):
{context}

Use the sentence: the German meaning Lewysohn gives, the source he cites (Talmud, Midrash, Bible, \
Targum), the Greek or Latin he compares, and your knowledge of rabbinic Hebrew and Aramaic. Decide \
which reading is the word Lewysohn printed. Choose A or B only. Say "confident": true only if one \
reading is clearly the right word here and the other is not (e.g. not a word, or the wrong word \
for this meaning or source); if both are possible, or if you are guessing, say false.

Answer with JSON only: {{"choice": "A" or "B", "confident": true or false, "note": "short reason"}}"""

TEXT_SCHEMA = {"type": "object", "properties": {
    "choice": {"type": "string", "enum": ["A", "B"]}, "confident": {"type": "boolean"}, "note": {"type": "string"}},
    "required": ["choice", "confident", "note"], "additionalProperties": False}

SCHEMA = {"type": "object", "properties": {
    "printed": {"type": "string"}, "confident": {"type": "boolean"}, "note": {"type": "string"}},
    "required": ["printed", "confident", "note"], "additionalProperties": False}


def strip(page: str, line: int, n_lines: int) -> Image.Image:
    gray = Image.open(DATA / "raw" / f"{page}.jpg").convert("L")
    x0, y0, x1, y1 = ocr.text_box(gray)
    lh = (y1 - y0) / max(n_lines, 1)
    y = y0 + lh * (line + 0.5)
    return gray.crop((x0, max(int(y - 2.6 * lh), 0), x1, min(int(y + 2.6 * lh), gray.height)))


def ask(img: Image.Image | None, prompt: str, schema: dict = SCHEMA) -> tuple[dict, float]:
    content = [{"type": "text", "text": prompt}]
    if img is not None:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=92)
        content.insert(0, {"type": "image_url", "image_url": {
            "url": "data:image/jpeg;base64," + base64.standard_b64encode(buf.getvalue()).decode()}})
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                      headers={"Authorization": "Bearer " + KEY_FILE.read_text(encoding="utf-8").strip()},
                      json={"model": MODEL, "max_tokens": 4000, "messages": [{"role": "user", "content": content}],
                            "response_format": {"type": "json_schema",
                                                "json_schema": {"name": "word", "strict": True, "schema": schema}},
                            "reasoning": {"effort": EFFORT}, "usage": {"include": True}}, timeout=300)
    d = r.json()
    if not r.ok or "error" in d:
        raise RuntimeError(f"HTTP {r.status_code}: {d.get('error', d)}")
    text = d["choices"][0]["message"]["content"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text), d.get("usage", {}).get("cost", 0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("first", type=int)
    p.add_argument("last", type=int)
    p.add_argument("--main", default="or-claude-opus-5.5@low+ital")
    p.add_argument("--mode", default="text", choices=["text", "image"],
                   help="text: choose A or B from the sentence (default); image: read a crop of the scan")
    # parallel workers: each writes its own file ({range}.{mode}{suffix}.json) and skips what any
    # worker of the same mode has decided (all files re-read before each flag)
    p.add_argument("--reverse", action="store_true", help="work from the last flag back")
    p.add_argument("--start", type=int, default=0, help="begin at this flag index")
    p.add_argument("--suffix", default="", help="output file suffix for an extra worker, e.g. 2")
    p.add_argument("--only-ties", action="store_true",
                   help="image mode: skip flags where the text judge agrees with Flash (2 of 3 already)")
    a = p.parse_args()
    rows = list(csv.DictReader((ROOT / "logs" / f"hebcheck_{a.first}-{a.last}.csv").open(encoding="utf-8-sig")))
    base = f"{a.first}-{a.last}{'' if a.mode == 'text' else '.image'}"
    out = DATA / "hebfix" / f"{base}{a.suffix}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"main": a.main, "model": MODEL, "items": []}

    def seen_now() -> set:
        s = set()
        for f in (DATA / "hebfix").glob(f"{base}*.json"):
            if f.name.endswith(".decisions.json") or (a.mode == "text" and ".image" in f.name):
                continue
            s |= {(d["page"], d["line"], d["main"]) for d in json.loads(f.read_text(encoding="utf-8"))["items"]}
        return s

    todo = [r for r in rows if r["kind"] in ("replace", "insert", "delete") and r["main"]][a.start:]
    if a.only_ties:
        text_file = DATA / "hebfix" / f"{a.first}-{a.last}.json"
        text = {(d["page"], d["line"], d["main"]): d["printed"]
                for d in json.loads(text_file.read_text(encoding="utf-8"))["items"]}
        todo = [r for r in todo if text.get((int(r["page"]), r["line"], r["main"])) != r["check"]]
        print(f"{len(todo)} flags where the text judge does not agree with Flash", flush=True)
    if a.reverse:
        todo.reverse()
    total = 0.0
    for i, r in enumerate(todo, 1):
        if (int(r["page"]), r["line"], r["main"]) in seen_now():
            continue
        k = hebcheck.key(int(r["page"]))
        _, lines = hebcheck.words(a.main, k)
        idx = next((j for j, l in enumerate(lines) if l.strip() == r["line"]), None)
        if idx is None:
            print(f"[{i}/{len(todo)}] p. {r['page']}: line not found, skipped", flush=True)
            continue
        try:
            if a.mode == "image":
                ans, cost = ask(strip(k, idx, len(lines)), PROMPT.format(
                    line=r["line"], a=r["main"], b=r["check"] or "(nothing)"))
            else:
                if not r["check"]:
                    continue  # nothing to choose between
                ctx = "\n".join((">> " if j == idx else "   ") + lines[j]
                                for j in range(max(idx - 4, 0), min(idx + 5, len(lines))))
                ans, cost = ask(None, TEXT_PROMPT.format(context=ctx, a=r["main"], b=r["check"]), TEXT_SCHEMA)
                ans["printed"] = r["main"] if ans.pop("choice") == "A" else r["check"]
        except Exception as e:
            print(f"[{i}/{len(todo)}] p. {r['page']} {r['main']}: FAILED {type(e).__name__}: {e}", flush=True)
            continue
        total += cost
        item = {"page": int(r["page"]), "line": r["line"], "main": r["main"], "check": r["check"], **ans}
        done["items"].append(item)
        out.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        verdict = "= main" if ans["printed"] == r["main"] else "= check" if ans["printed"] == r["check"] else "other"
        print(f"[{i}/{len(todo)}] p. {r['page']}: {r['main']} | {r['check']} -> {ans['printed']} "
              f"({verdict}{'' if ans['confident'] else ', not sure'}) ${cost:.4f}", flush=True)
        time.sleep(0.5)
    print(f"{len(todo)} decided this run, cost ${total:.4f}; wrote {out}")


if __name__ == "__main__":
    main()
