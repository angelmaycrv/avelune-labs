#!/usr/bin/env python3
"""Avelune Labs README banner «Бриф» (final). 1280x640, RU and EN. Writes brief.html next to this file.

Method: astudio-aio (direction contract, banner rules, lint, critique) + ui-ux-pro-max
(AI-Native UI + Minimalism, AI-Driven Dynamic Landing: prompt -> generated plan).
Render: node <astudio-aio>/scripts/render.cjs element brief.html --selector ".banner" --out out/banner.png --scale 2 --width 1400 --height 800
"""
import os, sys

NB = " "
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brief.html")
CMD = "/plugin install avelune-ceo@avelune-labs"

T = {
    "ru": dict(
        h1=["Опишите задачу.", "Получите план."],
        sub=(f"<b>Маркетинговое агентство внутри{NB}Claude.</b><br>Шесть плагинов, 101{NB}скилл<br>"
             f"и{NB}совет{NB}директоров из{NB}12{NB}агентов."),
        cta_label="Установка в Claude Code",
        ask=f"Нет заявок с{NB}сайта. Что делать?",
        head="План из 5 шагов",
        steps=[("Найти, где обрыв воронки", "avelune-insight:", "metrics"),
               ("Разобрать сайт и форму", "avelune-growth:", "cro"),
               ("Пересобрать оффер", "avelune-creative:", "offer"),
               ("Проверить на трафике", "avelune-growth:", "ab-tests"),
               ("Отчёт: что сработало", "avelune-insight:", "report")],
        note=f"Начинаю с{NB}первого шага.<br>Пришлите цифры за{NB}месяц: визиты, заявки, продажи.",
        input="Ответить или уточнить бюджет",
    ),
    "en": dict(
        h1=["Describe the task.", "Get the plan."],
        sub=(f"<b>A marketing agency inside{NB}Claude.</b><br>Six plugins, 101{NB}skills<br>"
             f"and a{NB}board{NB}of{NB}12{NB}agents."),
        cta_label="Install in Claude Code",
        ask=f"No leads from the{NB}site. What now?",
        head="A 5-step plan",
        steps=[("Find where the funnel leaks", "avelune-insight:", "metrics"),
               ("Review the site and form", "avelune-growth:", "cro"),
               ("Rebuild the offer", "avelune-creative:", "offer"),
               ("Test it on traffic", "avelune-growth:", "ab-tests"),
               ("Report what worked", "avelune-insight:", "report")],
        note=f"Starting with step one.<br>Send last month’s numbers: visits, leads, sales.",
        input="Reply or set a budget",
    ),
}

# crescent mark: the "lune" in Avelune
MOON = ('<svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="currentColor"/>'
        '<circle cx="16.5" cy="9" r="9.5" fill="var(--hole)"/></svg>')


def banner(lg, t, theme="light"):
    steps = "".join(
        f'<li class="{"now" if i == 1 else ""}"><b>{i}</b><span class="d">{d}</span>'
        f'<code><span>{ns}</span>{sk}</code></li>'
        for i, (d, ns, sk) in enumerate(t["steps"], 1))
    return f'''
<section class="banner {theme}" id="brief-{lg}{"-dark" if theme == "dark" else ""}" lang="{lg}">
  <div class="copy">
    <p class="mark">{MOON}Avelune Labs</p>
    <h1>{t["h1"][0]}<br>{t["h1"][1]}</h1>
    <p class="sub">{t["sub"]}</p>
    <div class="cta"><p>{t["cta_label"]}</p><code class="cmd">{CMD}</code></div>
  </div>
  <div class="chat">
    <p class="ask">{t["ask"]}</p>
    <p class="head"><span class="ava">{MOON}</span>{t["head"]}</p>
    <ol class="steps">{steps}</ol>
    <p class="note">{t["note"]}</p>
    <p class="input"><span><i class="caret"></i>{t["input"]}</span><i class="send"></i></p>
  </div>
</section>'''


CSS = r'''
* { box-sizing: border-box; }
body { margin: 0; padding: 40px; background: #6b6b6b; display: flex; flex-direction: column; gap: 40px; }

/* tokens: light (default) */
.banner {
  --ground: #EDEFF3; --ink: #14161B; --ink-2: #3B404A; --ink-3: #5B616C;
  --accent: #1D3FD8; --on-accent: #FFFFFF; --accent-ink: #1D3FD8; --mark: #1D3FD8;
  --card: #FFFFFF; --card-line: #D6DAE1; --row-line: #ECEEF2; --num: #EDEFF3; --num-ink: #3B404A;
  --chip: #EEF1FF; --chip-ink: #1D3FD8; --chip-ns: #3B54D4; --placeholder: #6A707C; --caret: #1D3FD8;
}
/* tokens: dark, deep blue-grey ground (not black) so it stays a panel on GitHub's #0d1117 */
.banner.dark {
  --ground: #121722; --ink: #EEF1F6; --ink-2: #B4BBC8; --ink-3: #8F98A8;
  --accent: #2F52F0; --on-accent: #FFFFFF; --mark: #7891FF;
  --card: #1A2030; --card-line: #2C3448; --row-line: #252C3D; --num: #262E41; --num-ink: #C3CAD6;
  --chip: #1F2C5C; --chip-ink: #D3DBFF; --chip-ns: #9DAEF7; --placeholder: #8E97A8; --caret: #7891FF;
}
.banner { position: relative; width: 1280px; height: 640px; overflow: hidden; flex: none;
  background: var(--ground); color: var(--ink); font-family: "Golos Text", sans-serif; }
:where(.banner p, .banner h1, .banner ol) { margin: 0; padding: 0; list-style: none; }
.banner code { font-family: inherit; }

/* left column: wordmark, headline, supporting line, action */
.copy { position: absolute; left: 92px; top: 60px; bottom: 56px; width: 520px; display: flex; flex-direction: column; }
.mark { display: flex; align-items: center; gap: 10px; font-family: "Wix Madefor Display", sans-serif; font-weight: 800;
  font-size: 21px; letter-spacing: -.01em; color: var(--ink); }
.mark .moon { width: 24px; height: 24px; color: var(--mark); --hole: var(--ground); }
h1 { margin-top: 50px; font-family: "Wix Madefor Display", sans-serif; font-weight: 800; font-size: 62px; line-height: 1.02;
  letter-spacing: -.04em; white-space: nowrap; }
.sub { margin-top: 26px; font-size: 20px; line-height: 1.45; color: var(--ink-2); max-width: 25em; text-wrap: pretty; }
.sub b { font-weight: 600; color: var(--ink); }
.cta { margin-top: auto; }
.cta p { font-size: 14px; color: var(--ink-3); margin-bottom: 10px; }
.cmd { display: inline-block; white-space: nowrap; background: var(--accent); color: var(--on-accent); font-weight: 600; font-size: 17px;
  padding: 13px 18px 14px; border-radius: 10px; }

/* right: the conversation card */
.chat { position: absolute; left: 676px; right: 92px; top: 56px; bottom: 56px; display: flex; flex-direction: column;
  background: var(--card); border: 1px solid var(--card-line); border-radius: 22px; padding: 24px 24px 22px; }
.ask { align-self: flex-end; background: var(--accent); color: var(--on-accent); font-size: 18px; font-weight: 500; line-height: 1.3;
  padding: 12px 16px 13px; border-radius: 16px 16px 4px 16px; }
.head { margin-top: 20px; display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 18px; }
.ava { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: var(--accent); color: var(--on-accent); }
.ava .moon { width: 14px; height: 14px; --hole: var(--accent); }
.steps { margin-top: 12px; display: flex; flex-direction: column; }
.steps li { display: grid; grid-template-columns: 28px 1fr auto; align-items: center; gap: 12px; height: 46px;
  border-top: 1px solid var(--row-line); }
.steps li:first-child { border-top: 0; }
.steps b { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: var(--num);
  font-size: 14px; font-weight: 600; color: var(--num-ink); font-variant-numeric: tabular-nums; }
.steps .now b { background: var(--accent); color: var(--on-accent); }
.steps .d { font-size: 17px; font-weight: 500; color: var(--ink); white-space: nowrap; }
.steps code { justify-self: end; white-space: nowrap; background: var(--chip); color: var(--chip-ink); font-weight: 700; font-size: 14px;
  padding: 5px 9px 6px; border-radius: 7px; }
.steps code span { font-weight: 400; color: var(--chip-ns); }
.note { margin-top: 12px; font-size: 16px; line-height: 1.45; color: var(--ink-2); text-wrap: balance; }
.input { margin-top: auto; display: flex; align-items: center; justify-content: space-between; height: 50px;
  padding: 0 7px 0 16px; border: 1.5px solid var(--card-line); border-radius: 14px; color: var(--placeholder); font-size: 16px; }
.input span { display: flex; align-items: center; gap: 8px; }
.caret { width: 2px; height: 20px; background: var(--caret); }
.send { position: relative; width: 36px; height: 36px; border-radius: 10px; background: var(--accent); }
.send::after { content: ""; position: absolute; left: 13px; top: 10px; border: 8px solid transparent;
  border-left: 12px solid var(--on-accent); border-right: 0; }
'''

FONTS = ("https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700"
         "&family=Wix+Madefor+Display:wght@800&display=swap&subset=cyrillic")


def page(sections):
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Avelune Labs banner</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>{CSS}</style></head>
<body>{"".join(sections)}
</body></html>
'''


if __name__ == "__main__":
    langs = sys.argv[1:] or ["ru", "en"]
    open(OUT, "w").write(page([banner(lg, T[lg], th) for th in ("light", "dark") for lg in langs]))
    print("wrote", OUT)
