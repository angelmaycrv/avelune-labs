#!/usr/bin/env python3
"""tone: render UI sounds and short sonic logos from notes, in code (this IS synthesis: say so in the report).

Use it only for designed tonal sounds where synthesis is the point (app events, a notification, a 1-3 s logo),
never as a stand-in for a recorded effect in a film.

  python tone.py set.json --out work/ui            # every sound of the set -> WAV + a measured table
  python tone.py set.json --out work/ui --only success

set.json
  {"key": "A", "sr": 48000, "peak_db": -1.0, "levels": {"tap": -12, "error": -3, "success": 0},
   "sounds": {
     "tap":     {"notes": [{"n": "A6", "dur": 0.035}], "wave": "sine", "attack": 0.002, "release": 0.03},
     "success": {"notes": [{"n": "E5", "t": 0, "dur": 0.12}, {"n": "A5", "t": 0.09, "dur": 0.32}],
                 "wave": "bell", "release": 0.25},
     "error":   {"notes": [{"n": "D#5", "t": 0, "dur": 0.12}, {"n": "A4", "t": 0.11, "dur": 0.22}], "wave": "triangle"},
     "logo":    {"notes": [{"n": "A4", "t": 0}, {"n": "C#5", "t": 0.18}, {"n": "E5", "t": 0.36}, {"n": "A5", "t": 0.54,
                 "dur": 1.2}], "wave": "bell", "release": 0.9}
   }}
  n        a note (A4 = 440 Hz, C#5, Bb3) or "hz": 523.25
  t / dur  start and length, seconds
  wave     sine | triangle | soft-square | bell (inharmonic partials 1, 2.76, 5.4 with faster decay) | pluck
  attack / release   seconds of the envelope (release is an exponential tail)
  gain_db  per note (inside a sound), or on the sound itself (after the peak, only down); detune_cents adds a second voice for width (stays mono-safe under 12 cents)
Every sound is written at the same peak; the table prints each one's loudness (LUFS of its audible part).
"levels": {"tap": -12, "error": -3, "success": 0} says how many dB under the loudest event each should sit (the
hierarchy in SKILL.md); the script prints the gain_db that gets it there.
"""
import argparse
import json
import math
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE.parent.parent / "sound-check" / "scripts" / "sound_check.py"
NOTE = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}


def hz(n):
    if isinstance(n, (int, float)):
        return float(n)
    m = re.fullmatch(r"([A-Ga-g])([#b]?)(-?\d)", n.strip())
    if not m:
        raise SystemExit(f"bad note {n!r}")
    semi = NOTE[m.group(1).upper()] + {"#": 1, "b": -1, "": 0}[m.group(2)] + 12 * (int(m.group(3)) - 4)
    return 440.0 * 2 ** (semi / 12)


def osc(kind, f, t):
    ph = 2 * math.pi * f * t
    if kind == "sine":
        return math.sin(ph)
    if kind == "triangle":
        return 2 / math.pi * math.asin(math.sin(ph))
    if kind == "soft-square":
        return math.tanh(2.5 * math.sin(ph)) / math.tanh(2.5)
    if kind == "bell":
        return (math.sin(ph) + 0.5 * math.exp(-t * 9) * math.sin(2.76 * ph) +
                0.25 * math.exp(-t * 16) * math.sin(5.4 * ph)) / 1.75
    if kind == "pluck":
        return (math.sin(ph) + 0.4 * math.exp(-t * 20) * math.sin(2 * ph) + 0.2 * math.exp(-t * 30) * math.sin(3 * ph)) / 1.6
    raise SystemExit(f"unknown wave {kind}")


def render(spec, sr):
    notes = spec["notes"]
    kind = spec.get("wave", "sine")
    att = float(spec.get("attack", 0.004))
    rel = float(spec.get("release", 0.08))
    end = max(float(n.get("t", 0)) + float(n.get("dur", 0.15)) + rel * 5 for n in notes)
    buf = [0.0] * int(end * sr + 1)
    for n in notes:
        f = hz(n.get("hz", n.get("n")))
        t0, dur = float(n.get("t", 0)), float(n.get("dur", 0.15))
        g = 10 ** (float(n.get("gain_db", 0)) / 20)
        det = float(n.get("detune_cents", spec.get("detune_cents", 0)))
        voices = [f] + ([f * 2 ** (det / 1200)] if det else [])
        i0, length = int(t0 * sr), int((dur + rel * 5) * sr)
        for k in range(length):
            if i0 + k >= len(buf):
                break
            t = k / sr
            env = min(1.0, t / att) if att > 0 else 1.0
            if t > dur:
                env *= math.exp(-(t - dur) / max(rel, 1e-3))
            v = sum(osc(kind, fv, t) for fv in voices) / len(voices)
            buf[i0 + k] += g * env * v
    # trim the inaudible tail
    pk = max(abs(x) for x in buf) or 1.0
    last = max(i for i, x in enumerate(buf) if abs(x) > pk * 10 ** (-60 / 20))
    return buf[: last + 1], pk


def write(path, buf, pk, sr, peak_db, gain_db=0.0):
    g = 10 ** (peak_db / 20) / pk * 10 ** (min(0.0, gain_db) / 20)
    w = wave.open(str(path), "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x * g)) * 32767)) for x in buf))
    w.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("set")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only")
    a = ap.parse_args()
    st = json.loads(Path(a.set).read_text(encoding="utf-8-sig"))
    sr = int(st.get("sr", 48000))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, spec in st["sounds"].items():
        if a.only and name != a.only:
            continue
        buf, pk = render(spec, sr)
        f = out / f"{name}.wav"
        write(f, buf, pk, sr, float(st.get("peak_db", -1.0)), float(spec.get("gain_db", 0)))
        r = subprocess.run([sys.executable, str(CHECK), "--clip", str(f), "--json", str(out / f"{name}.json")],
                           capture_output=True, text=True, encoding="utf-8")
        d = json.loads((out / f"{name}.json").read_text(encoding="utf-8"))["data"]
        rows.append((name, d))
    print(f"{'sound':<14}{'length s':>9}{'attack ms':>10}{'LUFS':>8}{'2-6 kHz %':>11}")
    louds = []
    for name, d in rows:
        m = d.get("clip_lufs")
        louds.append(m)
        bp = (d.get("band_energy_pct") or {}).get("presence 2-6k")
        print(f"{name:<14}{d['audible_s']:>9.3f}{d['attack_ms']:>10}{m if m is not None else 'n/a':>8}"
              f"{bp if bp is not None else 'n/a':>11}")
    levels = st.get("levels", {})                      # {"tap": -12, "success": 0}: dB against the loudest event
    vals = {n: d.get("clip_lufs") for n, d in rows if d.get("clip_lufs") is not None}
    if vals:
        top = max(vals.values())
        for n, v in vals.items():
            want = levels.get(n)
            if want is None:
                continue
            off = (v - top) - want
            if abs(off) <= 1.5:
                verdict = "OK"
            elif off > 0:
                cur = float(st["sounds"][n].get("gain_db", 0))
                verdict = f'set "gain_db": {min(0.0, cur - off):.1f} on the sound'
            else:
                verdict = "too quiet even at full peak: lower the loudest sounds instead"
            print(f"  {n}: {v - top:+.1f} dB against the loudest, wanted {want:+.0f}: {verdict}")
    print("synthesized in code: label these as designed UI tones in the report")


if __name__ == "__main__":
    main()
