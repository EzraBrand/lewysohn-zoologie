"""OCR the sample pages of Lewysohn, Die Zoologie des Talmuds (1858).

  uv run ocr.py openrouter --model anthropic/claude-opus-5.5 --effort low --tag ital   # all pages in data/raw/manifest.json
  uv run ocr.py openrouter 33 scan0013 --model anthropic/claude-opus-5.5 --effort low --tag ital   # only these pages
  uv run ocr.py claude --force         # redo pages that already have output

Writes data/ocr/{engine}/{page}.json and .md. Pages with output are skipped.
Ported from low-flora (Löw, Flora der Juden); the prompt is changed for Fraktur.
"""

import argparse
import base64
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(__file__).parent / "data"

MODEL = "claude-opus-5-5"
PRICE_IN, PRICE_OUT = 4.00, 20.00  # USD per MTok, claude-opus-5-5 (skill table, cached 06-Oct-2026)
MAX_EDGE, MAX_PIXELS = 2576, 3_750_000  # the API downscales images beyond either limit

BLOCK_TYPES = ["heading", "body", "footnote", "index_entry", "furniture"]
LANGS = ["deu", "lat", "fra", "eng", "ita", "grc", "heb", "arc", "syc", "ara", "fas", "translit", "other"]

PROMPT = """\
These images are one printed page of Ludwig Lewysohn, "Die Zoologie des Talmuds" (Frankfurt \
1858): a German scholarly text on the animals of the Talmud and Midrash, with Hebrew and \
Aramaic words (unpointed), some Greek, Latin and Arabic, and romanized transliterations. The \
German is set in Fraktur (blackletter); references, Latin and zoological names, and foreign \
words are set in roman type (Antiqua). The page is split into {n} image(s), top to bottom, cut \
at blank space between lines. Transcribe the whole page as one page.

Transcription rules:
- Transcribe exactly what is printed. Never translate, normalize, modernize, correct or expand \
abbreviations. Keep the original spelling (Thier, Abtheilung, ß, ä, old forms) and punctuation, \
including the dashes (—), tildes (~) and asterisks.
- Fraktur: write it in ordinary Latin letters. Write the long s (ſ) as "s". Read the \
Fraktur letter forms with care: long s vs. f, k vs. t, r vs. x, B vs. V, C vs. E, I vs. J, \
N vs. R, Z vs. 3. Write the Fraktur double hyphen at a line end as "-".
- Hebrew, Aramaic, Syriac, Arabic and Greek stay in their own script, in Unicode, in logical \
(reading) order. Keep vowel points and diacritics only where they are printed. Keep the \
diacritics of transliterations (ṭ, ḥ, ā, š, ʿ, ʾ ...).
- Keep each printed line as one line: separate lines with "\\n". Keep a hyphen at a line end \
as printed. Do not join lines.
- Subscripts: write "_{{14}}" for a subscript 14. Superscripts: write "^{{a}}". Write small \
capitals and letter-spaced (gesperrt) words as plain text with normal capitalization and \
spacing ("S ä u g e t h i e r e" -> "Säugethiere").
- Italics: wrap italic text in <i>...</i> (e.g. "<i>buṭm</i>, sont"). Open and close the tag \
inside one run; if an italic stretch continues into the next run, close it and open it again \
there. Punctuation after an italic word stays outside the tag unless it is clearly italic. \
Semitic scripts and Greek are never marked italic.
- Text you cannot read: write [?] for each unreadable stretch. Do not guess.

Blocks, in reading order:
- "furniture": running head, page number, printer's signature (e.g. "Zoologie des Talmuds. 1").
- "heading": a section or entry heading that stands on its own line(s), e.g. "§. 4.".
- "body": a paragraph of main text. A new paragraph starts at an indented line.
- "index_entry": a paragraph on an index or abbreviation-list page (keep the whole printed \
paragraph in one block; do not split it into single entries).
- "footnote": one footnote. Put its printed mark ("*)", "**)", "†)", "1)") in "marker" and \
not in the runs. In the main text, keep the footnote reference marks where they are printed.
For other block types, "marker" is "".

Runs: split each block into runs of one language each, in reading order. Codes: deu German, \
lat Latin (incl. botanical names), fra French, eng English, ita Italian, grc Greek, heb Hebrew, \
arc Aramaic (incl. Jewish Babylonian/Palestinian, Targum, Samaritan), syc Syriac, ara Arabic, \
fas Persian, translit romanized Semitic words, other. Numbers, references and punctuation go \
with the run around them. Concatenating the runs of a block must give the block text exactly \
(spaces and "\\n" included). If Hebrew vs. Aramaic is unclear, use heb.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": BLOCK_TYPES},
                    "marker": {"type": "string"},
                    "runs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "lang": {"type": "string", "enum": LANGS},
                                "text": {"type": "string"},
                            },
                            "required": ["lang", "text"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["type", "marker", "runs"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["blocks"],
    "additionalProperties": False,
}


# ---------- image preparation (Claude) ----------

def _span(profile: np.ndarray, thr: float, gap: int) -> tuple[int, int]:
    """Largest run of indices where profile > thr, bridging gaps up to `gap`."""
    idx = np.flatnonzero(profile > thr)
    breaks = np.flatnonzero(np.diff(idx) > gap)
    starts = np.r_[idx[0], idx[breaks + 1]]
    ends = np.r_[idx[breaks], idx[-1]] + 1
    k = int(np.argmax(ends - starts))
    return int(starts[k]), int(ends[k])


def text_box(gray: Image.Image, gap: float = 0.04) -> tuple[int, int, int, int]:
    """Bounding box of the text block, without the scan borders around the page."""
    small = np.asarray(gray.reduce(4)) < 140
    h, w = small.shape
    # blank out border lines (rows/columns that are mostly ink), then find the text block
    small[small.mean(axis=1) > 0.25, :] = False
    small[:, small.mean(axis=0) > 0.25] = False
    # gap 4%: bridges the space left by a removed column rule (two-column contents pages);
    # the registers need more (their column gap is wider): --columns passes 0.15
    x0, x1 = _span(small.mean(axis=0), 0.003, int(w * gap))
    rows = small[:, x0:x1].mean(axis=1)
    rows = np.where(rows > 0.4, 0, rows)
    ys = np.flatnonzero(rows > 0.002)
    if not len(ys):
        raise ValueError("no text found: blank page?")
    pad = 6
    # wide side margins: a column of page numbers (contents pages) can stand apart from the text
    # block after leader dots; some margin noise does not hurt the OCR
    side = max(pad, int(w * 0.06))
    return (max(x0 - side, 0) * 4, max(ys[0] - pad, 0) * 4,
            min(x1 + side, w) * 4, min(ys[-1] + 1 + pad, h) * 4)


def page_images(path: Path) -> list[Image.Image]:
    """Crop to the text block; cut in two at a blank row if the page is tall."""
    gray = Image.open(path).convert("L")
    columns = getattr(ARGS, "columns", False)
    page = gray.crop(text_box(gray, 0.15 if columns else 0.04))
    w, h = page.size
    if columns:  # two-column registers: cut at the blank gap near the middle
        ink = (np.asarray(page) < 140).mean(axis=0)
        lo, hi = int(w * 0.4), int(w * 0.6)
        cut = lo + int(np.argmin(np.convolve(ink[lo:hi], np.ones(15) / 15, "same")))
        return [page.crop((0, 0, cut, h)), page.crop((cut, 0, w, h))]
    if h <= MAX_EDGE * 1.1 or h < 1.3 * w:
        return [page]
    ink = (np.asarray(page) < 140).mean(axis=1)
    lo, hi = int(h * 0.4), int(h * 0.6)
    cut = lo + int(np.argmin(np.convolve(ink[lo:hi], np.ones(15) / 15, "same")))
    return [page.crop((0, 0, w, cut)), page.crop((0, cut, w, h))]


def jpeg_b64(img: Image.Image) -> str:
    s = min(1, MAX_EDGE / max(img.size), (MAX_PIXELS / (img.width * img.height)) ** 0.5)
    if s < 1:  # resize here, so we control the filter
        img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return base64.standard_b64encode(buf.getvalue()).decode()


# ---------- engines ----------

def parse_blocks(text: str) -> list[dict]:
    """Model JSON -> blocks; block lang = the language with the most characters."""
    text = text.strip()
    if text.startswith("```"):  # models without schema enforcement may fence the JSON
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    blocks = []
    for b in json.loads(text)["blocks"]:
        chars = {}
        for r in b["runs"]:
            chars[r["lang"]] = chars.get(r["lang"], 0) + len(r["text"].strip())
        blocks.append({"type": b["type"], "lang": max(chars, key=chars.get) if chars else "other",
                       "text": "".join(r["text"] for r in b["runs"]),
                       "marker": b.get("marker", ""), "runs": b["runs"]})
    return blocks


def run_openrouter(path: Path) -> dict:
    import requests

    key = Path(os.environ.get("OPENROUTER_KEY_FILE", Path.home() / "Desktop/Misc/key.txt"))
    imgs = page_images(path)
    content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{jpeg_b64(im)}"}}
               for im in imgs]
    cols = ("\nCorrection: here the two images are the LEFT and the RIGHT column of a two-column page "
            "(a register), not top and bottom. Transcribe the whole left column, then the whole right "
            "column; one entry per line.") if getattr(ARGS, "columns", False) else ""
    content.append({"type": "text", "text": PROMPT.format(n=len(imgs)) + cols
                    + "\nAnswer with the JSON object only."})
    t = time.monotonic()
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": "Bearer " + key.read_text(encoding="utf-8").strip()},
        json={"model": ARGS.model, "max_tokens": 32000,
              "messages": [{"role": "user", "content": content}],
              "response_format": {"type": "json_schema",
                                  "json_schema": {"name": "page", "strict": True, "schema": SCHEMA}},
              "reasoning": {"effort": ARGS.effort},
              "usage": {"include": True}},
        timeout=900)
    d = r.json()
    raw = DATA / "ocr" / "_raw" / f"{ARGS.model.split('/')[-1]}_{path.stem}.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    if not r.ok or "error" in d:
        raise RuntimeError(f"HTTP {r.status_code}: {d.get('error', d)}")
    ch = d["choices"][0]
    u = d.get("usage", {})
    if ch.get("finish_reason") not in ("stop", "end_turn"):
        raise RuntimeError(f"finish_reason={ch.get('finish_reason')}, cost ${u.get('cost', 0):.4f}")
    return {"blocks": parse_blocks(ch["message"]["content"]), "meta": {
        "engine": "openrouter", "model": d.get("model", ARGS.model), "provider": d.get("provider"),
        "effort": ARGS.effort, "reasoning_tokens":
            (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "images": [list(im.size) for im in imgs],
        "input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens"),
        "cost_usd": round(u.get("cost", 0), 4), "seconds": round(time.monotonic() - t, 1)}}


def run_claude(path: Path) -> dict:
    import anthropic

    imgs = page_images(path)
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                            "data": jpeg_b64(im)}} for im in imgs]
    content.append({"type": "text", "text": PROMPT.format(n=len(imgs))})
    client = anthropic.Anthropic()
    t = time.monotonic()
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
        output_config={"effort": ARGS.effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": content}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason != "end_turn":
        raise RuntimeError(f"stop_reason={msg.stop_reason} {getattr(msg, 'stop_details', '')}")
    text = next(b.text for b in msg.content if b.type == "text")
    u = msg.usage
    cost = (u.input_tokens * PRICE_IN + u.output_tokens * PRICE_OUT) / 1e6
    return {"blocks": parse_blocks(text), "meta": {
        "engine": "claude", "model": msg.model, "effort": ARGS.effort,
        "images": [list(im.size) for im in imgs],
        "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
        "cost_usd": round(cost, 4), "seconds": round(time.monotonic() - t, 1)}}


ENGINES = {"claude": run_claude, "openrouter": run_openrouter}


def to_md(page: dict, result: dict) -> str:
    out = [f"<!-- p. {page['label']}, scan {page['scan_index']}, "
           f"{result['meta'].get('model', result['meta']['engine'])} -->"]
    lrm = "‎"  # left-to-right mark: keeps a line that starts with Hebrew LTR on GitHub
    for b in result["blocks"]:
        text = lrm + b["text"].replace("\n", f"  \n{lrm}")  # keep printed line breaks
        if b["type"] == "heading":
            out.append(f"### {text}")
        elif b["type"] == "footnote":
            out.append(f"> {lrm}{b.get('marker', '')} {text}".replace("  \n", "  \n> "))
        elif b["type"] == "furniture":
            out.append(f"{lrm}*{text}*")
        else:
            out.append(text)
    return "\n\n".join(out) + "\n"


def main():
    global ARGS
    p = argparse.ArgumentParser()
    p.add_argument("engine", choices=ENGINES)
    p.add_argument("pages", nargs="*", help="page keys, e.g. 33 scan0013 (default: all in manifest)")
    p.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--model", help="openrouter model id, e.g. google/gemini-3.1-pro-preview")
    p.add_argument("--tag", default="", help="suffix for the output folder, e.g. a prompt version")
    p.add_argument("--force", action="store_true")
    p.add_argument("--columns", action="store_true", help="send the left and right column as two images (registers)")
    ARGS = p.parse_args()
    # output folder per engine; one folder per OpenRouter model
    name = f"or-{ARGS.model.split('/')[-1]}@{ARGS.effort}" if ARGS.engine == "openrouter" else ARGS.engine
    name += f"+{ARGS.tag}" if ARGS.tag else ""

    pages = json.loads((DATA / "raw" / "manifest.json").read_text(encoding="utf-8"))["pages"]
    if ARGS.pages:
        pages = [pg for pg in pages if Path(pg["file"]).stem in ARGS.pages]
    total, done = 0.0, 0
    for i, pg in enumerate(pages, 1):
        out = DATA / "ocr" / name / Path(pg["file"]).stem
        if out.with_suffix(".json").exists() and not ARGS.force:
            print(f"[{i}/{len(pages)}] {pg['file']}: done already", flush=True)
            continue
        try:
            res = ENGINES[ARGS.engine](DATA / pg["file"])
        except Exception as e:  # report and go on with the next page
            print(f"[{i}/{len(pages)}] {pg['file']}: FAILED {type(e).__name__}: {e}", flush=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        out.with_suffix(".md").write_text(to_md(pg, res), encoding="utf-8")
        total += res["meta"]["cost_usd"]
        done += 1
        print(f"[{i}/{len(pages)}] {pg['file']}: {len(res['blocks'])} blocks, "
              f"{res['meta']['seconds']} s, ${res['meta']['cost_usd']:.4f}", flush=True)
    print(f"{done} pages OCR'd this run, cost ${total:.4f}")


if __name__ == "__main__":
    main()
