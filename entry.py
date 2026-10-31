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
import difflib
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import abbrev as A
import translate as T

sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(__file__).parent / "data"
SOURCE = "or-claude-opus-5.5@low+ital"  # default OCR; an entry may set "source" (Sonnet from part 2 on)
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
    # first part, Allgemeine Zoologie: pp. 1-63 (p. 1 unnumbered = scan 15). All 62 page joins
    # checked by eye (logs/qa_1-63.csv): p. 3 ends "ברייתי***)" and p. 43 ends "(עצבים)" mid-sentence.
    "part1": {"pages": ["scan0015", *range(2, 64)], "title": "First part: General zoology (pp. 1–63)",
              "start": r"", "end": r"^Zweite\s+Abtheilung", "continue": [4, 44]},
    # second part, first class, Säugethiere: pp. 64-158; OCR by Sonnet 5.5 with the Flash check of
    # the Hebrew (decided 31-Oct-2026). All 94 page joins checked by eye (logs/qa_64-158.csv); these
    # run on although the page ends with ")", ";", ":" or "!" (a verse quotation on pp. 80-81).
    "mammals": {"pages": list(range(64, 159)), "title": "Second part, first class: Mammals (pp. 64–158)",
                "start": r"^Zweite\s+Abtheilung", "end": r"^Zweite\s+Klasse",
                "source": "or-claude-sonnet-5.5@low+ital", "continue": [76, 81, 85, 101, 129]},
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
FIXES = {  # by OCR source: the engines make different errors
    "or-claude-opus-5.5@low+ital": {
        69: [("heißt נער (Chulin 53, a)", "heißt עוא (Chulin 53, a)")],  # print: ע, full-height ו, א
        71: [("neben טגרים auch", "neben טגריס auch")],  # final letter is ס, as on gold p. 70
    },
    "or-claude-sonnet-5.5@low+ital": {
        69: [("heißt נהם (Chulin 53, a)", "heißt עוא (Chulin 53, a)")],
        71: [("neben טגרים auch", "neben טגריס auch")],
    },
}
# Systematic word errors of one OCR engine, corrected on every page of that source. Sonnet reads
# the Fraktur x of "Buxdorf" (Lewysohn's spelling of Buxtorf) as r; checked on p. 76 and against Flash.
WORD_FIXES = {
    "or-claude-sonnet-5.5@low+ital": [(r"\bBurdorf\b", "Buxdorf"), (r"\bBurtorf\b", "Buxtorf")],
}
# OCR block-type errors: {page: [(start of the block's text, correct type)]}, checked on the scan.
TYPE_FIXES = {
    16: [("die ihm hingeworfenen Speisen", "body"), ("Die von Raschi (Chulin 59, a)", "body")],
}
# Printer's errors in footnote marks: {page: {mark of the note as printed: mark in the text}}.
NOTE_MARK_FIXES = {
    52: {"*)": "**)"},  # text "darf**)", note printed "*) Aus diesem Grunde ..." (checked on the scan)
}
# Lewysohn separates the topics inside a paragraph with a long dash; in the joined text each
# topic becomes its own paragraph (the dash is dropped). Not before a digit: "S. 63 — 76" is a range.
DASH = re.compile(r"\s+—\s+(?=\D)")


def hebfix_decisions() -> dict[str, list[dict]]:
    """Hebrew corrections decided by vote (hebvote.py), by page key; p. 1 is scan0015."""
    out: dict[str, list[dict]] = {}
    for f in sorted((DATA / "hebfix").glob("*.decisions.json")):
        for d in json.loads(f.read_text(encoding="utf-8"))["items"]:
            out.setdefault("scan0015" if d["page"] == 1 else str(d["page"]), []).append(d)
    return out


HEBFIX = hebfix_decisions() if (DATA / "hebfix").exists() else {}


def apply_hebfix(page, blocks: list[dict]) -> None:
    """Replace each voted word, as a whole word, everywhere on its page.

    The OCR errors are systematic (final ם for ס, ו for ז), so a word misread once is usually
    misread at its other uses on the page too; the comparison may flag only one of them.
    """
    for d in HEBFIX.get(str(page), []):
        old, new = d["old"].split(), d["new"].split()
        if len(old) != len(new):
            print(f"HEBFIX p. {page}: word count differs, not applied: {d['old']} -> {d['new']}")
            continue
        for o, n in zip(old, new):
            if o == n:
                continue
            rx = re.compile(rf"(?<![א-ת]){re.escape(o)}(?![א-ת])")
            for b in blocks:
                b["text"] = rx.sub(n, b["text"])


def page_blocks(page, source: str = SOURCE) -> list[dict]:
    ocr = json.loads((DATA / "ocr" / source / f"{page}.json").read_text(encoding="utf-8"))
    gold = DATA / "gold" / f"{page}.txt"
    if gold.exists():
        return T.gold_page(gold, ocr)["blocks"]
    apply_hebfix(page, ocr["blocks"])
    for rx, new in WORD_FIXES.get(source, []):
        for blk in ocr["blocks"]:
            blk["text"] = re.sub(rx, new, blk["text"])
    for old, new in FIXES.get(source, {}).get(page, []):
        hits = [b for b in ocr["blocks"] if old in b["text"]]
        if not hits and any(new in b["text"] for b in ocr["blocks"]):
            continue  # the voted Hebrew corrections (HEBFIX) made it already
        if len(hits) != 1:
            sys.exit(f"p. {page}: correction {old!r} found {len(hits)} times, not once")
        hits[0]["text"] = hits[0]["text"].replace(old, new)
    for start, typ in TYPE_FIXES.get(page, []):
        hits = [b for b in ocr["blocks"] if b["text"].startswith(start)]
        if len(hits) != 1:
            sys.exit(f"p. {page}: type correction {start!r} found {len(hits)} times, not once")
        hits[0]["type"], hits[0]["marker"] = typ, ""
    for b in ocr["blocks"]:
        if b["type"] == "footnote" and b.get("marker") in NOTE_MARK_FIXES.get(page, {}):
            b["marker"] = NOTE_MARK_FIXES[page][b["marker"]]
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
        for b in page_blocks(page, cfg.get("source", SOURCE)):
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
                    # a footnote mark on the joined word belongs to the new page: put the page mark
                    # before it ("stal-|lend*)" -> "stallend [p. 137]*)"), so the note is found
                    m = re.match(r"(.*?)((?:\*{1,3}|†{1,2})\).*)$", word)
                    if m:
                        prev["text"] = f"{head}{m.group(1)} [p. {page}]{m.group(2)} {rest}"
                    else:
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


HEB_WORD = re.compile(r"[א-ת][֑-ׇא-ת'\"]*")


def sync_hebrew(de_blocks: list[dict], en_blocks: list[dict]) -> int:
    """Copy Hebrew words corrected by the vote (HEBFIX) from the German into the English.

    Hebrew is not translated, so each English paragraph has the Hebrew words of its German
    paragraph, in the same order. The two word lists are aligned; where the German has a voted
    new word and the English still has another word in that place, the English word is replaced.
    This lets a translation made before the vote take the corrections without a model call.
    """
    new_words = {w for ds in HEBFIX.values() for d in ds for w in d["new"].split()}
    if not new_words:
        return 0
    changed = 0
    for de, en in zip(de_blocks, en_blocks):
        dw = [m.group(0) for m in HEB_WORD.finditer(de["text"])]
        em = list(HEB_WORD.finditer(en["text"]))
        ew = [m.group(0) for m in em]
        repl = {}
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, dw, ew, autojunk=False).get_opcodes():
            if op == "replace" and i2 - i1 == j2 - j1:
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    if dw[i] in new_words and dw[i] != ew[j]:
                        repl[j] = dw[i]
        if repl:
            text, shift = en["text"], 0
            for j in sorted(repl):
                m = em[j]
                text = text[:m.start() + shift] + repl[j] + text[m.end() + shift:]
                shift += len(repl[j]) - len(m.group(0))
            en["text"] = text
            changed += len(repl)
    return changed


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
            # each chunk is saved as soon as it is translated, keyed by its source text and the
            # rules, so a run that stops (network error, credit limit) resumes where it stopped
            src_key = hashlib.sha1(json.dumps([T.RULES_VERSION, a.model, a.effort, ch], ensure_ascii=False)
                                   .encode("utf-8")).hexdigest()[:16]
            cache = out / "chunks" / f"{kind}-{i:03d}-{src_key}.json"
            if cache.exists():
                res = json.loads(cache.read_text(encoding="utf-8"))
                print(f"{kind} chunk {i}: done already", flush=True)
            else:
                for attempt in range(3):
                    try:
                        res = T.translate({"blocks": ch, "meta": {"entry": a.entry, "part": kind}}, a.model,
                                          a.effort, keys,
                                          extra=cfg.get("extra", T.CONTENTS if cfg.get("contents") else ""))
                        break
                    except Exception as e:  # network resets happen; the credit limit does not go away
                        print(f"{kind} chunk {i}: attempt {attempt + 1} FAILED {type(e).__name__}: {e}", flush=True)
                        if attempt == 2 or "credit" in str(e).lower() or "402" in str(e):
                            sys.exit(f"stopped at {kind} chunk {i}; the chunks done so far are saved, run again to resume")
                        time.sleep(20 * (attempt + 1))
                cache.parent.mkdir(exist_ok=True)
                cache.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
                cost += res["meta"]["cost_usd"]
                print(f"{kind} chunk {i}: {len(ch)} blocks, {res['meta']['seconds']} s, "
                      f"${res['meta']['cost_usd']:.4f}", flush=True)
            for src, b in zip(ch, res["blocks"]):
                target.append({**b, "page": src["page"]})
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
        if b["type"] == "heading":  # "Abtheilung" is "Part" everywhere (as in the contents)
            b["text"] = re.sub(r"\b(First|Second|Third) Division\b", r"\1 Part", b["text"])
    # v4 -> v5 differs only by this fixed step, so a v4 translation finished here is v5
    if raw["meta"].get("rules") == "v4":
        raw["meta"]["rules"] = "v5"
    de = json.loads((out / "de.json").read_text(encoding="utf-8"))
    n = restore_page_marks(de["main"], en_main) + restore_page_marks(de["notes"], en_notes)
    if n:
        print(f"page marks restored in {n} block(s)")
    # where the German has a page mark directly before a footnote mark ("stallend [p. 137]*)", see
    # build()), put the English pair in the same order, so the note is linked to the right page
    for d, e in zip(de["main"], en_main):
        for pg, mark in re.findall(r"\[p\. ([^\]\s]+)\](\*{1,3}|†{1,2})\)", d["text"]):
            e["text"] = re.sub(rf"{re.escape(mark)}\)\s*\[p\. {re.escape(pg)}\]", f"[p. {pg}]{mark})", e["text"])
    n = sync_hebrew(de["main"], en_main) + sync_hebrew(de["notes"], en_notes)
    if n:
        print(f"{n} Hebrew word(s) corrected in the English from the voted German")
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
