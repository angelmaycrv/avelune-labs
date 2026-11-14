import json
P=json.load(open('palette.json'))
def flow(lang):
    T = {
     'ru': dict(title='Как это работает', s1='Задача одной фразой', s1d='«Запусти продвижение стоматологии на ноябрь»',
                s2='Дирижёр avelune', s2d='разбивает на шаги и выбирает скиллы',
                s4='Проверки', checks=['creative-review: качество','ad-law и ad-marking: закон','supervisor: агенты по брифу','board: 12 мнений для больших решений'],
                s5='Результат и отчёт', s5d='тексты, планы, кампании, report через 2 недели',
                names=['Руководитель','Креатив','SMM','Рост и продажи','Аналитика и SEO','Защита','Звук и саунд-дизайн'],
                counts=['22 скилла','20 скиллов','20 скиллов','20 скиллов','12 скиллов','7 скиллов','18 скиллов']),
     'en': dict(title='How it works', s1='One-line task', s1d='“Run the clinic’s promotion for November”',
                s2='avelune conductor', s2d='splits it into steps and picks the skills',
                s4='Checks', checks=['creative-review: quality','ad-law, ad-marking: legal','supervisor: agents on brief','board: 12 views for big calls'],
                s5='Result and report', s5d='copy, plans, campaigns, a report two weeks later',
                names=['CEO','Creative','SMM','Growth & Sales','Insight & SEO','Shield','Sound & sound design'],
                counts=['22 skills','20 skills','20 skills','20 skills','12 skills','7 skills','18 skills']),
    }[lang]
    keys=['avelune-ceo','avelune-creative','avelune-smm','avelune-growth','avelune-insight','avelune-shield','avelune-sound']
    plug=''.join(f'<div class="pl"><img src="out/{k}.png"><div><b>{n}</b><span>{c}</span></div></div>' for k,n,c in zip(keys,T['names'],T['counts']))
    checks=''.join(f'<li>{c}</li>' for c in T['checks'])
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;width:1280px;height:560px;background:#0A0918;font-family:Inter,sans-serif;color:#fff;overflow:hidden}}
.w{{position:relative;width:1280px;height:560px;background:radial-gradient(700px 380px at 50% 0%,#2C2370aa,transparent 70%),linear-gradient(180deg,#110E2B,#08070F)}}
h2{{position:absolute;left:0;right:0;top:30px;text-align:center;margin:0;font:700 30px Unbounded;letter-spacing:-.01em}}
.card{{position:absolute;border-radius:22px;background:#ffffff0d;border:1px solid #ffffff1f;padding:20px 22px;box-sizing:border-box}}
.card h3{{margin:0 0 8px;font:700 19px Unbounded}}
.card p{{margin:0;font:500 15px/1.4 Inter;color:#C9C4E8}}
.n{{display:inline-flex;width:28px;height:28px;border-radius:50%;align-items:center;justify-content:center;font:700 14px Inter;background:linear-gradient(135deg,#FFD27A,#FF8AC2);color:#14102E;margin-bottom:10px}}
.c1{{left:40px;top:110px;width:240px;height:170px}}
.c2{{left:40px;top:310px;width:240px;height:170px}}
.mid{{position:absolute;left:340px;top:100px;width:560px;height:400px;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(4,1fr);gap:12px}}
.pl:last-child{{grid-column:span 2}}
.pl{{display:flex;align-items:center;gap:14px;border-radius:18px;background:#ffffff0b;border:1px solid #ffffff1a;padding:8px 14px}}
.pl img{{width:60px;height:60px;border-radius:15px}}
.pl b{{display:block;font:700 17px Inter}}
.pl span{{font:500 14px Inter;color:#A9A3CF}}
.c4{{left:960px;top:100px;width:280px;height:224px}}
.c4 ul{{margin:6px 0 0;padding-left:18px;font:500 14px/1.55 Inter;color:#D6D1F2}}
.c5{{left:960px;top:352px;width:280px;height:148px}}
.arr{{position:absolute;color:#8F84FF;font:700 26px Inter}}
</style></head><body><div class="w">
<h2>{T['title']}</h2>
<div class="card c1"><div class="n">1</div><h3>{T['s1']}</h3><p>{T['s1d']}</p></div>
<div class="arr" style="left:148px;top:280px">↓</div>
<div class="card c2"><div class="n">2</div><h3>{T['s2']}</h3><p>{T['s2d']}</p></div>
<div class="arr" style="left:298px;top:380px">→</div>
<div class="mid">{plug}</div>
<div class="arr" style="left:916px;top:205px">→</div>
<div class="card c4"><div class="n">3</div><h3>{T['s4']}</h3><ul>{checks}</ul></div>
<div class="arr" style="left:1090px;top:320px">↓</div>
<div class="card c5"><div class="n">4</div><h3>{T['s5']}</h3><p>{T['s5d']}</p></div>
</div></body></html>'''
for l in ('ru','en'): open(f'flow-{l}.html','w').write(flow(l))
