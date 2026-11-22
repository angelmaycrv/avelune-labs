#!/usr/bin/env python3
"""sources: where good free sounds come from, fetched ONE ROLE AT A TIME for the film at hand (no 10 GB packs).

Order for every role a film needs (starter_library.py --for-cues uses this):

  1. Kenney (kenney.nl): CC0 interface and UI sounds made for apps and games (clean, edited, no noise), taken file by
     file from their GitHub mirrors: only for click, pop, chime, UI and error roles.
  2. Freesound (freesound.org) with quality filters: rated 3.5+ by at least 3 people, the most downloaded first,
     CC0 or CC BY only (no NC). Needs a free API key once: freesound.org/apiv2/apply -> `sources.py freesound-key KEY`.
     With the key it takes the HQ OGG preview (~190 kbps). After `sources.py freesound-login` (one browser
     confirmation) it takes the ORIGINAL file (wav/flac, studio grade).
  3. Openverse: what is left. Its Freesound files are 128 kbps previews (quality grade C): only for quiet, minor
     sounds.

Every file is graded by real-sfx/scripts/quality.py right after the download; grade D (clipped, hissy, crushed) is
deleted at once.

  python sources.py status
  python sources.py kenney --role click --out DIR          # Kenney UI sounds for one role
  python sources.py freesound --role click --query "ui click soft" --n 6 --out DIR
  python sources.py freesound-key KEY
  python sources.py freesound-login                         # once: originals instead of previews
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
sys.path.insert(0, str(SKILLS / "real-sfx" / "scripts"))
UA = "avelune-sound/1.1 (+https://github.com/angelmaycrv/avelune-labs)"
HOME = Path.home() / ".avelune-sound"
FS_CONF = HOME / "freesound.json"
FS_API = "https://freesound.org/apiv2"

# Kenney's own site hands out a zip only through a one-time signed link behind a donation popup, so the packs are read
# from their CC0 mirrors on GitHub, file by file (git tree listing + raw file). More mirrors: add "owner/repo" here.
KENNEY_REPOS = ["Calinou/kenney-interface-sounds", "Calinou/kenney-ui-audio"]
# catalog type -> words a Kenney file name must carry to be filed under it
KENNEY = {
    "click": r"click|select|switch|toggle|tick|scroll|maximize|minimize|rollover|mouse",
    "pop": r"pluck|drop|bong|glass|confirmation|select",
    "chime": r"confirmation|glass|bong|pluck",
    "glitch": r"error|glitch",
    "ui": r"click|switch|confirmation|select|toggle|tick",
}
GH_API = "https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1"
GH_RAW = "https://raw.githubusercontent.com/{repo}/HEAD/{path}"


def _get(url, binary=True, headers=None, data=None, tries=3, timeout=90):
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=h, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
                return b if binary else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1))
                continue
            raise
        except urllib.error.URLError as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def _grade(path, role):
    try:
        import quality
        return quality.grade(path, role)
    except Exception as e:                       # no ffmpeg / broken file: keep, unjudged
        return {"grade": "?", "why": [f"not graded: {e}"]}


def keep_or_drop(path, role, log):
    """Grade a fresh download; delete grade D. Returns the grade record or None when dropped."""
    q = _grade(path, role)
    if q.get("grade") == "D":
        log(f"   drop {Path(path).name}: {'; '.join(q.get('why', [])[:2])}")
        try:
            os.remove(path)
        except OSError:
            pass
        return None
    return q


# ------------------------------------------------------------------ Kenney (GitHub mirrors)
def kenney_files(cache=HOME / "catalog" / "kenney_github.json", log=print):
    """[(repo, path, size)] of every audio file in the Kenney mirrors; listed once and cached."""
    try:
        data = json.loads(cache.read_text("utf-8"))
    except (OSError, ValueError):
        data = {}
    for repo in KENNEY_REPOS:
        if repo in data:
            continue
        try:
            t = json.loads(_get(GH_API.format(repo=repo), binary=False, headers={"Accept": "application/vnd.github+json"}))
            data[repo] = [(e["path"], e.get("size", 0)) for e in t.get("tree", [])
                          if e.get("type") == "blob" and re.search(r"\.(ogg|wav|flac)$", e["path"], re.I)]
            log(f"   kenney {repo}: {len(data[repo])} sounds listed")
        except Exception as e:
            log(f"   kenney {repo}: not listed ({e})")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data), "utf-8")
    return [(repo, p, sz) for repo, files in data.items() for p, sz in files]


def kenney_take(repo, path, dst, role, log=print):
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(_get(GH_RAW.format(repo=repo, path=urllib.parse.quote(path))))
    q = keep_or_drop(dst, role, log)
    if q is None:
        return None
    return {"id": f"kenney:{repo}:{path}", "file": dst.name, "title": Path(path).stem + f" ({repo.split('/')[-1]})",
            "creator": "Kenney (kenney.nl)", "creator_url": "https://kenney.nl", "license": "cc0",
            "license_version": "1.0", "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "source": "kenney", "landing": f"https://github.com/{repo}", "grade": q.get("grade"),
            "downloaded": time.strftime("%Y-%m-%d")}


def kenney(role, out, log=print, n=8, words=None):
    """Up to n Kenney sounds for `role` (or matching `words`), downloaded file by file into out/<role>/."""
    rx = re.compile(words or KENNEY.get(role, "$^"), re.I)
    rows = []
    for repo, path, _ in kenney_files(log=log):
        if len(rows) >= n:
            break
        if not rx.search(Path(path).stem):
            continue
        dst = Path(out) / role / f"kenney_{Path(path).name}"
        try:
            r = kenney_take(repo, path, dst, role, log)
        except Exception as e:
            log(f"   kenney {path}: {e}")
            continue
        if r:
            rows.append(r)
    log(f"   kenney: {len(rows)} sound(s) for {role}")
    return rows


# ------------------------------------------------------------------ Freesound
def fs_conf():
    try:
        return json.loads(FS_CONF.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def fs_save(c):
    HOME.mkdir(parents=True, exist_ok=True)
    FS_CONF.write_text(json.dumps(c, indent=1), "utf-8")


def fs_key():
    return os.environ.get("FREESOUND_API_KEY") or fs_conf().get("api_key")


def fs_bearer():
    """A valid OAuth2 access token, refreshed when it is about to expire; None without a login."""
    c = fs_conf()
    if not c.get("refresh_token") or not c.get("client_id"):
        return None
    if c.get("access_token") and c.get("expires", 0) > time.time() + 120:
        return c["access_token"]
    body = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["api_key"],
                                   "grant_type": "refresh_token", "refresh_token": c["refresh_token"]}).encode()
    try:
        t = json.loads(_get(f"{FS_API}/oauth2/access_token/", binary=False, data=body))
    except Exception:
        return None
    c.update(access_token=t["access_token"], refresh_token=t.get("refresh_token", c["refresh_token"]),
             expires=time.time() + int(t.get("expires_in", 86400)))
    fs_save(c)
    return c["access_token"]


FS_LICENSES = {"Creative Commons 0": "cc0", "Attribution": "by", "http://creativecommons.org/publicdomain/zero/1.0/": "cc0",
               "https://creativecommons.org/publicdomain/zero/1.0/": "cc0",
               "http://creativecommons.org/licenses/by/3.0/": "by", "http://creativecommons.org/licenses/by/4.0/": "by",
               "https://creativecommons.org/licenses/by/4.0/": "by"}


def _fs_lic(v):
    v = str(v or "")
    if v in FS_LICENSES:
        return FS_LICENSES[v]
    if "publicdomain/zero" in v:
        return "cc0"
    if re.search(r"licenses/by/\d", v):
        return "by"
    return None                                   # NC, sampling+ and the rest: not for ads


def fs_search(query, lo, hi, n=15, min_rating=3.5, min_ratings=3):
    key = fs_key()
    if not key:
        return None
    flt = (f'duration:[{lo} TO {hi}] avg_rating:[{min_rating} TO *] num_ratings:[{min_ratings} TO *] '
           f'license:("Creative Commons 0" OR "Attribution")')
    fields = "id,name,tags,username,license,avg_rating,num_ratings,num_downloads,duration,type,samplerate,bitdepth,previews,url"
    q = urllib.parse.urlencode({"query": query, "filter": flt, "sort": "downloads_desc", "fields": fields,
                                "page_size": n, "token": key})
    for path in ("/search/text/", "/search/"):
        try:
            d = json.loads(_get(f"{FS_API}{path}?{q}", binary=False))
            return d.get("results", [])
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
    return []


def freesound(role, queries, lo, hi, per_role, out, log=print, seen=None):
    """Up to `per_role` rated Freesound sounds for `role`; originals with a login, HQ previews without."""
    if not fs_key():
        log("   freesound: no API key (sources.py freesound-key KEY): skipped")
        return []
    seen = seen if seen is not None else set()
    bearer = fs_bearer()
    out_d = Path(out) / role
    out_d.mkdir(parents=True, exist_ok=True)
    rows = []
    for w in queries:
        try:
            res = fs_search(w, lo, hi) or []
        except Exception as e:
            log(f"   freesound '{w}': {e}")
            continue
        for h in res:
            if len(rows) >= per_role:
                break
            lic = _fs_lic(h.get("license"))
            if lic is None or h["id"] in seen:
                continue
            seen.add(h["id"])
            name = re.sub(r"[^\w\-]+", "_", h.get("name") or "sound").strip("_")[:50]
            if bearer:
                ext = (h.get("type") or "wav").lower()
                url, hdr = f"{FS_API}/sounds/{h['id']}/download/", {"Authorization": f"Bearer {bearer}"}
            else:
                url, hdr, ext = (h.get("previews") or {}).get("preview-hq-ogg"), {}, "ogg"
            if not url:
                continue
            dst = out_d / f"fs{h['id']}_{name}.{ext}"
            if not dst.exists():
                try:
                    dst.write_bytes(_get(url, headers=hdr))
                except Exception as e:
                    log(f"   freesound {h['id']}: download failed ({e})")
                    continue
            q = keep_or_drop(dst, role, log)
            if q is None:
                continue
            rows.append({"id": f"freesound:{h['id']}", "file": dst.name, "title": h.get("name"),
                         "creator": h.get("username"), "creator_url": f"https://freesound.org/people/{h.get('username')}/",
                         "license": lic, "license_version": "", "license_url": h.get("license"),
                         "source": "freesound", "landing": h.get("url"),
                         "rating": h.get("avg_rating"), "downloads": h.get("num_downloads"),
                         "grade": q.get("grade"), "original": bool(bearer),
                         "downloaded": time.strftime("%Y-%m-%d")})
            log(f"   freesound {q.get('grade')}  {h.get('avg_rating', 0):.1f}*  {h.get('num_downloads', 0):>6} dl  "
                f"{lic:<3} {dst.name[:60]}")
            time.sleep(0.4)
        if len(rows) >= per_role:
            break
    return rows


def freesound_login():
    c = fs_conf()
    if not c.get("api_key") or not c.get("client_id"):
        sys.exit("first: sources.py freesound-key KEY --client-id CLIENT_ID (both on freesound.org/apiv2/apply, "
                 "the 'Client id' and 'Client secret/Api key' of your credential)")
    url = f"{FS_API}/oauth2/authorize/?client_id={c['client_id']}&response_type=code"
    print("Open this link, log in to Freesound, press Authorize and copy the code it shows:\n  " + url)
    code = input("code: ").strip()
    body = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["api_key"],
                                   "grant_type": "authorization_code", "code": code}).encode()
    t = json.loads(_get(f"{FS_API}/oauth2/access_token/", binary=False, data=body))
    c.update(access_token=t["access_token"], refresh_token=t["refresh_token"],
             expires=time.time() + int(t.get("expires_in", 86400)))
    fs_save(c)
    print("ok: Freesound originals will be downloaded (wav/flac) instead of previews")


def status():
    c = fs_conf()
    print("kenney     : always on (CC0 UI sounds, file by file from " + ", ".join(KENNEY_REPOS) + ")")
    if fs_key():
        print("freesound  : key set; " + ("originals (logged in)" if c.get("refresh_token") else
                                          "HQ previews (sources.py freesound-login for originals)"))
    else:
        print("freesound  : off. Free key: https://freesound.org/apiv2/apply -> sources.py freesound-key KEY")
    print("openverse  : always on, last in line (128 kbps previews)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    k = sub.add_parser("kenney")
    k.add_argument("--role", required=True, choices=sorted(KENNEY))
    k.add_argument("--out", required=True)
    f = sub.add_parser("freesound")
    f.add_argument("--role", required=True)
    f.add_argument("--query", action="append", required=True)
    f.add_argument("--min-dur", type=float, default=0.05)
    f.add_argument("--max-dur", type=float, default=6.0)
    f.add_argument("--n", type=int, default=6)
    f.add_argument("--out", required=True)
    fk = sub.add_parser("freesound-key")
    fk.add_argument("key")
    fk.add_argument("--client-id", help="needed only for freesound-login (originals)")
    sub.add_parser("freesound-login")
    a = ap.parse_args()
    if a.cmd == "status":
        status()
    elif a.cmd == "kenney":
        rows = kenney(a.role, a.out)
        print(f"{len(rows)} sound(s)")
    elif a.cmd == "freesound":
        rows = freesound(a.role, a.query, a.min_dur, a.max_dur, a.n, a.out)
        print(f"{len(rows)} sound(s)")
    elif a.cmd == "freesound-key":
        c = fs_conf()
        c["api_key"] = a.key
        if a.client_id:
            c["client_id"] = a.client_id
        fs_save(c)
        print(f"saved to {FS_CONF}")
    elif a.cmd == "freesound-login":
        freesound_login()


if __name__ == "__main__":
    main()
