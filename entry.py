"""Join the pages of one entry into continuous text and translate it as a whole.

  uv run entry.py toc                      # build data/entries/toc/ (German + English)
  uv run entry.py toc --no-translate       # only the joined German text
  uv run entry.py lion-tiger --expand-only # redo the abbreviation step, no model call

Per page the source is the gold text if it exists, else the OCR (translate.py's default).
Running heads and page numbers are dropped. A paragraph that runs over a page break is joined,
and "[p. N]" marks where page N begins. Footnotes stay grouped by page and are listed after the
text. The text is translated in chunks of whole paragraphs with translate.translate().
"""

import argparse
import json
import re
import sys
from pathlib import Path

import abbrev as A
import translate as T

sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(__file__).parent / "data"
SOURCE = "or-claude-opus-5.5@low+ital"
CHUNK_CHARS = 6000

# start / end: regexes for the first block of the entry and the first block after it
ENTRIES = {
    # front matter, in book order. "contents" keeps the printed lines (no joins, no dash split);
    # "extra" replaces the contents rule in the prompt.
    "front": {"pages": ["scan0001", "scan0003", "scan0005", "scan0006"], "start": r"", "end": r"(?!)",
              "title": "Half-title, title page, dedication, motto", "contents": True, "extra": T.FRONT},
    # Vorrede, pp. VII-XII (p. VII unnumbered = scan 7). Page joins checked by eye: all five run on
    # mid-sentence; VII|VIII breaks "Auto-|da-fé's" at a real hyphen.
    "preface": {"pages": ["scan0007", "VIII", "IX", "X", "XI", "XII"], "title": "Preface (pp. VII–XII)",
                "start": r"", "end": r"(?!)", "keep_hyphen": ["VIII"]},
    # table of contents ("Inhalt"): one unnumbered page (scan 13).
    "toc": {"pages": ["scan0013"], "title": "Contents", "start": r"", "end": r"(?!)", "contents": True},
    # §§ 114-115: starts mid-p. 68, ends mid-p. 71. Page joins checked by eye: 68|69, 69|70 and
    # 70|71 all run on mid-sentence ("in der | Gestalt", "eine | Beute", "unrichtige | Kenntniß").
    "lion-tiger": {"pages": [68, 69, 70, 71], "title": "§§ 114–115: The lion, the tiger (pp. 68–71)",
                   "start": r"^§\.\s*114\b", "end": r"^§\.\s*116\b"},
}
# A paragraph continues on the next page if the page ends without sentence-final punctuation;
# "continue" / "break" in an entry override this for the pages listed (the first page of the pair).
SENTENCE_END = re.compile(r"[.!?:;)\]]\s*$")
# Corrections to the OCR of pages that have no gold text: (old, new), with enough context to be
# unique. Checked against the scan by Claude, 31-Oct-2026 (not by hand like a gold page).
FIXES = {
    69: [("heißt נער (Chulin 53, a)", "heißt עוא (Chulin 53, a)")],  # print: ע, full-height ו, א
    71: [("neben טגרים auch", "neben טגריס auch")],  # final letter is ס, as on gold p. 70
}
# Lewysohn separates the topics inside a paragraph with a long dash; in the joined text each
# topic becomes its own paragraph (the dash is dropped). Not before a digit: "S. 63 — 76" is a range.
DASH = re.compile(r"\s+—\s+(?=\D)")


def page_blocks(page) -> list[dict]:
    ocr = json.loads((DATA / "ocr" / SOURCE / f"{page}.json").read_text(encoding="utf-8"))
    gold = DATA / "gold" / f"{page}.txt"
    if gold.exists():
        return T.gold_page(gold, ocr)["blocks"]
    for old, new in FIXES.get(page, []):
        hits = [b for b in ocr["blocks"] if old in b["text"]]
        if len(hits) != 1:
            sys.exit(f"p. {page}: correction {old!r} found {len(hits)} times, not once")
        hits[0]["text"] = hits[0]["text"].replace(old, new)
    return ocr["blocks"]


def split_dashes(main: list[dict]) -> list[dict]:
    """Body paragraphs -> one paragraph per dash-separated topic; "page" = page where it starts."""
    out = []
    for b in main:
        if b["type"] != "body":
            out.append(b)
            continue
        page = b["page"]
        for part in DASH.split(b["text"]):
            out.append({**b, "text": part, "page": page})
            marks = T_PAGE_MARK.findall(part)
            if marks:
                page = int(marks[-1]) if marks[-1].isdigit() else marks[-1]
    return out


T_PAGE_MARK = re.compile(r"\[p\. ([^\]\s]+)\]")


def build(cfg: dict) -> tuple[list[dict], list[dict]]:
    """-> (main blocks, footnote blocks); each block has a "page".

    A footnote is kept when its mark occurs in the entry's own text on that page, so that an entry
    that starts or ends mid-page gets its notes and not those of the § before or after it.
    """
    main, notes, started, ended = [], [], False, False
    page_text: dict = {}  # page -> the entry's main text on that page
    for page in cfg["pages"]:
        first_on_page = True
        for b in page_blocks(page):
            text = b["text"].strip()
            if b["type"] == "furniture":
                continue
            if b["type"] == "footnote":
                notes.append({"type": "footnote", "marker": b.get("marker", ""), "text": text, "page": page})
                continue
            if not started:
                if not re.search(cfg["start"], text):
                    continue
                started = True
            elif re.search(cfg["end"], text):
                ended = True
            if ended:
                continue
            page_text[page] = page_text.get(page, "") + "\n" + text
            prev = main[-1] if main else None
            continues = (page in cfg.get("continue", []) or not SENTENCE_END.search(prev["text"] if prev else "")) \
                and page not in cfg.get("break", [])
            if first_on_page and prev and prev["type"] == "body" and b["type"] == "body" and continues \
                    and not cfg.get("contents"):  # a contents list is never joined across pages
                if prev["text"].endswith("-"):  # word broken over the page: marker after the word
                    word, _, rest = text.partition(" ")
                    # "keep_hyphen": pages whose first word follows a real hyphen ("Auto-|da-fé's")
                    head = prev["text"] if page in cfg.get("keep_hyphen", []) else prev["text"][:-1]
                    prev["text"] = f"{head}{word} [p. {page}] {rest}"
                else:
                    prev["text"] += f" [p. {page}] {text}"
            else:
                marker = f"[p. {page}] " if first_on_page and main else ""
                main.append({"type": b["type"], "marker": "", "text": marker + text, "page": page})
            first_on_page = False
        if ended:
            break
    if not started:
        sys.exit(f"start pattern {cfg['start']!r} not found")
    # A footnote at the top of a page whose mark is not in that page's text (or that has no mark)
    # continues the last note of the page before: e.g. the numbered list in note ***) of p. IX runs
    # over pp. X-XI, and the OCR gives each item ("4)", "5)") its own block. After the first note
    # whose mark is in the text, a note with an unknown mark belongs to the § before or after.
    kept, page_seen = [], {}
    for n in notes:
        in_text = n["marker"] and n["page"] in page_text and re.search(
            rf"(?<![*†]){re.escape(n['marker'])}", page_text[n["page"]])
        if in_text:
            page_seen[n["page"]] = True
            kept.append(n)
        elif not page_seen.get(n["page"]) and kept and kept[-1]["page"] != n["page"] or \
                not page_seen.get(n["page"]) and kept and kept[-1].get("continued_on") == n["page"]:
            prev = kept[-1]
            prev["text"] += "\n" + (f"{n['marker']} " if n["marker"] else "") + n["text"]
            prev["continued_on"] = n["page"]
            print(f"note on p. {n['page']} ({n['marker'] or 'no mark'}) joined to {prev['marker']} of p. {prev['page']}")
    return main, kept


def chunks(blocks: list[dict]) -> list[list[dict]]:
    out, cur = [], []
    for b in blocks:
        if cur and sum(len(x["text"]) for x in cur) + len(b["text"]) > CHUNK_CHARS:
            out.append(cur)
            cur = []
        cur.append(b)
    return out + [cur] if cur else out


def render(title: str, main: list[dict], notes: list[dict], lines: bool = False) -> str:
    """lines: a contents list; keep each printed line as a Markdown line break."""
    out = [f"# {title}", ""]
    for b in main:
        text = T.LRM + T.md_inline(b["text"])  # LRM: see translate.LRM
        if lines:
            text = re.sub(r"(?:\s*\.){3,}\s*", " … ", text).replace("\n", f"  \n{T.LRM}")
        elif b["type"] == "heading":  # "§. 115.\nDer Tiger." is one Markdown heading line
            text = text.replace("\n", " ")
        out += [f"### {text}" if b["type"] == "heading" else text, ""]
    if notes:
        out += ["---", "", "**Notes**", ""]
        for page in dict.fromkeys(n["page"] for n in notes):  # book order, not sorted as text
            label = f"unnumbered page (scan {int(page[4:])})" if str(page).startswith("scan") else f"p. {page}"
            out += [f"*{label}*", ""]
            for n in notes:
                if n["page"] != page:
                    continue
                text = f"{n['marker']} {T.md_inline(n['text'])}".strip()
                # a list in a note ("\n4) ...", joined over pages) keeps its line breaks
                text = re.sub(r"\n(?=\d+\) )", "\0", re.sub(r"-\n(?=\w)", "", text))
                out += [T.LRM + text.replace("\n", " ").replace("\0", f"  \n{T.LRM}") + "  "]
            out.append("")
    return "\n".join(out)


PAGE_MARK = re.compile(r"\[p\. [^\]\s]+\]")


def restore_page_marks(de_blocks: list[dict], en_blocks: list[dict]) -> int:
    """Copy the page marks from the German into the English, block by block and in order: the
    model may change them (the Roman-numeral rule turned "[p. VIII]" into "[p. 8]"). -> blocks fixed."""
    fixed = 0
    for de, en in zip(de_blocks, en_blocks):
        marks = PAGE_MARK.findall(de["text"])
        if len(PAGE_MARK.findall(en["text"])) != len(marks):
            print(f"PAGE MARKS: {len(marks)} in the German, a different number in the English: {en['text'][:60]!r}")
            continue
        it = iter(marks)
        new = PAGE_MARK.sub(lambda m: next(it), en["text"])
        fixed += new != en["text"]
        en["text"] = new
    return fixed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entry", choices=ENTRIES)
    p.add_argument("--model", default="anthropic/claude-opus-5.5")
    p.add_argument("--effort", default="medium")
    p.add_argument("--no-translate", action="store_true")
    p.add_argument("--expand-only", action="store_true",
                   help="no model call: redo the abbreviation step from en.raw.json")
    a = p.parse_args()
    cfg = ENTRIES[a.entry]
    out = DATA / "entries" / a.entry
    out.mkdir(parents=True, exist_ok=True)
    if a.expand_only:
        finish(cfg, out)
        return

    main_blocks, notes = build(cfg)
    if not cfg.get("contents"):
        main_blocks = split_dashes(main_blocks)
    (out / "de.json").write_text(json.dumps({"main": main_blocks, "notes": notes}, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
    (out / "de.md").write_text(render(cfg["title"], main_blocks, notes, cfg.get("contents", False)), encoding="utf-8")
    print(f"{len(main_blocks)} paragraphs, {len(notes)} footnotes, "
          f"{sum(len(b['text']) for b in main_blocks)} characters of main text")
    if a.no_translate:
        return

    keys = [str(pg) for pg in cfg["pages"]]
    en_main, en_notes, cost = [], [], 0.0
    for kind, blocks, target in (("text", main_blocks, en_main), ("notes", notes, en_notes)):
        for i, ch in enumerate(chunks(blocks), 1):
            res = T.translate({"blocks": ch, "meta": {"entry": a.entry, "part": kind}}, a.model, a.effort, keys,
                              extra=cfg.get("extra", T.CONTENTS if cfg.get("contents") else ""))
            for src, b in zip(ch, res["blocks"]):
                target.append({**b, "page": src["page"]})
            cost += res["meta"]["cost_usd"]
            print(f"{kind} chunk {i}: {len(ch)} blocks, {res['meta']['seconds']} s, "
                  f"${res['meta']['cost_usd']:.4f}", flush=True)
    meta = {"model": a.model, "effort": a.effort, "rules": T.RULES_VERSION, "cost_usd": round(cost, 4)}
    # the model's output, before the abbreviation step: --expand-only starts again from here
    (out / "en.raw.json").write_text(json.dumps({"main": en_main, "notes": en_notes, "meta": meta},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"translation cost ${cost:.4f}")
    finish(cfg, out)


def finish(cfg: dict, out: Path) -> None:
    """en.raw.json -> abbreviations expanded (abbrev.py) -> en.json and en.md."""
    raw = json.loads((out / "en.raw.json").read_text(encoding="utf-8"))
    en_main, en_notes = raw["main"], raw["notes"]
    for b in en_main + en_notes:  # also for outputs made before translate.modern_citations existed
        b["text"] = T.modern_citations(b["text"])
    # v4 -> v5 differs only by this fixed step, so a v4 translation finished here is v5
    if raw["meta"].get("rules") == "v4":
        raw["meta"]["rules"] = "v5"
    de = json.loads((out / "de.json").read_text(encoding="utf-8"))
    n = restore_page_marks(de["main"], en_main) + restore_page_marks(de["notes"], en_notes)
    if n:
        print(f"page marks restored in {n} block(s)")
    problems = A.check("\n".join(b["text"] for b in de["main"] + de["notes"]),
                       "\n".join(b["text"] for b in en_main + en_notes))
    for p in problems:
        print(f"ABBREVIATION CHECK: {p}")
    uses = A.expand([en_main, en_notes])
    raw["meta"]["abbreviations_expanded"] = sorted(uses)
    (out / "en.json").write_text(json.dumps({"main": en_main, "notes": en_notes, "meta": raw["meta"]},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "en.md").write_text(render(cfg["title"], en_main, en_notes, cfg.get("contents", False)),
                               encoding="utf-8")
    print(f"{len(uses)} abbreviations expanded, {len(problems)} check problem(s); wrote {out / 'en.md'}")


if __name__ == "__main__":
    main()
