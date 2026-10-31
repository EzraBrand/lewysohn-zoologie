"""Abbreviations: a reviewed table and a fixed expansion step after translation (no model).

  uv run abbrev.py                 # check all entries, render ABBREVIATIONS.md

abbreviations.json is maintained by hand (see its "note"). Rows with mode "expand" stay as printed
in the translation (the prompt says so) and expand() adds " [=expansion]" after the first use in a
document. Rows with mode "translate" are general German abbreviations the model renders in English.
check() counts each "expand" row in the German and in the English of an entry, so that a model
that translates or drops one (e.g. "Thierg." as "History of Animals") is caught.
Lewysohn's book has no list of abbreviations; the table is built from usage.
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
TABLE = ROOT / "abbreviations.json"
OUT_MD = ROOT / "ABBREVIATIONS.md"
KINDS = {"source": "Primary sources (Talmud, Midrash, Bible, classical works)",
         "bibliography": "Bibliography (authors and works cited by name)",
         "general": "General abbreviations"}


def items() -> list[dict]:
    return json.loads(TABLE.read_text(encoding="utf-8"))["items"] if TABLE.exists() else []


def pattern(abbr: str) -> str:
    """The abbreviation as a whole token: not inside a longer word."""
    return rf"(?<![\w.]){re.escape(abbr)}(?!\w)"


def joined(text: str) -> str:
    """German text with printed line breaks undone ("Ro-\\nsenmüller" -> "Rosenmüller")."""
    return re.sub(r"-\n(?=\w)", "", text).replace("\n", " ")


def found(text: str, rows: list[dict]) -> list[dict]:
    text = joined(text)
    return [r for r in rows if re.search(pattern(r["abbr"]), text)]


def prompt_rows(text: str) -> str:
    """The two lists for the translation prompt, limited to what occurs in the input."""
    rows = found(text, items())
    keep = ", ".join(f'"{r["abbr"]}"' for r in rows if r["mode"] == "expand") or "(none)"
    tr = ", ".join(f'"{r["abbr"]}" -> "{r["english"]}"' for r in rows if r["mode"] == "translate") or "(none)"
    return f"Keep as printed: {keep}\nTranslate: {tr}"


def expand(docs: list[list[dict]]) -> dict[str, int]:
    """Add " [=expansion]" after the first use of each "expand" row, in reading order, in place.

    docs: lists of blocks ({"text": ...}) that form one document (main text, then notes).
    -> {abbr: number of uses}. Longest abbreviation first, so "Midr. Jalk. Schim." is two hits.
    """
    rows = sorted((r for r in items() if r["mode"] == "expand"), key=lambda r: -len(r["abbr"]))
    if not rows:
        return {}
    by_abbr = {r["abbr"]: r for r in rows}
    rx = re.compile("|".join(f"({pattern(r['abbr'])})" for r in rows))
    uses: dict[str, int] = {}
    for blocks in docs:
        for b in blocks:
            def sub(m):
                a = m.group(0)
                uses[a] = uses.get(a, 0) + 1
                return f"{a} [={by_abbr[a]['expansion']}]" if uses[a] == 1 else a
            b["text"] = rx.sub(sub, b["text"])
    return uses


def check(de_text: str, en_text: str) -> list[str]:
    """-> problems: "expand" rows whose count differs between German and English."""
    out = []
    en_text = re.sub(r" \[=[^\]]*\]", "", en_text)
    for r in items():
        if r["mode"] != "expand":
            continue
        n_de = len(re.findall(pattern(r["abbr"]), joined(de_text)))
        n_en = len(re.findall(pattern(r["abbr"]), en_text))
        if n_de != n_en:
            out.append(f"{r['abbr']}: {n_de} in the German, {n_en} in the English")
    return out


def entry_texts(path: Path) -> tuple[str, str, dict[str, list]]:
    de = json.loads((path / "de.json").read_text(encoding="utf-8"))
    en = json.loads((path / "en.json").read_text(encoding="utf-8")) if (path / "en.json").exists() else None
    pages: dict[str, list] = {}
    for b in de["main"] + de["notes"]:
        for r in found(b["text"], items()):
            pages.setdefault(r["abbr"], [])
            if b["page"] not in pages[r["abbr"]]:
                pages[r["abbr"]].append(b["page"])
    de_text = "\n".join(b["text"] for b in de["main"] + de["notes"])
    en_text = "\n".join(b["text"] for b in en["main"] + en["notes"]) if en else ""
    return de_text, en_text, pages


def render(pages: dict[str, list]) -> str:
    lines = ["# Abbreviations and short references", "",
             "Generated file: edit `abbreviations.json` and run `uv run abbrev.py`. Lewysohn's book has "
             "no list of abbreviations; this table is built from the abbreviations as they occur, and "
             "reviewed by hand. **expand**: kept as printed in the English, with the expansion added "
             "after the first use (a fixed step, not the model). **translate**: a general German "
             "abbreviation, rendered in English by the translation. Basis: **Vorrede** = from Lewysohn's "
             "preface; **standard**; **general knowledge**; **guess** = not certain, check.", ""]
    for kind, title in KINDS.items():
        rows = sorted((r for r in items() if r["kind"] == kind), key=lambda r: r["abbr"].casefold())
        if not rows:
            continue
        lines += [f"## {title}", "", "| Abbreviation | Expansion | Mode | Basis | Pages |", "|---|---|---|---|---|"]
        for r in rows:
            exp = r["expansion"] + (f" → *{r['english']}*" if r["mode"] == "translate" else "")
            cells = [r["abbr"], exp, r["mode"], r["basis"], ", ".join(str(p) for p in pages.get(r["abbr"], []))]
            lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
        lines.append("")
    return "\n".join(lines)


def main():
    pages: dict[str, list] = {}
    for path in sorted((ROOT / "data" / "entries").iterdir()):
        de_text, en_text, p = entry_texts(path)
        for k, v in p.items():
            pages.setdefault(k, []).extend(x for x in v if x not in pages[k])
        if en_text:
            problems = check(de_text, en_text)
            print(f"{path.name}: " + ("; ".join(problems) if problems else "every 'expand' abbreviation kept"))
    OUT_MD.write_text(render(pages), encoding="utf-8")
    print(f"wrote {OUT_MD.name}")


if __name__ == "__main__":
    main()
