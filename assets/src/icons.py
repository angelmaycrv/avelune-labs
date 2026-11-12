import json
P = {
 "avelune-ceo":      ("#F7B93E","#FF8A3D"),
 "avelune-creative": ("#FF5FA2","#B44DFF"),
 "avelune-smm":      ("#33D1FF","#3D7BFF"),
 "avelune-growth":   ("#46E08A","#13B5A6"),
 "avelune-insight":  ("#8F7CFF","#4F8CFF"),
 "avelune-shield":   ("#FF7A59","#FF3D6E"),
}
G = {
 # compass north star
 "avelune-ceo": '<polygon points="512,250 560,464 774,512 560,560 512,774 464,560 250,512 464,464" fill="url(#g)"/><polygon points="512,370 538,486 654,512 538,538 512,654 486,538 370,512 486,486" fill="#fff" opacity=".95" transform="rotate(45 512 512)"/><circle cx="512" cy="512" r="30" fill="#0E0C22"/>',
 # sparks
 "avelune-creative": '<path d="M480 260 C500 400 520 420 660 440 C520 460 500 480 480 620 C460 480 440 460 300 440 C440 420 460 400 480 260Z" fill="url(#g)"/><path d="M660 560 C668 620 676 628 736 636 C676 644 668 652 660 712 C652 652 644 644 584 636 C644 628 652 620 660 560Z" fill="#fff"/><path d="M360 640 C365 676 370 681 406 686 C370 691 365 696 360 732 C355 696 350 691 314 686 C350 681 355 676 360 640Z" fill="#fff" opacity=".8"/>',
 # chat bubbles
 "avelune-smm": '<rect x="270" y="300" width="380" height="260" rx="70" fill="url(#g)"/><path d="M340 540 L320 640 L430 552Z" fill="url(#g)"/><rect x="430" y="470" width="330" height="220" rx="64" fill="#fff"/><path d="M690 670 L720 760 L610 684Z" fill="#fff"/><circle cx="530" cy="580" r="20" fill="#0E0C22"/><circle cx="595" cy="580" r="20" fill="#0E0C22"/><circle cx="660" cy="580" r="20" fill="#0E0C22"/>',
 # growth arrow
 "avelune-growth": '<rect x="280" y="600" width="80" height="140" rx="18" fill="#fff" opacity=".35"/><rect x="400" y="530" width="80" height="210" rx="18" fill="#fff" opacity=".55"/><rect x="520" y="450" width="80" height="290" rx="18" fill="#fff" opacity=".75"/><rect x="640" y="360" width="80" height="380" rx="18" fill="#fff"/><path d="M270 540 L420 420 L520 470 L700 290" stroke="url(#g)" stroke-width="44" fill="none" stroke-linecap="round" stroke-linejoin="round"/><polygon points="760,230 742,370 640,268" fill="url(#g)"/>',
 # lens
 "avelune-insight": '<circle cx="470" cy="470" r="190" fill="none" stroke="url(#g)" stroke-width="56"/><path d="M610 610 L760 760" stroke="url(#g)" stroke-width="72" stroke-linecap="round"/><rect x="390" y="470" width="40" height="80" rx="10" fill="#fff"/><rect x="450" y="420" width="40" height="130" rx="10" fill="#fff"/><rect x="510" y="380" width="40" height="170" rx="10" fill="#fff"/>',
 # shield
 "avelune-shield": '<path d="M512 250 L740 330 L740 520 C740 650 640 740 512 790 C384 740 284 650 284 520 L284 330Z" fill="url(#g)"/><path d="M412 520 L490 598 L630 450" stroke="#fff" stroke-width="52" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
}
def icon(name):
    a,b = P[name]
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:transparent}}</style></head><body>
<svg width="1024" height="1024" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>
<radialGradient id="glow" cx="30%" cy="22%" r="80%"><stop offset="0" stop-color="{a}" stop-opacity=".55"/><stop offset=".45" stop-color="{b}" stop-opacity=".18"/><stop offset="1" stop-color="#0E0C22" stop-opacity="0"/></radialGradient>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1B1640"/><stop offset="1" stop-color="#0A0918"/></linearGradient>
<clipPath id="c"><rect x="0" y="0" width="1024" height="1024" rx="230"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="1024" height="1024" fill="url(#bg)"/>
<rect width="1024" height="1024" fill="url(#glow)"/>
<path d="M860 80 a300 300 0 1 0 120 420 a240 240 0 1 1 -120 -420z" fill="#fff" opacity=".06"/>
<circle cx="170" cy="840" r="5" fill="#fff" opacity=".5"/><circle cx="880" cy="760" r="4" fill="#fff" opacity=".4"/><circle cx="120" cy="200" r="3" fill="#fff" opacity=".5"/><circle cx="820" cy="140" r="4" fill="#fff" opacity=".35"/>
{G[name]}
<rect x="6" y="6" width="1012" height="1012" rx="226" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="12"/>
</g></svg></body></html>'''
for n in P:
    open(f"icon-{n}.html","w").write(icon(n))
json.dump(P,open("palette.json","w"))
print("ok")
