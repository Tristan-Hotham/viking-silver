"""Step 5. Build ../index.html and ../README.md from page_template.html and README_template.md.

Every number in the text is a placeholder like {{overlap.r15.viking_mean|pct1}} filled from
../data/results.json. The page data (hoards with their metrics, Norse names, the 10 km grid, the
baseline hoards and the Danelaw line) are embedded as `const D = ...`.
Formats: int, pct0, pct1, f1, f2, f3, words, raw.
Run: python3 05_build_site.py
"""
import json, math, os, re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
h = pd.read_csv(os.path.join(ROOT, "data", "hoards.csv"))
m = pd.read_csv(os.path.join(ROOT, "data", "hoard_metrics.csv"))
cols = ["hoard", "norse_share_10km", "norse_share_15km", "norse_share_25km", "norse_n_15km", "settle_n_15km",
        "nearest_norse_name", "nearest_norse_km", "coast_km", "tidal_km", "major_river_km", "verdict"]
h = h.merge(m[cols], on="hoard", how="left")
h["pieces"] = [None if pd.isna(c) and pd.isna(o) else int(max(0 if pd.isna(c) else c, 0 if pd.isna(o) else o)) for c, o in zip(h.coins, h.objects)]
h["list_url"] = h.source.str.split(" ").str[0]
keep = ["hoard", "country", "list_section", "set_viking", "in_stats", "date_text", "date_sort", "place_text", "lat", "lon", "precision",
        "year_found", "museum", "contents", "pieces", "approx", "coins", "objects", "article", "list_url"] + cols[1:]
H = json.loads(h[keep].to_json(orient="records"))
for r in H:
    for k, v in list(r.items()):
        if isinstance(v, float) and k not in ("lat", "lon"):
            r[k] = round(v, 4)
D = dict(R=R, P=P, H=H)


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "words":
        w = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen".split()
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    return str(v)


def sub(m_):
    path, _, f = m_.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


t = open(os.path.join(HERE, "page_template.html")).read()
t = re.sub(r"\{\{(.+?)\}\}", sub, t)
t = t.replace("/*DATA*/", "const D = " + json.dumps(D, separators=(",", ":")) + ";")
open(os.path.join(ROOT, "index.html"), "w").write(t)
print("index.html", len(t.encode()) // 1024, "KB")
md = re.sub(r"\{\{(.+?)\}\}", sub, open(os.path.join(HERE, "README_template.md")).read())
open(os.path.join(ROOT, "README.md"), "w").write(md)
print("README.md written")
