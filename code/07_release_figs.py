"""Step 7. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png).

All numbers come from data/results.json and the data CSVs. Fonts: Fraunces, Source Serif 4 and IBM Plex
Mono if FONT_DIR points to them (as in the collage), otherwise matplotlib defaults.
Run: FONT_DIR=/path/to/fonts python3 07_release_figs.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "")
SER, MONO = "serif", "monospace"
if FD:
    for f in os.listdir(FD):
        if f.endswith(".ttf"):
            fm.fontManager.addfont(os.path.join(FD, f))
    SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#5B6870", "axes.labelcolor": "#17212A",
                     "xtick.color": "#5B6870", "ytick.color": "#17212A", "axes.spines.top": False, "axes.spines.right": False})
COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
H = pd.read_csv(os.path.join(ROOT, "data", "hoard_metrics.csv"))
O = pd.read_csv(os.path.join(ROOT, "data", "hoards_other_periods_gb.csv"))
N = pd.read_csv(os.path.join(ROOT, "data", "norse_names.csv")); N = N[N.element_core.notna()].copy()
tr = Transformer.from_crs(4326, 27700, always_xy=True)
FG, MUT, SIL, SLATE, RUST, MOSS, GOLD = "#17212A", "#5B6870", "#9FB2C1", "#2E4558", "#B4532A", "#5C7F5A", "#9C7A2B"
short = lambda n: n.replace(" (Harrogate Hoard)", "").replace(" Hoard", "").replace(" hoard", "")
PAPER = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAPER, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
LAND = []
for g in json.load(open(COAST)):
    for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = np.array(p[0])
        if ring[:, 1].min() < 49.6 and ring[:, 0].max() > 1.0:
            continue
        LAND.append(tr.transform(ring[:, 0], ring[:, 1]))
V = H[H.set_viking & H.lat.notna() & (H.country == "GB")].copy()
V["x"], V["y"] = tr.transform(V.lon.values, V.lat.values)
A = H[~H.set_viking & H.lat.notna() & (H.country == "GB")].copy(); A["x"], A["y"] = tr.transform(A.lon.values, A.lat.values)
O["x"], O["y"] = tr.transform(O.lon.values, O.lat.values)
N["x"], N["y"] = tr.transform(N.lon.values, N.lat.values)
pieces = R["silver"]["items_or_coins"]
dl = np.array(R["danelaw"]["coords"]); DX, DY = tr.transform(dl[:, 0], dl[:, 1])


def save(fig, name, blog):
    fig.savefig(os.path.join(BLOG if blog else PAPER, name), dpi=(190 if blog else 200), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    if blog:  # blog images are exactly 1520 px wide
        from PIL import Image
        p = os.path.join(BLOG, name); im = Image.open(p)
        im.resize((1520, round(im.height * 1520 / im.width)), Image.LANCZOS).save(p, optimize=True)


def base(ax, bg, land, edge, ylim=(150000, 1000000)):
    ax.set_facecolor(bg)
    for x, y in LAND:
        ax.fill(x, y, color=land, lw=0, zorder=1); ax.plot(x, y, color=edge, lw=.4, zorder=1)
    ax.set_aspect("equal"); ax.set_xlim(60000, 660000); ax.set_ylim(*ylim); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)


def hoard_r(names):
    sz = np.array([pieces.get(h, 0) for h in names])
    return np.where(sz > 0, 30 + np.log10(np.maximum(sz, 1)) * 55, 45)


# 1 map
for blog in (False, True):
    fig, ax = plt.subplots(figsize=(8, 10.5) if blog else (6.4, 8.4), facecolor="#F5F7F6" if blog else "white")
    base(ax, "#F5F7F6" if blog else "white", "#E2E8E8" if blog else "#EEEEEE", "#B9C3C4", (150000, 1050000))
    ax.scatter(N.x, N.y, s=3 if blog else 2, c=RUST, lw=0, alpha=.85, zorder=2, rasterized=True, label=f"Settlement with a Norse name ({len(N):,})")
    ax.scatter(O.x, O.y, s=14, marker="^", facecolors="none", edgecolors=MOSS, lw=.8, zorder=3, label=f"Hoard of another period ({len(O)})")
    ax.scatter(A.x, A.y, s=26, facecolors="white", edgecolors=SLATE, lw=1, zorder=3, label="Other hoard dated 793 to 1066")
    ax.scatter(V.x, V.y, s=hoard_r(V.hoard), c=SIL, edgecolors=FG, lw=1.1, zorder=4, label="Viking hoard (size = pieces)")
    ax.plot(DX, DY, color=FG, lw=1.3, ls=(0, (4, 3)), zorder=5, label="Danelaw line (approximate)")
    for nm, dx, dy, ha in [("Cuerdale Hoard", -18000, 6000, "right"), ("Watlington Hoard", -16000, -6000, "right"), ("Eye Hoard", -15000, -5000, "right"),
                           ("Vale of York Hoard (Harrogate Hoard)", 20000, -32000, "left"), ("Skaill Hoard", -16000, 0, "right"), ("Bryn Maelgwyn Hoard", -12000, 10000, "right")]:
        h = V[V.hoard == nm]
        if len(h):
            ax.text(h.x.iloc[0] + dx, h.y.iloc[0] + dy, short(nm), fontsize=9 if not blog else 11, color=FG, ha=ha, va="center", zorder=6)
    ax.text(568000, 455000, "Lincolnshire:\n%d Norse\nnames, no\nlisted hoard" % R["lincolnshire"]["norse"], fontsize=9 if not blog else 11, color=GOLD, ha="left", zorder=6)
    ax.legend(loc="upper center", frameon=False, fontsize=8.5 if not blog else 11, markerscale=.8, bbox_to_anchor=(.5, .0), ncol=2)
    save(fig, "b_map.png" if blog else "f_map.png", blog)

# 2 per-hoard share
S = H[H.set_viking & H.in_stats].sort_values("norse_share_15km")
o = R["overlap"]["r15"]
for blog in (False, True):
    fig, ax = plt.subplots(figsize=(8, 6.2) if blog else (6.4, 5.2), facecolor="#F5F7F6" if blog else "white"); ax.set_facecolor(fig.get_facecolor())
    y = np.arange(len(S)); v = S.norse_share_15km.values * 100
    ax.hlines(y, 0, v, color=SLATE, lw=1.4, alpha=.5)
    ax.scatter(v, y, s=70, c=np.where(v == 0, "white", SIL), edgecolors=FG, lw=1.2, zorder=3)
    for val, c, ls, lab in [(o["viking_vs_settlements_gb"]["random_mean"], MUT, ":", "random place"), (o["other_periods_mean"], MOSS, "--", "hoards of other periods"), (o["viking_mean"], RUST, "-", "Viking hoards, mean")]:
        ax.axvline(val * 100, color=c, ls=ls, lw=1.5, label=f"{lab} {val*100:.1f}%")
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    ax.set_yticks(y); ax.set_yticklabels([short(n) for n in S.hoard]); ax.set_xlim(-1, 36); ax.set_ylim(-.7, len(S) + .3)
    ax.set_xlabel("Share of settlements within 15 km with a Norse name (%)")
    save(fig, "b_share.png" if blog else "f_share.png", blog)

# 3 group comparison (paper)
fig, ax = plt.subplots(figsize=(6.4, 3.6), facecolor="white")
groups = [("Random place", lambda r: R["overlap"][r]["viking_vs_settlements_gb"]["random_mean"], "#BBBBBB"), ("Hoards of other periods", lambda r: R["overlap"][r]["other_periods_mean"], MOSS),
          ("Other hoards 793 to 1066", lambda r: R["overlap"][r]["other_dated_mean"], GOLD), ("Viking hoards", lambda r: R["overlap"][r]["viking_mean"], SLATE)]
for i, r in enumerate(["r10", "r15", "r25"]):
    for j, (lab, f, c) in enumerate(groups):
        ax.bar(i + (j - 1.5) * .2, f(r) * 100, .18, color=c, edgecolor=FG, lw=.5, label=lab if i == 0 else None, hatch=["", "//", "..", ""][j])
ax.set_xticks(range(3)); ax.set_xticklabels(["10 km", "15 km", "25 km"]); ax.set_ylabel("Norse share (%)"); ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper center", bbox_to_anchor=(.5, -.12))
save(fig, "f_groups.png", False)

# 4 Danelaw
d = R["danelaw"]
rows = [("All settlements", d["settlements"], "#BBBBBB"), ("Hoards of other periods", d["other_periods"], MOSS), ("Other hoards 793 to 1066", d["other_dated"], GOLD),
        ("Viking hoards", d["viking"], SLATE), ("Norse-named settlements", d["norse_names"], RUST)]
for blog in (False, True):
    fig, ax = plt.subplots(figsize=(8, 3.6) if blog else (6.4, 3.0), facecolor="#F5F7F6" if blog else "white"); ax.set_facecolor(fig.get_facecolor())
    for i, (lab, r_, c) in enumerate(rows):
        ax.barh(i, r_["share"] * 100, color=c, height=.62, edgecolor=FG, lw=.4)
        ax.text(r_["share"] * 100 + 1, i, f"{r_['share']*100:.1f}%  (n = {r_['n']:,})", va="center", fontsize=9.5)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r_[0] for r_ in rows]); ax.set_xlim(0, 125); ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Share north and east of the approximate Danelaw line, England (%)")
    save(fig, "b_danelaw.png" if blog else "f_danelaw.png", blog)

# 5 names without silver: Norse names coloured by distance to the nearest Viking hoard
T = cKDTree(np.c_[V[H.loc[V.index, "in_stats"]].x, V[H.loc[V.index, "in_stats"]].y])
N["km"] = T.query(np.c_[N.x, N.y])[0] / 1000
for blog in (False, True):
    fig, ax = plt.subplots(figsize=(8, 8.6) if blog else (6.4, 6.9), facecolor="#F5F7F6" if blog else "white")
    base(ax, fig.get_facecolor(), "#E2E8E8" if blog else "#EEEEEE", "#B9C3C4", (150000, 620000))
    ax.set_xlim(150000, 660000)
    sc = ax.scatter(N.x, N.y, s=8 if blog else 5, c=np.minimum(N.km, 130), cmap="cividis_r", lw=0, zorder=2, rasterized=True)
    VV = V[V.y < 620000]
    ax.scatter(VV.x, VV.y, s=hoard_r(VV.hoard), c=SIL, edgecolors=FG, lw=1.1, zorder=4)
    ax.plot(DX, DY, color=FG, lw=1.2, ls=(0, (4, 3)), zorder=3)
    cb = fig.colorbar(sc, ax=ax, shrink=.5, pad=.01); cb.set_label("km to nearest Viking hoard (capped at 130)")
    save(fig, "b_gap.png" if blog else "f_gap.png", blog)

# 6 sizes
P = sorted(pieces.items(), key=lambda t: t[1])
for blog in (False, True):
    fig, ax = plt.subplots(figsize=(8, 5.6) if blog else (6.4, 4.6), facecolor="#F5F7F6" if blog else "white"); ax.set_facecolor(fig.get_facecolor())
    ax.barh(range(len(P)), [p[1] for p in P], color=[SLATE if p[0] == "Cuerdale Hoard" else SIL for p in P], edgecolor=FG, lw=.4, height=.7)
    ax.set_xscale("log"); ax.set_xlim(1, 30000); ax.set_xticks([1, 10, 100, 1000, 10000]); ax.set_xticklabels(["1", "10", "100", "1,000", "10,000"]); ax.minorticks_off()
    for i, p in enumerate(P):
        ax.text(p[1] * 1.15, i, f"{p[1]:,}", va="center", fontsize=9)
    ax.set_yticks(range(len(P))); ax.set_yticklabels([short(p[0]) for p in P]); ax.set_xlabel("Coins or items stated in the lists (log scale)")
    save(fig, "b_sizes.png" if blog else "f_sizes.png", blog)
print("figures written")
