#!/usr/bin/env python3
"""Openverse audio search and download with licence tracking. Standard library only.

  python openverse.py search "whoosh" --license cc0 --category sound_effect --max-dur 3
  python openverse.py search "door creak" --commercial --source freesound --json > hits.json
  python openverse.py get ID [ID ...] --out sfx/          # downloads + writes sfx/CREDITS.md and sfx/credits.json
  python openverse.py credits sfx/                         # prints the attribution block for a video description

Optional: OPENVERSE_TOKEN (bearer token from /v1/auth_tokens/token/) for higher rate limits.
Openverse: https://openverse.org, API https://api.openverse.org/v1/ . Each sound keeps its own licence: check it.
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

API = os.environ.get("OPENVERSE_API", "https://api.openverse.org/v1")
UA = "avelune-sound-openverse/1.0 (+https://github.com/angelmaycrv/avelune-labs)"
# Safe for commercial work that edits the sound (trim, pitch, layer): no NC, no ND, no Sampling+ (bans advertising).
SAFE = {"cc0", "pdm", "by"}
# Allowed with care: BY-SA makes the derived sound share-alike too.
CAREFUL = {"by-sa": "share-alike: the edited sound must carry BY-SA as well"}
ATTRIBUTION_FREE = {"cc0", "pdm"}


def _req(url, binary=False, tries=3):
    headers = {"User-Agent": UA, "Accept": "*/*" if binary else "application/json"}
    tok = os.environ.get("OPENVERSE_TOKEN")
    if tok and url.startswith(API):
        headers["Authorization"] = f"Bearer {tok}"
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                data = r.read()
                return data if binary else json.loads(data.decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:  # rate limited: back off
                time.sleep(5 * (i + 1)); continue
            if e.code >= 500:
                time.sleep(2 * (i + 1)); continue
            raise SystemExit(f"Openverse HTTP {e.code} for {url}: {e.read()[:300]!r}")
        except urllib.error.URLError as e:
            last = e; time.sleep(2 * (i + 1))
    raise SystemExit(f"Openverse request failed: {last}")


def search(a):
    p = {"q": a.query, "page_size": a.n, "page": a.page}
    if a.license: p["license"] = a.license
    if a.commercial: p["license_type"] = "commercial,modification"
    if a.category: p["category"] = a.category
    if a.source: p["source"] = a.source
    if a.length: p["length"] = a.length
    if a.extension: p["extension"] = a.extension
    data = _req(f"{API}/audio/?{urllib.parse.urlencode(p)}")
    hits = []
    for r in data.get("results", []):
        dur = (r.get("duration") or 0) / 1000.0  # Openverse reports milliseconds
        if a.max_dur and dur and dur > a.max_dur: continue
        if a.min_dur and dur and dur < a.min_dur: continue
        hits.append({k: r.get(k) for k in ("id", "title", "creator", "creator_url", "license", "license_version",
                                           "license_url", "source", "provider", "category", "filetype", "url",
                                           "foreign_landing_url", "attribution", "tags")} | {"duration_s": round(dur, 2)})
    if a.json:
        print(json.dumps({"count": data.get("result_count"), "results": hits}, ensure_ascii=False, indent=1))
        return
    print(f"{data.get('result_count', 0)} matches, showing {len(hits)}")
    for h in hits:
        lic = f"{h['license']}{' ' + h['license_version'] if h.get('license_version') else ''}"
        flag = "" if h["license"] in SAFE else ("  [SA]" if h["license"] in CAREFUL else "  [not for commercial edits]")
        print(f"{h['id']}  {h['duration_s']:>6.2f}s  {lic:<10} {h['source'] or '':<14} {(h['title'] or '')[:60]}{flag}")


def _slug(s):
    s = re.sub(r"[^\w\-]+", "_", s or "sound", flags=re.U).strip("_")
    return s[:60] or "sound"


def get(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    credits_json = out / "credits.json"
    credits = json.loads(credits_json.read_text("utf-8")) if credits_json.exists() else []
    known = {c["id"] for c in credits}
    for i in a.ids:
        r = _req(f"{API}/audio/{i}/")
        lic = r.get("license")
        if lic in CAREFUL:
            print(f"note {i}: {lic}: {CAREFUL[lic]}")
        elif lic not in SAFE and not a.allow_any:
            print(f"skip {i}: licence {lic} limits commercial or edited use (NC, ND or Sampling+); --allow-any for personal work")
            continue
        url = r.get("url")
        if not url:
            print(f"skip {i}: no file url"); continue
        ext = (r.get("filetype") or Path(urllib.parse.urlparse(url).path).suffix.lstrip(".") or "mp3").lower()
        f = out / f"{_slug(r.get('title'))}__{i[:8]}.{ext}"
        if not f.exists():
            f.write_bytes(_req(url, binary=True))
        print(f"ok  {f.name}  ({r.get('license')}, {r.get('source')})")
        if i not in known:
            credits.append({"id": i, "file": f.name, "title": r.get("title"), "creator": r.get("creator"),
                            "creator_url": r.get("creator_url"), "license": r.get("license"),
                            "license_version": r.get("license_version"), "license_url": r.get("license_url"),
                            "source": r.get("source"), "landing": r.get("foreign_landing_url"),
                            "attribution": r.get("attribution"), "downloaded": time.strftime("%Y-%m-%d")})
    credits_json.write_text(json.dumps(credits, ensure_ascii=False, indent=1), "utf-8")
    (out / "CREDITS.md").write_text(credits_md(credits), "utf-8")
    print(f"credits: {out / 'CREDITS.md'}")


def credits_md(credits):
    lines = ["# Sound credits", "", "Sounds found via Openverse (openverse.org). Each keeps its own licence.", ""]
    for c in credits:
        lic = f"{(c.get('license') or '').upper()} {c.get('license_version') or ''}".strip()
        need = "" if c.get("license") in ATTRIBUTION_FREE else " (attribution required)"
        lines.append(f"- \"{c.get('title')}\" by {c.get('creator') or 'unknown'} — {lic}{need} — "
                     f"{c.get('landing') or ''} — file {c.get('file')}")
    return "\n".join(lines) + "\n"


def credits(a):
    p = Path(a.dir) / "credits.json"
    if not p.exists(): raise SystemExit(f"no {p}")
    cs = [c for c in json.loads(p.read_text("utf-8")) if c.get("license") not in ATTRIBUTION_FREE]
    if not cs:
        print("All sounds are CC0 / public domain: no attribution required (still appreciated)."); return
    print("Sounds:")
    for c in cs:
        print(f"\"{c.get('title')}\" by {c.get('creator')}, {(c.get('license') or '').upper()} "
              f"{c.get('license_version') or ''}, {c.get('landing') or ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="search audio")
    s.add_argument("query")
    s.add_argument("--license", help="comma list: cc0,pdm,by,by-sa,by-nd,by-nc,by-nc-sa,by-nc-nd,sampling+,nc-sampling+")
    s.add_argument("--commercial", action="store_true", help="only licences that allow commercial use and modification")
    s.add_argument("--category", help="e.g. sound_effect, music, podcast")
    s.add_argument("--source", help="e.g. freesound, jamendo, wikimedia_audio")
    s.add_argument("--length", choices=["shortest", "short", "medium", "long"])
    s.add_argument("--extension", help="e.g. wav, mp3, ogg, flac")
    s.add_argument("--min-dur", type=float, help="seconds")
    s.add_argument("--max-dur", type=float, help="seconds")
    s.add_argument("-n", type=int, default=20, help="results per page (anonymous max is 20)")
    s.add_argument("--page", type=int, default=1)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=search)
    g = sub.add_parser("get", help="download by id and record credits")
    g.add_argument("ids", nargs="+"); g.add_argument("--out", default="sfx")
    g.add_argument("--allow-any", action="store_true", help="also download NC / ND / Sampling+ sounds (personal work)")
    g.set_defaults(fn=get)
    c = sub.add_parser("credits", help="print attribution text"); c.add_argument("dir"); c.set_defaults(fn=credits)
    a = ap.parse_args()
    if sys.version_info < (3, 9): raise SystemExit("Python 3.9+ needed")
    a.fn(a)


if __name__ == "__main__":
    main()
