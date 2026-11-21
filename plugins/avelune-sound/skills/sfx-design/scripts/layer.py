#!/usr/bin/env python3
"""layer: build one designed sound from pieces of REAL recordings (attack + body + tail), then measure it.

  python layer.py recipe.json --out work/designed/hit_logo.wav [--role hit]

recipe.json
  {"sr": 48000, "peak_db": -1.0,
   "layers": [
     {"file": "D:/SFX/wood_hit.wav", "start": 0.12, "dur": 0.30, "gain_db": 0,  "role": "attack",
      "highpass": 1500, "fade_out": 0.05},
     {"file": "D:/SFX/door_slam.wav", "start": 0.0, "dur": 0.9, "gain_db": -4, "pitch": -5, "role": "body",
      "lowpass": 2500, "at": 0.0},
     {"file": "D:/SFX/sub_boom.wav", "dur": 1.2, "gain_db": -8, "role": "sub", "lowpass": 120, "at": 0.005},
     {"file": "D:/SFX/room.wav", "start": 2.0, "dur": 1.5, "gain_db": -18, "role": "tail", "at": 0.05,
      "fade_in": 0.02, "fade_out": 0.8, "reverse": false}
   ]}
  file      a real recording (your library, the starter library, an Openverse download)
  start/dur seconds inside the file (earshot find or real-sfx listen.py onsets give clean trims)
  at        where the layer starts in the result, seconds (default 0)
  pitch     semitones, varispeed (lower = bigger and longer, as a tape slowed down)
  reverse   true: play backwards (a hit becomes a swell into the moment)
  highpass / lowpass   Hz; each layer should own its band (attack high, body mid, sub low)
  fade_in / fade_out   seconds (default 0.002 / 0.02: no clicks at the cut)
After the render: the sound's shape and tone are printed by sound_check.py --clip, with the role's usual shape.
Everything is real recordings: no oscillator, no noise generator.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE.parent.parent / "sound-check" / "scripts" / "sound_check.py"


def run(args):
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit("ffmpeg failed: " + r.stderr[-1200:])
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recipe")
    ap.add_argument("--out", required=True)
    ap.add_argument("--role", help="hit, whoosh, riser, pop, click, chime ... for the shape check")
    a = ap.parse_args()
    rc = json.loads(Path(a.recipe).read_text(encoding="utf-8-sig"))
    sr = int(rc.get("sr", 48000))
    layers = rc["layers"]
    if not layers:
        sys.exit("no layers")
    tmp = Path(tempfile.mkdtemp(prefix="layer_"))
    parts = []
    for i, L in enumerate(layers):
        f = Path(L["file"])
        if not f.exists():
            sys.exit(f"layer {i}: no file {f}")
        chain = []
        if L.get("pitch"):
            k = 2 ** (float(L["pitch"]) / 12)
            chain += [f"asetrate={int(sr * k)}", f"aresample={sr}"]
        if L.get("reverse"):
            chain.append("areverse")
        if L.get("highpass"):
            chain.append(f"highpass=f={L['highpass']}")
        if L.get("lowpass"):
            chain.append(f"lowpass=f={L['lowpass']}")
        fi, fo = float(L.get("fade_in", 0.002)), float(L.get("fade_out", 0.02))
        chain.append(f"afade=t=in:d={fi}")
        chain.append("areverse,afade=t=in:d=%s,areverse" % fo)
        if L.get("gain_db"):
            chain.append(f"volume={float(L['gain_db'])}dB")
        at = int(round(float(L.get("at", 0)) * 1000))
        if at > 0:
            chain.append(f"adelay={at}|{at}")
        args = ["ffmpeg", "-v", "error", "-y"]
        if L.get("start"):
            args += ["-ss", f"{float(L['start']):.4f}"]
        if L.get("dur"):
            args += ["-t", f"{float(L['dur']):.4f}"]
        out = tmp / f"l{i}.wav"
        args += ["-i", f, "-af", f"aresample={sr},aformat=sample_fmts=flt:channel_layouts=stereo," + ",".join(chain),
                 "-c:a", "pcm_f32le", out]
        run(args)
        parts.append(out)
    mix = tmp / "mix.wav"
    ins = []
    for p in parts:
        ins += ["-i", p]
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", "".join(f"[{i}]" for i in range(len(parts))) +
         f"amix=inputs={len(parts)}:normalize=0:duration=longest[o]", "-map", "[o]", "-c:a", "pcm_f32le", mix])
    # peak to peak_db (sample peak; the master's limiter handles true peak later)
    vol = run(["ffmpeg", "-hide_banner", "-i", mix, "-af", "volumedetect", "-f", "null", "-"]).stderr
    mx = float(vol.split("max_volume:")[1].split("dB")[0]) if "max_volume:" in vol else 0.0
    g = float(rc.get("peak_db", -1.0)) - mx
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", mix, "-af", f"volume={g:.2f}dB", "-c:a", "pcm_s24le", a.out])
    print(f"written {a.out}: {len(parts)} layers, peak {rc.get('peak_db', -1.0)} dBFS (gain {g:+.1f} dB)")
    args = [sys.executable, CHECK, "--clip", a.out] + (["--role", a.role] if a.role else [])
    sys.exit(subprocess.call([str(x) for x in args]))


if __name__ == "__main__":
    main()
