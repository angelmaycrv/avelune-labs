#!/usr/bin/env python3
"""concept_check: does the finished sound follow the sound concept written before any sound was picked?

The agent cannot hear, so taste is checked against a written intent (work/concept.json, step 1.5 of video-sound):
the tone of the brand, the one hero moment, the moments that stay silent, the music policy, the material palette.
This script compares that intent with what real-sfx actually placed (*_resolved_cues.json).

  python concept_check.py work/concept.json result/film_sfx_resolved_cues.json [--json result/concept_check.json]
  python concept_check.py --template > work/concept.json      # an empty concept to fill in

Exit code: 0 PASS, 1 WARN, 2 FAIL. Every WARN/FAIL line ends with a fix after '->'.
Why these rules (sources in ../references/craft.md):
  - one hero moment, louder than the rest, with air before it (Thom: contrast; Murch: density obeys dynamics)
  - at most 2-3 sounds of one kind at once, about 5 in all (Murch, "law of two and a half")
  - one object, one source (a slot machine made of three libraries does not read as one machine)
  - tone decides the palette (sonic branding: brand attributes -> sound attributes)
  - music only by the concept (never carried over from another task)
"""
import argparse
import json
import os
import statistics
import sys
from pathlib import Path

TEMPLATE = {
    "_help": "Fill BEFORE picking sounds, from THIS film's frames and brief (nothing from earlier tasks). Times in "
             "seconds. Replace every <...>. See video-sound SKILL.md step 1.5 and references/craft.md.",
    "genre": "<one of: brand-promo, product-ui, app-ad, meme, edit, tutorial, story, game-trailer>",
    "tone": ["<1-2 of: premium, luxury, brand, corporate, tech, playful, kids, calm, wellness, energetic, meme, epic, dark>"],
    "audience_feel": "<one sentence: what the viewer feels at the end>",
    "arc": [{"t": 0.0, "beat": "hook: <what happens>"}, {"t": None, "beat": "build: <...>"},
            {"t": None, "beat": "payoff: <...>"}],
    "hero": {"t": None, "what": "<the one moment that matters most>", "treatment": "<e.g. impact + tail>"},
    "objects": [{"name": "<an object that sounds several times>", "times": [None, None], "material": "<one source>"}],
    "silent": [{"from": None, "to": None, "why": "<breath before the hero, a pause after it>"}],
    "music": "none",
    "palette": ["<2-3 material families for the whole film>"],
    "avoid": ["<words of file names that do not fit the tone>"],
}

# tone -> roles that do not belong (FAIL if used), roles to keep rare (WARN above max count)
TONE_RULES = {
    "premium":   {"forbid": {"meme", "cartoon"}, "rare": {"glitch": 1, "sub_drop": 1, "error": 0}},
    "luxury":    {"forbid": {"meme", "cartoon"}, "rare": {"glitch": 0, "sub_drop": 1, "error": 0}},
    "brand":     {"forbid": {"meme"}, "rare": {"sub_drop": 1, "error": 0}},
    "corporate": {"forbid": {"meme", "cartoon"}, "rare": {"glitch": 1, "sub_drop": 1}},
    "tech":      {"forbid": {"meme", "cartoon"}, "rare": {"sub_drop": 1}},
    "calm":      {"forbid": {"meme", "glitch", "error"}, "rare": {"hit": 2, "sub_drop": 0, "whoosh": 3}},
    "wellness":  {"forbid": {"meme", "glitch", "error"}, "rare": {"hit": 1, "sub_drop": 0}},
    "kids":      {"forbid": {"error"}, "rare": {"sub_drop": 0, "glitch": 0}},
    "playful":   {"forbid": set(), "rare": {"sub_drop": 1}},
    "energetic": {"forbid": set(), "rare": {}},
    "meme":      {"forbid": set(), "rare": {}},
    "dark":      {"forbid": {"cartoon"}, "rare": {}},
    "epic":      {"forbid": {"cartoon", "meme"}, "rare": {}},
}
# roles that share a "colour" (Murch): sounds of one colour mask each other first
COLOUR = {"hit": "impact", "sub_drop": "impact", "design": "impact", "thump": "impact",
          "whoosh": "air", "riser": "air", "glitch": "air",
          "click": "tick", "ui": "tick", "pop": "tick", "typing": "tick", "data": "tick",
          "chime": "tone", "coin": "tone", "glass": "tone",
          "foley": "object", "paper": "object", "water": "object", "camera": "object",
          "ambience": "bed"}


class Report:
    def __init__(self):
        self.rows, self.data = [], {}

    def add(self, st, name, value, fix=""):
        self.rows.append({"status": st, "check": name, "value": value, "fix": fix})

    def verdict(self):
        s = {r["status"] for r in self.rows}
        return "FAIL" if "FAIL" in s else "WARN" if "WARN" in s else "PASS"

    def print(self):
        for r in self.rows:
            print(f"{r['status']:5s} {r['check']}: {r['value']}")
            if r["fix"] and r["status"] in ("WARN", "FAIL"):
                print(f"      -> {r['fix']}")
        print(f"VERDICT: {self.verdict()}")


def level(c):
    for k in ("peak_after_db", "loud_after_db"):      # peak: short clips gate low on loudness
        if c.get(k) is not None:
            return float(c[k])
    return None


def span(c, cap=None):
    s = c.get("start")
    s = float(s) if s is not None else float(c["t"])
    d = max(0.05, float(c.get("seg") or 0.3))
    return s, s + (min(d, cap) if cap else d)


def src_path(c):
    return Path(str(c.get("source_file") or c.get("file") or "").replace("\\", "/"))


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def check_quality(concept, fx, rep):
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "real-sfx" / "scripts"))
        import quality
    except Exception as e:
        rep.add("WARN", "качество записей", f"не проверено: {e}")
        return
    ht = (concept.get("hero") or {}).get("t")
    obj = [(float(o["times"][0]), float(o["times"][1])) for o in concept.get("objects") or []
           if len(o.get("times") or []) == 2]
    graded, bad_hero, bad_key, broken, prev = {}, [], [], [], []
    for c in fx:
        f = str(c.get("source_file") or c.get("file") or "")
        if not f or not Path(f).exists():
            continue
        if f not in graded:
            graded[f] = quality.grade(f, c.get("role"))
        q = graded[f]
        t = float(c["t"])
        is_hero = ht is not None and abs(t - float(ht)) <= 0.12
        is_obj = any(a - 0.05 <= t <= b + 0.05 for a, b in obj)
        tag = f"{fmt(t)} {c.get('role')} {Path(f.replace(chr(92), '/')).name[:40]} [{q['grade']}: {(q.get('why') or ['-'])[0]}]"
        if q["grade"] == "D":
            broken.append(tag)
        elif q["grade"] == "C" and is_hero:
            bad_hero.append(tag)
        elif q["grade"] == "C" and is_obj:
            bad_key.append(tag)
        elif q["grade"] == "C":
            prev.append(tag)
    counts = {}
    for q in graded.values():
        counts[q["grade"]] = counts.get(q["grade"], 0) + 1
    rep.data["quality"] = {"counts": counts, "files": {k: {"grade": v["grade"], "why": v.get("why")} for k, v in graded.items()}}
    summary = ", ".join(f"{g} {counts[g]}" for g in sorted(counts)) or "нет файлов"
    if broken:
        rep.add("FAIL", "качество записей", "битые записи (клиппинг, шум у самого звука, пережатие): " + "; ".join(broken)[:400],
                "замени эти звуки: picker уже опускает оценку D, возьми следующий кандидат или докачай роль "
                "(starter_library.py --for-cues ... --register)")
    if bad_hero:
        rep.add("WARN", "качество главного звука", "главная точка на превью-качестве: " + "; ".join(bad_hero)[:300],
                "главный звук берут студийным (A/B): оригинал со страницы в CREDITS.md, Freesound с входом "
                "(sources.py freesound-login) или своя библиотека")
    if bad_key:
        rep.add("WARN", "качество предметов", "предметы на превью-качестве: " + "; ".join(bad_key)[:300],
                "предмет звучит долго и близко: возьми запись A/B")
    if not broken and not bad_hero and not bad_key:
        rep.add("PASS", "качество записей",
                summary + (f"; превью-качество только у мелочей ({len(prev)})" if prev else ""))


def check(concept, res, rep):
    cues = [c for c in res.get("cues", res if isinstance(res, list) else []) if isinstance(c, dict) and "t" in c]
    fx = [c for c in cues if not c.get("bed") and c.get("role") != "ambience"]
    rep.data["cues"] = len(cues)
    if not cues:
        rep.add("FAIL", "звуки", "в листе нет ни одного звука", "проверь путь к *_resolved_cues.json")
        return
    tones = [t.lower() for t in (concept.get("tone") or [])]
    if not tones or not concept.get("genre") or "<" in json.dumps(concept, ensure_ascii=False):
        rep.add("FAIL", "замысел", "в concept.json остались незаполненные поля <...> (или нет жанра и тона)",
                "заполни concept.json до подбора звуков (шаг 1.5): жанр, тон, герой, тишина, музыка")
        return

    # 1. hero moment
    hero = concept.get("hero") or {}
    if hero.get("t") is None:
        rep.add("FAIL", "главная точка", "в замысле нет главной точки",
                "выбери одну главную точку на 10-15 с (раскрытие, лого, результат) и запиши hero.t")
    else:
        ht = float(hero["t"])
        near = [c for c in fx if abs(float(c["t"]) - ht) <= 0.12]
        if not near:
            rep.add("FAIL", "главная точка", f"на {fmt(ht)} ({hero.get('what', '')}) нет звука",
                    f"поставь главный звук на кадр {fmt(ht)}: удар + хвост, см. рецепт «главная точка» в SKILL.md")
        else:
            hl = max((level(c) for c in near if level(c) is not None), default=None)
            others = [level(c) for c in fx if c not in near and level(c) is not None]
            if hl is not None and others:
                top = max(others)
                med = statistics.median(others)
                rep.data["hero_over_loudest_other_db"] = round(hl - top, 1)
                rep.data["hero_over_median_db"] = round(hl - med, 1)
                if hl < top - 1.0:
                    loudest = max((c for c in fx if c not in near and level(c) is not None), key=level)
                    rep.add("FAIL", "главная точка", f"на {fmt(ht)} тише, чем звук на {fmt(float(loudest['t']))} "
                            f"({loudest.get('role')}, на {top - hl:.1f} дБ громче)",
                            "главная точка должна быть самой громкой: опусти остальные (sheet.py gain work/cues.json "
                            "--db -3 --at T) или подними главную (sheet.py set work/cues.json --at T gain_db=+2)")
                elif hl - top < 2.0:
                    loudest = max((c for c in fx if c not in near and level(c) is not None), key=level)
                    rep.add("WARN", "главная точка", f"{fmt(ht)} почти не громче звука на {fmt(float(loudest['t']))} "
                            f"({loudest.get('role')}, разница {hl - top:+.1f} дБ)",
                            f"опусти звук на {fmt(float(loudest['t']))} на 3-4 дБ: главная точка должна выделяться")
                elif hl - med < 3.0:
                    rep.add("WARN", "главная точка", f"громче середины остальных всего на {hl - med:.1f} дБ",
                            "отдели главную точку: остальное на 3-6 дБ тише")
                else:
                    rep.add("PASS", "главная точка", f"{fmt(ht)}: громче середины на {hl - med:.1f} дБ, "
                            f"громче самого громкого другого на {hl - top:+.1f} дБ")
            busy = [c for c in fx if ht - 0.45 <= span(c)[1] - 0.05 and float(c["t"]) < ht - 0.08
                    and level(c) is not None and hl is not None and level(c) > hl - 6]
            if busy:
                rep.add("WARN", "воздух перед главной точкой",
                        f"{len(busy)} громких звука(ов) в 0.45 с перед {fmt(ht)}: "
                        + ", ".join(f"{fmt(float(c['t']))} {c.get('role')}" for c in busy[:4]),
                        "перед главной точкой нужна пауза или подводка (райзер), а не другие удары: "
                        "убери или опусти их на 6+ дБ")

    # 2. silent zones
    zones = [z for z in (concept.get("silent") or []) if z.get("from") is not None and z.get("to") is not None]
    clean = 0
    for z in zones:
        a, b = float(z["from"]), float(z["to"])
        inside = [c for c in fx if a <= float(c["t"]) < b]
        if inside:
            rep.add("FAIL", "тишина по замыслу", f"{fmt(a)}-{fmt(b)} ({z.get('why', '')}): {len(inside)} звук(а)",
                    "убери звуки из зоны тишины (sheet.py drop work/cues.json --at T) или поправь замысел")
        else:
            clean += 1
    if zones and clean == len(zones):
        rep.add("PASS", "тишина по замыслу", f"{clean} зон(ы) тишины пустые")

    # 3. tone: roles that do not belong
    roles = [c.get("role") for c in fx]
    counts = {r: roles.count(r) for r in set(roles)}
    rep.data["roles"] = counts
    bad, rare_over = set(), []
    for t in tones:
        rule = TONE_RULES.get(t)
        if not rule:
            continue
        bad |= {r for r in counts if r in rule["forbid"]}
        rare_over += [(r, counts.get(r, 0), mx) for r, mx in rule["rare"].items() if counts.get(r, 0) > mx]
    if bad:
        rep.add("FAIL", "тон", f"тон {', '.join(tones)}, а в ролике " + ", ".join(f"{r} x{counts[r]}" for r in sorted(bad)),
                "эти роли не подходят тону: замени их (search.py ... --role) или убери")
    for r, n, mx in sorted(set(rare_over)):
        rep.add("WARN", "тон", f"{r}: {n} (для тона {', '.join(tones)} не больше {mx})",
                "оставь только там, где это главная точка, остальные замени более мягкими")
    for word in concept.get("avoid") or []:
        w = str(word).lower()
        hits = [c for c in fx if w.split()[0] in (src_path(c).name + " " + str(c.get("label", ""))).lower()]
        if hits and len(w) > 3:
            rep.add("WARN", "избегать", f"«{word}» встречается: " + ", ".join(fmt(float(c['t'])) for c in hits[:4]),
                    "замени эти звуки")
    if not bad and not rare_over:
        rep.add("PASS", "тон", f"роли подходят тону {', '.join(tones) or '?'}")

    # 4. music policy
    music = str(concept.get("music") or "none").lower()
    base = [str(b) for b in (res.get("base_audio") or [])] if isinstance(res, dict) else []
    video = str(res.get("video") or "") if isinstance(res, dict) else ""
    extra = [b for b in base if Path(b).name.split(":")[0] != Path(video).name]
    if music.startswith("none") and extra:
        rep.add("FAIL", "музыка", f"в замысле музыки нет, а в сведении подложка: {', '.join(Path(b).name for b in extra)}",
                "убери --base-audio с музыкой: музыку добавляют только по просьбе пользователя (правило 6)")
    elif music.startswith("user:"):
        want = Path(music[5:]).name.lower()
        if extra and not any(want in Path(b).name.lower() for b in extra):
            rep.add("FAIL", "музыка", f"пользователь дал {want}, а в сведении {', '.join(Path(b).name for b in extra)}",
                    "используй трек пользователя")
    else:
        rep.add("PASS", "музыка", f"по замыслу ({music})")

    # 5. density: same colour at once, all at once
    events = []
    for c in fx:
        s, e = span(c, cap=0.8)         # a long decaying tail is not a layer the ear follows
        events += [(s, 1, c), (e, -1, c)]
    events.sort(key=lambda x: (x[0], x[1]))
    active, worst_all, worst_col = [], (0, 0.0), {}
    for t, kind, c in events:
        if kind == 1:
            active.append(c)
            if len(active) > worst_all[0]:
                worst_all = (len(active), t)
            col = COLOUR.get(c.get("role"), c.get("role"))
            n = sum(1 for x in active if COLOUR.get(x.get("role"), x.get("role")) == col)
            if n > worst_col.get(col, (0, 0))[0]:
                worst_col[col] = (n, t)
        elif c in active:
            active.remove(c)
    rep.data["max_simultaneous"] = worst_all[0]
    over_col = {k: v for k, v in worst_col.items() if v[0] > 3}
    if worst_all[0] > 5 or over_col:
        msg = f"до {worst_all[0]} звуков сразу на {fmt(worst_all[1])}"
        if over_col:
            msg += "; одного рода: " + ", ".join(f"{k} x{n} на {fmt(t)}" for k, (n, t) in over_col.items())
        rep.add("WARN", "плотность", msg, "больше 2-3 звуков одного рода сливаются в кашу (Мёрч): оставь главный, "
                "остальные убери или разнеси по времени")
    else:
        rep.add("PASS", "плотность", f"максимум {worst_all[0]} звуков сразу")

    # 6. one object, one source
    for ob in concept.get("objects") or []:
        ts = ob.get("times") or []
        if len(ts) != 2:
            continue
        a, b = float(ts[0]), float(ts[1])
        # the object's own sounds: mechanical/contact roles; a win chime or a whoosh next to it is another object
        inside = [c for c in fx if a - 0.05 <= float(c["t"]) <= b + 0.05
                  and c.get("role") in ("foley", "click", "hit", "thump", "pop", "typing", "ui", "glass", "paper")]
        fams = {}
        for c in inside:
            sp = src_path(c)
            fam = str(sp.parent).lower() + "|" + sp.stem.split("_")[0][:12].lower()
            fams.setdefault(fam, []).append(c)
        if len(fams) > 2:
            rep.add("WARN", "один предмет — один источник",
                    f"«{ob.get('name')}» ({fmt(a)}-{fmt(b)}) собран из {len(fams)} разных записей: "
                    + ", ".join(src_path(v[0]).name for v in fams.values())[:200],
                    "возьми все звуки этого предмета из одной записи (её разные куски: slice) или одного пака")
        elif inside:
            rep.add("PASS", "один предмет — один источник", f"«{ob.get('name')}»: {len(inside)} звук(а) из "
                    f"{len(fams)} записи(ей)")
    # 8. recording quality (real-sfx quality.py): a deaf picker cannot hear hiss or a crushed preview
    if not os.environ.get("AVELUNE_NO_QUALITY"):
        check_quality(concept, fx, rep)
    # 7. arc: something at the hook
    first = min((float(c["t"]) for c in fx), default=99)
    if first > 0.5:
        rep.add("WARN", "хук", f"первый звук только на {fmt(first)}", "первый кадр звучит: акцент на 0.0-0.3 с")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("concept", nargs="?")
    ap.add_argument("resolved", nargs="?", help="real-sfx *_resolved_cues.json")
    ap.add_argument("--json")
    ap.add_argument("--template", action="store_true")
    a = ap.parse_args()
    if a.template:
        print(json.dumps(TEMPLATE, ensure_ascii=False, indent=1))
        return
    if not a.concept or not a.resolved:
        ap.error("give CONCEPT.json and RESOLVED_CUES.json (or --template)")
    concept = json.loads(Path(a.concept).read_text(encoding="utf-8-sig"))
    res = json.loads(Path(a.resolved).read_text(encoding="utf-8-sig"))
    rep = Report()
    check(concept, res, rep)
    rep.print()
    if a.json:
        Path(a.json).write_text(json.dumps({"verdict": rep.verdict(), "checks": rep.rows, "data": rep.data},
                                           ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit({"PASS": 0, "WARN": 1, "FAIL": 2}[rep.verdict()])


if __name__ == "__main__":
    main()
