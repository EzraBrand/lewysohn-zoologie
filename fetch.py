"""Fetch page images of Lewysohn, Die Zoologie des Talmuds (1858), from the Frankfurt UB IIIF server.

  uv run fetch.py list --from 1 --to 20         # scan index, label, image id
  uv run fetch.py preview 13 15 16              # 1000px previews for picking pages
  uv run fetch.py sample                        # full-res sample set + data/raw/manifest.json

Scan index = 1-based position in the IIIF manifest (same as the viewer's page counter).
Printed page = scan index - 14 for the main text (p. 1 is scan 15).
All responses are cached; requests are sequential with a delay.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://sammlungen.ub.uni-frankfurt.de"
RECORD = "https://nbn-resolving.org/urn:nbn:de:hebis:30:1-113735"
RECORD_ID = 1043079
DELAY = 2.0
DATA = Path(__file__).parent / "data"

# (scan index, why). Picked from previews; see README.
SAMPLE = [
    (13, "toc"),  # Inhalt: one page, unnumbered
    *[(s, "entry") for s in range(82, 86)],  # pp. 68-71: §§ 114-115, lion and tiger (test entry)
]

session = requests.Session()
session.headers["User-Agent"] = "lewysohn-zoologie OCR research (personal research; sequential, cached)"
_last = 0.0


def get(url: str) -> requests.Response:
    global _last
    wait = DELAY - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    r = session.get(url, timeout=120)
    _last = time.monotonic()
    r.raise_for_status()
    return r


def manifest() -> dict:
    path = DATA / "cache" / "manifests" / f"{RECORD_ID}.json"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(get(f"{BASE}/i3f/v20/{RECORD_ID}/manifest").content)
    return json.loads(path.read_text(encoding="utf-8"))


def canvases() -> list[dict]:
    out = []
    for i, c in enumerate(manifest()["sequences"][0]["canvases"], start=1):
        res = c["images"][0]["resource"]
        out.append({
            "scan_index": i,
            "label": c["label"],
            # "[13]" = unnumbered page; the number is the scan index, not a page number.
            "printed_page": None if c["label"].startswith("[") else c["label"],
            "image_id": res["service"]["@id"].rsplit("/", 1)[-1],
            "width": c["width"],
            "height": c["height"],
        })
    return out


def page_key(c: dict) -> str:
    return c["printed_page"] or f"scan{c['scan_index']:04d}"


def download(url: str, path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    tmp.write_bytes(get(url).content)
    tmp.replace(path)
    print(f"  saved {path.relative_to(DATA.parent)}", flush=True)


def cmd_list(a):
    for c in canvases():
        if a.start <= c["scan_index"] <= a.to:
            print(f"{c['scan_index']:4d}  {c['label']:>8}  {c['image_id']}")


def cmd_preview(a):
    cs = canvases()
    for i in a.scan:
        c = cs[i - 1]
        download(f"{BASE}/i3f/v20/{c['image_id']}/full/1000,/0/default.jpg",
                 DATA / "preview" / f"{i:04d}_{page_key(c)}.jpg")


def cmd_sample(a):
    records = []
    cs = canvases()
    for scan, why in SAMPLE:
        c = cs[scan - 1]
        url = f"{BASE}/i3f/v20/{c['image_id']}/full/full/0/default.jpg"
        path = DATA / "raw" / f"{page_key(c)}.jpg"
        print(f"scan {scan} = p. {c['label']} ({why})", flush=True)
        download(url, path)
        records.append({**c, "kind": why, "source_url": url, "file": path.relative_to(DATA).as_posix()})
    out = {"work": "Lewysohn, Die Zoologie des Talmuds (1858)", "record": RECORD,
           "licence": "Public Domain Mark 1.0", "record_id": RECORD_ID, "pages": records}
    (DATA / "raw" / "manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(records)} pages; manifest at data/raw/manifest.json")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(required=True)
    s = sub.add_parser("list")
    s.add_argument("--from", dest="start", type=int, default=1)
    s.add_argument("--to", type=int, default=10**6)
    s.set_defaults(func=cmd_list)
    s = sub.add_parser("preview")
    s.add_argument("scan", type=int, nargs="+")
    s.set_defaults(func=cmd_preview)
    s = sub.add_parser("sample")
    s.set_defaults(func=cmd_sample)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
