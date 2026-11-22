#!/usr/bin/env python3
"""mixdown: voice + music (+ a ready effects track) -> a mix at a platform's loudness, checked by numbers.

Needs Python 3.9+ and ffmpeg/ffprobe. No numpy.

  # a voice-over film: voice chain, music carved and ducked under the voice, master to -14 LUFS / -1 dBTP, mp4
  python mixdown.py mix --voice vo.wav --music music.mp3 --video film.mp4 --out result/film_mix.mp4 --platform social
  # with the effects track real-sfx made (it already sits at its level)
  python mixdown.py mix --voice vo.wav --music m.wav --sfx result/film_sfx_sfx_track.wav --video film.mp4 --out ...
  # only bring a finished mix to a platform's norm (gain + true-peak limiter, checked after the encode)
  python mixdown.py master mix.wav result/mix_master.wav --platform podcast
  python mixdown.py master film.mp4 result/film_master.mp4 --platform youtube

What `mix` does, with the numbers it aims at (each one is printed and checked at the end):
  voice   highpass 80 Hz, compressor 3:1 (--voice-chain light, default) [+ denoise + de-esser: clean | none]
  music   -3 dB at 3 kHz (room for the voice, --carve-db), level so that under speech it sits --margin LU
          (default 15) under the voice, ducked by --duck-db (default 8) with a 120 ms lead and 350 ms release;
          after the render the margin is measured and the music corrected, up to 3 rounds
  master  one constant gain to the platform's loudness, a 4x-oversampled limiter at the true-peak ceiling,
          re-measured after the AAC encode and corrected (gain or ceiling), up to 4 rounds
  stems   <out>_voice_in_mix.wav, <out>_music_in_mix.wav: the stems at the level they have in the master, so that
          sound_check.py can judge voice over music; a report <out>_report.json
Exit code: the verdict of sound_check (0 PASS, 1 WARN, 2 FAIL).
"""
import argparse
import array
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "sound-check" / "scripts"))
import sound_check as sc  # noqa: E402

SR = 48000


def run(args, check=True):
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        sys.exit("ffmpeg failed:\n" + " ".join(map(str, args))[:600] + "\n" + r.stderr[-1500:])
    return r


def to_wav(src, dst, chain="", ch=2, start=0.0, dur=None):
    args = ["ffmpeg", "-v", "error", "-y"]
    args += ["-i", src, "-map", "0:a:0"]
    if dur:
        args += ["-t", f"{dur:.3f}"]
    af = ",".join(x for x in [chain, f"aresample={SR}", f"aformat=sample_fmts=flt:channel_layouts={'stereo' if ch == 2 else 'mono'}"] if x)
    if start > 0:
        ms = int(start * 1000)
        af = f"adelay={ms}|{ms}," + af
    args += ["-af", af, "-c:a", "pcm_f32le", dst]
    run(args)


VOICE_CHAINS = {
    "none": "",
    "light": "highpass=f=80,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=1",
    "clean": "highpass=f=80,afftdn=nr=10:nf=-45,deesser=i=0.3,"
             "acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=1",
}


def gain_curve(voice_wav, duration, duck_db, lead=0.12, attack=0.06, release=0.35, rate=1000):
    """A control signal: 1.0 in pauses, -duck_db under speech, opening `lead` s before a phrase."""
    L = sc.loudness(voice_wav, series=True)
    frames = sc.speech_frames(L["M"], L["I"])
    speech = set(frames)
    n = int(duration * rate) + 1
    target = [1.0] * n
    low = 10 ** (-duck_db / 20)
    for i in speech:
        t = L["M"][i][0]
        # momentary loudness is a 400 ms window ending at t: the speech is in [t - 0.4, t]
        a, b = max(0.0, t - 0.4 - lead), t
        for k in range(int(a * rate), min(n, int(b * rate) + 1)):
            target[k] = low
    out, g = [], 1.0
    ka = 1 - math.exp(-1 / (attack * rate))
    kr = 1 - math.exp(-1 / (release * rate))
    for v in target:
        g += (v - g) * (ka if v < g else kr)
        out.append(g)
    return out, rate, len(speech) / max(1, len(L["M"]))


def write_control(curve, rate, path):
    import wave
    w = wave.open(str(path), "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(array.array("h", (int(max(0.0, min(1.0, v)) * 32767) for v in curve)).tobytes())
    w.close()


def lufs(path):
    return sc.loudness(path)["I"]


def margin_under_speech(voice, music):
    V = sc.loudness(voice, series=True)
    M = sc.loudness(music, series=True)
    sp = set(sc.speech_frames(V["M"], V["I"]))
    n = min(len(V["M"]), len(M["M"]))
    m = [V["M"][i][1] - M["M"][i][1] for i in range(n) if i in sp and M["M"][i][1] > -70]
    return statistics.median(m) if m else None


def render_master(src, dst, gain_db, ceiling_db, video=None):
    """Gain, then a limiter at 4x oversampling (so it catches inter-sample peaks), then the file."""
    lim = 10 ** (ceiling_db / 20)
    af = (f"volume={gain_db:.2f}dB,aresample={SR * 4},alimiter=limit={lim:.5f}:attack=3:release=60:level=false,"
          f"aresample={SR}")
    args = ["ffmpeg", "-v", "error", "-y"]
    if video:
        args += ["-i", video, "-i", src, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", af,
                 "-c:a", "aac", "-b:a", "256k", "-shortest", dst]
    else:
        codec = ["-c:a", "pcm_s24le"] if dst.lower().endswith(".wav") else ["-c:a", "aac", "-b:a", "256k"]
        args += ["-i", src, "-map", "0:a:0", "-af", af] + codec + [dst]
    run(args)


def master(src, dst, plat, video=None):
    """Bring a mix to the platform's loudness with a constant gain and a true-peak limiter; re-measure the written
    file (after the AAC encode) and correct the gain or the ceiling, up to 4 rounds."""
    L0 = sc.loudness(src)
    if L0["I"] is None:
        sys.exit("the mix is silent")
    gain, ceiling = plat["I"] - L0["I"], plat["tp"] - 0.3
    info = {"input_i": L0["I"], "input_tp": L0["TP"]}
    for rnd in range(6):
        render_master(src, dst, gain, ceiling, video)
        L = sc.loudness(dst)
        info.update(gain_db=gain, ceiling_db=ceiling, output_i=L["I"], output_tp=L["TP"], rounds=rnd + 1)
        di, dtp = plat["I"] - L["I"], L["TP"] - plat["tp"]
        if abs(di) <= 0.3 and dtp <= 0.05:
            break
        if dtp > 0.05:
            ceiling -= dtp + 0.1
            if rnd >= 2:                 # the AAC encode overshoots whatever the ceiling: give up some loudness
                gain -= dtp + 0.1
                continue
        if abs(di) > 0.3:
            gain += di
    if info["output_tp"] > plat["tp"] + 0.05:
        print(f"WARN master: true peak {info['output_tp']:.1f} dBTP is still over the {plat['tp']:g} ceiling after "
              f"{info['rounds']} rounds: lower the loudest sound in the mix and master again")
    limited = info["gain_db"] + L0["TP"] - info["ceiling_db"]
    info["limited_db"] = round(max(0.0, limited), 1)
    if limited > 6:
        print(f"master: the limiter takes up to {limited:.0f} dB off the loudest peaks: a sparse or peaky mix. Lower "
              "the loudest sound (a hit, a boom) or compress the voice, then master again; or accept a lower loudness")
    return info


def cmd_master(a):
    plat = sc.PLATFORMS[a.platform]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    info = master(a.input, a.out, plat, video=a.input if sc.probe(a.input)["video"] and a.out.lower().endswith(
        (".mp4", ".mov", ".m4v")) else None)
    print(f"master: {info['input_i']:.1f} -> {info['output_i']:.1f} LUFS (target {plat['I']}), gain "
          f"{info['gain_db']:+.1f} dB, limiter up to {info['limited_db']} dB, true peak {info['output_tp']:.1f} dBTP")
    return check(a.out, a.platform, None, None, None, a.out)


def check(out, platform, voice, music, sfx, base):
    args = argparse.Namespace(file=out, platform=platform, voice=voice, music=music, sfx=sfx, cues=None,
                              sfx_only=False)
    rep = sc.Report()
    sc.check_mix(args, rep)
    print("\n== sound_check ==")
    rep.print()
    Path(str(Path(base).with_suffix("")) + "_report.json").write_text(
        json.dumps({"verdict": rep.verdict(), "checks": rep.rows, "data": rep.data}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return {"PASS": 0, "WARN": 1, "FAIL": 2}[rep.verdict()]


def cmd_mix(a):
    plat = sc.PLATFORMS[a.platform]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    stem = str(out.with_suffix(""))
    tmp = Path(tempfile.mkdtemp(prefix="mixdown_"))
    vinfo = sc.probe(a.video) if a.video else None
    dur = vinfo["duration"] if vinfo else max(sc.probe(a.voice)["duration"] + a.voice_at, 0.1)

    v = str(tmp / "voice.wav")
    to_wav(a.voice, v, VOICE_CHAINS[a.voice_chain], ch=2, start=a.voice_at, dur=dur)
    vI = lufs(v)
    if vI is None:
        sys.exit("the voice track is silent")
    # voice to -18 LUFS before the master: headroom for music and effects
    v2 = str(tmp / "voice_l.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", v, "-af", f"volume={-18 - vI:.2f}dB", "-c:a", "pcm_f32le", v2])
    vI = -18.0
    print(f"voice: chain '{a.voice_chain}', set to {vI:.1f} LUFS")

    parts = [v2]
    music_final = None
    if a.music:
        m = str(tmp / "music.wav")
        carve = f"equalizer=f=3000:t=q:w=1:g={-abs(a.carve_db)}" if a.carve_db else ""
        to_wav(a.music, m, carve, ch=2, start=a.music_at, dur=dur)
        curve, rate, share = gain_curve(v2, dur, a.duck_db)
        ctrl = tmp / "duck.wav"
        write_control(curve, rate, ctrl)
        mI = lufs(m) or -30.0
        # music level in pauses: margin - duck under the voice, so that under speech it is `margin` under it
        gain = (vI - (a.margin - a.duck_db)) - mI
        for rnd in range(3):
            md = str(tmp / f"music_d{rnd}.wav")
            run(["ffmpeg", "-v", "error", "-y", "-i", m, "-i", str(ctrl), "-filter_complex",
                 f"[1]aresample={SR},aformat=channel_layouts=stereo[c];[0]volume={gain:.2f}dB[mm];[mm][c]amultiply,"
                 f"atrim=0:{dur:.3f}[o]", "-map", "[o]", "-c:a", "pcm_f32le", md])
            mg = margin_under_speech(v2, md)
            print(f"music round {rnd + 1}: gain {gain:+.1f} dB, duck {a.duck_db} dB, voice over music under speech "
                  f"{'n/a' if mg is None else f'{mg:.1f} LU'} (target {a.margin})")
            music_final = md
            if mg is None or abs(mg - a.margin) <= 1.0:
                break
            gain -= (a.margin - mg)
        parts.append(music_final)
    if a.sfx:
        s = str(tmp / "sfx.wav")
        to_wav(a.sfx, s, f"volume={a.sfx_gain_db}dB" if a.sfx_gain_db else "", ch=2, dur=dur)
        parts.append(s)

    pre = str(tmp / "premix.wav")
    ins = []
    for p in parts:
        ins += ["-i", p]
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex",
         "".join(f"[{i}]" for i in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0:duration=longest,"
         f"atrim=0:{dur:.3f}[o]", "-map", "[o]", "-c:a", "pcm_f32le", pre])

    info = master(pre, str(out), plat, video=a.video if a.video and str(out).lower().endswith((".mp4", ".mov", ".m4v"))
                  else None)
    g = info["gain_db"]
    print(f"master: {info['input_i']:.1f} -> {info['output_i']:.1f} LUFS (target {plat['I']}), gain {g:+.1f} dB, "
          f"limiter up to {info['limited_db']} dB, true peak {info['output_tp']:.1f} dBTP")
    vs, ms = stem + "_voice_in_mix.wav", (stem + "_music_in_mix.wav") if music_final else None
    run(["ffmpeg", "-v", "error", "-y", "-i", v2, "-af", f"volume={g:.2f}dB", "-c:a", "pcm_s24le", vs])
    if ms:
        run(["ffmpeg", "-v", "error", "-y", "-i", music_final, "-af", f"volume={g:.2f}dB", "-c:a", "pcm_s24le", ms])
    shutil.rmtree(tmp, ignore_errors=True)
    return check(str(out), a.platform, vs, ms, None, str(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mix")
    m.add_argument("--voice", required=True)
    m.add_argument("--music")
    m.add_argument("--sfx", help="a ready effects track (real-sfx *_sfx_track.wav), kept at its level")
    m.add_argument("--sfx-gain-db", type=float, default=0.0)
    m.add_argument("--video", help="mux the result into this video (stream copied)")
    m.add_argument("--out", required=True)
    m.add_argument("--platform", default="social", choices=[k for k, v in sc.PLATFORMS.items() if v])
    m.add_argument("--voice-chain", default="light", choices=sorted(VOICE_CHAINS))
    m.add_argument("--voice-at", type=float, default=0.0, help="seconds: where the voice starts on the timeline")
    m.add_argument("--music-at", type=float, default=0.0)
    m.add_argument("--margin", type=float, default=15.0, help="LU the music sits under the voice during speech")
    m.add_argument("--duck-db", type=float, default=8.0, help="how much the music dips under speech")
    m.add_argument("--carve-db", type=float, default=3.0, help="cut at 3 kHz on the music (0 = off)")
    m.set_defaults(fn=cmd_mix)
    s = sub.add_parser("master")
    s.add_argument("input")
    s.add_argument("out")
    s.add_argument("--platform", default="social", choices=[k for k, v in sc.PLATFORMS.items() if v])
    s.set_defaults(fn=cmd_master)
    a = ap.parse_args()
    sc.need_tools()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
