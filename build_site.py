"""Build the reading edition in docs/ (served by GitHub Pages from main:/docs).

  uv run build_site.py

Pages: an index, one page per document (a whole entry or a single translated page) with German
and English side by side, and a searchable abbreviation table. Built only from files in data/;
no model calls. Scans are shown from Frankfurt's IIIF server.
"""

import html
import json
import re
import sys
from pathlib import Path

import fetch
import translate as T

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "docs"
REPO = "https://github.com/EzraBrand/lewysohn-zoologie"
OCR_SOURCE = "or-claude-opus-5.5@low+ital"
TRANSLATION = f"claude-opus-5.5@medium-{T.RULES_VERSION}"
IIIF = "https://sammlungen.ub.uni-frankfurt.de/i3f/v20"
VIEWER = "https://sammlungen.ub.uni-frankfurt.de/freimann/content/pageview"

DOCS = [
    {"slug": "lion-tiger", "kind": "entry", "entry": "lion-tiger", "pages": [68, 69, 70, 71],
     "title": "The lion, the tiger", "sub": "§§ 114–115 · pp. 68–71 · Hebrew, Aramaic, Greek, Arabic, footnotes"},
]
# table of contents: page keys as in data/raw (scanNNNN for an unnumbered page)
CONTENTS = [
    {"slug": "contents", "kind": "entry", "entry": "toc", "pages": ["scan0013"],
     "title": "Contents", "sub": "The printed Inhalt: parts and classes (one page)"},
]
for c in CONTENTS:
    c["contents"] = True

RTL_OR_GREEK = r"[֐-׿יִ-ﭏ؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿܀-ݏͰ-Ͽἀ-῿]"
_TAIL = r"[^\s\[\]<>()*†,;:.?!]*"  # a run ends before Latin punctuation and footnote marks
RUN = re.compile(rf"({RTL_OR_GREEK}{_TAIL}(?:\s+{RTL_OR_GREEK}{_TAIL})*)(\s\[(?!=)([^\]]+)\])?")
import abbrev  # noqa: E402  (the whole abbreviation, e.g. "B. Kama", gets the tooltip, not only "Kama")
_ABBRS = "|".join(re.escape(r["abbr"]) for r in sorted(abbrev.items(), key=lambda r: -len(r["abbr"])))
EXPANSION = re.compile(rf"((?<![\w.])(?:{_ABBRS})|[^\s(\[]\S*)\s\[=([^\]]*)\]")
PAGE_MARK = re.compile(r"\[p\. ([^\]\s]+)\]")
PARTICLES = {"el", "al", "ul", "il", "ad", "an", "as", "aš", "at", "ha", "ba", "bi", "li", "wa", "be", "le"}
NOTE_MARK = re.compile(r"(\*{1,3}|†{1,2}|<sup>\d{1,2}</sup>)\)")  # numbered notes are superscripts


def mark_key(mark: str) -> str:
    """'*)', '<sup>1</sup>)', '^{1})', '1)' -> '*', '1', '1', '1'."""
    return re.sub(r"<sup>|</sup>|\^\{|\}|\)|\s", "", mark)


def scan_ids() -> dict[str, str]:
    """page key (printed page, or scanNNNN for an unnumbered page) -> IIIF image id."""
    return {c["printed_page"] or f"scan{c['scan_index']:04d}": c["image_id"] for c in fetch.canvases()}


def page_label(key) -> str:
    key = str(key)
    return f"unnumbered (scan {int(key[4:])})" if key.startswith("scan") else f"p.&nbsp;{key}"


def script_class(run: str) -> str:
    c = ord(run[0])
    if 0x0370 <= c <= 0x03FF or 0x1F00 <= c <= 0x1FFF:
        return "grc"
    if 0x0700 <= c <= 0x074F:
        return "syc"
    if 0x0600 <= c <= 0x06FF or 0x0750 <= c <= 0x077F or c >= 0xFB50:
        return "ara"
    return "heb"


def inline(text: str, page: int, ctx: dict) -> str:
    """One paragraph of text -> HTML. ctx: ids (page -> image id), notes ((page, mark) -> n)."""
    s = html.escape(text, quote=False).replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    s = re.sub(r"\^\{(.+?)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"_\{(.+?)\}", r"<sub>\1</sub>", s)
    # printed line breaks: re-join words split at a line end ("Te-\nrebinthus"), but keep the
    # hyphen after Arabic/Hebrew particles in transliterations ("el-\nanbāṭ") and before capitals
    def hyphen(m):
        return m.group(0).replace("\n", "") if m.group(1).lower() in PARTICLES else m.group(1) + m.group(2)
    s = re.sub(r"(\w+)-\n([a-zäöüßāēīōūăĕŏḥṭṣḳ])", hyphen, s)
    if ctx.get("lines"):  # a contents list: one entry per line; leader dots -> " … "
        s = re.sub(r"(?:\s*\.){3,}\s*", " … ", s).replace("\n", "<br>")
    s = s.replace("-\n", "-").replace("\n", " ")

    def run(m):
        cls = script_class(m.group(1))
        direction = "ltr" if cls == "grc" else "rtl"
        out = f'<bdi class="{cls}" dir="{direction}">{m.group(1)}</bdi>'
        br = m.group(3)
        # a bracket is a transliteration only where the rules add one: Syriac -> Hebrew letters,
        # Arabic/Greek -> Latin. Any other bracket (e.g. the author's own "[בית]") stays text.
        is_tr = br and ((cls == "syc" and re.match(r"[א-ת]", br)) or
                        (cls in ("ara", "grc") and re.match(r"[A-Za-zʾʿĀ-ž(]", br)))
        if br and not is_tr:
            return out + " [" + RUN.sub(run, br) + "]"
        if br:
            tr = html.escape(m.group(3), quote=True)
            out = (f'<span class="nl" data-tr="{tr}" tabindex="0">{out}</span>'
                   f'<span class="tr"> [{m.group(3)}]</span>')
        return out
    s = RUN.sub(run, s)
    s = EXPANSION.sub(lambda m: f'<abbr title="{html.escape(m.group(2), quote=True)}">{m.group(1)}</abbr>'
                                f'<span class="exp"> [={m.group(2)}]</span>', s)

    # footnote marks and page marks, in reading order (a page mark changes the page for what follows)
    out, cur = [], str(page)
    for part in re.split(r"(\[p\. [^\]\s]+\])", s):
        m = PAGE_MARK.fullmatch(part)
        if m:
            cur = m.group(1)
            img = ctx["ids"].get(cur)
            href = f"{VIEWER}/{img}" if img else "#"
            out.append(f'<a class="pg" href="{href}" target="_blank" rel="noopener" '
                       f'title="Scan of this page">{page_label(cur)}</a>')
            continue
        def note(n):
            num = ctx["notes"].get((cur, mark_key(n.group(1))))
            if num is None:
                return n.group(0)
            return f'<a class="fn" href="#{ctx["lang"]}-n{num}" id="{ctx["lang"]}-r{num}">{num}</a>'
        out.append(NOTE_MARK.sub(note, part))
    return "".join(out)


def common_names(doc: dict) -> dict[int, list[dict]]:
    """English line number -> plant_names.json rows, for a contents list (else empty)."""
    table = ROOT / "plant_names.json"
    if not doc.get("contents") or not table.exists():
        return {}
    out = {}
    for r in json.loads(table.read_text(encoding="utf-8")).get(doc["entry"], []):
        out.setdefault(r["line"], []).append(r)
    return out


def common_name_html(r: dict) -> str:
    text = r["english"] + ("?" if not r["sure"] else "")
    if r["modern"]:
        text += f"; now {r['modern']}"
    return f'<span class="cn"> [={html.escape(text)}]</span>'


def paragraph_page(text: str, start: str) -> str:
    marks = PAGE_MARK.findall(text)
    return marks[-1] if marks else start


def load_doc(doc: dict) -> dict:
    """-> {"de": [blocks], "en": [blocks], "de_notes", "en_notes"}; every block has "page"."""
    if doc["kind"] == "entry":
        de = json.loads((DATA / "entries" / doc["entry"] / "de.json").read_text(encoding="utf-8"))
        en = json.loads((DATA / "entries" / doc["entry"] / "en.json").read_text(encoding="utf-8"))
        return {"de": de["main"], "en": en["main"], "de_notes": de["notes"], "en_notes": en["notes"],
                "rules": en["meta"].get("rules", "?")}
    raise ValueError(f"unknown document kind {doc['kind']!r}")


FONTS = ("https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,400;0,600;1,400"
         "&family=Noto+Serif+Hebrew&family=Noto+Sans+Syriac&family=Noto+Naskh+Arabic&display=swap")


def page_html(title: str, body: str, desc: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="style.css">
</head>
<body>
{body}
<script src="app.js"></script>
</body>
</html>
"""


def header(active: str) -> str:
    links = [("index.html", "Entries"), ("abbreviations.html", "Abbreviations"), (REPO, "Code and data")]
    nav = " ".join(f'<a href="{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in links)
    return (f'<header class="site"><a class="brand" href="index.html">Lewysohn, <i>Zoologie des Talmuds</i> '
            f'<span>· reading edition (test)</span></a><nav>{nav}</nav></header>')


CN_TOGGLE = '<label><input type="checkbox" data-toggle="show-cn" checked> Common names</label>'
TOGGLES = """<div class="toggles" role="group" aria-label="Display">
<label><input type="checkbox" data-toggle="show-de" checked> German</label>
<label><input type="checkbox" data-toggle="show-exp"> Abbreviations inline</label>
<label><input type="checkbox" data-toggle="show-tr"> Transliterations inline</label>
{cn}</div>"""


def doc_html(doc: dict) -> str:
    d = load_doc(doc)
    ids = scan_ids()
    # number the footnotes through the document; (page, mark) -> number
    keymap = {}
    for i, n in enumerate(d["de_notes"], 1):
        keymap[(str(n["page"]), mark_key(n.get("marker", "")))] = i
    rows = []
    pages = [str(p) for p in doc["pages"]]
    cur = {"de": pages[0], "en": pages[0]}
    lines = doc.get("contents", False)
    names = common_names(doc)
    en_line = 0  # line number in the English contents list, as in plant_names.json
    for de, en in zip(d["de"], d["en"]):
        cells = []
        for lang, b in (("de", de), ("en", en)):
            ctx = {"ids": ids, "notes": keymap, "lang": lang, "lines": lines}
            raw, spans = b["text"], {}
            if lang == "en" and names:
                out_lines = []
                for line in raw.split("\n"):
                    for r in names.get(en_line, []):
                        k = f"⟦cn{len(spans)}⟧"  # placeholder, replaced after inline()
                        line = line.replace(r["latin"], r["latin"] + k, 1)
                        spans[k] = common_name_html(r)
                    out_lines.append(line)
                    en_line += 1
                raw = "\n".join(out_lines)
            text = inline(raw, cur[lang], ctx)
            for k, v in spans.items():
                text = text.replace(k, v)
            cur[lang] = paragraph_page(b["text"], cur[lang])
            tag = "h3" if b["type"] == "heading" else "p"
            cells.append(f'<div class="cell {lang}" lang="{"de" if lang == "de" else "en"}"><{tag}>{text}</{tag}></div>')
        rows.append(f'<div class="row">{"".join(cells)}</div>')
    notes = []
    for i, (de, en) in enumerate(zip(d["de_notes"], d["en_notes"]), 1):
        cells = []
        for lang, b in (("de", de), ("en", en)):
            ctx = {"ids": ids, "notes": {}, "lang": lang}
            cells.append(f'<div class="cell {lang}" id="{lang}-n{i}"><p><a class="fnback" href="#{lang}-r{i}">{i}</a> '
                         f'<span class="pgref">{page_label(b["page"])}</span> {inline(b["text"], b["page"], ctx)}</p></div>')
        notes.append(f'<div class="row note">{"".join(cells)}</div>')
    thumbs = "".join(
        f'<a href="{VIEWER}/{ids[p]}" target="_blank" rel="noopener" title="Scan of this page">'
        f'<img loading="lazy" src="{IIIF}/{ids[p]}/full/160,/0/default.jpg" alt="Scan" width="160">'
        f'<span>{page_label(p)}</span></a>' for p in pages if p in ids)
    notes_html = f'<h2 id="notes">Notes</h2>\n{"".join(notes)}' if notes else ""
    body = f"""{header("")}
<main class="doc">
<h1>{html.escape(doc["title"])}</h1>
<p class="sub">{html.escape(doc["sub"])}</p>
<details class="about"><summary>How to read this page</summary>
<p>Left: Lewysohn's German text (printed in Fraktur) as transcribed by Claude Opus 5.5; pp. 68 and 70
are checked by hand, pp. 69 and 71 are not (two Hebrew words on them corrected against the scan).
The paragraphs are split where Lewysohn separates topics with a long dash. Right: an English
translation by Claude Opus 5.5 (rules {d["rules"]}). Hebrew-script words are not transliterated;
Arabic and Greek words show a transliteration when you point at them. Dotted words are
abbreviations: point at them for the expansion, from a table reviewed by hand
(<a href="abbreviations.html">table</a>), added by a program after translation. “p. 69” links to
the scan of that page. Numbers link to the footnotes below. Machine output: check the scan before
you cite.</p></details>
{TOGGLES.format(cn=CN_TOGGLE if names else "")}
<div class="scans" aria-label="Scans">{thumbs}</div>
<div class="cols-head row"><div class="cell de">German (Lewysohn)</div><div class="cell en">English</div></div>
{"".join(rows)}
{notes_html}
</main>
<footer>Source: <a href="https://nbn-resolving.org/urn:nbn:de:hebis:30:1-113735">Frankfurt UB, Freimann
collection</a>, Public Domain Mark 1.0 · Transcription, translation and code: <a href="{REPO}/blob/main/LICENSE">MIT License</a> · <a href="{REPO}">{REPO.split("//")[1]}</a></footer>"""
    return page_html(f"{doc['title']} · Lewysohn, Zoologie des Talmuds", body, doc["sub"])


def index_html() -> str:
    li = lambda ds: "".join(f'<li><a href="{d["slug"]}.html"><strong>{html.escape(d["title"])}</strong></a>'
                            f'<span>{html.escape(d["sub"])}</span></li>' for d in ds)
    items = li(DOCS) + "</ul><h2>Tables of contents</h2><ul class=\"docs\">" + li(CONTENTS)
    body = f"""{header("index.html")}
<main class="index">
<h1>Ludwig Lewysohn, <i>Die Zoologie des Talmuds</i></h1>
<p class="lede">Frankfurt am Main, 1858: the first systematic collection of the Talmudic and
Midrashic material on animals, in German (set in Fraktur) with Hebrew, Aramaic, Greek and Latin.
This is a test reading edition: machine transcription and English translation of a few pages,
made to see what current tools can do. The companion project for plants is
<a href="https://ezrabrand.github.io/low-flora/">Löw, <i>Die Flora der Juden</i></a>.</p>
<ul class="docs">{items}</ul>
<h2>What this is, and what it is not</h2>
<ul class="plain">
<li>The transcription and the translation are machine output (Claude Opus 5.5). Two pages
(pp. 68 and 70) were checked by hand.</li>
<li>The book has no list of abbreviations. They are expanded from a table built from the text and
reviewed by hand (<a href="abbreviations.html">table</a>); “guess” marks an expansion that is not
certain.</li>
<li>Each page links to the scan: please check it before citing anything.</li>
<li>Code, data, method and costs: <a href="{REPO}">{REPO.split("//")[1]}</a>.</li>
</ul>
</main>
<footer>Scans: Frankfurt UB, Freimann collection, Public Domain Mark 1.0. Transcription, translation and code: <a href="{REPO}/blob/main/LICENSE">MIT License</a>.</footer>"""
    return page_html("Lewysohn, Zoologie des Talmuds · reading edition", body,
                     "Machine transcription and English translation of pages of Ludwig Lewysohn, Die Zoologie des Talmuds (1858)")


def abbreviations_html() -> str:
    import abbrev
    pages: dict = {}
    for path in sorted((DATA / "entries").iterdir()):
        for k, v in abbrev.entry_texts(path)[2].items():
            pages.setdefault(k, []).extend(str(x) for x in v if str(x) not in pages.get(k, []))
    kinds = {"source": "Primary source", "bibliography": "Bibliography", "general": "General"}
    rows = "".join(
        f'<tr><td>{html.escape(r["abbr"])}</td><td>{html.escape(r["expansion"])}'
        + (f' → <i>{html.escape(r["english"])}</i>' if r["mode"] == "translate" else "")
        + f'</td><td>{kinds[r["kind"]]}</td><td>{html.escape(r["basis"])}</td>'
        f'<td>{", ".join(pages.get(r["abbr"], []))}</td></tr>'
        for r in sorted(abbrev.items(), key=lambda r: r["abbr"].casefold()))
    body = f"""{header("abbreviations.html")}
<main class="index">
<h1>Abbreviations and short references</h1>
<p class="lede">Lewysohn's book has no list of abbreviations. This table is built from the
abbreviations as they occur and reviewed by hand. Sources and bibliography stay as printed in the
English, and a program adds the expansion after the first use; general German abbreviations are
translated (→). Basis: <b>Vorrede</b> = from Lewysohn's preface; <b>standard</b>; <b>general
knowledge</b>; <b>guess</b> = not certain, check.</p>
<input id="filter" type="search" placeholder="Filter, e.g. Thierg. or Bochart" aria-label="Filter">
<table class="abbr"><thead><tr><th>Abbreviation</th><th>Expansion</th><th>Kind</th><th>Basis</th><th>Pages</th></tr></thead>
<tbody>{rows}</tbody></table>
</main>"""
    return page_html("Abbreviations · Lewysohn, Zoologie des Talmuds", body)


CSS = """:root{--bg:#fbfaf7;--fg:#22201c;--muted:#6b665d;--line:#e4e0d6;--accent:#7a4b12;--panel:#f2efe7;--mark:#efe3cf}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17161a;--fg:#e8e4dc;--muted:#a39d92;--line:#33313a;--accent:#e0a95c;--panel:#201f25;--mark:#3a3022}}
:root[data-theme="dark"]{--bg:#17161a;--fg:#e8e4dc;--muted:#a39d92;--line:#33313a;--accent:#e0a95c;--panel:#201f25;--mark:#3a3022}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 "Noto Serif",Georgia,serif}
a{color:var(--accent)}
header.site{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;align-items:baseline;justify-content:space-between;padding:.8rem 1rem;border-bottom:1px solid var(--line)}
header.site .brand{color:var(--fg);text-decoration:none;font-weight:600}
header.site .brand span{color:var(--muted);font-weight:400}
header.site nav a{margin-left:1rem;text-decoration:none}
header.site nav a[aria-current]{text-decoration:underline}
main{max-width:1200px;margin:0 auto;padding:1rem}
main.index{max-width:760px}
h1{font-size:1.9rem;margin:.6rem 0 .2rem}
.sub,.lede{color:var(--muted)}
.lede{font-size:1.05rem}
ul.docs{list-style:none;padding:0}
ul.docs li{padding:.7rem 0;border-bottom:1px solid var(--line);display:flex;flex-direction:column}
ul.docs li span{color:var(--muted);font-size:.95rem}
ul.plain li{margin:.3rem 0}
details.about{background:var(--panel);padding:.6rem .9rem;border-radius:6px;margin:.8rem 0}
details.about p{margin:.5rem 0 0;font-size:.95rem}
.toggles{display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;margin:.8rem 0;font-size:.95rem}
.scans{display:flex;gap:.6rem;overflow-x:auto;padding:.4rem 0 .8rem;border-bottom:1px solid var(--line)}
.scans a{flex:0 0 auto;text-align:center;text-decoration:none;font-size:.8rem;color:var(--muted)}
.scans img{display:block;width:80px;height:auto;border:1px solid var(--line);background:#fff}
.row{display:grid;grid-template-columns:1fr 1fr;gap:2rem;border-bottom:1px solid var(--line)}
.cols-head{font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);padding:.6rem 0 .2rem}
.cell p,.cell h3{margin:.7rem 0}
.cell h3{font-size:1.05rem}
.cell.de{color:var(--muted)}
body:not(.show-de) .row{grid-template-columns:1fr;max-width:760px}
body:not(.show-de) .cell.de{display:none}
.row.note{font-size:.9rem}
h2#notes{margin-top:2rem}
bdi.heb{font-family:"Noto Serif Hebrew",serif;font-size:1.08em}
bdi.syc{font-family:"Noto Sans Syriac",sans-serif;font-size:1.08em}
bdi.ara{font-family:"Noto Naskh Arabic",serif;font-size:1.05em}
.nl{border-bottom:1px dotted var(--muted);cursor:help;position:relative}
.nl:hover::after,.nl:focus::after{content:attr(data-tr);position:absolute;left:0;top:1.6em;background:var(--fg);color:var(--bg);font:14px/1.3 "Noto Serif",serif;padding:.2rem .45rem;border-radius:4px;white-space:nowrap;z-index:2}
abbr{text-decoration:underline dotted var(--muted);cursor:help}
.exp,.tr{display:none;color:var(--muted)}
.cn{color:var(--muted);font-size:.92em}
body:not(.show-cn) .cn{display:none}
body.show-exp .exp,body.show-tr .tr{display:inline}
a.pg{font-size:.75rem;background:var(--mark);color:var(--fg);padding:0 .3rem;border-radius:3px;text-decoration:none;white-space:nowrap;vertical-align:.1em}
a.fn{font-size:.72em;vertical-align:super;line-height:0;text-decoration:none;padding:0 .1em}
a.fnback{font-weight:600;text-decoration:none}
.pgref{color:var(--muted);font-size:.85em}
input#filter{width:100%;padding:.5rem .7rem;font:inherit;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);margin:.5rem 0 1rem}
table.abbr{width:100%;border-collapse:collapse;font-size:.92rem}
table.abbr th,table.abbr td{text-align:left;vertical-align:top;padding:.35rem .5rem;border-bottom:1px solid var(--line)}
table.abbr td:first-child{white-space:nowrap;font-weight:600}
footer{max-width:1200px;margin:2rem auto;padding:1rem;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line)}
@media (max-width:760px){body{font-size:16px}.row{grid-template-columns:1fr;gap:0}.cell.de{border-bottom:1px dashed var(--line)}table.abbr td:nth-child(3),table.abbr th:nth-child(3){display:none}}
"""

JS = """(function(){
  var store={get:function(k){try{return localStorage.getItem(k)}catch(e){return null}},
             set:function(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
  document.querySelectorAll('[data-toggle]').forEach(function(box){
    var cls=box.getAttribute('data-toggle'), saved=store.get('lz-'+cls);
    if(saved!==null) box.checked = saved==='1';
    var apply=function(){document.body.classList.toggle(cls, box.checked); store.set('lz-'+cls, box.checked?'1':'0');};
    box.addEventListener('change', apply); apply();
  });
  var f=document.getElementById('filter');
  if(f){f.addEventListener('input',function(){var q=f.value.toLowerCase();
    document.querySelectorAll('table.abbr tbody tr').forEach(function(tr){
      tr.style.display = tr.textContent.toLowerCase().indexOf(q)>=0 ? '' : 'none';});});}
})();
"""


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "app.js").write_text(JS, encoding="utf-8")
    (OUT / "index.html").write_text(index_html(), encoding="utf-8")
    (OUT / "abbreviations.html").write_text(abbreviations_html(), encoding="utf-8")
    for d in DOCS + CONTENTS:
        if d["kind"] == "entry" and not (DATA / "entries" / d["entry"] / "en.json").exists():
            print(f"skip docs/{d['slug']}.html (no translation yet)")
            continue
        (OUT / f"{d['slug']}.html").write_text(doc_html(d), encoding="utf-8")
        print(f"wrote docs/{d['slug']}.html")
    print("wrote docs/index.html, docs/abbreviations.html")


if __name__ == "__main__":
    main()
