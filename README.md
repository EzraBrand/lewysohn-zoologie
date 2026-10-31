# lewysohn-zoologie

OCR and English translation of Ludwig Lewysohn, *Die Zoologie des Talmuds: eine umfassende
Darstellung der rabbinischen Zoologie* (Frankfurt a. M.: Baer, 1858; XII, 400 pp.), the first
systematic collection of the Talmudic and Midrashic material on animals.

Same pipeline, rules and output as my Löw project,
[low-flora](https://github.com/EzraBrand/low-flora) (Löw, *Die Flora der Juden*). Work in
progress: small steps, each checked by hand before the next.

**Reading edition (web):** https://ezrabrand.github.io/lewysohn-zoologie/ — German and English side
by side, scans linked from each page mark, Arabic and Greek transliterations as tooltips, numbered
footnotes. Built by `build_site.py` into `docs/` (GitHub Pages serves `main:/docs`).

**A whole entry:** [§§ 114–115, the lion and the tiger, in English](data/entries/lion-tiger/en.md)
(and the [joined German text](data/entries/lion-tiger/de.md)).

## Status (31-Oct-2026)

| Step | Status |
|---|---|
| 1. Sources and book structure | done (see [Source](#source) and [Structure](#structure)) |
| 2. Table of contents: OCR and translation | done: [German](data/entries/toc/de.md), [English](data/entries/toc/en.md); no OCR errors |
| 2a. Front matter: half-title, title page, dedication, motto | done: [English](data/entries/front/en.md) ([German](data/entries/front/de.md)) |
| 2b. Preface (Vorrede, pp. VII–XII) | done: [English](data/entries/preface/en.md) ([German](data/entries/preface/de.md)); not checked by hand |
| 3. Abbreviation table | the book has **no list of abbreviations**; a reviewed table built from §§ 114–115 ([ABBREVIATIONS.md](ABBREVIATIONS.md), 34 rows), expanded by a fixed step after translation (`abbrev.py`) |
| 4. One whole test entry: §§ 114–115, the lion and the tiger, pp. 68–71 | done: OCR ([68](data/ocr/or-claude-opus-5.5%40low%2Bital/68.md), [69](data/ocr/or-claude-opus-5.5%40low%2Bital/69.md), [70](data/ocr/or-claude-opus-5.5%40low%2Bital/70.md), [71](data/ocr/or-claude-opus-5.5%40low%2Bital/71.md)); **gold pages [68](data/gold/68.txt) and [70](data/gold/70.txt)** checked by hand; page joins checked by eye; translated with rules v4 ([English](data/entries/lion-tiger/en.md), $0.119) |
| 5. Reading edition (`build_site.py`) | done for the test entry and the contents; the abbreviation page is a placeholder |

## Source

Frankfurt UB, Freimann-Sammlung, record 1043079, URN
[urn:nbn:de:hebis:30:1-113735](https://nbn-resolving.org/urn:nbn:de:hebis:30:1-113735), Public
Domain Mark 1.0. Chosen after a comparison on 31-Oct-2026:

| | Frankfurt UB (used) | archive.org, Toronto copy | HathiTrust |
|---|---|---|---|
| Id | 1043079 | [diezoologiedesta00lewyuoft](https://archive.org/details/diezoologiedesta00lewyuoft) | [011567939](https://catalog.hathitrust.org/Record/011567939): `hvd.hnrmpn`, `hvd.ah58ms` (Harvard, Google scans) |
| Image size | 3308×5315 px, about 2.5 MB JPG | 1840×3177 px | not measured (page viewer behind a Cloudflare check) |
| Complete | yes: 414 scans, pp. 2–400 numbered, no gaps or duplicates | yes: 422 leaves | not checked |
| Section table | yes, in the IIIF manifest | no | — |

- IIIF Presentation 2.0 manifest: `https://sammlungen.ub.uni-frankfurt.de/i3f/v20/1043079/manifest`;
  images: `.../i3f/v20/{image id}/full/full/0/default.jpg`. The search pages are behind bot
  protection; the IIIF endpoints are not.
- Scan index = position in the manifest; **printed page = scan − 14** (p. 1 is scan 15, unnumbered).
  Labels in brackets (`[13]`) are unnumbered pages, and the number is the scan index.
- Scans are not stored in this repository; `fetch.py` downloads them (sequential, 2 s delay, cached).
- **archive.org's OCR text is unusable.** The German is set in Fraktur, and archive.org's OCR read it
  as roman type ("Zoologie kg ^almuH"). It is kept as a baseline to score against gold pages, not
  as a source.

## Structure

The German is set in **Fraktur**; references, Latin, zoological names and foreign words in roman
type (Antiqua). Hebrew and Aramaic are unpointed and set in the line; there is some Greek, Latin and
a little Arabic. Footnotes `*)`, `**)`, `***)` restart on each page.

| Part | Printed pp. | Scans |
|---|---|---|
| Title, dedication, motto | — | 1–6 |
| Vorrede (signed Worms, 5 March 1858) | VII–XII | 7–12 |
| Inhalt (one page) | unnumbered | 13 |
| 1st part: Allgemeine Zoologie | 1–63 | 15–77 |
| 2nd part: Specielle Zoologie, 8 classes: Säugethiere 64, Vögel 159, Amphibien 218, Fische 243, Weichthiere 279, Insecten 285, Würmer 334, Zoophyten 342 | 64–349 | 78–363 |
| 3rd part: Fabelhafte Thiere | 350–357 | 364–371 |
| Nachtrag, Anhang, Zusätze und Verbesserungen | 358, 368, 376 | 372, 382, 390 |
| Registers: I Greek, II Latin, III Hebrew and Aramaic, IV German | 377–400 | 391–414 |

The text is divided into **numbered §§ that run through the whole book** (§. 1 on p. 1; about
500 in all); a § usually treats one animal or topic. The registers give page numbers; the
cross-references in the text give §§. The printed Inhalt lists only the parts and classes, not the
Vorrede or the registers.

## Setup

- Python 3.13 with uv: `uv sync`
- OpenRouter key: a text file, default `%USERPROFILE%\Desktop\Misc\key.txt` (set `OPENROUTER_KEY_FILE`).

## Run

```
uv run fetch.py list --from 10 --to 20                 # scan index, label, image id
uv run fetch.py preview 82 83 84                       # 1000 px previews to pick pages
uv run fetch.py sample                                 # full-res sample + data/raw/manifest.json

uv run ocr.py openrouter --model anthropic/claude-opus-5.5 --effort low --tag ital   # all sample pages
uv run ocr.py openrouter 68 --model anthropic/claude-opus-5.5 --effort low --tag ital

uv run eval.py draft 68 --from "or-claude-opus-5.5@low+ital"   # start a gold page
uv run eval.py                                         # CER table (needs gold pages)

uv run entry.py toc                                    # contents page, lines kept, in English
uv run translate.py 68 69                              # single pages in English
uv run entry.py lion-tiger                             # §§ 114–115: join, translate, expand abbreviations
uv run entry.py lion-tiger --expand-only               # redo only the abbreviation step (no model call)
uv run abbrev.py                                       # check all entries, render ABBREVIATIONS.md
uv run ia_ocr.py 68 70                                 # archive.org's OCR as a baseline engine for eval.py
uv run build_site.py                                   # reading edition in docs/
```

Page keys are printed page numbers, or `scanNNNN` for an unnumbered page. Output folders and
formats are as in low-flora, without the volume level: `data/ocr/{engine}/{page}.json` and `.md`,
`data/gold/{page}.txt`, `data/translation/{model}@{effort}-{rules}/{page}.json`,
`data/entries/{entry}/de.md` and `en.md` (`en.raw.json` = the model's output before the
abbreviation step).

### Changes from low-flora

- `fetch.py`: one Frankfurt record instead of four volumes.
- `ocr.py`: the prompt describes Lewysohn and **Fraktur** (long s → `s`; a list of Fraktur
  letter pairs that are easy to confuse; letter-spaced words as plain text; `§. N.` as a heading).
  Only the OpenRouter and Anthropic engines are kept (no Tesseract or Kraken yet).
- `translate.py`: the prompt and examples are about zoology; rules v4 (see below).
- `entry.py`:
  - In contents mode, each printed line is a Markdown line break in `de.md` / `en.md`.
  - A footnote is kept when its mark occurs in the entry's own text on that page, so an entry that
    starts or ends mid-page (as most §§ do) gets its own notes and not its neighbour's.
  - **Paragraphs are split at Lewysohn's long dashes** (` — `, not before a digit, so ranges like
    "S. 63 — 76" stay); the dash itself is dropped. Main text only, not footnotes.
  - `FIXES`: corrections to the OCR of pages without gold text, each checked against the scan.
  - A footnote at the top of a page whose mark is not in that page's text continues the last note
    of the page before (the numbered list in note `***)` of the preface runs over pp. IX–XI).
  - `keep_hyphen`: page breaks at a real hyphen ("Auto-|da-fé's").
  - After translation (fixed steps, no model): the page marks are copied from the German (the model
    turned `[p. VIII]` into `[p. 8]`); Talmud folios get the modern form; `abbrev.py` checks and
    expands the abbreviations.
- `abbrev.py`: new. A reviewed table (`abbreviations.json`) and a fixed expansion step after
  translation, as with the Jastrow/BDB mappings in [Bekiut](https://github.com/EzraBrand/bekiut).
  The book has no list of abbreviations; the table is built from the text.
- `ia_ocr.py`: new. archive.org's OCR per page, from its DjVu XML, as a baseline for `eval.py`.
- `build_site.py`: one volume, entries only; the tooltip covers the whole abbreviation ("B. Kama").

## Translation rules (v5, 31-Oct-2026)

German and French → English, with the author's hedges kept. Latin (including zoological names),
English, references and the author's romanizations stay as printed. Hebrew script is not
transliterated. Syriac gets Hebrew letters in brackets (in code); Arabic and Persian get IJMES, and
Greek gets SBL transliteration in brackets. Roman numerals → Arabic (`I 346` → `1, 346`).
"Palästina" → "Eretz Yisrael" (titles and English quotations stay as printed). Gold text is
translated where it exists.

New in v4:
- **Abbreviations** are no longer expanded by the model. The prompt lists the abbreviations of the
  input in two groups. Sources and bibliography (mode `expand`) stay exactly as printed, German
  titles of classical works included ("Thierg.", "Naturg."). General German abbreviations (mode
  `translate`) are rendered in English (S. → p., vgl. → cf.). After translation, `abbrev.py`
  counts each `expand` abbreviation in the German and the English (a mismatch means the model
  translated or dropped one), then adds ` [=expansion]` after its first use in the document. For a
  classical work the expansion gives the English and the Latin title: `Thierg. [=Aelian, On the
  Nature of Animals (De natura animalium; German title Thiergeschichte)]`.
- The author's romanized Hebrew titles keep his spelling ("Schir ha-Jichud", not "Shir ha-Yiḥud").
- An abbreviation is expanded only at its **first use** in a document. "Midr. Jalk. Schim." is a
  row of its own, so it is expanded as one title.

New in v5: **Talmud folio references in the modern form** in the English: "Sanhedrin 106, a" →
"Sanhedrin 106a", "ibid. 64, a" → "ibid. 64a". A fixed step after translation
(`translate.modern_citations`), so a v4 translation becomes v5 without a model call. Only a side
`a`/`b` after "number, " changes; Mishnah and Jerusalem Talmud references ("Aboth 5, 20",
"B. batra 2, 3") stay. The German stays as printed.

## Results: CER on the gold pages (pp. 68 and 70)

| Engine | All | Latin script | Hebrew | Arabic | Greek |
|---|---|---|---|---|---|
| Opus 5.5 @low +ital | 0.0% | 0.0% | 0.7% (1 letter) | 0.0% | 0.0% |
| archive.org's OCR (Toronto copy) | 30.7% | 36.8% | 110% | 100% | 100% |

Gold characters: 4,620 (Latin script 3,251, Hebrew 152, Arabic 6, Greek 6). The gold pages were made
from the Opus draft and checked by hand, so the Opus numbers favour Opus; the one Hebrew error
(טגרים for טגריס) is the only change that the check made. Two pages only: rough signals.

## Costs so far

| Step | Pages | Cost | Per page |
|---|---|---|---|
| OCR, Opus 5.5 @low +ital, contents page | 1 | $0.040 | $0.040 |
| OCR, Opus 5.5 @low +ital, pp. 68–71 | 4 | $0.335 | $0.084 (21–28 s) |
| Translation of the contents, Opus 5.5 @medium | 1 | $0.017 | — |
| Translation of §§ 114–115, rules v3 (from OCR; replaced) | 4 | $0.109 | $0.027 |
| Translation of §§ 114–115, rules v4 (3 chunks, 47 s) | 4 | $0.119 | $0.030 |
| OCR, front matter and preface | 10 | $0.526 | $0.012–0.078 |
| Translation, front matter | 4 | $0.023 | — |
| Translation, preface (3 chunks) | 6 | $0.133 | $0.022 |

OpenRouter prices. Total so far: about $1.30. Translation is much cheaper per page than in Löw
(octavo pages, about 1,700 characters each). A full run of about 414 pages would be about $35 for
OCR and about $15–25 for translation.

## Notes

- **Fraktur works well with Opus 5.5.** On the gold pages the German (Latin script) has no errors:
  long s, ß, letter-spaced words, old spellings (Thier, Heerden, Sprüchwort), and even the
  printer's error "aehtiopische" are as printed.
- **Hebrew is the weak point, and the errors are plausible words.** Three errors in 4 pages, each a
  real word or form:
  - p. 69: print **עוא** (the roar when the lion sees its prey, Chulin 53a); OCR **נער**, a real
    word for a lion's roar (Jer. 51:38) that is not on the page.
  - pp. 70 and 71: print **טגריס**; OCR **טגרים** (final ם for ס, twice).

  This is the same kind of error as the Syriac in Löw: hard to notice. pp. 69 and 71 are corrected
  in `entry.py` (`FIXES`), checked by me against the scan; p. 70 is corrected in its gold text.
- Small: p. 71 print ῞Υλη, OCR Ὑλη (accent lost). On p. 70 the gold keeps ויהורא (the Talmud word
  is זיהרא; the first letter in the print is unclear).
- **Translation of §§ 114–115 (v4):** accurate, hedges kept, the three `[p. N]` marks in place,
  all 22 source and bibliography abbreviations kept as printed and expanded once. The model wrote
  "Varro" for Lewysohn's "Varo".
- **Preface (pp. VII–XII):** read against the scans; no OCR error found. Printer's errors kept as
  printed: "babyl. Taldmud", "bot sich … darin dem Mangel", "Worms., den". The Kusari quotation on
  p. VIII ends מגאלינום in the print (the Hebrew Kusari has מגאלינוס). The translation is close
  and keeps the author's modesty formulas. The abbreviation check reports "Kusari: 2 in the
  German, 3 in the English"; this is correct ("Kusaricommentar" → "Kusari commentary").
- **Abbreviations:** 61 rows from §§ 114–115 and the front matter. Five expansions are marked
  **guess** (which work by Gesenius, Fürst, Voigt, Münster is meant; "D. m." as Doctor medicinae);
  check them when more entries cite them. "Klein's Jahrbuch" (preface, note) is not identified.
- Block types are not consistent: `§. 115.` and `Der Tiger.` are one heading block on p. 70, two on p. 68.
- The contents page was OCR'd and translated without an error (13 lines, 13 page numbers).
  Abtheilung is translated "Part", Klasse "Class".
- **Existing work:** Natan Slifkin wrote in 2012
  (["A Few Announcements"](https://www.rationalistjudaism.com/p/a-few-announcements)) that he was
  studying this book for his doctorate, was running the PDF through OCR, and proposed a
  collaborative translation with facing text. I found no sign that it was published. Not contacted.

## Next decision points

1. **Hebrew check:** 3 Hebrew errors in 4 pages. Options: a second engine on the Hebrew runs only,
   with a person reviewing where they differ; or a check of each Hebrew word against a word list
   (Jastrow headwords in Bekiut), flagging words not found.
2. **Next part, in book order:** the first part, *Allgemeine Zoologie* (pp. 1–63, §§ 1 to about
   100): about $7 for OCR and translation. Then the classes. A gold page from each part, to see
   whether the CER holds.
3. Abbreviations: grow the table with each entry; resolve the **guess** rows.
4. Reading edition: links from `§. N` cross-references to their §, and the registers as data.
5. Full run: about $50–60 in total.

## License

The code and everything added in this repository (transcriptions, gold pages, translations and
documentation) are under the [MIT License](LICENSE), © 2026 Ezra Brand.

Lewysohn's *Die Zoologie des Talmuds* (1858) is in the public domain; the scans are by the
Frankfurt University Library (Freimann collection), Public Domain Mark 1.0, and are not stored here.
