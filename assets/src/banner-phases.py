#!/usr/bin/env python3
"""Avelune Labs banners: three art directions, RU and EN, 1280x640. Writes banners.html."""
import sys, os

NB = " "
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banners-phases.html")

T = {
    "ru": dict(
        h1=["Маркетинговое", "агентство", "внутри Claude"],
        h1_wide=[f"Маркетинговое агентство", f"внутри{NB}Claude"],
        sub=f"Шесть плагинов, 101{NB}скилл и{NB}совет{NB}директоров из{NB}12{NB}агентов.",
        cmd="/plugin install avelune-ceo@avelune-labs",
        depts=[("ceo", "Руководитель", 22), ("creative", "Креатив и тексты", 20), ("smm", "SMM", 20),
               ("growth", "Рост и продажи", 20), ("insight", "Аналитика и SEO", 12), ("shield", "Защита", 7)],
        board_head=("Отделы", "Скиллов"), total="Всего",
        note=["Совет", "директоров", f"12{NB}мест"],
        task=f"Запусти продвижение стоматологии на{NB}ноябрь, бюджет 150{NB}тысяч",
        plan_head="план из 7 шагов",
        plan=[("avelune-insight:metrics", "первичные записи"),
              ("avelune-insight:local-seo", "карточки на картах"),
              ("avelune-growth:reviews", f"14{NB}отзывов"),
              ("avelune-growth:yandex-direct", f"100{NB}тыс.{NB}₽"),
              ("avelune-smm:content-plan", "VK и Telegram"),
              ("avelune-growth:sales-scripts", "скрипт звонков"),
              ("avelune-insight:report", f"через 2{NB}недели")],
    ),
    "en": dict(
        h1=["A marketing", "agency", "inside Claude"],
        h1_wide=["A marketing agency", f"inside{NB}Claude"],
        sub=f"Six plugins, 101{NB}skills and a{NB}board{NB}of{NB}12{NB}agents.",
        cmd="/plugin install avelune-ceo@avelune-labs",
        depts=[("ceo", "Executive", 22), ("creative", "Creative and copy", 20), ("smm", "Social", 20),
               ("growth", "Growth and sales", 20), ("insight", "Analytics and SEO", 12), ("shield", "Shield", 7)],
        board_head=("Departments", "Skills"), total="Total",
        note=["Board of", "directors", f"12{NB}seats"],
        task=f"Promote a dental clinic in{NB}November, budget 150k{NB}roubles",
        plan_head="a 7-step plan",
        plan=[("avelune-insight:metrics", "first visits"),
              ("avelune-insight:local-seo", "map listings"),
              ("avelune-growth:reviews", f"14{NB}reviews"),
              ("avelune-growth:yandex-direct", f"100k{NB}₽"),
              ("avelune-smm:content-plan", "VK and Telegram"),
              ("avelune-growth:sales-scripts", "call script"),
              ("avelune-insight:report", f"in 2{NB}weeks")],
    ),
}


def moon_svg(uid, d, frac, waxing, lit, dark, crater):
    """Flat moon phase. frac = illuminated fraction (0..1)."""
    r = d / 2
    c = r
    if frac >= 0.999:
        lit_path = f'<circle cx="{c}" cy="{c}" r="{r}"/>'
    else:
        rx = abs(1 - 2 * frac) * r
        sweep = 1 if frac > 0.5 else 0
        p = (f"M{c},{c - r} A{r},{r} 0 0 1 {c},{c + r} "
             f"A{rx:.2f},{r} 0 0 {sweep} {c},{c - r} Z")
        tr = "" if waxing else f' transform="translate({d},0) scale(-1,1)"'
        lit_path = f'<path d="{p}"{tr}/>'
    # craters: fixed relative positions, clipped to the lit area
    cr = [(0.30, 0.34, 0.11), (0.62, 0.26, 0.07), (0.70, 0.62, 0.13), (0.38, 0.70, 0.08), (0.52, 0.48, 0.05)]
    if frac < 0.3:
        cr = []
    craters = "".join(f'<circle cx="{x * d:.1f}" cy="{y * d:.1f}" r="{s * d:.1f}"/>' for x, y, s in cr)
    return (f'<svg class="moon" width="{d}" height="{d}" viewBox="0 0 {d} {d}" aria-hidden="true">'
            f'<defs><clipPath id="lit-{uid}">{lit_path}</clipPath></defs>'
            f'<circle cx="{c}" cy="{c}" r="{r}" fill="{dark}"/>'
            f'<g fill="{lit}">{lit_path}</g>'
            f'<g fill="{crater}" clip-path="url(#lit-{uid})">{craters}</g></svg>')


def h1(lines):
    return "<br>".join(lines)


def banner_phases(lang, t):
    # order on the row: a full lunar cycle with the conductor as the full moon
    order = ["creative", "smm", "growth", "ceo", "insight", "shield"]
    phase = {"creative": (0.18, True), "smm": (0.5, True), "growth": (0.8, True),
             "ceo": (1.0, True), "insight": (0.72, False), "shield": (0.4, False)}
    names = {k: n for k, n, _ in t["depts"]}
    cells = []
    for k in order:
        f, wx = phase[k]
        lit = "#F6D44A" if k == "ceo" else "#F4EFE4"
        crater = "#E3BF2E" if k == "ceo" else "#DCD5C6"
        svg = moon_svg(f"{lang}-{k}", 164, f, wx, lit, "#1430A6", crater)
        cells.append(f'<li>{svg}<span class="dept">{names[k]}</span>'
                     f'<span class="slug">avelune-{k}</span></li>')
    return f'''
<section class="banner phases" id="phases-{lang}" lang="{lang}">
  <p class="mark">Avelune Labs</p>
  <h1>{h1(t["h1_wide"])}</h1>
  <p class="sub">{t["sub"]}</p>
  <code class="cmd">{t["cmd"]}</code>
  <ol class="cycle">{"".join(cells)}</ol>
</section>'''


def banner_directory(lang, t):
    rows = "".join(f'<li><span>{n}</span><span>{c}</span></li>' for _, n, c in t["depts"])
    total = sum(c for *_, c in t["depts"])
    return f'''
<section class="banner directory" id="directory-{lang}" lang="{lang}">
  <div class="copy">
    <p class="mark">Avelune Labs</p>
    <h1>{h1(t["h1"])}</h1>
    <p class="sub">{t["sub"]}</p>
    <code class="cmd">{t["cmd"]}</code>
  </div>
  <div class="board" aria-label="directory">
    <div class="felt">
      <p class="bh"><span>{t["board_head"][0]}</span><span>{t["board_head"][1]}</span></p>
      <ul>{rows}<li class="gap"></li><li><span>{t["total"]}</span><span>{total}</span></li></ul>
    </div>
    <div class="note"><i class="tape"></i>{"<br>".join(t["note"])}</div>
  </div>
</section>'''


def banner_session(lang, t):
    plan = "".join(f'<li><b>{i}</b><span class="sk">{s}</span><span class="why">{w}</span></li>'
                   for i, (s, w) in enumerate(t["plan"], 1))
    return f'''
<section class="banner session" id="session-{lang}" lang="{lang}">
  <div class="copy">
    <p class="mark">Avelune Labs</p>
    <h1>{h1(t["h1"])}</h1>
    <p class="sub">{t["sub"]}</p>
    <code class="cmd">{t["cmd"]}</code>
  </div>
  <div class="term">
    <p class="bar"><span>claude</span><span>~/klinika</span></p>
    <div class="prompt"><span class="caret">&gt;</span> {t["task"]}</div>
    <p class="said"><span class="dot">●</span> avelune-ceo:avelune <span class="dim">· {t["plan_head"]}</span></p>
    <ol class="plan">{plan}</ol>
  </div>
</section>'''


CSS = r'''
:root { --nb: 0; }
* { box-sizing: border-box; }
body { margin: 0; padding: 40px; background: #6b6b6b; display: flex; flex-direction: column; gap: 40px; }
.banner { position: relative; width: 1280px; height: 640px; overflow: hidden; flex: none; }
.banner h1, .banner p, .banner ol, .banner ul { margin: 0; padding: 0; list-style: none; }
.mark { font-family: "Unbounded", sans-serif; font-weight: 600; font-size: 20px; letter-spacing: -.01em; }
.cmd { display: inline-block; font-size: 19px; padding: 13px 20px 14px; border-radius: 8px; white-space: nowrap; }

/* A. Phases: drenched cobalt, bone ink, one lunar-yellow full moon */
.phases { background: #1D3FD8; color: #F4EFE4; font-family: "Onest", sans-serif; }
.phases .mark { position: absolute; left: 92px; top: 64px; }
.phases h1 { position: absolute; left: 88px; top: 112px; font-family: "Unbounded", sans-serif; font-weight: 600;
  font-size: 66px; line-height: 1.04; letter-spacing: -.035em; white-space: nowrap; }
.phases .sub { position: absolute; left: 838px; top: 200px; width: 350px; font-size: 21px; line-height: 1.38; color: #F4EFE4; }
.phases .cmd { position: absolute; right: 92px; top: 55px; font-family: "Onest", sans-serif; font-weight: 600; font-size: 16px;
  background: #F4EFE4; color: #1430A6; padding: 11px 14px 12px; }
.phases .cycle { position: absolute; left: 92px; right: 92px; bottom: 56px; display: flex; justify-content: space-between; }
.phases .cycle li { display: flex; flex-direction: column; align-items: center; width: 164px; }
.phases .moon { display: block; }
.phases .dept { margin-top: 16px; font-weight: 600; font-size: 18px; line-height: 1.2; text-align: center; }
.phases .slug { margin-top: 3px; font-size: 14px; color: #C9D3FF; }

/* B. Directory: lobby letter board on a signal-orange wall */
.directory { background: #FF5B2E; color: #15120F; font-family: "Golos Text", sans-serif; }
.directory .copy { position: absolute; left: 88px; top: 60px; bottom: 60px; width: 560px; display: flex; flex-direction: column; }
.directory h1 { margin-top: 38px; font-family: "Unbounded", sans-serif; font-weight: 600; font-size: 54px;
  line-height: 1.04; letter-spacing: -.035em; }
.directory .sub { margin-top: 24px; font-size: 21px; line-height: 1.38; max-width: 25em; font-weight: 500; }
.directory .cmd { margin-top: auto; align-self: flex-start; font-family: "Golos Text", sans-serif; font-weight: 600;
  background: #15120F; color: #FFE7DC; }
.board { position: absolute; right: 88px; top: 64px; width: 470px; height: 512px; padding: 14px;
  background: linear-gradient(#D9D5CE, #A9A49B); border-radius: 6px;
  box-shadow: 0 2px 0 #7a3a22, 0 26px 40px -12px rgba(90, 24, 0, .55); }
.felt { height: 100%; border-radius: 2px; padding: 22px 26px;
  background: repeating-linear-gradient(#1B1A19 0 6px, #0F0E0E 6px 8px); color: #F3F1EB;
  text-transform: uppercase; font-weight: 600; font-size: 21px; letter-spacing: .07em; line-height: 40px; }
.felt .bh, .felt li { display: flex; justify-content: space-between; }
.felt .bh { color: #FFB59A; font-size: 17px; letter-spacing: .12em; border-bottom: 0; margin-bottom: 8px; }
.felt li.gap { height: 24px; }
.felt li span:last-child { font-variant-numeric: tabular-nums; }
.note { position: absolute; left: -46px; bottom: -22px; width: 196px; padding: 22px 20px 20px; transform: rotate(-4deg);
  background: #FBF7EC; color: #15120F; font-weight: 600; font-size: 22px; line-height: 1.18;
  box-shadow: 0 10px 18px -6px rgba(40, 10, 0, .45); }
.note .tape { position: absolute; left: 58px; top: -13px; width: 80px; height: 26px; background: rgba(255, 246, 222, .78);
  transform: rotate(3deg); box-shadow: 0 1px 2px rgba(60, 20, 0, .15); }

/* C. Session: a real Claude Code exchange on a signal-yellow field */
.session { background: #FFD23F; color: #16140F; font-family: "JetBrains Mono", monospace; }
.session .copy { position: absolute; left: 88px; top: 60px; bottom: 60px; width: 470px; display: flex; flex-direction: column; }
.session .mark { font-size: 20px; }
.session h1 { margin-top: 38px; font-family: "Unbounded", sans-serif; font-weight: 600; font-size: 50px;
  line-height: 1.05; letter-spacing: -.035em; }
.session .sub { margin-top: 24px; font-size: 18px; line-height: 1.45; max-width: 26em; }
.session .cmd { margin-top: auto; align-self: flex-start; font-family: "JetBrains Mono", monospace; font-size: 17px;
  background: #16140F; color: #FFD23F; }
.term { position: absolute; left: 600px; top: 64px; width: 760px; height: 640px; background: #17161A; color: #EDE9DF;
  border-radius: 14px 0 0 0; padding: 0 0 0 30px; font-size: 16.5px; line-height: 1.5; }
.term .bar { display: flex; gap: 26px; height: 46px; align-items: center; color: #8E8A80; font-size: 14px; }
.term .bar span:first-child { color: #FFD23F; }
.term .prompt { margin: 6px 56px 0 0; padding: 14px 18px; border: 1.5px solid #4A4740; border-radius: 10px; color: #FFFFFF; }
.term .caret { color: #FFD23F; }
.term .said { margin-top: 22px; }
.term .dot { color: #FFD23F; }
.term .dim { color: #A9A498; }
.term .plan { margin-top: 8px; }
.term .plan li { display: grid; grid-template-columns: 30px 312px 1fr; padding: 2px 0; }
.term .plan b { color: #A9A498; font-weight: 400; }
.term .plan .sk { color: #FFFFFF; }
.term .plan .why { color: #B9B4A8; white-space: nowrap; }
'''

FONTS = ("https://fonts.googleapis.com/css2?family=Unbounded:wght@600&family=Onest:wght@400;600"
         "&family=Golos+Text:wght@500;600&family=JetBrains+Mono:wght@400;700&display=swap&subset=cyrillic")


def page(sections, lang="ru"):
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><title>Avelune Labs banners</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>{CSS}</style></head>
<body>{"".join(sections)}
</body></html>
'''


if __name__ == "__main__":
    langs = sys.argv[1:] or ["ru", "en"]
    secs = []
    for lg in langs:
        t = T[lg]
        secs += [banner_phases(lg, t), banner_directory(lg, t), banner_session(lg, t)]
    open(OUT, "w").write(page(secs))
    print("wrote", OUT)
