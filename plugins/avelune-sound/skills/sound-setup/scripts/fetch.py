#!/usr/bin/env python3
"""fetch: download exactly the sounds a film needs, one by one, from three professional free sources.

Before the sound design the agent writes a SOUND PLAN (work/sound_plan.json): every sound the film needs, what it
is for, the search words, its length and character. This script searches the three sources for each line of the plan,
downloads only the best few matches, grades every file (real-sfx quality.py: D is deleted, C only for minor sounds)
and connects them to real-sfx. Nothing else is downloaded: no packs, no "starter libraries".

Sources (all allow commercial use and editing):
  sonniss    Sonniss GDC bundles: studio WAV from professional vendors, royalty-free, no attribution. The archives
             are huge, so the script reads only their table of contents (remotezip.py) into a local catalog once
             and then takes single files out of the archives over HTTP Range.
  freesound  Freesound API: rated 3.5+ by 3+ people, most downloaded first, CC0 / CC BY only. Free key:
             freesound.org/apiv2/apply -> sources.py freesound-key KEY. Originals after sources.py freesound-login.
  kenney     Kenney CC0 interface sounds (clicks, switches, confirmations) from their GitHub mirrors, file by file:
             first in line for click / ui / pop.
  (openverse is NOT used here: amateur recordings as 128 kbps previews. starter_library.py still has it.)

  python fetch.py template > work/sound_plan.json      # the plan format
  python fetch.py catalog                              # once: read the archive lists (a few MB, not the sounds)
  python fetch.py plan work/sound_plan.json --register # search + download + grade + connect, per plan line
  python fetch.py search "whoosh soft air" --role whoosh   # try the search words of one line first
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SKILLS / "real-sfx" / "scripts"))
import remotezip  # noqa: E402
import sources as src  # noqa: E402

HOME = Path.home() / ".avelune-sound"
CAT_DIR = HOME / "catalog"
OUT = HOME / "library" / "online"
AUDIO = re.compile(r"\.(wav|flac|aif|aiff|ogg|mp3)$", re.I)
SONNISS_PAGE = "https://gdc.sonniss.com/"
# the current year on the first page, 2015-2024 on the archive page; files on downloads.sonniss.com
SONNISS_PAGES = ["https://gdc.sonniss.com/", "https://sonniss.com/gameaudiogdc/"]

TEMPLATE = {
    "film": "<what the film is, one line>",
    "sounds": [
        {"id": "hook_whoosh", "for": "0:00.08 the card opens out of a line of light", "role": "whoosh",
         "query": ["whoosh air soft", "swoosh light fast"], "dur": [0.3, 1.5],
         "character": "soft, airy, bright, little low end", "avoid": ["horror", "monster"], "n": 3},
        {"id": "logo_hit", "for": "0:04.70 hero: the logo assembles", "role": "hit", "hero": True,
         "query": ["impact soft deep", "hit cinematic soft"], "dur": [0.5, 3.0],
         "character": "round soft punch, short tail, not a boom", "avoid": ["explosion", "gun"], "n": 4},
        {"id": "slot_reels", "for": "0:00.62-0:01.72 slot reels spin and stop", "role": "foley",
         "query": ["slot machine reel", "ratchet mechanism"], "dur": [0.5, 6.0],
         "character": "mechanical ticks, one recording for spin and stops", "n": 3},
    ],
    "avoid": ["<words no file of this film may carry: from concept.avoid, e.g. horror, gore, meme>"],
}

# role -> extra words a matching file name may carry (UCS category ids included: WHSH, IMPT, UI ...)
ROLE_WORDS = {
    "whoosh": ["whoosh", "swoosh", "swish", "whsh", "swsh", "pass", "swipe", "woosh"],
    "hit": ["impact", "hit", "punch", "thud", "slam", "impt", "boom", "stinger"],
    "impact": ["impact", "hit", "punch", "thud", "slam", "impt"],
    "riser": ["riser", "rise", "rising", "build", "tension", "swell", "uplifter"],
    "click": ["click", "button", "tap", "ui", "switch", "toggle", "select"],
    "ui": ["ui", "interface", "notification", "button", "click", "confirm", "beep"],
    "pop": ["pop", "bubble", "pluck", "plop"],
    "chime": ["chime", "bell", "ding", "sparkle", "shimmer", "twinkle", "magic", "magc", "glint"],
    "coin": ["coin", "coins", "money", "cash", "jackpot", "payout"],
    "foley": ["foley", "mechanism", "mechanical", "handle", "cloth", "object"],
    "glitch": ["glitch", "digital", "data", "error", "static"],
    "ambience": ["ambience", "amb", "room", "tone", "roomtone", "atmos", "background"],
    "paper": ["paper", "page", "book", "rustle"],
    "typing": ["typing", "keyboard", "keys", "type"],
}


def tokens(text):
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)          # UIClick -> UI Click, WHSHAir -> WHSH Air
    return [w for w in re.split(r"[^a-z0-9]+", t.lower()) if w]


# ------------------------------------------------------------------ catalogs
def _cat_path(source):
    return CAT_DIR / f"{source}.json"


def load_catalog(source):
    try:
        return json.loads(_cat_path(source).read_text("utf-8"))
    except (OSError, ValueError):
        return {"archives": []}


def sonniss_archives():
    """Direct .zip links of every GDC bundle still served (about 75 archives, ~200 GB: only their lists are read)."""
    urls = set()
    for page in SONNISS_PAGES:
        try:
            html = src._get(page, binary=False, headers={"User-Agent": remotezip.UA})
        except Exception as e:
            print(f"  sonniss: {page} not read ({e})")
            continue
        for u in re.findall(r'href="([^"]+?\.zip)"', html, re.I):
            u = urllib.parse.urljoin(page, u.replace("&amp;", "&"))
            if urllib.parse.urlparse(u).netloc.endswith("downloads.sonniss.com"):
                urls.add(u)
    return sorted(urls)


def _label(url):
    return urllib.parse.unquote(Path(urllib.parse.urlparse(url).path).stem).replace("Sonniss.com", "").strip(" -")


def build_catalog(log=print):
    """Read the table of contents of every Sonniss GDC archive (a few KB each, over HTTP Range) into
    ~/.avelune-sound/catalog/sonniss.json, and list the Kenney mirrors. Archives already listed are skipped."""
    CAT_DIR.mkdir(parents=True, exist_ok=True)
    cat = load_catalog("sonniss")
    known = {a["url"] for a in cat["archives"]}
    urls = sonniss_archives()
    if not urls:
        log("sonniss: no archive links found on " + ", ".join(SONNISS_PAGES))
    for url in urls:
        if url in known:
            continue
        try:
            ms = remotezip.list_members(url)
        except Exception as e:
            log(f"  sonniss {_label(url)}: not listed ({e})")
            continue
        files = [{"p": m["name"], "s": m["size"], "c": m["csize"], "o": m["offset"], "m": m["method"],
                  "crc": m["crc"], "f": m["flags"]} for m in ms if AUDIO.search(m["name"])]
        cat["archives"].append({"label": _label(url), "url": url, "files": files, "listed": time.strftime("%Y-%m-%d")})
        log(f"  sonniss {_label(url)}: {len(files)} sounds")
        _cat_path("sonniss").write_text(json.dumps(cat, ensure_ascii=False), "utf-8")
    _cat_path("sonniss").write_text(json.dumps(cat, ensure_ascii=False), "utf-8")
    n = sum(len(a["files"]) for a in cat["archives"])
    log(f"sonniss: {len(cat['archives'])} archive(s), {n} sounds in the catalog")
    k = src.kenney_files(log=log)
    log(f"kenney: {len(k)} UI sounds listed")


def _has(w, pt):
    return w in pt or (len(w) >= 4 and any(x.startswith(w) for x in pt))


def _score(want, rw, path, avoid=()):
    """How well a file path fits the search words. The first word is the thing itself (impact, whoosh, coin): it,
    or a word of the role, must be in the path; a match on an adjective alone (soft, deep) does not count."""
    pt = set(tokens(path))
    if any(_has(w, pt) for w in avoid):
        return 0.0
    name_t = set(tokens(Path(path).stem))
    found = [w for w in set(want) if _has(w, pt)]
    if not found or not ((want and _has(want[0], pt)) or rw & pt):
        return 0.0
    return 2.0 * len(found) / max(1, len(set(want))) + 0.5 * sum(1 for w in found if w in name_t) + \
        (0.8 if rw & pt else 0.0)


def search_catalog(source, query_words, role, n=10, max_mb=40.0, avoid=()):
    """Best files for ONE line of the plan. Every search phrase is scored on its own and a file keeps its best."""
    best = {}
    for phrase in query_words:
        for sc, a, f in _search_one(source, phrase, role, max_mb, [w for x in avoid for w in tokens(x)]):
            k = (a["label"], f["p"])
            if k not in best or sc > best[k][0]:
                best[k] = (sc, a, f)
    hits = sorted(best.values(), key=lambda h: (-h[0], h[2].get("s", 0)))
    return hits[:n]


def _search_one(source, phrase, role, max_mb, avoid):
    want = [w for w in tokens(phrase) if len(w) > 1]
    rw = set(ROLE_WORDS.get(role, []))
    if source == "kenney":
        hits = []
        for repo, path, size in src.kenney_files(log=lambda *_: None):
            sc = _score(want, rw, path, avoid)
            if sc > 0:
                hits.append((sc, {"label": repo, "url": None, "repo": repo}, {"p": path, "s": size}))
        return hits
    hits = []
    for a in load_catalog(source)["archives"]:
        for f in a["files"]:
            if f["s"] > max_mb * 1e6:                 # 100-200 MB ambience takes: too big to fetch for one cue
                continue
            score = _score(want, rw, f["p"], avoid)
            if score > 0:
                hits.append((score, a, f))
    return hits


# ------------------------------------------------------------------ plan
def _safe(name):
    return re.sub(r"[^\w\-. ]+", "_", name).strip()[:90]


def take_archive_file(source, a, f, dst_dir, role, log):
    dst = dst_dir / f"{source}_{_safe(Path(f['p']).name)}"
    if source == "kenney":
        try:
            r = src.kenney_take(a["repo"], f["p"], dst, role, log)
        except Exception as e:
            log(f"     kenney: {Path(f['p']).name}: not taken ({e})")
            return None, None
        return (dst, r) if r else (None, None)
    if not dst.exists():
        m = {"name": f["p"], "method": f["m"], "csize": f["c"], "size": f["s"], "offset": f["o"], "crc": f["crc"],
             "flags": f.get("f", 0)}
        try:
            remotezip.extract(a["url"], m, dst)
        except Exception as e:
            log(f"     {source}: {Path(f['p']).name}: not taken ({e})")
            return None, None
    q = src.keep_or_drop(dst, role, log)
    if q is None:
        return None, None
    lic = "cc0" if source == "kenney" else "sonniss-gdc"
    row = {"id": f"{source}:{a['label']}:{f['p']}", "file": dst.name, "title": Path(f["p"]).stem,
           "creator": "Kenney (kenney.nl)" if source == "kenney" else f"Sonniss GDC bundle ({a['label']})",
           "license": lic, "license_version": "", "landing": "https://kenney.nl" if source == "kenney" else SONNISS_PAGE,
           "source": source, "grade": q.get("grade"), "downloaded": time.strftime("%Y-%m-%d")}
    return dst, row


def run_plan(plan_path, out=OUT, register=False, tier="main", log=print):
    plan = json.loads(Path(plan_path).read_text("utf-8-sig"))
    if "<" in json.dumps({k: plan.get(k) for k in ("film", "avoid")}):
        sys.exit("fill the plan first (fetch.py template shows the format)")
    out = Path(out)
    report, credits_all = [], []
    have_cat = bool(load_catalog("sonniss")["archives"])
    if not have_cat:
        log("no archive catalogs yet: reading them once (fetch.py catalog)")
        build_catalog(log=log)
    for item in plan.get("sounds", []):
        role = item.get("role") or "foley"
        q = item.get("query") or [item.get("id", role)]
        lo, hi = (item.get("dur") or [0.05, 8.0])[:2]
        n = int(item.get("n") or 3)
        hero = bool(item.get("hero"))
        avoid = list(item.get("avoid") or []) + list(plan.get("avoid") or [])
        d = out / _safe(item.get("id") or role)
        d.mkdir(parents=True, exist_ok=True)
        log(f"\n[{item.get('id')}] {role}: {', '.join(q)}  ({item.get('for', '')})")
        kept = []
        # studio files first, then rated Freesound, then Kenney (clean but game-like) for UI roles
        order = ["sonniss", "freesound", "kenney"]
        if role in ("click", "ui", "pop"):
            order = ["kenney", "sonniss", "freesound"]
        for source in order:
            if len(kept) >= n:
                break
            if source == "freesound":
                rows = src.freesound(role, q, lo, hi, n - len(kept), d.parent, log=log) if src.fs_key() else []
                if not src.fs_key():
                    log("   freesound: no key (sources.py status): skipped")
                for r in rows:                       # freesound() writes into <out>/<role>/: move to the plan line
                    p = d.parent / role / r["file"]
                    if p.exists() and p.parent != d:
                        p.replace(d / r["file"])
                    kept.append(r)
                continue
            for score, a, f in search_catalog(source, q, role, n=4 * n, avoid=avoid):
                if len(kept) >= n:
                    break
                dst, row = take_archive_file(source, a, f, d, role, log)
                if row is None:
                    continue
                if row["grade"] == "C" and hero:
                    log(f"     skip for the hero (grade C): {dst.name}")
                    continue
                kept.append(row)
                log(f"   {source:<9} {row['grade']}  {dst.name[:70]}")
        (d / "credits.json").write_text(json.dumps(kept, ensure_ascii=False, indent=1), "utf-8")
        for r in kept:
            r2 = dict(r)
            r2["file"] = f"{d.name}/{r['file']}"
            credits_all.append((role, r2))
        report.append((item, kept))
    # catalog.csv + CREDITS.md for real-sfx and for the video description
    import csv
    sys.path.insert(0, str(SKILLS / "openverse" / "scripts"))
    import openverse as ov
    cat = out / "catalog.csv"
    rows = []
    if cat.exists():
        with open(cat, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    files = {r2["file"] for _, r2 in credits_all}
    rows = [r for r in rows if r["file"] not in files] + [
        {"file": r2["file"], "type": _type(role), "source": r2.get("title") or r2["file"], "hit": "", "hits_in_source": ""}
        for role, r2 in credits_all]
    with open(cat, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "type", "source", "hit", "hits_in_source"])
        w.writeheader()
        w.writerows(rows)
    allc = []
    for sub in sorted(p for p in out.iterdir() if p.is_dir()):
        cj = sub / "credits.json"
        if cj.exists():
            for c in json.loads(cj.read_text("utf-8")):
                c["file"] = f"{sub.name}/{c['file']}"
                allc.append(c)
    (out / "CREDITS.md").write_text(ov.credits_md(allc), "utf-8")
    log("\nPLAN RESULT")
    missing = []
    for item, kept in report:
        g = "".join(sorted(r.get("grade") or "?" for r in kept))
        srcs = ",".join(sorted({r["source"] for r in kept}))
        log(f"  {item.get('id', ''):<16} {len(kept)}/{item.get('n', 3)}  grades {g or '-':<6} {srcs}")
        if not kept:
            missing.append(item.get("id"))
    if missing:
        log("  NOTHING FOUND for: " + ", ".join(missing) + " -> other search words (fetch.py search ...), "
            "your own library, or silence there and a line in the report")
    if register:
        setup = SKILLS / "real-sfx" / "scripts" / "setup.py"
        subprocess.call([sys.executable, str(setup), "add-library", "online", str(out), "--tier", tier, "--index"],
                        env=dict(os.environ, PYTHONUTF8="1"))
    else:
        log(f'connect: python "{SKILLS / "real-sfx" / "scripts" / "setup.py"}" add-library online "{out}" --tier {tier} --index')


def _type(role):
    # real-sfx catalog types (build_index.PACK_TYPE_ROLES)
    return {"hit": "impact", "impact": "impact", "thump": "impact", "click": "click", "ui": "ui", "pop": "pop",
            "chime": "chime", "coin": "chime", "whoosh": "whoosh", "riser": "riser", "foley": "foley",
            "glitch": "glitch", "ambience": "ambience", "paper": "paper", "typing": "typing"}.get(role, "other")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template")
    sub.add_parser("catalog")
    p = sub.add_parser("plan")
    p.add_argument("plan")
    p.add_argument("--out", default=str(OUT))
    p.add_argument("--register", action="store_true")
    p.add_argument("--tier", choices=["main", "extra"], default="main")
    s = sub.add_parser("search")
    s.add_argument("query", nargs="+")
    s.add_argument("--role", default="foley")
    s.add_argument("--n", type=int, default=12)
    a = ap.parse_args()
    if a.cmd == "template":
        print(json.dumps(TEMPLATE, ensure_ascii=False, indent=1))
    elif a.cmd == "catalog":
        build_catalog()
    elif a.cmd == "plan":
        run_plan(a.plan, a.out, a.register, a.tier)
    elif a.cmd == "search":
        for source in ("sonniss", "kenney"):
            for score, arc, f in search_catalog(source, [" ".join(a.query)], a.role, a.n):
                print(f"{source:<8} {score:4.1f}  {f['s'] / 1e6:6.2f} MB  {arc['label'][:24]:<24} {f['p'][:90]}")
        if src.fs_key():
            for h in (src.fs_search(" ".join(a.query), 0.05, 30) or [])[:a.n]:
                print(f"freesound {h.get('avg_rating', 0):.1f}*  {h.get('num_downloads', 0):>6} dl  "
                      f"{src._fs_lic(h.get('license')) or 'NC':<4} {h.get('name', '')[:70]}")
        else:
            print("freesound: no key (sources.py status)")


if __name__ == "__main__":
    main()
