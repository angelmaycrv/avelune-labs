#!/usr/bin/env python3
"""starter_library: REAL recordings fetched per role for the film at hand, sorted by role, ready for real-sfx.

Sources in order (sources.py): Kenney CC0 packs (clean, small), Freesound rated 3.5+ and most downloaded (free API key;
originals after a one-time login), then Openverse. Every download is graded (real-sfx quality.py) and grade D is
deleted; a role counts as covered only by grade A/B sounds, so a library of previews gets better ones fetched.

For when the user has no sound folder, or theirs lacks a role (no risers, no paper, no room tone).
Only licences that allow commercial use and editing (CC0, PDM, CC BY); CREDITS.md is written beside the sounds.

  python starter_library.py --dry                       # what it would fetch, nothing downloaded
  python starter_library.py --register                  # fetch ~6 sounds per role, connect them to real-sfx, index
  python starter_library.py --roles whoosh,riser,paper --per-role 8 --register --tier extra
  python starter_library.py --out "D:/Sounds/starter"   # another place (default ~/.avelune-sound/library/starter)
  # what a film needs and the libraries lack: kinds of the event list (BEFORE from_cues.py, which drops kinds it
  # has no sound for) or roles of a cue sheet, with fewer than 3 sounds in the index
  python starter_library.py --for-cues work/events.json --register
  # one unusual moment (a door creak, a camera shutter): own search words for one role
  python starter_library.py --role foley --query "door creak" --query "old door squeak" --register

After the download, if earshot is installed, drop what reads as code-synthesized:
  earshot realness "<out>/whoosh"     (keep 'likely real', read the evidence of 'uncertain')
Openverse files from Freesound are 128 kbps previews (grade C): for a hero sound take the original from the landing
page listed in CREDITS.md, or set up the Freesound key.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
sys.path.insert(0, str(SKILLS / "openverse" / "scripts"))
sys.path.insert(0, str(HERE))
import openverse as ov  # noqa: E402

# role (the real-sfx catalog type) -> search words, duration window (s), category
# category stays None: Openverse leaves it empty for Freesound, so category=sound_effect finds nothing there
ROLES = {
    "whoosh":   (["whoosh", "swoosh", "swish fast"], 0.2, 2.5, None),
    "impact":   (["impact hit", "thud", "punch impact", "wood hit"], 0.1, 2.5, None),
    "riser":    (["riser", "rising whoosh", "tension rise"], 1.5, 8.0, None),
    "pop":      (["pop", "bubble pop", "cork pop"], 0.03, 1.0, None),
    "click":    (["mouse click", "button click", "switch click"], 0.02, 1.0, None),
    "typing":   (["keyboard typing", "typing keys"], 1.0, 20.0, None),
    "paper":    (["paper rustle", "page turn", "paper crumple"], 0.2, 4.0, None),
    "chime":    (["chime", "bell ding", "glass ding"], 0.2, 4.0, None),
    "glitch":   (["glitch", "static burst"], 0.1, 2.0, None),
    "foley":    (["cloth movement", "footstep", "object drop"], 0.1, 3.0, None),
    "ambience": (["room tone", "ambience wind", "city ambience distant"], 20.0, 180.0, None),
}


# real-sfx cue roles -> the catalog type that feeds them
CUE_ROLE_TYPE = {"hit": "impact", "thump": "impact", "impact": "impact", "whoosh": "whoosh", "riser": "riser",
                 "pop": "pop", "click": "click", "ui": "click", "key": "typing", "typing": "typing",
                 "paper": "paper", "chime": "chime", "bell": "chime", "glass": "chime", "glitch": "glitch",
                 "error": "glitch", "foley": "foley", "ambience": "ambience", "wipe": "whoosh", "swish": "whoosh",
                 "thud": "impact", "boom": "impact", "tick": "click", "step": "foley", "cloth": "foley",
                 "room": "ambience", "atmosphere": "ambience", "coin": "chime", "coins": "chime", "money": "chime",
                 "cash": "chime", "win": "chime", "magic": "chime", "sparkle": "chime", "shimmer": "chime",
                 "reveal": "chime", "spin": "foley", "ratchet": "foley", "slot": "foley", "reel": "foley",
                 "door": "foley", "drop": "impact", "sub_drop": "impact", "transition": "whoosh", "swoosh": "whoosh",
                 "notification": "pop", "toggle": "click", "button": "click", "tap": "click"}


def needed_roles(cues_path, min_have=3):
    """Catalog types the cue sheet asks for and the indexed libraries hold fewer than `min_have` sounds of."""
    sys.path.insert(0, str(SKILLS / "real-sfx" / "scripts"))
    import common
    d = json.loads(Path(cues_path).read_text(encoding="utf-8-sig"))
    cues = d.get("cues", d) if isinstance(d, dict) else d
    want, unknown = {}, set()
    for c in cues:
        if not isinstance(c, dict) or c.get("uisfx") or c.get("file") or c.get("id") is not None:
            continue
        r = (c.get("pick") or {}).get("role") or c.get("role") or c.get("type") or c.get("kind")
        if r in CUE_ROLE_TYPE:
            want[CUE_ROLE_TYPE[r]] = want.get(CUE_ROLE_TYPE[r], 0) + 1
        elif r:
            unknown.add(str(r))
    have = {}
    try:
        idx = json.loads(common.index_path().read_text(encoding="utf-8"))
        for snd in idx.get("sounds", []):
            if (snd.get("q") or {}).get("grade") in ("C", "D"):
                continue                       # preview-grade or broken: does not count as having the role
            for r in snd.get("roles") or [snd.get("role")]:
                t = CUE_ROLE_TYPE.get(r)
                if t:
                    have[t] = have.get(t, 0) + 1
    except Exception:
        pass
    for t, n in sorted(want.items()):
        print(f"  {t}: {n} cue(s), {have.get(t, 0)} good sound(s) (grade A/B) in the libraries")
    if unknown:
        print(f"  not checked (no catalog type for these kinds): {', '.join(sorted(unknown))}: fetch them by hand "
              f"with --role TYPE --query WORDS if the libraries lack them")
    return [t for t in want if have.get(t, 0) < min_have], bool(have)


def pick(role, per_role, quiet, queries=None):
    words, lo, hi, cat = ROLES[role]
    if queries:
        words = queries
    seen, picks = set(), []
    for w in words:
        args = argparse.Namespace(query=w, license="cc0,pdm,by", commercial=True, category=cat, source=None,
                                  length=None, extension=None, min_dur=lo, max_dur=hi, n=20, page=1, json=True)
        import io
        import contextlib
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ov.search(args)
        except SystemExit as e:
            if not quiet:
                print(f"  {role}: search '{w}' failed: {e}")
            continue
        res = json.loads(buf.getvalue() or "{}").get("results", [])
        if not res and not quiet:
            print(f"  {role}: Openverse answered, but nothing for '{w}' in {lo}-{hi} s (CC0/PDM/BY)")
        for h in res:
            if h["id"] in seen or h.get("license") not in ov.SAFE:
                continue
            seen.add(h["id"])
            picks.append(h)
        if len(picks) >= per_role * 2:
            break
        time.sleep(0.5)
    # prefer lossless files and the middle of the duration window
    mid = (lo + min(hi, lo * 4)) / 2
    picks.sort(key=lambda h: ((h.get("filetype") or "") not in ("wav", "flac", "aiff"),
                              abs((h.get("duration_s") or mid) - mid)))
    return picks[:per_role]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(Path.home() / ".avelune-sound" / "library" / "starter"))
    ap.add_argument("--roles", default=",".join(ROLES), help="comma list of: " + ", ".join(ROLES))
    ap.add_argument("--per-role", type=int, default=6)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--register", action="store_true", help="connect to real-sfx and build the index")
    ap.add_argument("--tier", choices=["main", "extra"], default=None,
                    help="extra when the user has a library of their own: then these fill only the gaps "
                         "(default: extra with --for-cues / --query, main otherwise)")
    ap.add_argument("--for-cues", help="fetch only the roles this cue sheet needs and the libraries lack")
    ap.add_argument("--role", help="with --query: the catalog type the sounds are filed under")
    ap.add_argument("--query", action="append", help="own search words (English), with --role")
    ap.add_argument("--name", help="library name in real-sfx (default starter, or openverse for gaps)")
    ap.add_argument("--source", choices=["auto", "kenney", "freesound", "openverse"], default="auto",
                    help="auto (default): Kenney, then rated Freesound, then Openverse for the rest")
    a = ap.parse_args()
    gap_mode = bool(a.for_cues or a.query)
    name = a.name or ("openverse" if gap_mode else "starter")
    tier = a.tier or ("extra" if gap_mode else "main")
    out = Path(a.out if a.out != ap.get_default("out") or not gap_mode
               else str(Path.home() / ".avelune-sound" / "library" / "openverse"))
    if a.for_cues:
        roles, has_lib = needed_roles(a.for_cues)
        if not has_lib:
            tier = a.tier or "main"
        if not roles:
            print("nothing to fetch: every role of the sheet has 3+ sounds in the libraries")
            return
        print("fetching for: " + ", ".join(roles))
    elif a.query:
        if not a.role:
            sys.exit("--query needs --role (one of: " + ", ".join(ROLES) + ")")
        roles = [a.role]
    else:
        roles = [r.strip() for r in a.roles.split(",") if r.strip()]
    bad = [r for r in roles if r not in ROLES]
    if bad:
        sys.exit(f"unknown roles: {bad}; known: {', '.join(ROLES)}")
    import sources as src
    rows, total = [], 0
    for role in roles:
        d = out / role
        got = []                                         # credit rows of this run for this role
        words, lo, hi, _ = ROLES[role]
        if a.query:
            words = a.query
        # 1. Kenney (clean CC0 game/app packs, a few MB, only the packs this role needs)
        if a.source in ("auto", "kenney") and role in src.KENNEY and not a.dry:
            got += src.kenney(role, out)
        # 2. Freesound, rated and most downloaded first (needs the free key)
        if a.source in ("auto", "freesound") and len(got) < a.per_role and not a.dry:
            got += src.freesound(role, words, lo, min(hi, 30.0), a.per_role - len(got) if a.source == "auto"
                                 else a.per_role, out)
        # 3. Openverse for what is still missing (128 kbps previews: grade C, minor sounds only)
        need = a.per_role - len(got) if a.source == "auto" else (a.per_role if a.source == "openverse" else 0)
        if need > 0:
            picks = pick(role, need, False, a.query if a.query else None)
            print(f"{role}: openverse {len(picks)} found")
            for h in picks:
                print(f"   {h['id'][:8]}  {h.get('duration_s', 0):>6.2f}s  {h['license']:<4} {h.get('source') or '':<12} "
                      f"{(h.get('title') or '')[:50]}")
            if picks and not a.dry:
                g = argparse.Namespace(ids=[h["id"] for h in picks], out=str(d), allow_any=False)
                try:
                    ov.get(g)
                except SystemExit as e:
                    print(f"  {role}: download stopped: {e}")
                ids = {h["id"] for h in picks}
                cj = d / "credits.json"
                for c in (json.loads(cj.read_text("utf-8")) if cj.exists() else []):
                    if c.get("id") in ids and (d / c["file"]).exists():
                        q = src.keep_or_drop(d / c["file"], role, print)
                        if q is not None:
                            c["grade"] = q.get("grade")
                            got.append(c)
        if a.dry:
            continue
        cj = d / "credits.json"
        old_c = json.loads(cj.read_text("utf-8")) if cj.exists() else []
        mine = {c["file"] for c in got}
        merged = [c for c in old_c if c["file"] not in mine and (d / c["file"]).exists()] + got
        if merged:
            d.mkdir(parents=True, exist_ok=True)
            cj.write_text(json.dumps(merged, ensure_ascii=False, indent=1), "utf-8")
        grades = {}
        for c in got:
            grades[c.get("grade", "?")] = grades.get(c.get("grade", "?"), 0) + 1
        print(f"{role}: {len(got)} kept " + " ".join(f"{k}:{v}" for k, v in sorted(grades.items())))
        for c in got:
            rows.append({"file": f"{role}/{c['file']}", "type": role, "source": c.get("title") or c["file"],
                         "hit": "", "hits_in_source": ""})
            total += 1
    if a.dry:
        print("dry run: nothing downloaded")
        return
    if not rows:
        sys.exit("nothing downloaded (no internet to kenney.nl / freesound.org / api.openverse.org, no results, or "
                 "every file failed the quality grade). Use your own folder: real-sfx setup.py scan PATH")
    cat = out / "catalog.csv"
    if cat.exists():                                  # keep what earlier runs filed
        with open(cat, newline="", encoding="utf-8") as f:
            old = list(csv.DictReader(f))
        files = {r["file"] for r in rows}
        rows = [r for r in old if r["file"] not in files] + rows
    with open(cat, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "type", "source", "hit", "hits_in_source"])
        w.writeheader()
        w.writerows(rows)
    credits = []
    for role in sorted({p.name for p in out.iterdir() if p.is_dir()}):
        cj = out / role / "credits.json"
        if cj.exists():
            for c in json.loads(cj.read_text("utf-8")):
                c["file"] = f"{role}/{c['file']}"
                credits.append(c)
    (out / "CREDITS.md").write_text(ov.credits_md(credits), "utf-8")
    print(f"\n{total} new sounds in {out}  (catalog.csv, CREDITS.md: {len(credits)} sounds in all)")
    if a.register:
        setup = SKILLS / "real-sfx" / "scripts" / "setup.py"
        subprocess.call([sys.executable, str(setup), "add-library", name, str(out), "--tier", tier,
                         "--index"], env=dict(os.environ, PYTHONUTF8="1"))
    else:
        print(f'connect: python "{SKILLS / "real-sfx" / "scripts" / "setup.py"}" add-library {name} "{out}" '
              f"--tier {tier} --index")


if __name__ == "__main__":
    main()
