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
| 3. Abbreviation table | the book has **no list of abbreviations**; to be built from usage during step 4 |
| 4. One whole test entry: §§ 114–115, the lion and the tiger, pp. 68–71 | OCR done ([68](data/ocr/or-claude-opus-5.5%40low%2Bital/68.md), [69](data/ocr/or-claude-opus-5.5%40low%2Bital/69.md), [70](data/ocr/or-claude-opus-5.5%40low%2Bital/70.md), [71](data/ocr/or-claude-opus-5.5%40low%2Bital/71.md)); joined and translated from the unchecked OCR ([English](data/entries/lion-tiger/en.md), $0.109); page joins checked by eye; **gold drafts for pp. 68 and 70 still wait for a hand check** ([68 notes](data/gold/68.notes.md), [70 notes](data/gold/70.notes.md)) |
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
uv run entry.py lion-tiger                             # §§ 114–115, pages joined, in English
uv run build_site.py                                   # reading edition in docs/
```

Page keys are printed page numbers, or `scanNNNN` for an unnumbered page. Output folders and
formats are as in low-flora, without the volume level: `data/ocr/{engine}/{page}.json` and `.md`,
`data/gold/{page}.txt`, `data/translation/{model}@{effort}-{rules}/{page}.json`,
`data/entries/{entry}/de.md` and `en.md`.

### Changes from low-flora

- `fetch.py`: one Frankfurt record instead of four volumes.
- `ocr.py`: the prompt describes Lewysohn and **Fraktur** (long s → `s`; a list of Fraktur
  letter pairs that are easy to confuse; letter-spaced words as plain text; `§. N.` as a heading).
  Only the OpenRouter and Anthropic engines are kept (no Tesseract or Kraken yet).
- `translate.py`: the prompt and examples are about zoology; the translation rules (v3) are unchanged.
- `entry.py`: in contents mode, each printed line is a Markdown line break in `de.md` / `en.md`.
  A footnote is kept when its mark occurs in the entry's own text on that page, so an entry that
  starts or ends mid-page (as most §§ do) gets its own notes and not its neighbour's.
- `build_site.py`: one volume, entries only; no abbreviation table yet.
- `abbrev.py` is not ported (the book has no list of abbreviations).

## Translation rules (v3, from low-flora)

German and French → English, with the author's hedges kept. Latin (including zoological names),
English, references and the author's romanizations stay as printed. Hebrew script is not
transliterated. Syriac gets Hebrew letters in brackets (in code); Arabic and Persian get IJMES, and
Greek gets SBL transliteration in brackets. Abbreviations: `Abbr. [=expansion]` at the first use.
Roman numerals → Arabic (`I 346` → `1, 346`). "Palästina" → "Eretz Yisrael" (titles and English
quotations stay as printed). Gold text is translated where it exists. Details: `translate.py` and
the low-flora README.

## Costs so far

| Step | Pages | Cost | Per page |
|---|---|---|---|
| OCR, Opus 5.5 @low +ital, contents page | 1 | $0.040 | $0.040 |
| OCR, Opus 5.5 @low +ital, pp. 68–71 | 4 | $0.335 | $0.084 (21–28 s) |
| Translation of the contents, Opus 5.5 @medium | 1 | $0.017 | — |
| Translation of §§ 114–115, Opus 5.5 @medium (3 chunks, 45 s) | 4 | $0.109 | $0.027 |

OpenRouter prices. Total so far: about $0.50. Translation is much cheaper per page than in Löw
(octavo pages, about 1,700 characters each). A full run of about 414 pages would be about $35 for
OCR and about $25–50 for translation (Löw's translation cost was $0.06–0.13 per page).

## Notes

- **Fraktur works well with Opus 5.5.** On pp. 68–71 I found no error in the German when I read
  the OCR against the scans: long s, ß, letter-spaced words, old spellings (Thier, Heerden,
  Sprüchwort), and even the printer's error "aehtiopische" are as printed. Not yet measured
  against gold.
- **Hebrew: one fluent but wrong word.** p. 69: the print has עיא (or עוא) for the lion's roar
  when it sees its prey (Chulin 53a); the OCR wrote **נער**, a real word for a lion's roar
  (Jer. 51:38) that is not on the page. This is the same kind of error as the Syriac in Löw:
  plausible and hard to notice. Hebrew in the gold pages needs a careful check.
- Small: p. 71 print ῞Υλη, OCR Ὑλη (accent lost); p. 70 the first letter of ויהורא/זיהורא is unclear.
- **Translation of §§ 114–115:** accurate, hedges kept, the three `[p. N]` marks in place. Two
  small rule breaks: the model changed the author's romanization "Schir ha-Jichud" to
  "Shir ha-Yiḥud", and gave "Thierg." as "History of Animals" in one note but kept it in the text.
  The p. 69 OCR error (נער) is in the translation too: it was made from the unchecked OCR.
- Block types are not consistent: `§. 115.` and `Der Tiger.` are one heading block on p. 70, two on p. 68.
- **No list of abbreviations** in the book. The references are mostly full tractate names
  (Chulin 53, a; B. Kama 16, b), so the table will be smaller than Löw's; the Vorrede names the
  Talmud editions used.
- The contents page was OCR'd and translated without an error (13 lines, 13 page numbers).
  Abtheilung is translated "Part", Klasse "Class".
- **Existing work:** Natan Slifkin wrote in 2012
  (["A Few Announcements"](https://www.rationalistjudaism.com/p/a-few-announcements)) that he was
  studying this book for his doctorate, was running the PDF through OCR, and proposed a
  collaborative translation with facing text. I found no sign that it was published. Not contacted.

## Next decision points

1. Check the gold drafts for pp. 68 and 70 (rename `.draft.txt` → `.txt`); then the CER of Opus
   and of archive.org's OCR on them.
2. After the gold check: translate §§ 114–115 again from the gold text (`uv run entry.py lion-tiger`)
   and rebuild the site.
3. Abbreviations: build the table from usage and make the expansion a deterministic step after
   translation (as the Jastrow/BDB mappings in
   [Bekiut](https://github.com/EzraBrand/bekiut)), not a model step.
4. Hebrew check: a second engine on the Hebrew runs only, and a person reviews where they differ
   (catches errors like נער for עיא).
5. Reading edition: links from `§. N` cross-references to their §, and the registers as data.
6. Full run: about $60–85 in total; needs a larger OpenRouter limit (the current key has about $5 left).

## License

The code and everything added in this repository (transcriptions, gold pages, translations and
documentation) are under the [MIT License](LICENSE), © 2026 Ezra Brand.

Lewysohn's *Die Zoologie des Talmuds* (1858) is in the public domain; the scans are by the
Frankfurt University Library (Freimann collection), Public Domain Mark 1.0, and are not stored here.
