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

**Companion project:** [talmud-zoology-factcheck](https://github.com/EzraBrand/talmud-zoology-factcheck)
([page](https://ezrabrand.github.io/talmud-zoology-factcheck/)) checks the Talmud's statements on animals, and
Lewysohn's comments on them, against modern zoology, with links to the §§ of this edition.

**§ links:** each § in the reading edition has a fixed anchor, `#s` + its number
(`mammals.html#s119` for § 119), and each page opens with a collapsible list of its §§.

**In English: the whole book** (01-Nov-2026): the [front matter](data/entries/front/en.md), the
[preface](data/entries/preface/en.md), the [contents](data/entries/toc/en.md), the
[first part, General zoology](data/entries/part1/en.md) (pp. 1–63), the eight classes of the second
part ([mammals](data/entries/mammals/en.md), [birds](data/entries/birds/en.md),
[amphibians](data/entries/amphibians/en.md), [fish](data/entries/fish/en.md),
[molluscs](data/entries/molluscs/en.md), [insects](data/entries/insects/en.md),
[worms](data/entries/worms/en.md), [zoophytes](data/entries/zoophytes/en.md)), the
[fabulous animals](data/entries/fabulous/en.md), the [supplement, appendix and corrections](data/entries/addenda/en.md)
and the [registers](data/entries/registers/en.md) (pp. 377–400).

## Status (01-Nov-2026)

| Part | Pages | OCR | Hebrew check | Translation |
|---|---|---|---|---|
| Front matter, preface, contents | 4 + VII–XII + 1 | Opus 5.5 | read by eye | done |
| First part: General zoology | 1–63 | Opus 5.5 | Flash + vote: 50 changes | done ($2.02) |
| Second part, class 1: Mammals | 64–159 | Sonnet 5.5 | Flash + vote: 111 changes | done ($2.97) |
| §§ 114–115, lion and tiger (test entry) | 68–71 | Opus 5.5; **gold pp. 68, 70** | by hand | done |
| Classes 2–8 (birds to zoophytes), fabulous animals, supplement and appendix | 159–376 | Sonnet 5.5 | Flash + vote: 248 changes | done |
| Registers I–IV | 377–400 | Opus 5.5 (4 pages by column) | Flash + text judge: 21 changes | done; printed lines kept |

Abbreviations: the book has **no list of abbreviations**; a reviewed table of 144 rows
([ABBREVIATIONS.md](ABBREVIATIONS.md)), built from the text, expanded by a fixed step after
translation (`abbrev.py`).

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

# a part of the book (here the mammals, OCR by Sonnet with the Flash check of the Hebrew)
uv run ocr.py openrouter $(seq 64 158) --model anthropic/claude-sonnet-5.5 --effort low --tag ital
uv run ocr.py openrouter $(seq 64 158) --model google/gemini-3.8-flash --effort low --tag ital
uv run qa.py 64 158 --main "or-claude-sonnet-5.5@low+ital"       # lengths, notes, page joins
uv run hebcheck.py 64 158 --main "or-claude-sonnet-5.5@low+ital" # Hebrew words where the two differ
uv run hebjudge.py 64 158 --main "or-claude-sonnet-5.5@low+ital" # text judge
uv run hebjudge.py 64 158 --main "or-claude-sonnet-5.5@low+ital" --mode image --only-ties
uv run hebvote.py 64 158                                         # 2 of 3 -> data/hebfix/*.decisions.json
uv run abbrev.py --candidates mammals                            # new abbreviations, for review
uv run entry.py mammals                                          # join, translate, fixed steps

# the registers: two columns; text_box may keep only one, so these pages go column by column
uv run ocr.py openrouter 387 388 389 399 --model anthropic/claude-opus-5.5 --effort low --tag ital --force --columns
# parallel judges: text workers write {range}_wN.json, image workers {range}.imageN.json
uv run hebjudge.py 159 376 --main "or-claude-sonnet-5.5@low+ital" --start 130 --suffix _w2
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
- `qa.py`: new. Per page: length against archive.org's (dropped text), footnote marks against
  notes, footnotes before the body text (body typed as a footnote), and each page break for the
  join check by eye.
- `hebcheck.py`, `hebjudge.py`, `hebvote.py`: new. The second reading of the Hebrew (see Notes).
- `entry.py` also has: per-entry OCR source; `WORD_FIXES` (a systematic word error of one engine,
  e.g. Sonnet's "Burdorf" for "Buxdorf"); `TYPE_FIXES` (block types); `NOTE_MARK_FIXES` (printer's
  errors in footnote marks); the voted Hebrew corrections, applied page-wide in the German and
  copied into an existing English translation (`sync_hebrew`).
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

## Results

### OCR engines (pp. 68–71)

CER against the two gold pages (pp. 68, 70); the three known Hebrew errors are on pp. 69–71.

| Engine | $/page | s/page | CER all | Latin script | Hebrew | 3 known Hebrew words | Notes |
|---|---|---|---|---|---|---|---|
| Opus 5.5 @low +ital | 0.084 | 24 | 0.0% | 0.0% | 0.7% | 0 of 3 | |
| Sonnet 5.5 @low +ital | 0.042 | 15 | 0.1% | 0.0% | 2.0% | 0 of 3 | reads Fraktur x as r ("Burdorf") |
| Gemini 3.8 Flash @low +ital | 0.009 | 14 | 0.8% | 0.2% | 16%* | **3 of 3** | tz → ß; reverses right-to-left lists |
| Gemini 3.1 Pro @low +ital | 0.031 | 21 | 2.0% | 1.7% | 15%* | 2 of 3 | |
| Haiku 5.5 @low +ital | 0.002 | 14 | 1.2% | 0.2% | 3.9% | 0 of 3 | dropped the Arabic and the Greek |
| archive.org's OCR (Toronto copy) | — | — | 30.7% | 36.8% | 110% | — | read the Fraktur as roman type |

\* Mostly one reversed list. Gold characters: 4,620 (Latin script 3,251, Hebrew 152, Arabic 6,
Greek 6). The gold pages were made from the Opus draft and checked by hand, so the numbers favour
Opus. Two pages only: rough signals. No engine dropped text (all page lengths within 1% of Opus).

**Choice (31-Oct-2026):** Opus for the front matter and part 1 (already done); from the mammals on,
**Sonnet for the page and Gemini 3.8 Flash as a second reader of the Hebrew** ($0.051 per page).

### The second reading of the Hebrew

1. `hebcheck.py` aligns the Hebrew words of the main OCR and of Flash (vowel points removed, final
   letters kept) and lists every difference. Part 1: 172 differences in 1,432 Hebrew words (16 only
   in the order of a list); mammals: 223 in 1,645.
2. `hebjudge.py` decides each difference twice: the **text judge** (Opus @medium) chooses between
   the two readings from the sentence (Lewysohn's German gloss, the source he cites); the **image
   judge** (Opus @medium) reads a strip of the scan around the line.
3. `hebvote.py`: the main OCR is changed where at least two of Flash, the text judge and the image
   judge agree against it, and only if the words differ by a letter or two (a pair of different
   list words is an alignment error, listed for review).

On the known cases each check alone was wrong at least once: the image judge kept טגרים (the same
ם/ס bias as the OCR), the text judge "corrected" the printed עוא to נער, a better-known word for a
lion's roar. The vote of the three was right in all three cases.

Part 1: 150 flags → **50 changes**, 80 kept, 14 without a majority, 6 for review
(`logs/hebvote_1-63.csv`). Mammals (Sonnet as the main OCR; the image judge only on the 78 flags
where the text judge and Flash disagree): 189 flags → **111 changes**, 36 kept, 29 without a
majority, 13 for review (`logs/hebvote_64-158.csv`). Sonnet's typical error is ר for ד
(ארני שרה → אדני שדה, the Mishnah's "man of the field"; דורם → דורס; חחול → חתול). The changes are mostly systematic: final ם for ס (סרים → סריס,
כרם → כרס, מרם → מרס), ו for ז (ויהורא → זיהורא), doubled ו (וושט → ושט), ם for ב (ערקום → ערקוב).
They are applied to every use of the word on its page, in the German and, by a fixed step, in an
English translation made before the vote. Cost: about $0.03 per flag.

Birds to the appendix (pp. 159–376, Sonnet): 3,832 Hebrew words, 551 differences; 490 flags →
**248 changes**, 132 kept, 88 without a majority, 22 for review (`logs/hebvote_159-376.csv`); the
image judge only on the 283 flags where the text judge and Flash disagree. Typical: ח for ת
(חרנגול → תרנגול, חולעת → תולעת), ר for ד (ריה → דיה), final ם for ס (סום → סוס).

Registers (pp. 377–400, Opus): 972 Hebrew words, 139 differences; 92 flags → **21 changes**, 69
without a majority (kept), 2 for review (`logs/hebvote_377-400.csv`). **No image judge here**: its
strip is cut by line number on a one-column page, which does not work on the two-column registers;
so a change needs Flash and the text judge to agree.

## Costs so far

| Step | Pages | Cost | Per page |
|---|---|---|---|
| Contents, front matter, preface, §§ 114–115 (OCR and translation, all versions) | 19 | about $1.30 | — |
| Model test, OCR of pp. 68–71 with 4 other engines | 4 | $0.34 | — |
| Part 1: OCR, Opus 5.5 | 63 | $5.30 | $0.084 |
| Part 1: OCR, Flash (Hebrew check) | 63 | $0.55 | $0.009 |
| Part 1: text and image judges (150 flags; about 100 judged twice by parallel workers) | — | about $3.90 | — |
| Part 1: translation (25 chunks) | 63 | $2.02 | $0.032 |
| Mammals: OCR, Sonnet 5.5 and Flash | 91 | $4.43 | $0.049 |
| Mammals: text judge (203 flags) and image judge (78 ties, 3 workers) | — | $3.50 | — |
| Mammals: translation (first run lost at chunk 26 by a network reset: $1.86; second run) | 95 | $4.83 | $0.051 |
| pp. 159–400: OCR, Sonnet 5.5 (4 parallel workers) | 242 | $9.81 | $0.041 |
| pp. 159–400: OCR, Flash (Hebrew check) | 242 | $2.01 | $0.008 |
| Registers: OCR again with Opus 5.5 (Sonnet dropped text), 4 pages again by column | 24 | $1.82 | $0.076 |
| pp. 159–376: text judge (521 flags, 4 workers) and image judge (283 ties, 3 workers, some overlap) | — | $12.46 | — |
| Registers: text judge (92 flags) | — | $0.94 | — |
| pp. 159–400: translation (9 entries and the registers, run in parallel; includes chunks lost when a run was stopped) | 242 | $7.56 | $0.031 |

OpenRouter prices. Total for this project: about $63 (the key had $13.88 of usage from other
projects before this one). Translations are saved chunk by chunk, so a stopped run resumes; OCR
and the judges skip what is done, so they run as parallel workers (OCR of 242 pages: about 15
minutes with 4 workers per model).

## Notes

- **Fraktur works well.** On the gold pages the German (Latin script) has no errors with Opus or
  Sonnet: long s, ß, letter-spaced words, old spellings (Thier, Heerden, Sprüchwort), and even the
  printer's error "aehtiopische" are as printed. One systematic Sonnet error: the Fraktur x in
  "Buxdorf" read as r ("Burdorf", 14 times in the mammals), corrected by `WORD_FIXES`.
- **Hebrew is the weak point, and the errors are plausible words** (see the second reading above).
- **OCR block errors are rare but real:** on p. 16 Opus typed two body paragraphs as footnotes
  (`TYPE_FIXES`; `qa.py` now flags footnotes before the body text); on p. 52 the book itself has
  `**)` in the text and `*)` at the note (`NOTE_MARK_FIXES`).
- **Page joins:** 62 in part 1 and 94 in the mammals, all checked by eye; 7 needed a `continue`
  (a page ending with a footnote mark, ")", ";", ":" or a verse line mid-sentence).
- Small: p. 71 print ῞Υλη, OCR Ὑλη (accent lost). On p. 70 the gold keeps ויהורא; the vote on
  pp. 50–51 chose זיהורא for the same word (the Talmud form, Chulin 53a), so p. 70 may need a look.
- **Translation:** accurate, hedges kept. The model wrote "Varro" for Lewysohn's "Varo", and
  "Division" for "Abtheilung" in part 1 (now a term rule, "Part", and a fixed step for headings).
- **Preface (pp. VII–XII):** read against the scans; no OCR error found. Printer's errors kept as
  printed: "babyl. Taldmud", "bot sich … darin dem Mangel", "Worms., den". The Kusari quotation on
  p. VIII ends מגאלינום in the print (the Hebrew Kusari has מגאלינוס). The abbreviation check
  reports "Kusari: 2 in the German, 3 in the English"; this is correct ("Kusaricommentar" →
  "Kusari commentary").
- **Abbreviations:** 144 rows (13 added for pp. 159–400: Winer, Blumenbach, Sch. Ar., Or. Chajim,
  i. l. and others). Rows marked **guess**: Gesenius, Fürst, Münster, "D. m.", Or. Ester, Mytholog. Wörterb. Not identified: "Klein's Jahrbuch" (preface), "i. d. e. S." (part 1,
  twice). Voigt is now certain (p. 9: "Voigt, Lehrb. d. Zool.").
- The contents page was OCR'd and translated without an error (13 lines, 13 page numbers).
- **Pages shared by two parts** (01-Nov-2026): each class heading stands mid-page, so an entry now
  includes the first page of the next one. Before this, the end of § 181 (ambergris) on p. 159 was
  missing from the mammals; it is now translated and added. A footnote whose mark is in the other
  part of a shared page is left out (p. 279: the note belongs to the molluscs, not the fish).
- **More Sonnet errors** (from p. 159 on): "Burxdorf" for Buxdorf, "a. a. D." for "a. a. O." (Fraktur O
  and D look alike), both in `WORD_FIXES`; the heading "Vierte Klasse." typed as a running head on
  p. 243 (`TYPE_FIXES`). Not corrected (the translation reads them correctly): 13 Fraktur double
  hyphens written as "=" ("unvol= lem", but also the real hyphen "Nord= und Ostsee") and 6 long s
  (ſ) in the German.
- **Registers:** two columns. On pp. 387–389 and 399 the text-block crop kept only one column, so
  both engines read half the page; `ocr.py --columns` cuts the page at the column gap and sends the
  two columns as two images. Sonnet also dropped most of pp. 383–384, so the registers are Opus.
  In the English, all 1,830 page numbers are the same as in the German and in the same order; the
  German register IV is translated line by line and keeps the German alphabetical order.
- **Page joins** pp. 159–376: all checked from `logs/qa_159-400.csv`; 10 needed a `continue`.
- **Existing work:** Natan Slifkin wrote in 2012
  (["A Few Announcements"](https://www.rationalistjudaism.com/p/a-few-announcements)) that he was
  studying this book for his doctorate, was running the PDF through OCR, and proposed a
  collaborative translation with facing text. I found no sign that it was published. Not contacted.

## Next decision points

1. **Review by hand:** part 1: 6 review cases and 14 without a majority (`logs/hebvote_1-63.csv`);
   mammals: 13 and 29 (`logs/hebvote_64-158.csv`).
2. **p. 69 in the mammals:** the vote and the manual correction agree on עוא; check that p. 70's
   gold ויהורא should be זיהורא, as the vote chose on pp. 50–51.
3. **A gold page from part 1 and from the mammals**, to measure the CER after the vote.
4. **Review by hand, pp. 159–400:** 22 review cases and 88 without a majority
   (`logs/hebvote_159-376.csv`); registers: 2 and 69 (`logs/hebvote_377-400.csv`).
5. **A gold page from the birds or insects**, to measure the error rate of the Sonnet + vote setup.
6. Abbreviations: resolve the **guess** rows. Reading edition: links from `§. N` cross-references
   to their §, and from the register page numbers to the pages.

## License

The code and everything added in this repository (transcriptions, gold pages, translations and
documentation) are under the [MIT License](LICENSE), © 2026 Ezra Brand.

Lewysohn's *Die Zoologie des Talmuds* (1858) is in the public domain; the scans are by the
Frankfurt University Library (Freimann collection), Public Domain Mark 1.0, and are not stored here.
