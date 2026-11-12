#!/usr/bin/env python3
"""Avelune Labs banners, round 2: five art directions (astudio-aio method + ui-ux-pro-max styles), RU and EN, 1280x640."""
import os, sys, math

NB = " "
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "banners-variants.html")
CMD = "/plugin install avelune-ceo@avelune-labs"

T = {
    "ru": dict(
        h1=["Маркетинговое агентство", f"внутри{NB}Claude"],
        sub=f"Шесть плагинов, 101{NB}скилл и{NB}совет{NB}директоров из{NB}12{NB}агентов.",
        legend=("скилл", "дирижёр /avelune", "агент совета"),
        groups=[("Руководитель", 22, "22 скилла"), ("Креатив и тексты", 20, "20 скиллов"), ("SMM", 20, "20 скиллов"),
                ("Рост и продажи", 20, "20 скиллов"), ("Аналитика и SEO", 12, "12 скиллов"), ("Защита", 7, "7 скиллов")],
        board_group=("Совет", "12 агентов"),
        st_h1=["Маркетинговое", f"агентство в{NB}Claude"],
        burst=["101", "скилл"],
        stickers=[("Руководитель", "/avelune-ceo:board"), ("Креатив", "/avelune-creative:hooks"),
                  ("SMM", "/avelune-smm:content-plan"), ("Рост", "/avelune-growth:yandex-direct"),
                  ("Аналитика", "/avelune-insight:local-seo"), ("Защита", "/avelune-shield:ad-marking")],
        bd_h1=["Совет директоров", f"в{NB}вашем Claude"],
        bd_sub=f"Avelune Labs: маркетинговое агентство из{NB}шести{NB}плагинов. Двенадцать директоров оценивают каждое решение независимо.",
        seats=["Финансы", "Маркетинг", "Продукт", "Технологии", "Продажи", "Юрист",
               "Операции", "Данные", "Бренд", "Клиент", "Риски", "Стратег"],
        lineup=[("Руководитель", 22), ("Креатив и тексты", 20), ("SMM", 20), ("Рост и продажи", 20),
                ("Аналитика и SEO", 12), ("Защита", 7)],
        lu_h1=f"Маркетинговое агентство внутри{NB}Claude",
        lu_sub=f"Шесть плагинов, 101{NB}скилл и{NB}совет{NB}директоров из{NB}12{NB}агентов.",
        lu_note=f"Кегль строки равен числу скиллов в{NB}плагине",
        br_h1=["Опишите задачу.", "Получите план."],
        br_sub=f"Avelune Labs: маркетинговое агентство внутри{NB}Claude. Шесть плагинов и{NB}101{NB}скилл.",
        br_ask=f"Нет заявок с{NB}сайта. Что делать?",
        br_head="План из 5 шагов",
        br_more="Уточнить задачу или бюджет",
        br_steps=[("avelune-insight:metrics", "найти, где обрыв"), ("avelune-growth:cro", "разобрать сайт"),
                  ("avelune-creative:offer", "пересобрать оффер"), ("avelune-growth:ab-tests", f"проверить на{NB}трафике"),
                  ("avelune-insight:report", "что сработало")],
    ),
    "en": dict(
        h1=["A marketing agency", f"inside{NB}Claude"],
        sub=f"Six plugins, 101{NB}skills and a{NB}board{NB}of{NB}12{NB}agents.",
        legend=("skill", "conductor /avelune", "board agent"),
        groups=[("Executive", 22, "22 skills"), ("Creative and copy", 20, "20 skills"), ("Social", 20, "20 skills"),
                ("Growth and sales", 20, "20 skills"), ("Analytics and SEO", 12, "12 skills"), ("Shield", 7, "7 skills")],
        board_group=("Board", "12 agents"),
        st_h1=["A marketing", f"agency in{NB}Claude"],
        burst=["101", "skills"],
        stickers=[("Executive", "/avelune-ceo:board"), ("Creative", "/avelune-creative:hooks"),
                  ("Social", "/avelune-smm:content-plan"), ("Growth", "/avelune-growth:yandex-direct"),
                  ("Analytics", "/avelune-insight:local-seo"), ("Shield", "/avelune-shield:ad-marking")],
        bd_h1=["A board of directors", f"in{NB}your Claude"],
        bd_sub=f"Avelune Labs: a marketing agency in{NB}six plugins. Twelve directors judge each decision independently.",
        seats=["Finance", "Marketing", "Product", "Tech", "Sales", "Legal",
               "Operations", "Data", "Brand", "Customer", "Risk", "Strategist"],
        lineup=[("Executive", 22), ("Creative and copy", 20), ("Social", 20), ("Growth and sales", 20),
                ("Analytics and SEO", 12), ("Shield", 7)],
        lu_h1=f"A marketing agency inside{NB}Claude",
        lu_sub=f"Six plugins, 101{NB}skills and a{NB}board{NB}of{NB}12{NB}agents.",
        lu_note="Line size equals the number of skills in the plugin",
        br_h1=["Describe the task.", "Get the plan."],
        br_sub=f"Avelune Labs: a marketing agency inside{NB}Claude. Six plugins and 101{NB}skills.",
        br_ask=f"No leads from the{NB}site. What now?",
        br_head="A 5-step plan",
        br_more="Add details or a budget",
        br_steps=[("avelune-insight:metrics", "find where it breaks"), ("avelune-growth:cro", "review the site"),
                  ("avelune-creative:offer", "rebuild the offer"), ("avelune-growth:ab-tests", "test on traffic"),
                  ("avelune-insight:report", "see what worked")],
    ),
}


def v1_table(lg, t):
    """Swiss Modernism 2.0 + data hero: 101 skills counted as squares, the conductor in red."""
    blocks = []
    for gi, (name, n, unit) in enumerate(t["groups"]):
        cells = "".join('<i class="sq"></i>' for _ in range(n - (1 if gi == 0 else 0)))
        if gi == 0:
            cells += '<i class="sq red"></i>'
        blocks.append(f'<li><div class="units">{cells}</div><p class="gn">{name}</p><p class="gc">{unit}</p></li>')
    circles = "".join('<i class="ci"></i>' for _ in range(12))
    blocks.append(f'<li><div class="units">{circles}</div><p class="gn">{t["board_group"][0]}</p>'
                  f'<p class="gc">{t["board_group"][1]}</p></li>')
    a, b, c = t["legend"]
    return f'''
<section class="banner v1" id="v1-table-{lg}" lang="{lg}">
  <p class="mark">Avelune Labs</p><code class="cmd">{CMD}</code>
  <h1>{t["h1"][0]}<br>{t["h1"][1]}</h1>
  <div class="aside"><p class="sub">{t["sub"]}</p>
    <p class="legend"><span><i class="sq"></i>{a}</span><span><i class="sq red"></i>{b}</span><span><i class="ci"></i>{c}</span></p></div>
  <ol class="chart">{"".join(blocks)}</ol>
</section>'''


def v2_stickers(lg, t):
    """Neubrutalism (ui-ux-pro-max pick for marketing agencies): the agency's sticker pack of real commands."""
    fills = ["#FFD93D", "#4ECDC4", "#FFFFFF", "#FF9F43", "#B8F35A", "#8EC5FF"]
    rots = [-3, 2, -1.5, 2.5, -2, 1.5]
    st = "".join(f'<li style="--f:{fills[i]};--r:{rots[i]}deg"><b>{n}</b><code>{c}</code></li>'
                 for i, (n, c) in enumerate(t["stickers"]))
    return f'''
<section class="banner v2" id="v2-stickers-{lg}" lang="{lg}">
  <p class="mark">Avelune Labs</p><code class="cmd">{CMD}</code>
  <h1>{t["st_h1"][0]}<br>{t["st_h1"][1]}</h1>
  <div class="burst"><svg viewBox="0 0 200 200" aria-hidden="true"><polygon points="{burst_points()}"/></svg>
    <p><b>{t["burst"][0]}</b>{t["burst"][1]}</p></div>
  <ul class="pack">{st}</ul>
</section>'''


def burst_points(n=18, r1=96, r2=80, c=100):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.pi * i / n - math.pi / 2
        pts.append(f"{c + r * math.cos(a):.1f},{c + r * math.sin(a):.1f}")
    return " ".join(pts)


def v3_board(lg, t):
    """Bauhaus: the board of twelve becomes a round table drawn in primary geometry."""
    cx, cy, rs, rl = 888, 322, 160, 210
    shapes = []
    for i, label in enumerate(t["seats"]):
        a = 2 * math.pi * i / 12 - math.pi / 2
        x, y = cx + rs * math.cos(a), cy + rs * math.sin(a)
        k = i % 3
        if k == 0:
            shapes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="22" fill="#D02020"/>')
        elif k == 1:
            shapes.append(f'<rect x="{x - 20:.1f}" y="{y - 20:.1f}" width="40" height="40" fill="#1040C0" '
                          f'transform="rotate({math.degrees(a) + 90:.1f} {x:.1f} {y:.1f})"/>')
        else:
            p = []
            for j in range(3):
                b = a + math.pi + 2 * math.pi * j / 3
                p.append(f"{x + 25 * math.cos(b):.1f},{y + 25 * math.sin(b):.1f}")
            shapes.append(f'<polygon points="{" ".join(p)}" fill="#121212"/>')
        lx, ly = cx + rl * math.cos(a), cy + rl * math.sin(a)
        anchor = "middle" if abs(math.cos(a)) < 0.3 else ("start" if math.cos(a) > 0 else "end")
        dy = 5 if abs(math.sin(a)) < 0.9 else (16 if math.sin(a) > 0 else -6)
        shapes.append(f'<text x="{lx:.1f}" y="{ly + dy:.1f}" text-anchor="{anchor}">{label}</text>')
    svg = (f'<svg class="table" width="1280" height="640" viewBox="0 0 1280 640" aria-hidden="true">'
           f'<circle cx="{cx}" cy="{cy}" r="114" fill="#F0C020"/>'
           f'<text class="n" x="{cx}" y="{cy + 40}" text-anchor="middle">12</text>{"".join(shapes)}</svg>')
    return f'''
<section class="banner v3" id="v3-board-{lg}" lang="{lg}">
  <div class="copy"><p class="mark">Avelune Labs</p>
    <h1>{t["bd_h1"][0]}<br>{t["bd_h1"][1]}</h1>
    <p class="sub">{t["bd_sub"]}</p><code class="cmd">{CMD}</code></div>
  {svg}
</section>'''


def v4_lineup(lg, t):
    """Bold typography poster (ui-ux-pro-max Exaggerated Minimalism): a festival line-up, line size = skill count."""
    lines = "".join(f'<li style="--n:{n}"><span>{name}</span><sup>{n}</sup></li>' for name, n in t["lineup"])
    return f'''
<section class="banner v4" id="v4-lineup-{lg}" lang="{lg}">
  <ol class="lineup">{lines}</ol>
  <div class="copy"><p class="mark">Avelune Labs</p>
    <h1>{t["lu_h1"]}</h1><p class="sub">{t["lu_sub"]}</p>
    <p class="note">{t["lu_note"]}</p><code class="cmd">{CMD}</code></div>
</section>'''


def v5_brief(lg, t):
    """AI-Native UI + Minimalism (ui-ux-pro-max pick for AI products), AI-Driven Dynamic Landing: ask, get a plan."""
    steps = "".join(f'<li><b>{i}</b><code>{s}</code><span>{d}</span></li>' for i, (s, d) in enumerate(t["br_steps"], 1))
    return f'''
<section class="banner v5" id="v5-brief-{lg}" lang="{lg}">
  <div class="copy"><p class="mark">Avelune Labs</p>
    <h1>{t["br_h1"][0]}<br>{t["br_h1"][1]}</h1>
    <p class="sub">{t["br_sub"]}</p><code class="cmd">{CMD}</code></div>
  <div class="chat">
    <p class="ask">{t["br_ask"]}</p>
    <p class="head"><i></i>{t["br_head"]}</p>
    <ol class="steps">{steps}</ol>
    <p class="input"><span>{t["br_more"]}</span><i></i></p>
  </div>
</section>'''


CSS = r'''
* { box-sizing: border-box; }
body { margin: 0; padding: 40px; background: #6b6b6b; display: flex; flex-direction: column; gap: 40px; }
.banner { position: relative; width: 1280px; height: 640px; overflow: hidden; flex: none; }
.banner h1, .banner p, .banner ol, .banner ul { margin: 0; padding: 0; list-style: none; }
.banner code { font-family: inherit; }
.cmd { display: inline-block; white-space: nowrap; }

/* V1 Swiss table: cool grey, black, one red square */
.v1 { background: #E8EAED; color: #111316; font-family: "Geologica", sans-serif; }
.v1 .mark { position: absolute; left: 92px; top: 62px; font-weight: 700; font-size: 20px; letter-spacing: -.01em; }
.v1 .cmd { position: absolute; right: 92px; top: 52px; background: #111316; color: #FFFFFF; font-weight: 600;
  font-size: 16px; padding: 12px 16px 13px; border-radius: 4px; }
.v1 h1 { position: absolute; left: 89px; top: 112px; font-weight: 800; font-size: 68px; line-height: 1.0;
  letter-spacing: -.045em; white-space: nowrap; }
.v1 .aside { position: absolute; left: 812px; top: 196px; width: 376px; }
.v1 .sub { font-size: 19px; line-height: 1.4; }
.v1 .legend { display: flex; flex-wrap: nowrap; gap: 6px 16px; white-space: nowrap; margin-top: 14px; font-size: 14px; color: #4E535B; }
.v1 .legend span { display: inline-flex; align-items: center; gap: 7px; }
.v1 .legend .sq, .v1 .legend .ci { width: 12px; height: 12px; }
.v1 .chart { position: absolute; left: 92px; right: 92px; bottom: 54px; display: flex; justify-content: space-between; align-items: flex-end; }
.v1 .chart li { width: 119px; }
.v1 .units { display: flex; flex-wrap: wrap-reverse; gap: 5px; width: 119px; }
.v1 .sq { display: inline-block; width: 26px; height: 26px; background: #111316; }
.v1 .sq.red { background: #E5372A; }
.v1 .ci { display: inline-block; width: 26px; height: 26px; border-radius: 50%; border: 3px solid #111316; }
.v1 .gn { margin-top: 14px; font-weight: 700; font-size: 16px; line-height: 1.2; white-space: nowrap; }
.v1 .gc { margin-top: 2px; font-size: 14px; color: #4E535B; }

/* V2 Neubrutalist sticker pack on hot pink */
.v2 { background: #FF6BAA; color: #111111; font-family: "Golos Text", sans-serif; }
.v2 .mark { position: absolute; left: 92px; top: 60px; font-weight: 700; font-size: 21px; }
.v2 .cmd { position: absolute; right: 92px; top: 50px; background: #111111; color: #FFFFFF; font-weight: 600; font-size: 16px;
  padding: 12px 16px 13px; border: 3px solid #111111; box-shadow: 5px 5px 0 #FFFFFF; }
.v2 h1 { position: absolute; left: 90px; top: 108px; font-family: "Dela Gothic One", sans-serif; font-weight: 400;
  font-size: 58px; line-height: 1.08; letter-spacing: -.01em; white-space: nowrap; }
.v2 .burst { position: absolute; right: 110px; top: 128px; width: 168px; height: 168px; transform: rotate(10deg); }
.v2 .burst svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.v2 .burst polygon { fill: #FFD93D; stroke: #111111; stroke-width: 4; stroke-linejoin: round; }
.v2 .burst p { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-weight: 700; font-size: 20px; line-height: 1; }
.v2 .burst b { font-family: "Dela Gothic One", sans-serif; font-weight: 400; font-size: 46px; line-height: 1.05; }
.v2 .pack { position: absolute; left: 92px; right: 92px; bottom: 60px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px 26px; }
.v2 .pack li { background: var(--f); border: 3px solid #111111; box-shadow: 6px 6px 0 #111111; transform: rotate(var(--r));
  padding: 12px 16px 13px; }
.v2 .pack b { display: block; font-weight: 700; font-size: 22px; line-height: 1.15; }
.v2 .pack code { display: block; margin-top: 3px; font-weight: 600; font-size: 16px; white-space: nowrap; }

/* V3 Bauhaus round table on off-white */
.v3 { background: #F0F0F0; color: #121212; font-family: "Onest", sans-serif; }
.v3 .copy { position: absolute; left: 92px; top: 62px; bottom: 58px; width: 500px; display: flex; flex-direction: column; }
.v3 .mark { font-family: "Unbounded", sans-serif; font-weight: 800; font-size: 19px; }
.v3 h1 { margin-top: 40px; font-family: "Unbounded", sans-serif; font-weight: 800; font-size: 44px; line-height: 1.08;
  letter-spacing: -.04em; white-space: nowrap; }
.v3 .sub { margin-top: 22px; font-size: 19px; line-height: 1.45; max-width: 25em; }
.v3 .cmd { margin-top: auto; align-self: flex-start; background: #121212; color: #FFFFFF; font-weight: 600; font-size: 16px;
  padding: 12px 16px 13px; }
.v3 .table { position: absolute; left: 0; top: 0; }
.v3 .table text { font-family: "Onest", sans-serif; font-size: 15px; font-weight: 600; fill: #121212; }
.v3 .table text.n { font-family: "Unbounded", sans-serif; font-weight: 800; font-size: 104px; letter-spacing: -.06em; }

/* V4 line-up poster on emerald */
.v4 { background: #0B6E4F; color: #F1F4EE; font-family: "Golos Text", sans-serif; }
.v4 .lineup { position: absolute; left: 86px; top: 50%; transform: translateY(-50%); }
.v4 .lineup li { display: flex; align-items: flex-start; gap: .12em; font-family: "Sofia Sans Extra Condensed", sans-serif;
  font-weight: 900; text-transform: uppercase; font-size: calc(var(--n) * 4.55px); line-height: .9; letter-spacing: -.005em; }
.v4 .lineup sup { font-family: "Golos Text", sans-serif; font-weight: 700; font-size: 17px; line-height: 1; color: #FFD84D;
  margin-top: .3em; letter-spacing: 0; }
.v4 .copy { position: absolute; left: 834px; right: 92px; top: 62px; bottom: 58px; display: flex; flex-direction: column; }
.v4 .mark { font-weight: 700; font-size: 20px; }
.v4 h1 { margin-top: 36px; font-weight: 700; font-size: 38px; line-height: 1.12; letter-spacing: -.02em; }
.v4 .sub { margin-top: 18px; font-size: 18px; line-height: 1.45; }
.v4 .note { margin-top: auto; font-size: 14px; line-height: 1.4; color: #CFE3D8; }
.v4 .note::before { content: ""; display: inline-block; width: 10px; height: 10px; background: #FFD84D; margin-right: 8px; }
.v4 .cmd { margin-top: 14px; align-self: flex-start; background: #FFD84D; color: #0A3D2C; font-weight: 700; font-size: 14.5px;
  padding: 11px 13px 12px; border-radius: 6px; }

/* V5 AI-native chat, cool grey, one cobalt accent */
.v5 { background: #EDEFF3; color: #14161B; font-family: "Golos Text", sans-serif; }
.v5 .copy { position: absolute; left: 92px; top: 62px; bottom: 58px; width: 520px; display: flex; flex-direction: column; }
.v5 .mark { font-family: "Wix Madefor Display", sans-serif; font-weight: 800; font-size: 20px; }
.v5 h1 { margin-top: 40px; font-family: "Wix Madefor Display", sans-serif; font-weight: 800; font-size: 60px; line-height: 1.04;
  letter-spacing: -.035em; }
.v5 h1 br + * { }
.v5 .sub { margin-top: 24px; font-size: 19px; line-height: 1.45; max-width: 25em; color: #3E434D; }
.v5 .cmd { margin-top: auto; align-self: flex-start; background: #1D3FD8; color: #FFFFFF; font-weight: 600; font-size: 16px;
  padding: 13px 18px 14px; border-radius: 10px; }
.v5 .chat { position: absolute; left: 660px; right: 92px; top: 56px; bottom: 56px; background: #FFFFFF; border: 1px solid #D5D9E0;
  border-radius: 22px; padding: 26px 26px; display: flex; flex-direction: column; }
.v5 .input { margin-top: auto; display: flex; align-items: center; justify-content: space-between; height: 52px; padding: 0 8px 0 18px;
  border: 1.5px solid #D5D9E0; border-radius: 14px; color: #6A707C; font-size: 16px; }
.v5 .input i { width: 36px; height: 36px; border-radius: 10px; background: #1D3FD8; position: relative; }
.v5 .input i::after { content: ""; position: absolute; left: 12px; top: 10px; border: 8px solid transparent; border-left: 12px solid #FFFFFF; border-right: 0; }
.v5 .ask { margin-left: auto; width: fit-content; max-width: 360px; background: #1D3FD8; color: #FFFFFF; font-size: 18px; line-height: 1.35;
  padding: 12px 16px; border-radius: 16px 16px 4px 16px; font-weight: 500; }
.v5 .head { margin-top: 24px; display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 18px; }
.v5 .head i { width: 22px; height: 22px; border-radius: 50%; background: #1D3FD8; position: relative; }
.v5 .head i::after { content: ""; position: absolute; left: 6px; top: 6px; width: 10px; height: 10px; border-radius: 50%; background: #FFFFFF;
  clip-path: inset(0 0 0 50%); }
.v5 .steps { margin-top: 16px; display: flex; flex-direction: column; gap: 13px; }
.v5 .steps li { display: grid; grid-template-columns: 30px 232px 1fr; align-items: center; gap: 10px; }
.v5 .steps b { width: 30px; height: 30px; border-radius: 50%; background: #EDEFF3; display: grid; place-items: center; font-size: 14px; }
.v5 .steps code { background: #E7ECFF; color: #1D3FD8; font-weight: 600; font-size: 15px; padding: 6px 10px; border-radius: 7px;
  white-space: nowrap; width: fit-content; }
.v5 .steps span { font-size: 17px; color: #3E434D; white-space: nowrap; }
'''

FONTS = ("https://fonts.googleapis.com/css2?family=Geologica:wght@400;600;700;800&family=Dela+Gothic+One"
         "&family=Golos+Text:wght@400;500;600;700&family=Unbounded:wght@800&family=Onest:wght@400;600"
         "&family=Sofia+Sans+Extra+Condensed:wght@900&family=Wix+Madefor+Display:wght@800&display=swap&subset=cyrillic")


def page(sections):
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Avelune Labs banners</title>
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
        secs += [v1_table(lg, t), v2_stickers(lg, t), v3_board(lg, t), v4_lineup(lg, t), v5_brief(lg, t)]
    open(OUT, "w").write(page(secs))
    print("wrote", OUT)
