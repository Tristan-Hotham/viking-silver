"""Step 6. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder of TTFs as FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono from
github.com/google/fonts); otherwise the system serif is used.
Run: FONT_DIR=/path/to/fonts python3 06_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(54.5))
X0, X1, Y0, Y1 = -6.6 * K, 1.9 * K, -55.9, -50.6  # England, Wales and southern Scotland
Hh = 600; Ww = Hh * (X1 - X0) / (Y1 - Y0)


def pr(lat, lon):
    return (lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh


COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
land = ""
for g in json.load(open(COAST)):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = poly[0]
        if min(q[1] for q in ring) < 49.6 and max(q[0] for q in ring) > 1.0:
            continue
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in ring)) + "Z"
names = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.7"/>' for x, y in (pr(a, b) for a, b, *_ in P["names"]) if 0 <= x <= Ww and 0 <= y <= Hh)
hoards = ""
for h in R["hoards"]:
    if h["lat"] is None or h["country"] != "GB" or h["list_section"] != "Viking hoards":
        continue
    x, y = pr(h["lat"], h["lon"])
    if not (0 <= x <= Ww and 0 <= y <= Hh):
        continue
    n = max((h.get("coins") or 0), (h.get("objects") or 0))
    r = 6 + (math.log10(n) * 3.2 if n else 0)
    hoards += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 2.2:.1f}" fill="url(#glow)"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#D7E0E6" stroke="#0F171D" stroke-width="1.5"/><circle cx="{x - r * .3:.1f}" cy="{y - r * .3:.1f}" r="{max(1.5, r * .28):.1f}" fill="#fff"/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "Fraunces[SOFT,WONK,opsz,wght].ttf", "100 900"), ("Source Serif 4", "SourceSerif4[opsz,wght].ttf", "200 900"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
o = R["overlap"]["r15"]["viking_vs_settlements_gb"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 75% 45%,#24333F 0%,#18232C 60%,#141D24 100%);color:#E6ECEE;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:84px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#9AA8AF;display:flex;gap:12px;align-items:center}}
.k b{{background:#D7E0E6;color:#18232C;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:66px;top:128px;margin:0;font:900 120px/.88 Fraunces,Georgia,serif;letter-spacing:-.02em;font-variation-settings:"SOFT" 50;color:#D7E0E6}}
h1 em{{font-style:normal;color:#E58A55;display:block}}
p{{position:absolute;left:70px;top:378px;width:560px;margin:0;font-size:27px;line-height:1.36;color:#D3DBDF}}
p b{{color:#fff}}
.f{{position:absolute;left:70px;bottom:44px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#71818A}}
svg{{position:absolute;right:30px;top:15px;-webkit-mask-image:linear-gradient(to right,transparent 0,#000 22%);mask-image:linear-gradient(to right,transparent 0,#000 22%)}}
</style></head><body>
<div class="k"><b>Data study</b><span>Vikings × place names</span></div>
<h1>Silver and<em>names</em></h1>
<p>Around Viking hoards, Norse place names are <b>{o['ratio']:.1f} times</b> as common as around a random place. Yet Lincolnshire, crowded with Norse names, has no listed Viking hoard at all.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><defs><radialGradient id="glow"><stop offset="0" stop-color="#D7E0E6" stop-opacity=".55"/><stop offset="1" stop-color="#D7E0E6" stop-opacity="0"/></radialGradient></defs>
<path d="{land}" fill="#22313C" stroke="#3C4C57" stroke-width="1"/><g fill="#E58A55" fill-opacity=".8">{names}</g>{hoards}</svg>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
