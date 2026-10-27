"""Step 8. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Silver_and_Names.tex and compile it with xelatex (figures from 07_release_figs.py).
Placeholders: {{path|fmt}} as in 05_build_site.py, with % escaped for LaTeX.
Run: python3 08_paper.py
"""
import json, os, re, shutil, subprocess
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Silver_and_Names"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "words":
        w = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen".split()
        return w[int(v)]
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
H = pd.read_csv(os.path.join(ROOT, "data", "hoard_metrics.csv"))
V = H[H.set_viking].sort_values("date_sort")
pieces = R["silver"]["items_or_coins"]
rows = ""
for r in V.itertuples():
    sh = "" if pd.isna(r.norse_share_15km) or not r.in_stats else f"{r.norse_share_15km * 100:.1f}"
    nn = "" if pd.isna(r.norse_share_15km) or not r.in_stats else f"{tex(r.nearest_norse_name)} ({r.nearest_norse_km:.1f})"
    pc_ = f"{pieces[r.hoard]:,}" if r.hoard in pieces else ""
    nm = r.hoard.replace(" (Harrogate Hoard)", "").replace(" Hoard", "").replace(" hoard", "")
    note = {"Galloway Hoard": "not mapped", "Storr Rock Hoard": "approx., not tested", "Mullaghboden Hoard": "Ireland, not tested"}.get(r.hoard, "")
    rows += f"{tex(nm)} & {tex(r.date_text)} & {tex(r.year_found)} & {pc_} & {sh} & {nn} & {note}\\\\\n"
T1 = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The Viking hoards in the Wikipedia lists. Pieces: coins or items where the list "
      "states a number (Cuerdale from the article on the hoard). Norse \\%: share of OS Open Names settlements within 15 km with a Norse "
      "element. Nearest: nearest Norse-named settlement (km).}\\label{tab:hoards}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lllrrll}\\toprule Hoard & Date (list) & Found & Pieces & Norse \\% & Nearest (km) & Note\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}}\\end{table}")
rows = ""
for r in ("r10", "r15", "r25"):
    o = R["overlap"][r]; km = r[1:]
    rows += (f"{km} km & {o['viking_mean'] * 100:.1f} & {o['viking_vs_settlements_gb']['ratio']:.2f} & {o['viking_vs_settlements_gb']['p_one_sided']:.4f} & "
             f"{o['other_dated_mean'] * 100:.1f} & {o['other_periods_mean'] * 100:.1f} & {o['settlements_mean'] * 100:.1f} & "
             f"{o['mw_viking_vs_other_periods_p']:.3f} & {o['mw_viking_vs_other_dated_p']:.3f}\\\\\n")
T2 = ("\\begin{table}[tbp]\\centering\\small\\caption{Mean share (\\%) of settlements with a Norse element within each radius. Ratio and p: "
      "Viking hoards against 20,000 random draws of the same number of settlements (one-sided). The last two columns are one-sided "
      "Mann-Whitney p values for Viking hoards against hoards of other periods and against other hoards dated 793 to 1066.}\\label{tab:tests}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lrrrrrrrr}\\toprule Radius & Viking & Ratio & p (random) & Other 793 to 1066 & Other periods & "
      "All settlements & p (periods) & p (793 to 1066)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}}\\end{table}")
rows = "".join(f"{tex(a['area'])} & {a['norse']:,} & {a['settlements']:,} & {a['share'] * 100:.1f} & {a['viking_hoards']} & {a['median_hoard_km']:.0f}\\\\\n" for a in R["areas_top"])
T3 = ("\\begin{table}[tbp]\\centering\\small\\caption{The twelve OS Open Names areas with the most Norse-named settlements, the number of "
      "located Viking hoards in each, and the median distance (km) from their settlements to the nearest one.}\\label{tab:areas}"
      "\\begin{tabular}{lrrrrr}\\toprule Area & Norse names & Settlements & Share (\\%) & Viking hoards & Median km\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}\\end{table}")

s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_HOARDS}}", T1).replace("{{TABLE_TESTS}}", T2).replace("{{TABLE_AREAS}}", T3)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-600:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p):
        os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
