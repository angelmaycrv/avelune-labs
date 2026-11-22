#!/usr/bin/env python3
"""quality: is this recording good enough for an ad? Numbers instead of ears.

A deaf agent picks by name and tags, so a hissy phone recording called "coin" wins as easily as a studio one. This
grades the RECORDING, not its fit to the moment:

  A  lossless (wav/flac/aiff) at 44.1 kHz or more, clean floor, no clipping: studio grade
  B  good lossy file (>= 160 kbps) or lossless with a little noise: fine for ads
  C  preview-grade: lossy <= 128 kbps (Openverse/Freesound previews), sample rate under 44.1 kHz, audible hiss
     (the quiet part of the sound is less than 42 dB under the peak) or a long dead head. Only for quiet, minor sounds
  D  do not use: clipped (flat-topped peaks), hiss/room noise less than 28 dB under the peak, under 22 kHz, or
     under 96 kbps

The noise test is skipped for beds and textures (ambience, atmosphere, vehicle, water, granular): their "noise" is
the sound itself.

  python quality.py FILE [FILE ...] [--role hit] [--json]
  python quality.py --index                 # grade every sound in library_index.json (kept, re-done when changed)
  python quality.py --cues result/x_resolved_cues.json [--json out.json]   # the sounds a finished sheet used

The picker (picker.py) pushes C down and D to the bottom; concept_check.py fails a hero or object sound of grade D
and warns on C.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

LOSSLESS = {"pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "pcm_f64le", "pcm_s16be", "pcm_s24be", "pcm_s32be",
            "pcm_u8", "flac", "alac", "wavpack", "ape", "tta"}
BED_ROLES = {"ambience", "atmosphere", "vehicle", "water", "granular", "room", "texture"}
GRADES = "ABCD"
VERSION = 1


def _num(v, default=None):
    try:
        f = float(v)
        return f if f == f else default
    except (TypeError, ValueError):
        return default


def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                        "stream=codec_name,sample_rate,bit_rate,bits_per_raw_sample,bits_per_sample,channels:"
                        "format=bit_rate,duration", "-of", "json", str(path)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        d = json.loads(p.stdout or "{}")
    except ValueError:
        return None
    st = (d.get("streams") or [{}])[0]
    fm = d.get("format") or {}
    if not st:
        return None
    br = _num(st.get("bit_rate")) or _num(fm.get("bit_rate"))
    return {"codec": st.get("codec_name") or "?", "sr": int(_num(st.get("sample_rate"), 0) or 0),
            "kbps": round(br / 1000) if br else None, "ch": int(_num(st.get("channels"), 1) or 1),
            "bits": int(_num(st.get("bits_per_raw_sample")) or _num(st.get("bits_per_sample")) or 0),
            "dur": round(_num(fm.get("duration"), 0.0), 3)}


_STAT = re.compile(r"(Peak level dB|RMS level dB|Flat factor):\s*(-?[\d.]+|-?inf)")


def levels(path, max_s=10.0):
    """Peak, flat factor (clipped tops) and the dead head on the native file, plus the noise floor read from the
    envelope: the quietest 20 ms windows (digital silence left out) against the loudest. A sound that never gets
    quiet (a tone, a loop, a riser) has no floor to judge and gets `floor` None."""
    p = subprocess.run(["ffmpeg", "-nostats", "-v", "info", "-i", str(path), "-vn", "-af",
                        "silencedetect=n=-55dB:d=0.12,astats=measure_perchannel=none:measure_overall="
                        "Peak_level+RMS_level+Flat_factor", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = {}
    for k, v in _STAT.findall(p.stderr):
        out[k] = -999.0 if "inf" in v else float(v)
    head = 0.0
    m = re.search(r"silence_start: (-?[\d.]+)", p.stderr)
    if m and abs(float(m.group(1))) < 0.02:
        e = re.search(r"silence_end: ([\d.]+)", p.stderr)
        head = float(e.group(1)) if e else 0.0
    floor = span = None
    try:
        from common import decode_mono
        a, rate = decode_mono(path, rate=16000)       # the floor needs no top end: 16 kHz keeps indexing fast
        a = a[: int(max_s * rate)]
        w = rate // 50
        env = []
        for i in range(0, len(a) - w + 1, w):
            seg = a[i:i + w]
            env.append(math.sqrt(sum(v * v for v in seg) / w))
        db = [20 * math.log10(e / 32768.0) for e in env if e > 3.0]   # under 3/32768 (-81 dBFS): digital silence
        if len(db) >= 10:
            sm = [sum(db[i:i + 5]) / 5 for i in range(len(db) - 4)]
            lo, hi = min(sm), max(db)
            span = hi - lo
            # noise is a PLATEAU: the level the sound sits on for a while (160 ms or more within 3 dB of the
            # quietest part), not the last instant of a fade. A tone or a loop that never gets 15 dB quieter has
            # no floor to judge.
            near = sum(1 for v in db if v <= lo + 3.0)
            if span >= 15 and near >= 8:
                floor = lo
    except Exception:
        pass
    return {"peak": out.get("Peak level dB"), "rms": out.get("RMS level dB"), "floor": floor, "span": span,
            "flat": out.get("Flat factor"), "head": round(head, 3)}


def grade(path, role=None):
    """The grade of one file and the reasons, worst first."""
    pr = probe(path)
    if pr is None:
        return {"grade": "D", "why": ["no audio stream (broken file)"]}
    lv = levels(path)
    why, g = [], 0

    def worse(level, text):
        nonlocal g
        g = max(g, level)
        why.append((level, text))

    lossless = pr["codec"] in LOSSLESS
    if pr["sr"] and pr["sr"] < 22050:
        worse(3, f"{pr['sr']} Hz: the top of the sound is cut off")
    elif pr["sr"] and pr["sr"] < 44100:
        worse(2, f"{pr['sr']} Hz: dull top")
    if not lossless and pr["codec"] in ("vorbis", "opus"):
        kb = pr["kbps"] or 0                       # VBR: a simple short sound gets a low rate and loses nothing
        if kb and kb < 48:
            worse(2, f"{pr['codec']} {kb} kbps: low-rate lossy")
        else:
            worse(1, f"{pr['codec']} {kb or '?'} kbps: lossy (VBR)")
    elif not lossless:
        kb = pr["kbps"] or 0
        if kb and kb < 96:
            worse(3, f"{pr['codec']} {kb} kbps: heavily compressed")
        elif kb and kb <= 130:
            worse(2, f"{pr['codec']} {kb} kbps: preview-grade compression (take the original from the landing page)")
        else:
            worse(1, f"{pr['codec']} {kb or '?'} kbps: lossy")
    elif pr["bits"] and pr["bits"] < 16:
        worse(2, f"{pr['bits']}-bit")
    peak, floor, flat = lv.get("peak"), lv.get("floor"), lv.get("flat")
    if flat is not None and flat > 8:
        worse(3, f"clipped: flat-topped peaks (flat factor {flat:.0f})")
    elif flat is not None and flat > 2:
        worse(2, f"slightly clipped (flat factor {flat:.1f})")
    bed = (role or "").lower() in BED_ROLES
    if not bed and peak is not None and floor is not None:
        gap = peak - floor
        if gap < 28:
            worse(3, f"hiss / room noise only {gap:.0f} dB under the peak")
        elif gap < 42:
            worse(2, f"audible hiss: floor {gap:.0f} dB under the peak")
        elif gap < 55 and lossless:
            worse(1, f"light noise floor ({gap:.0f} dB under the peak)")
    if peak is not None and peak < -30:
        worse(2, f"very quiet recording (peak {peak:.0f} dBFS): its noise comes up with it")
    if not bed and lv.get("head", 0) > 0.35 and pr["dur"] and pr["dur"] < 6:
        worse(2, f"{lv['head']:.2f} s of silence before the sound (sloppy edit)")
    why.sort(key=lambda t: -t[0])
    return {"grade": GRADES[g], "why": [t for _, t in why], "codec": pr["codec"], "sr": pr["sr"], "kbps": pr["kbps"],
            "peak": peak, "floor": None if floor is None else round(floor, 1), "head": lv.get("head"), "v": VERSION}


def _mtime(p):
    try:
        return round(os.path.getmtime(p), 1)
    except OSError:
        return None


def grade_index(workers=6):
    from common import index_path
    ip = Path(index_path())
    data = json.loads(ip.read_text("utf-8"))
    items = data.get("sounds", data) if isinstance(data, dict) else data
    todo = [s for s in items if not (isinstance(s.get("q"), dict) and s["q"].get("v") == VERSION
                                     and s["q"].get("mtime") == _mtime(s["path"]))]
    print(f"{len(items)} sounds, {len(todo)} to grade")

    def one(s):
        q = grade(s["path"], s.get("role"))
        q["mtime"] = _mtime(s["path"])
        s["q"] = q
        return q["grade"]

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, _ in enumerate(ex.map(one, todo), 1):
            if i % 200 == 0:
                print(f"  {i}/{len(todo)}")
    ip.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    count = {g: 0 for g in GRADES}
    for s in items:
        count[(s.get("q") or {}).get("grade", "D")] += 1
    by_lib = {}
    for s in items:
        by_lib.setdefault(s.get("library", "?"), {g: 0 for g in GRADES})[(s.get("q") or {}).get("grade", "D")] += 1
    print("grades: " + "  ".join(f"{g} {count[g]}" for g in GRADES))
    for lib, c in sorted(by_lib.items()):
        print(f"  {lib:<20} " + "  ".join(f"{g} {c[g]}" for g in GRADES))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--role")
    ap.add_argument("--index", action="store_true", help="grade library_index.json in place")
    ap.add_argument("--cues", help="resolved cues JSON of a finished sheet")
    ap.add_argument("--json", nargs="?", const="-", help="JSON to stdout, or to this file")
    a = ap.parse_args()
    if a.index:
        grade_index()
        return
    rows = []
    if a.cues:
        cues = json.loads(Path(a.cues).read_text("utf-8"))
        cues = cues.get("cues", cues) if isinstance(cues, dict) else cues
        seen = {}
        for c in cues:
            f = c.get("source_file") or c.get("file")
            if not f:
                continue
            if f not in seen:
                seen[f] = grade(f, c.get("role"))
            rows.append({"t": c.get("t"), "role": c.get("role"), "file": f, **seen[f]})
    for f in a.files:
        rows.append({"file": f, "role": a.role, **grade(f, a.role)})
    if not rows:
        ap.error("give files, --cues or --index")
    if a.json:
        txt = json.dumps(rows, ensure_ascii=False, indent=1)
        if a.json == "-":
            print(txt)
        else:
            Path(a.json).write_text(txt, "utf-8")
    if a.json != "-":
        for r in rows:
            t = f"{r['t']:>6.2f}s " if isinstance(r.get("t"), (int, float)) else ""
            print(f"{r['grade']}  {t}{(r.get('role') or ''):<9} {Path(r['file']).name[:55]:<55} "
                  f"{'; '.join(r['why'][:2]) or 'clean'}")
        worst = max((GRADES.index(r["grade"]) for r in rows), default=0)
        print(f"worst: {GRADES[worst]}")


if __name__ == "__main__":
    main()
