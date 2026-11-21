#!/usr/bin/env python3
"""sound_check: the agent's measuring ears. Numbers with thresholds and a verdict, no "sounds good".

Needs only Python 3.9+ and ffmpeg/ffprobe in PATH (no numpy, no models).

  # a finished film or track against a platform's norm
  python sound_check.py FILM.mp4 --platform social [--json report.json]
  # with the stems as they sit in the mix: is the voice clear over the music, how deep is the ducking
  python sound_check.py FILM.mp4 --platform social --voice voice_in_mix.wav --music music_in_mix.wav
  # with the effects track and the cue list: pacing of accents, sync of short sounds, effects over speech
  python sound_check.py FILM.mp4 --sfx film_sfx_track.wav --cues resolved_cues.json [--voice ...]
  # one sound: length, attack, decay, peak, loudness, tone
  python sound_check.py --clip hit.wav [--role hit]
  # loudness-matched A/B: how B differs from A, in numbers
  python sound_check.py --ab a.wav b.wav

Exit code: 0 = PASS, 1 = WARN only, 2 = FAIL (or a file that cannot be read).
Every FAIL and WARN line names the fix. Thresholds are in THRESHOLDS / PLATFORMS below, with their sources.
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
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Integrated loudness target, tolerance, true-peak ceiling. Sources: ITU-R BS.1770-5 (the meter), EBU R 128 (TV,
# -23 LUFS, -1 dBTP), ATSC A/85 (-24 LKFS, -2 dBTP), Spotify and YouTube help pages (about -14 LUFS, -1 dBTP),
# AES TD1008 / Apple Podcasts (-16 LUFS stereo), Sony ASWG-R001 (console games -24, mobile -18).
# TikTok, Instagram and VK publish no norm: -14 is the common web practice the mix is judged against.
PLATFORMS = {
    "social":   {"I": -14.0, "tol": 1.0, "tp": -1.0, "lra_max": 10.0, "label": "Reels / TikTok / Shorts / VK Клипы"},
    "youtube":  {"I": -14.0, "tol": 1.0, "tp": -1.0, "lra_max": 12.0, "label": "YouTube"},
    "music":    {"I": -14.0, "tol": 1.0, "tp": -1.0, "lra_max": 14.0, "label": "стриминг музыки"},
    "podcast":  {"I": -16.0, "tol": 1.0, "tp": -1.0, "lra_max": 8.0, "label": "подкаст, видеокурс, голос"},
    "tv-ebu":   {"I": -23.0, "tol": 0.5, "tp": -1.0, "lra_max": 15.0, "label": "ТВ, EBU R 128"},
    "tv-atsc":  {"I": -24.0, "tol": 2.0, "tp": -2.0, "lra_max": 15.0, "label": "ТВ, ATSC A/85"},
    "game-console": {"I": -24.0, "tol": 2.0, "tp": -1.0, "lra_max": 20.0, "label": "игра, консоль/ПК"},
    "game-mobile":  {"I": -18.0, "tol": 2.0, "tp": -1.0, "lra_max": 15.0, "label": "игра, телефон"},
    "none":     None,
}

THRESHOLDS = {
    # music under a voice: 12-20 dB under it by loudness is the working range of ad and video mixers
    "voice_margin_fail": 7.0, "voice_margin_warn": 10.0,
    # an effect louder than the voice at the same moment covers a word
    "sfx_over_voice_db": -3.0,
    # mono: what the mix loses when summed (0 = equal channels, 3 = unrelated, 6+ = something cancels)
    "mono_warn": 3.5, "mono_fail": 6.0,
    # phone speaker: almost nothing under 150-200 Hz; a mix whose loudness lives in the lows is quieter there
    "phone_drop_warn": 4.0,
    # accents (hits, whooshes, risers, booms) per 15 s in a film with music or voice: 3-6 (video-sound rule)
    "accents_per_15s_max": 6, "accents_per_15s_min": 1,
    # sync of short sounds to their cue (a frame at 25 fps is 40 ms)
    "sync_ok_ms": 45, "sync_warn_ms": 100,
    # 250 ms windows quieter than -70 dBFS in a film whose sound is only effects (finished SFX reels: 0 % in 7 of 9)
    "silence_warn_frac": 0.05,
    # the first second should sound (part of the hook)
    "first_second_min_dbfs": -40.0,
}

ACCENT_ROLES = {"hit", "impact", "whoosh", "riser", "boom", "drop", "swell", "stinger", "logo", "transition", "wipe",
                "thump", "cut_hit", "reverse_swell", "braam", "sting"}
SHORT_ROLES = {"hit", "impact", "click", "pop", "key", "tick", "thump", "ui", "knock", "tap", "select", "toggle",
               "cut_hit", "bell", "chime", "coin", "drop_water", "bead", "snap"}


# ---------------------------------------------------------------------------------------------------------- ffmpeg
def need_tools():
    miss = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
    if miss:
        print("BLOCKED: no " + ", ".join(miss) + " in PATH. Windows: winget install Gyan.FFmpeg; macOS: brew install "
              "ffmpeg; Linux: apt install ffmpeg. Then open a new terminal.", file=sys.stderr)
        sys.exit(2)


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,channels,sample_rate:format=duration",
             "-of", "json", str(path)])
    if r.returncode != 0:
        sys.exit(f"cannot read {path}: {r.stderr.strip()[:300]}")
    d = json.loads(r.stdout or "{}")
    aud = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    vid = [s for s in d.get("streams", []) if s.get("codec_type") == "video"]
    return {"duration": float(d.get("format", {}).get("duration") or 0), "audio": bool(aud),
            "channels": int(aud[0].get("channels") or 0) if aud else 0, "video": bool(vid)}


def loudness(path, pre=None, series=False):
    """BS.1770 integrated loudness, LRA, true peak; with series=True also the momentary loudness every 100 ms."""
    af = (pre + "," if pre else "") + "ebur128=peak=true" + (":framelog=verbose" if series else "")
    r = run(["ffmpeg", "-nostats", "-hide_banner"] + (["-v", "verbose"] if series else []) +
            ["-i", str(path), "-map", "0:a:0", "-af", af, "-f", "null", "-"])
    err = r.stderr
    out = {"I": None, "LRA": None, "TP": None, "M": []}
    summ = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    m = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summ)
    out["I"] = float(m.group(1)) if m and m.group(1) != "-inf" else None
    m = re.search(r"LRA:\s+(-?[\d.]+) LU", summ)
    out["LRA"] = float(m.group(1)) if m else None
    m = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summ)
    out["TP"] = float(m.group(1)) if m and m.group(1) != "-inf" else -120.0
    if series:
        for t, mm in re.findall(r" t: ([\d.]+)\s+TARGET:.*?M:\s*(-?[\d.]+|-inf)", err):
            out["M"].append((float(t), float(mm) if mm != "-inf" else -120.0))
    return out


def rms_db_many(path, chains):
    """RMS level (dBFS) of the audio after each filter chain, in one ffmpeg pass."""
    n = len(chains)
    graph = f"[0:a:0]asplit={n}" + "".join(f"[s{i}]" for i in range(n)) + ";"
    graph += ";".join(f"[s{i}]{c + ',' if c else ''}astats=metadata=0:measure_perchannel=none[o{i}]"
                      for i, c in enumerate(chains))
    args = ["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-filter_complex", graph]
    for i in range(n):
        args += ["-map", f"[o{i}]", "-f", "null", "-"]
    r = run(args)
    vals = {}
    for idx, v in re.findall(r"\[Parsed_astats_(\d+) @[^\]]*\]\s*RMS level dB:\s*(-?[\d.]+|-inf)", r.stderr):
        vals.setdefault(int(idx), float(v) if v != "-inf" else -150.0)
    order = sorted(vals)
    return [vals[k] for k in order] if len(order) == n else [None] * n


def decode(path, sr=16000, ch=1, start=None, dur=None):
    args = ["ffmpeg", "-v", "error"]
    if start is not None:
        args += ["-ss", f"{start:.3f}"]
    if dur is not None:
        args += ["-t", f"{dur:.3f}"]
    # ffmpeg's own stereo->mono downmix adds the channels at 0.707 each (+3 dB on a centred sound): average them
    mono = "pan=mono|c0=0.5*c0+0.5*c1," if ch == 1 and probe(path)["channels"] >= 2 else ""
    args += ["-i", str(path), "-map", "0:a:0", "-af", f"{mono}aresample={sr}", "-ac", str(ch), "-f", "f32le", "-"]
    r = subprocess.run(args, capture_output=True)
    a = array.array("f")
    a.frombytes(r.stdout[: len(r.stdout) // 4 * 4])
    return a


def envelope(samples, sr, win_ms=5.0):
    """Peak level (dBFS) per window."""
    w = max(1, int(sr * win_ms / 1000))
    env = []
    for i in range(0, len(samples), w):
        seg = samples[i:i + w]
        p = max(max(seg), -min(seg)) if seg else 0.0
        env.append(20 * math.log10(p) if p > 1e-7 else -140.0)
    return env


def db(x):
    return 10 * math.log10(x) if x > 1e-15 else -150.0


def fmt_t(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


# ---------------------------------------------------------------------------------------------------------- report
class Report:
    def __init__(self):
        self.rows, self.data = [], {}

    def add(self, status, name, value, fix=""):
        self.rows.append({"status": status, "check": name, "value": value, "fix": fix})

    def verdict(self):
        st = [r["status"] for r in self.rows]
        return "FAIL" if "FAIL" in st else ("WARN" if "WARN" in st else "PASS")

    def print(self):
        for r in self.rows:
            line = f"{r['status']:<5} {r['check']}: {r['value']}"
            if r["fix"] and r["status"] in ("FAIL", "WARN"):
                line += f"\n      -> {r['fix']}"
            print(line)
        print(f"VERDICT: {self.verdict()}")


# ---------------------------------------------------------------------------------------------------------- checks
BANDS = [("sub <60", "lowpass=f=60,lowpass=f=60"),
         ("low 60-250", "highpass=f=60,lowpass=f=250"),
         ("mid 250-2k", "highpass=f=250,lowpass=f=2000"),
         ("presence 2-6k", "highpass=f=2000,lowpass=f=6000"),
         ("air >6k", "highpass=f=6000,highpass=f=6000")]


def band_shares(path):
    vals = rms_db_many(path, [c for _, c in BANDS])
    if None in vals:
        return None
    p = [10 ** (v / 10) for v in vals]
    tot = sum(p) or 1e-12
    return {name: round(100 * x / tot, 1) for (name, _), x in zip(BANDS, p)}


def mono_loss(path):
    l, r, m = rms_db_many(path, ["pan=mono|c0=c0", "pan=mono|c0=c1", "pan=mono|c0=0.5*c0+0.5*c1"])
    if None in (l, r, m):
        return None
    mean_lr = db((10 ** (l / 10) + 10 ** (r / 10)) / 2)
    return round(mean_lr - m, 2)


def check_mix(a, rep):
    info = probe(a.file)
    if not info["audio"]:
        rep.add("FAIL", "audio", "в файле нет звуковой дорожки", "собери файл со звуком (mix.py / mixdown.py)")
        return
    plat = PLATFORMS.get(a.platform)
    L = loudness(a.file, series=True)
    rep.data.update({"duration_s": round(info["duration"], 2), "integrated_lufs": L["I"], "lra_lu": L["LRA"],
                     "true_peak_dbtp": L["TP"], "platform": a.platform})
    # loudness
    if L["I"] is None:
        rep.add("FAIL", "громкость", "тишина (интегральная громкость не измеряется)", "в файле нет звука выше -70 LUFS")
        return
    if plat:
        d = L["I"] - plat["I"]
        st = "PASS" if abs(d) <= plat["tol"] else ("WARN" if abs(d) <= plat["tol"] + 1.0 else "FAIL")
        rep.add(st, f"громкость ({plat['label']})", f"{L['I']:.1f} LUFS при норме {plat['I']:.0f} ±{plat['tol']:g}",
                f"python mixdown.py master IN OUT --platform {a.platform}  (усиление + лимитер true peak, проверка после кодека), "
                f"или ffmpeg -i IN -af loudnorm=I={plat['I']:g}:TP={plat['tp']:g}:LRA=11 OUT")
        st = "PASS" if L["TP"] <= plat["tp"] + 0.05 else ("WARN" if L["TP"] <= 0.0 else "FAIL")
        rep.add(st, "true peak", f"{L['TP']:.1f} dBTP при потолке {plat['tp']:g}",
                f"лимитер перед кодеком: alimiter=limit={10 ** ((plat['tp'] - 0.5) / 20):.3f}:level=false, "
                f"или mixdown.py master (лимитирует сам)")
        if L["LRA"] is not None:
            st = "PASS" if L["LRA"] <= plat["lra_max"] else "WARN"
            rep.add(st, "диапазон громкости LRA", f"{L['LRA']:.1f} LU (ориентир до {plat['lra_max']:g})",
                    "тихие места потеряются на телефоне: компрессия голоса acompressor=threshold=-24dB:ratio=3:"
                    "attack=10:release=150 или поднять тихие сцены")
    else:
        rep.add("INFO", "громкость", f"{L['I']:.1f} LUFS, true peak {L['TP']:.1f} dBTP, LRA {L['LRA']} LU")

    # phone speaker
    Lp = loudness(a.file, pre="highpass=f=150,highpass=f=150")
    if Lp["I"] is not None:
        drop = L["I"] - Lp["I"]
        rep.data["phone_drop_lu"] = round(drop, 1)
        st = "PASS" if drop <= THRESHOLDS["phone_drop_warn"] else "WARN"
        rep.add(st, "динамик телефона (срез ниже 150 Гц)", f"громкость падает на {drop:.1f} LU",
                "громкость держится на басе, которого телефон не играет: срежь саб у музыки/эффектов "
                "(highpass=f=40), добавь гармоники баса (лёгкая сатурация) или подними середину голоса 1-4 кГц")

    # mono
    if info["channels"] >= 2:
        ml = mono_loss(a.file)
        if ml is not None:
            rep.data["mono_loss_db"] = ml
            st = "PASS" if ml <= THRESHOLDS["mono_warn"] else ("WARN" if ml <= THRESHOLDS["mono_fail"] else "FAIL")
            rep.add(st, "моно-совместимость", f"сумма в моно теряет {ml:.1f} дБ",
                    "что-то в противофазе: найди звук (verify.py real-sfx печатает строку mono:) и поставь ему "
                    "\"mono\": true, или сузь стерео: stereotools=mlev=1:slev=0.6")

    # tonal balance (orientation, not a norm)
    bs = band_shares(a.file)
    if bs:
        rep.data["band_energy_pct"] = bs
        notes = []
        if bs["sub <60"] > 35:
            notes.append("гул в сабе (>35 % энергии ниже 60 Гц)")
        if bs["presence 2-6k"] < 2:
            notes.append("глухо: почти нет 2-6 кГц (разборчивость)")
        if bs["air >6k"] > 25:
            notes.append("резко: >25 % энергии выше 6 кГц")
        rep.add("WARN" if notes else "PASS", "тональный баланс (ориентир)",
                ", ".join(f"{k} {v}%" for k, v in bs.items()) + (f"; {'; '.join(notes)}" if notes else ""),
                "сравни с референсом той же площадки: python sound_check.py --ab REF.wav MIX.wav")

    # first second, silence
    s = decode(a.file, sr=8000, ch=1)
    env = envelope(s, 8000, 5.0)
    first = max(env[:200]) if env else -140
    rep.data["first_second_peak_dbfs"] = round(first, 1)
    if first < THRESHOLDS["first_second_min_dbfs"]:
        rep.add("WARN", "первая секунда", f"пик {first:.0f} dBFS: начало почти беззвучное",
                "звук на первом кадре — часть хука: акцент на 0.0-0.3 с или музыка с первой доли")
    w = 50                                           # 50 x 5 ms = 250 ms windows
    wins = [max(env[i:i + w]) for i in range(0, max(0, len(env) - w + 1), w)]
    if wins:
        sil = sum(1 for v in wins if v < -70) / len(wins)
        rep.data["digital_silence_frac"] = round(sil, 3)
        if a.sfx_only:
            st = "PASS" if sil <= THRESHOLDS["silence_warn_frac"] else "WARN"
            rep.add(st, "цифровая тишина между звуками", f"{100 * sil:.0f}% окон по 250 мс тише -70 dBFS",
                    "плёнка звучит голо: подложи атмосферу (bed.py real-sfx, уровень -54 dBFS)")

    # stems
    if a.voice:
        check_voice(a, rep)
    if a.cues:
        check_cues(a, rep, info["duration"])


def speech_frames(vM, vI):
    return [i for i, (t, m) in enumerate(vM) if m > max(-50.0, (vI or -30) - 10)]


def check_voice(a, rep):
    V = loudness(a.voice, series=True)
    if V["I"] is None or not V["M"]:
        rep.add("WARN", "голос", "в дорожке голоса нет звука", "проверь путь к стему голоса")
        return
    sp = set(speech_frames(V["M"], V["I"]))
    if not sp:
        rep.add("WARN", "голос", f"речь не найдена: голос тише -50 LUFS (интегрально {V['I']:.0f} LUFS)",
                "проверь, что передан стем голоса в том виде, как он стоит в миксе")
        return
    rep.data["speech_share"] = round(len(sp) / max(1, len(V["M"])), 2)
    if a.music:
        Mu = loudness(a.music, series=True)
        n = min(len(Mu["M"]), len(V["M"]))
        margins = [V["M"][i][1] - Mu["M"][i][1] for i in range(n) if i in sp and Mu["M"][i][1] > -70]
        quiet = max(-60.0, (V["I"] or -30) - 20)       # clear pauses only, not the tails of words
        pauses = [Mu["M"][i][1] for i in range(n) if V["M"][i][1] < quiet and Mu["M"][i][1] > -70]
        under = [Mu["M"][i][1] for i in range(n) if i in sp and Mu["M"][i][1] > -70]
        if margins:
            med = statistics.median(margins)
            low10 = sorted(margins)[max(0, len(margins) // 10 - 1)]
            rep.data["voice_over_music_lu"] = round(med, 1)
            rep.data["voice_over_music_worst10_lu"] = round(low10, 1)
            st = ("FAIL" if med < THRESHOLDS["voice_margin_fail"] else
                  "WARN" if med < THRESHOLDS["voice_margin_warn"] else "PASS")
            rep.add(st, "голос над музыкой", f"медиана {med:.1f} LU, худшие 10% {low10:.1f} LU (рабочий диапазон 12-20)",
                    f"опусти музыку на {max(0.0, 12 - med):.0f} дБ или углуби даккинг: "
                    "python mixdown.py mix --voice V --music M --duck-db 10 ...")
            def mg(i):
                return V["M"][i][1] - Mu["M"][i][1]
            # a stretch of at least 300 ms inside speech (the edges of words are not judged)
            worst = sorted((max(mg(i - 1), mg(i), mg(i + 1)), V["M"][i][0]) for i in range(1, n - 1)
                           if {i - 1, i, i + 1} <= sp and Mu["M"][i][1] > -70)[:3]
            if worst and worst[0][0] < THRESHOLDS["voice_margin_fail"]:
                rep.add("WARN", "где голос тонет", ", ".join(f"{fmt_t(t)} ({m:.0f} LU)" for m, t in worst),
                        "послушай эти места; точечно: volume=enable='between(t,T1,T2)':volume=-4dB на музыке")
        else:
            rep.add("INFO", "голос над музыкой", "музыка не звучит во время речи")
        if under and pauses:
            depth = statistics.median(pauses) - statistics.median(under)
            rep.data["duck_depth_db"] = round(depth, 1)
            rep.add("INFO", "глубина даккинга", f"музыка в паузах громче, чем под речью, на {depth:.1f} дБ "
                    "(ориентир 6-10 дБ)")
    if a.sfx:
        S = loudness(a.sfx, series=True)
        n = min(len(S["M"]), len(V["M"]))
        bad = [S["M"][i][0] for i in range(n)
               if i in sp and S["M"][i][1] > V["M"][i][1] + THRESHOLDS["sfx_over_voice_db"]]
        # group consecutive frames
        groups = []
        for t in bad:
            if groups and t - groups[-1][1] <= 0.15:
                groups[-1][1] = t
            else:
                groups.append([t, t])
        rep.data["sfx_over_voice"] = [round(g[0], 2) for g in groups]
        st = "PASS" if not groups else "WARN"
        rep.add(st, "эффекты поверх речи", "нет" if not groups else
                f"{len(groups)} мест(а): " + ", ".join(fmt_t(g[0]) for g in groups[:6]),
                "сдвинь эффект в паузу речи, опусти его (sheet.py gain SHEET --db -4 --between T1 T2) или mix.py --voice-safe")


def load_cues(path):
    d = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    cues = d.get("cues", d) if isinstance(d, dict) else d
    out = []
    load_cues.resolved = any(isinstance(c, dict) and "anchor" in c and "file" in c for c in cues)
    for c in cues:
        if not isinstance(c, dict) or "t" not in c or c.get("bed") or c.get("texture"):
            continue
        role = str(c.get("role") or c.get("type") or c.get("kind") or c.get("label") or "").lower().split()[0:1]
        out.append({"t": float(c["t"]), "role": role[0] if role else ""})
    return sorted(out, key=lambda c: c["t"])


def check_cues(a, rep, duration):
    cues = load_cues(a.cues)
    rep.data["cues"] = len(cues)
    acc = [c["t"] for c in cues if c["role"] in ACCENT_ROLES]
    if acc and duration > 0:
        per = []
        t0 = 0.0
        while t0 < duration - 1e-6:
            per.append((t0, sum(1 for t in acc if t0 <= t < t0 + 15)))
            t0 += 15
        mx = max(per, key=lambda x: x[1])
        rep.data["accents_per_15s"] = [n for _, n in per]
        if not a.sfx_only and mx[1] > THRESHOLDS["accents_per_15s_max"]:
            rep.add("WARN", "темп акцентов", f"{mx[1]} крупных акцентов в окне {fmt_t(mx[0])}-{fmt_t(mx[0] + 15)} "
                    "(ориентир 3-6 на 15 с под музыкой или голосом)",
                    "ковёр вместо акцентов: оставь удар/вжух на главных склейках, остальное убери или опусти на 6 дБ")
        else:
            rep.add("PASS", "темп акцентов", "по окнам 15 с: " + ", ".join(str(n) for _, n in per))
    if a.sfx and getattr(load_cues, "resolved", False):
        rep.add("INFO", "синхрон", "лист real-sfx: синхрон по якорю каждого звука проверяет verify.py "
                "(строка 'N present, N judged (K off)'), его вердикт главный")
    elif a.sfx:
        s = decode(a.sfx, sr=8000, ch=1)
        env = envelope(s, 8000, 2.5)                    # 2.5 ms windows
        res, offs = [], []
        for c in cues:
            if c["role"] not in SHORT_ROLES:
                continue
            i0 = max(0, int((c["t"] - 0.25) / 0.0025))
            i1 = min(len(env), int((c["t"] + 0.25) / 0.0025))
            best = None
            for i in range(i0 + 8, i1):
                floor = max(env[i - 8:i])                # the 20 ms before
                if env[i] > -50 and env[i] - floor >= 10:
                    t = i * 0.0025
                    if best is None or abs(t - c["t"]) < abs(best - c["t"]):
                        best = t
            if best is None:
                res.append((c["t"], None))
            else:
                offs.append(1000 * (best - c["t"]))
                res.append((c["t"], offs[-1]))
        if res:
            miss = [t for t, o in res if o is None or abs(o) > THRESHOLDS["sync_warn_ms"]]
            late = [t for t, o in res if o is not None and THRESHOLDS["sync_ok_ms"] < abs(o) <= THRESHOLDS["sync_warn_ms"]]
            med = statistics.median(offs) if offs else None
            rep.data["sync_short"] = {"n": len(res), "median_ms": round(med, 1) if med is not None else None,
                                      "miss": [round(t, 2) for t in miss], "loose": [round(t, 2) for t in late]}
            st = "FAIL" if len(miss) > max(1, len(res) // 10) else ("WARN" if miss or late else "PASS")
            rep.add(st, "синхрон коротких звуков", f"{len(res)} звуков, медиана {med:+.0f} мс" if med is not None
                    else f"{len(res)} звуков, ни одной атаки рядом с метками",
                    (f"мимо (>100 мс или нет атаки): {', '.join(fmt_t(t) for t in miss[:8])}; " if miss else "") +
                    (f"неточно (45-100 мс): {', '.join(fmt_t(t) for t in late[:8])}; " if late else "") +
                    "сдвиг: sheet.py shift SHEET --by -0.04 --role click, проверка verify.py real-sfx")


# ---------------------------------------------------------------------------------------------------------- clip
def clip_stats(path):
    info = probe(path)
    sr = 16000
    s = decode(path, sr=sr, ch=1)
    if not s:
        sys.exit(f"no audio in {path}")
    env = envelope(s, sr, 1.0)                         # 1 ms
    pk = max(env)
    ipk = env.index(pk)
    above = [i for i, v in enumerate(env) if v > pk - 40]
    start, end = (above[0], above[-1]) if above else (0, len(env) - 1)
    # attack: from -20 dB under the peak to -3 dB under it
    a20 = next((i for i in range(start, ipk + 1) if env[i] >= pk - 20), start)
    a3 = next((i for i in range(a20, ipk + 1) if env[i] >= pk - 3), ipk)
    # decay: from the peak to 30 dB under it
    d30 = next((i for i in range(ipk, len(env)) if env[i] < pk - 30), len(env) - 1)
    L = loudness(path, pre="apad=pad_dur=0.5", series=True)
    maxM = max((m for _, m in L["M"]), default=None)
    aud = max(0.001, (end - start) / 1000)
    # a sound shorter than the 400 ms window reads quieter than it is: the loudness of its audible part
    clip_l = None if maxM is None or maxM < -70 else round(maxM + (10 * math.log10(0.4 / aud) if aud < 0.4 else 0), 1)
    bs = band_shares(path)
    return {"file": str(path), "duration_s": round(info["duration"], 3), "audible_s": round((end - start) / 1000, 3),
            "lead_silence_ms": start, "peak_dbfs": round(pk, 1), "true_peak_dbtp": L["TP"],
            "peak_at_ms": ipk, "attack_ms": a3 - a20, "decay_to_-30db_ms": d30 - ipk,
            "integrated_lufs": L["I"], "max_momentary_lufs": maxM, "clip_lufs": clip_l, "band_energy_pct": bs,
            "channels": info["channels"]}


ROLE_SHAPE = {  # what a role usually measures like in finished films (real-sfx and earshot measurements, sfx-design)
    "hit": {"attack_ms": (0, 15), "audible_s": (0.15, 1.5)},
    "click": {"attack_ms": (0, 5), "audible_s": (0.01, 0.15)},
    "pop": {"attack_ms": (0, 10), "audible_s": (0.03, 0.35)},
    "whoosh": {"attack_ms": (60, 900), "audible_s": (0.25, 1.6)},
    "riser": {"attack_ms": (800, 8000), "audible_s": (1.0, 8.0)},
    "ui": {"attack_ms": (0, 10), "audible_s": (0.02, 0.7)},
    "chime": {"attack_ms": (0, 15), "audible_s": (0.2, 2.0)},
    "ambience": {"audible_s": (5.0, 1e9)},
}


def check_clip(a, rep):
    st = clip_stats(a.clip)
    rep.data.update(st)
    rep.add("INFO", "звук", f"слышно {st['audible_s']:.2f} с (тишина в начале {st['lead_silence_ms']} мс), "
            f"атака {st['attack_ms']} мс, спад до -30 дБ {st['decay_to_-30db_ms']} мс, пик {st['peak_dbfs']} dBFS "
            f"на {st['peak_at_ms']} мс, громкость звука {st['clip_lufs']} LUFS")
    if st["band_energy_pct"]:
        rep.add("INFO", "тембр", ", ".join(f"{k} {v}%" for k, v in st["band_energy_pct"].items()))
    if st["true_peak_dbtp"] is not None and st["true_peak_dbtp"] > -0.1:
        rep.add("FAIL", "клиппинг", f"true peak {st['true_peak_dbtp']:.1f} dBTP",
                "нормализуй пик: ffmpeg -i IN -af volume=-1.5dB OUT, или loudnorm/alimiter")
    if st["lead_silence_ms"] > 30:
        rep.add("WARN", "тишина в начале", f"{st['lead_silence_ms']} мс до звука",
                f"обрежь: ffmpeg -ss {st['lead_silence_ms'] / 1000:.3f} -i IN OUT, иначе звук опоздает к кадру")
    shape = ROLE_SHAPE.get(a.role or "")
    if shape:
        for k, (lo, hi) in shape.items():
            v = st.get(k)
            if v is None:
                continue
            ok = lo <= v <= hi
            rep.add("PASS" if ok else "WARN", f"форма для роли {a.role}: {k}", f"{v} (обычно {lo}-{hi})",
                    "другой кандидат, обрезка (atrim) или fit_dur/pitch в листе real-sfx")


def check_ab(a, rep):
    A, B = clip_stats(a.ab[0]), clip_stats(a.ab[1])
    la, lb = A["clip_lufs"], B["clip_lufs"]
    rep.data.update({"a": A, "b": B})
    if la is not None and lb is not None:
        rep.add("INFO", "громкость", f"B громче A на {lb - la:+.1f} LU: сравнивай после выравнивания "
                f"(ffmpeg -i B -af volume={la - lb:+.1f}dB B_matched.wav), громче почти всегда кажется лучше")
    if A["band_energy_pct"] and B["band_energy_pct"]:
        diffs = [f"{k} {B['band_energy_pct'][k] - A['band_energy_pct'][k]:+.1f} п.п." for k in A["band_energy_pct"]]
        rep.add("INFO", "тембр B относительно A", ", ".join(diffs))
    rep.add("INFO", "форма", f"атака {A['attack_ms']} -> {B['attack_ms']} мс, спад {A['decay_to_-30db_ms']} -> "
            f"{B['decay_to_-30db_ms']} мс, длина {A['audible_s']} -> {B['audible_s']} с")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="finished film or track")
    ap.add_argument("--platform", default="social", choices=sorted(PLATFORMS))
    ap.add_argument("--voice", help="voice stem as it sits in the mix (same start, same gain)")
    ap.add_argument("--music", help="music stem as it sits in the mix")
    ap.add_argument("--sfx", help="effects-only track (real-sfx: *_sfx_track.wav or *_sfx_track_nobed.wav)")
    ap.add_argument("--cues", help="cue list or real-sfx resolved cues JSON")
    ap.add_argument("--sfx-only", action="store_true", help="the film's sound is only effects (no music, no voice)")
    ap.add_argument("--clip", help="measure one sound")
    ap.add_argument("--role", help="with --clip: expected role (hit, click, pop, whoosh, riser, ui, chime, ambience)")
    ap.add_argument("--ab", nargs=2, metavar=("A", "B"), help="compare two sounds")
    ap.add_argument("--json", help="write the numbers and verdict here")
    a = ap.parse_args()
    need_tools()
    rep = Report()
    if a.clip:
        check_clip(a, rep)
    elif a.ab:
        check_ab(a, rep)
    elif a.file:
        check_mix(a, rep)
    else:
        ap.error("give a FILE, --clip or --ab")
    rep.print()
    if a.json:
        Path(a.json).write_text(json.dumps({"verdict": rep.verdict(), "checks": rep.rows, "data": rep.data},
                                           ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit({"PASS": 0, "WARN": 1, "FAIL": 2}[rep.verdict()])


if __name__ == "__main__":
    main()
