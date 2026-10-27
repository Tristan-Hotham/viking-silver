"""Step 4. Do the silver and the names agree? Every number used on the page, paper, blog and collage.

Inputs
  data/hoards.csv                   Viking Age hoards (step 2)
  data/hoards_other_periods_gb.csv  every other located hoard in the Great Britain list (baseline)
  work/settlements.csv              all OS Open Names settlements with a Norse element flag (step 3)
  ../did-lighthouses-work/release/build/ne10m_land_british_isles.json  Natural Earth 10m land (public domain)
  ../osrivers/Data/oprvrs_gb.gpkg   OS Open Rivers (OGL v3)

Main sets
  VIK   the "Viking hoards" tables of the lists, located in Great Britain to village level (in_stats)
  AGE   VIK plus every other located Great Britain hoard dated 793 to 1066 by the list
  OTH   every other located hoard in the Great Britain list (all other periods): where hoards of any
        date have been found and reported, so it shares the biases of discovery and recording
  SET   all settlements in OS Open Names (a settlement-weighted random place)

Measures
  Norse share within R km: of all OS Open Names settlements within R km of a point, the share with a
  core Norse element. R = 15 km in the headline, 10 and 25 km as checks.
  Monte Carlo: 20,000 random draws of n settlements (n = number of hoards) give the chance that a
  random set of places would be as Norse as the hoards' surroundings.

Writes data/results.json, data/hoard_metrics.csv, data/grid10km.csv, data/page_data.json.
Run: python3 04_analysis.py
"""
import json, os, sqlite3, sys
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.stats import mannwhitneyu
from shapely import contains_xy
from shapely.geometry import LineString, Polygon

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); HIST = os.path.join(ROOT, "..")
sys.path.insert(0, HERE)
TO_BNG = Transformer.from_crs(4326, 27700, always_xy=True)
TO_LL = Transformer.from_crs(27700, 4326, always_xy=True)
COAST = os.path.join(HIST, "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
RIVERS = os.path.join(HIST, "osrivers", "Data", "oprvrs_gb.gpkg")
rng = np.random.default_rng(1840)
R = {}


def rnd(x, k=3):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


# ------------------------------------------------------------------ load
H = pd.read_csv(os.path.join(ROOT, "data", "hoards.csv"))
O = pd.read_csv(os.path.join(ROOT, "data", "hoards_other_periods_gb.csv"))
S = pd.read_csv(os.path.join(ROOT, "work", "settlements.csv"), keep_default_na=False)
S["norse"] = S.core != ""
S["norse_broad"] = S.broad != ""
for df in (H, O):
    ok = df.lat.notna()
    x, y = TO_BNG.transform(df.lon.where(ok, 0).values, df.lat.where(ok, 0).values)
    df["x"] = np.where(ok, x, np.nan); df["y"] = np.where(ok, y, np.nan)
GB = H[H.in_stats].copy()
VIK = GB[GB.set_viking].copy()
AGE = GB.copy()
ASX = GB[~GB.set_viking].copy()  # dated 793 to 1066 but listed outside the Viking tables
R["counts"] = dict(
    hoards_all=int(len(H)), hoards_viking_tables=int(H.set_viking.sum()),
    hoards_viking_gb=int((H.set_viking & (H.country == "GB")).sum()),
    hoards_viking_ie=int((H.set_viking & (H.country == "IE")).sum()),
    hoards_viking_age_extra=int((~H.set_viking).sum()),
    vik_in_stats=int(len(VIK)), age_in_stats=int(len(AGE)), other_dated_in_stats=int(len(ASX)),
    other_periods_baseline=int(len(O)), not_located=H[H.precision == "not located"].hoard.tolist(),
    approximate=H[H.precision.str.contains("approximate")].hoard.tolist(),
    settlements=int(len(S)), norse_core=int(S.norse.sum()), norse_broad=int(S.norse_broad.sum()),
    norse_share_gb=rnd(S.norse.mean(), 4),
    norse_share_by_country={c: rnd(g.norse.mean(), 4) for c, g in S.groupby("country")},
    norse_by_country={c: int(g.norse.sum()) for c, g in S.groupby("country")},
    elements={k: int(v) for k, v in S[S.norse].core.value_counts().items()},
    elements_broad={k: int(v) for k, v in S[S.norse_broad].broad.value_counts().items()},
    wikidata_matched=int((H.wikidata.notna() & (H.wikidata != "")).sum()),
    wikidata_max_offset_km=rnd(H.wikidata_offset_km.max(), 2))

# ------------------------------------------------------------------ Norse share around points
TS = cKDTree(np.c_[S.x.values, S.y.values])
NORSE = S.norse.values; NORSEB = S.norse_broad.values
TN = cKDTree(np.c_[S.x.values[NORSE], S.y.values[NORSE]])


def share_at(x, y, r_km, flag=NORSE):
    idx = TS.query_ball_point(np.c_[x, y], r_km * 1000)
    n = np.array([len(i) for i in idx]); k = np.array([flag[i].sum() if len(i) else 0 for i in idx])
    return np.where(n > 0, k / np.maximum(n, 1), np.nan), n, k


for df in (H, O):
    ok = df.x.notna().values
    for r in (5, 10, 15, 25):
        sh, n, k = share_at(df.x.values[ok], df.y.values[ok], r)
        df.loc[ok, f"norse_share_{r}km"] = sh; df.loc[ok, f"norse_n_{r}km"] = k; df.loc[ok, f"settle_n_{r}km"] = n
    shb, _, _ = share_at(df.x.values[ok], df.y.values[ok], 15, NORSEB)
    df.loc[ok, "norse_broad_share_15km"] = shb
    d, i = TN.query(np.c_[df.x.values[ok], df.y.values[ok]])
    df.loc[ok, "nearest_norse_km"] = d / 1000
    df.loc[ok, "nearest_norse_name"] = S.name1.values[NORSE][i]
GB = H[H.in_stats].copy(); VIK = GB[GB.set_viking].copy(); ASX = GB[~GB.set_viking].copy(); AGE = GB

# settlement-level share (each settlement's own neighbourhood): the baseline distribution
for r in (10, 15, 25):
    sh, _, _ = share_at(S.x.values, S.y.values, r)
    S[f"ns{r}"] = sh


def mc(sub, r=15, draws=20000, pool=None):
    """Chance that n random settlements have a mean Norse share at least as high as the hoards'."""
    pool = S if pool is None else pool
    v = pool[f"ns{r}"].values; n = len(sub)
    obs = float(sub[f"norse_share_{r}km"].mean())
    sims = v[rng.integers(0, len(v), size=(draws, n))].mean(1)
    return dict(n=int(n), observed=rnd(obs, 4), random_mean=rnd(sims.mean(), 4),
                random_p95=rnd(np.percentile(sims, 95), 4), ratio=rnd(obs / sims.mean(), 2),
                p_one_sided=rnd((np.sum(sims >= obs) + 1) / (draws + 1), 4))


ENG = S[S.country == "England"]
R["overlap"] = {}
for r in (10, 15, 25):
    R["overlap"][f"r{r}"] = dict(
        viking_vs_settlements_gb=mc(VIK, r), viking_vs_settlements_england=mc(VIK[S.country.values[TS.query(np.c_[VIK.x.values, VIK.y.values])[1]] == "England"], r, pool=ENG),
        age_vs_settlements_gb=mc(AGE, r), other_dated_vs_settlements_gb=mc(ASX, r),
        other_periods_vs_settlements_gb=mc(O, r),
        viking_mean=rnd(VIK[f"norse_share_{r}km"].mean(), 4), viking_median=rnd(VIK[f"norse_share_{r}km"].median(), 4),
        other_periods_mean=rnd(O[f"norse_share_{r}km"].mean(), 4), other_periods_median=rnd(O[f"norse_share_{r}km"].median(), 4),
        other_dated_mean=rnd(ASX[f"norse_share_{r}km"].mean(), 4),
        settlements_mean=rnd(S[f"ns{r}"].mean(), 4), settlements_median=rnd(S[f"ns{r}"].median(), 4),
        mw_viking_vs_other_periods_p=rnd(mannwhitneyu(VIK[f"norse_share_{r}km"], O[f"norse_share_{r}km"], alternative="greater").pvalue, 4),
        mw_viking_vs_other_dated_p=rnd(mannwhitneyu(VIK[f"norse_share_{r}km"], ASX[f"norse_share_{r}km"], alternative="greater").pvalue, 4))
# broad element set as a check
S["nsb15"] = share_at(S.x.values, S.y.values, 15, NORSEB)[0]
obs = float(VIK.norse_broad_share_15km.mean()); sims = S.nsb15.values[rng.integers(0, len(S), size=(20000, len(VIK)))].mean(1)
R["overlap"]["broad15"] = dict(observed=rnd(obs, 4), random_mean=rnd(sims.mean(), 4), ratio=rnd(obs / sims.mean(), 2),
                               p_one_sided=rnd((np.sum(sims >= obs) + 1) / 20001, 4))
# Percentile of each hoard (share of all settlements whose own 15 km circle is strictly less Norse)
# Percentile of each hoard's neighbourhood among all settlements' neighbourhoods
pct = np.sort(S.ns15.values)
for df in (H, O):
    df["norse_pct_rank_15km"] = [rnd(np.searchsorted(pct, v, side="left") / len(pct) * 100, 1) if pd.notna(v) else None for v in df.norse_share_15km]
GB = H[H.in_stats].copy(); VIK = GB[GB.set_viking].copy(); ASX = GB[~GB.set_viking].copy()
R["overlap"]["viking_any_norse_within_5km"] = int((VIK.nearest_norse_km <= 5).sum())
R["overlap"]["viking_any_norse_within_5km_share"] = rnd((VIK.nearest_norse_km <= 5).mean(), 3)
R["overlap"]["other_any_norse_within_5km_share"] = rnd((O.nearest_norse_km <= 5).mean(), 3)
dS, _ = TN.query(np.c_[S.x.values, S.y.values], k=2)
self_n = np.where(NORSE, dS[:, 1], dS[:, 0]) / 1000  # a Norse settlement's nearest *other* Norse settlement
R["overlap"]["settlements_any_norse_within_5km_share"] = rnd((self_n <= 5).mean(), 3)
R["overlap"]["viking_median_nearest_norse_km"] = rnd(VIK.nearest_norse_km.median(), 1)
R["overlap"]["other_median_nearest_norse_km"] = rnd(O.nearest_norse_km.median(), 1)
R["overlap"]["settlements_median_nearest_norse_km"] = rnd(np.median(self_n), 1)
R["overlap"]["viking_above_gb_median"] = int((VIK.norse_pct_rank_15km > 50).sum())
R["overlap"]["viking_top_quartile"] = int((VIK.norse_pct_rank_15km > 75).sum())
R["overlap"]["viking_top_decile"] = int((VIK.norse_pct_rank_15km > 90).sum())
R["overlap"]["viking_zero_norse_15km"] = VIK[VIK.norse_n_15km == 0].hoard.tolist()

# ------------------------------------------------------------------ 10 km grid (for maps)
gx = (S.x // 10000).astype(int); gy = (S.y // 10000).astype(int)
G = S.assign(gx=gx, gy=gy).groupby(["gx", "gy"]).agg(n=("norse", "size"), k=("norse", "sum")).reset_index()
G["share"] = G.k / G.n
cx, cy = (G.gx * 10000 + 5000).values, (G.gy * 10000 + 5000).values
G["lon"], G["lat"] = TO_LL.transform(cx, cy)
TV = cKDTree(np.c_[VIK.x.values, VIK.y.values])
G["viking_hoard_km"] = TV.query(np.c_[cx, cy])[0] / 1000
G.round({"share": 4, "lon": 4, "lat": 4, "viking_hoard_km": 1}).to_csv(os.path.join(ROOT, "data", "grid10km.csv"), index=False)

# Names without silver: Norse names far from any located Viking hoard
S["viking_hoard_km"] = TV.query(np.c_[S.x.values, S.y.values])[0] / 1000
NS = S[S.norse]
R["names_without_silver"] = dict(
    norse_within_25km=rnd((NS.viking_hoard_km <= 25).mean(), 3), norse_within_50km=rnd((NS.viking_hoard_km <= 50).mean(), 3),
    norse_beyond_50km=int((NS.viking_hoard_km > 50).sum()), norse_beyond_50km_share=rnd((NS.viking_hoard_km > 50).mean(), 3),
    all_within_50km=rnd((S.viking_hoard_km <= 50).mean(), 3),
    norse_median_km=rnd(NS.viking_hoard_km.median(), 1), all_median_km=rnd(S.viking_hoard_km.median(), 1))
AREA = S.groupby("area").agg(settlements=("norse", "size"), norse=("norse", "sum"), country=("country", "first"),
                             median_hoard_km=("viking_hoard_km", "median")).reset_index()
AREA["share"] = AREA.norse / AREA.settlements
# hoards by area: nearest settlement's area (the list's county field uses historic names)
_, si = TS.query(np.c_[GB.x.values, GB.y.values])
GB["area"] = S.area.values[si]; H.loc[GB.index, "area"] = GB.area
VIK = GB[GB.set_viking].copy(); ASX = GB[~GB.set_viking].copy()
AREA["viking_hoards"] = AREA.area.map(VIK.area.value_counts()).fillna(0).astype(int)
AREA["age_hoards"] = AREA.area.map(GB.area.value_counts()).fillna(0).astype(int)
AREA = AREA.sort_values("norse", ascending=False)
AREA.round({"share": 4, "median_hoard_km": 1}).to_csv(os.path.join(ROOT, "data", "areas.csv"), index=False)
top = AREA.head(12)
R["areas_top"] = [dict(area=a.area, norse=int(a.norse), settlements=int(a.settlements), share=rnd(a.share, 3),
                       viking_hoards=int(a.viking_hoards), age_hoards=int(a.age_hoards), median_hoard_km=rnd(a.median_hoard_km, 1))
                  for a in top.itertuples()]
LINCS = AREA[AREA.area == "Lincolnshire"].iloc[0]
R["lincolnshire"] = dict(norse=int(LINCS.norse), share=rnd(LINCS.share, 3), viking_hoards=int(LINCS.viking_hoards),
                         age_hoards=int(LINCS.age_hoards), median_hoard_km=rnd(LINCS.median_hoard_km, 1),
                         share_of_england_norse=rnd(LINCS.norse / S[(S.country == "England")].norse.sum(), 3))
# the five 10 km squares with most Norse names: nearest Viking hoard
gt = G.sort_values("k", ascending=False).head(10)
R["top_cells"] = [dict(lat=rnd(g.lat, 3), lon=rnd(g.lon, 3), norse=int(g.k), settlements=int(g.n),
                       nearest_viking_hoard_km=rnd(g.viking_hoard_km, 0),
                       names=S[(gx == g.gx) & (gy == g.gy) & S.norse].name1.head(6).tolist()) for g in gt.itertuples()]
# cells with at least 5 Norse names: how many have a Viking hoard within 25 km?
R["top_cells_km"] = dict(min=rnd(gt.viking_hoard_km.min(), 0), max=rnd(gt.viking_hoard_km.max(), 0))
rich = G[G.k >= 5]
R["rich_cells"] = dict(n=int(len(rich)), with_hoard_25km=int((rich.viking_hoard_km <= 25).sum()),
                       with_hoard_50km=int((rich.viking_hoard_km <= 50).sum()))

# ------------------------------------------------------------------ Danelaw (approximate; from dale-down-fell-beck)
DANELAW = [(0.80, 51.51), (0.45, 51.47), (0.25, 51.46), (0.07, 51.50), (0.005, 51.508),
           (-0.04, 51.565), (-0.02, 51.67), (-0.03, 51.81), (-0.08, 51.80), (-0.21, 51.80), (-0.36, 51.82),
           (-0.42, 51.88), (-0.465, 51.905), (-0.467, 52.136),
           (-0.53, 52.15), (-0.625, 52.165), (-0.70, 52.155), (-0.72, 52.087), (-0.853, 52.058),
           (-0.99, 52.134), (-1.08, 52.23), (-1.17, 52.335), (-1.30, 52.497), (-1.42, 52.55), (-1.55, 52.58),
           (-1.70, 52.61), (-1.855, 52.656), (-2.89, 53.19)]
poly_ll = DANELAW + [(-3.10, 53.35), (-3.6, 54.2), (-3.6, 55.1), (-2.0, 55.9), (2.2, 55.9), (2.2, 51.3), (0.80, 51.30)]
px, py = TO_BNG.transform([p[0] for p in poly_ll], [p[1] for p in poly_ll])
DPOLY = Polygon(list(zip(px, py)))


def ne_share(df):
    e = df[df.country == "England"] if "country" in df else df
    return rnd(contains_xy(DPOLY, e.x.values, e.y.values).mean(), 3), int(len(e))


Oe = O.copy(); Oe["country"] = "England"
_, oi = TS.query(np.c_[O.x.values, O.y.values]); Oe["country"] = S.country.values[oi]
_, vi = TS.query(np.c_[VIK.x.values, VIK.y.values]); VIK["country_s"] = S.country.values[vi]
_, ai = TS.query(np.c_[ASX.x.values, ASX.y.values]); ASX["country_s"] = S.country.values[ai]
VE = VIK[VIK.country_s == "England"]; AE = ASX[ASX.country_s == "England"]
R["danelaw"] = dict(
    note="North and east of the approximate treaty line of Alfred and Guthrum (hand-placed, from the dale-down-fell-beck project); England only",
    coords=DANELAW,
    viking=dict(share=rnd(contains_xy(DPOLY, VE.x.values, VE.y.values).mean(), 3), n=int(len(VE)), inside=int(contains_xy(DPOLY, VE.x.values, VE.y.values).sum())),
    other_dated=dict(share=rnd(contains_xy(DPOLY, AE.x.values, AE.y.values).mean(), 3), n=int(len(AE)), inside=int(contains_xy(DPOLY, AE.x.values, AE.y.values).sum())),
    other_periods=dict(share=ne_share(Oe)[0], n=ne_share(Oe)[1]),
    norse_names=dict(share=ne_share(S[S.norse])[0], n=ne_share(S[S.norse])[1]),
    settlements=dict(share=ne_share(S)[0], n=ne_share(S)[1]))
VIK["danelaw_side"] = contains_xy(DPOLY, VIK.x.values, VIK.y.values) & (VIK.country_s == "England")
R["danelaw"]["viking_outside"] = VIK[(VIK.country_s == "England") & ~VIK.danelaw_side].hoard.tolist()

# ------------------------------------------------------------------ coast and rivers
import geo_utils as env  # noqa: E402
land = json.load(open(COAST)); cpts = []
for g in land:
    for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        for ring in p:
            a = np.array(ring)
            if a[:, 1].min() < 49.6 and a[:, 0].max() > 1.0:
                continue  # France
            x, y = TO_BNG.transform(a[:, 0], a[:, 1]); cpts.append(np.c_[x, y])
TC = cKDTree(env.densify(cpts, 200.0))
con = sqlite3.connect(RIVERS)
links = con.execute("select geometry, form, watercourse_name, length, start_node, end_node from watercourse_link where form != 'canal'").fetchall()
# major rivers: links sharing a name are joined into one river when their ends lie within 3 km of each
# other (this bridges short unnamed lake or channel links); a river counts as major at 50 km or more.
dec = [env.decode(geom) for geom, *_ in links]
parent = list(range(len(links)))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i


byname = {}
for i, (_, _, nm, L, a, b) in enumerate(links):
    if nm:
        byname.setdefault(nm, []).append(i)
for nm, ids in byname.items():
    if len(ids) < 2:
        continue
    ends = np.array([[dec[i][0][0], dec[i][-1][-1]] for i in ids]).reshape(-1, 2)
    for u, v in cKDTree(ends).query_pairs(3000.0):
        ra, rb = find(ids[u // 2]), find(ids[v // 2])
        if ra != rb:
            parent[ra] = rb
comp_len = {}
for i, (_, _, nm, L, a, b) in enumerate(links):
    if nm:
        comp_len[find(i)] = comp_len.get(find(i), 0) + L
major, tidal = [], []
for i, (geom, form, nm, L, a, b) in enumerate(links):
    lines = dec[i]
    if form == "tidalRiver":
        tidal += lines
    if nm and comp_len[find(i)] >= 50000:
        major += lines
TT = cKDTree(np.vstack([env.densify(tidal, 100.0), env.densify(cpts, 200.0)]))
TM = cKDTree(env.densify(major, 100.0))
R["rivers"] = dict(major_river_rule="a named watercourse at least 50 km long in total, joining same-named links whose ends lie within 3 km (OS Open Rivers, canals excluded)",
                   n_major_rivers=int(sum(v >= 50000 for v in comp_len.values())),
                   major_rivers_km=int(sum(v for v in comp_len.values() if v >= 50000) / 1000))
for df in (H, O):
    ok = df.x.notna().values
    xy = np.c_[df.x.values[ok], df.y.values[ok]]
    df.loc[ok, "coast_km"] = TC.query(xy)[0] / 1000
    df.loc[ok, "tidal_km"] = TT.query(xy)[0] / 1000
    df.loc[ok, "major_river_km"] = TM.query(xy)[0] / 1000
samp = S.sample(8000, random_state=1)
sxy = np.c_[samp.x.values, samp.y.values]
samp = samp.assign(coast_km=TC.query(sxy)[0] / 1000, tidal_km=TT.query(sxy)[0] / 1000, major_river_km=TM.query(sxy)[0] / 1000)
GB = H[H.in_stats].copy(); VIK = GB[GB.set_viking].copy(); ASX = GB[~GB.set_viking].copy()
R["water"] = {}
for k in ("coast_km", "tidal_km", "major_river_km"):
    R["water"][k] = dict(viking_median=rnd(VIK[k].median(), 1), other_dated_median=rnd(ASX[k].median(), 1),
                         other_periods_median=rnd(O[k].median(), 1), settlements_median=rnd(samp[k].median(), 1),
                         viking_within_5km=int((VIK[k] <= 5).sum()), viking_within_10km=int((VIK[k] <= 10).sum()),
                         settlements_within_5km_share=rnd((samp[k] <= 5).mean(), 3),
                         settlements_within_10km_share=rnd((samp[k] <= 10).mean(), 3),
                         other_within_5km_share=rnd((O[k] <= 5).mean(), 3),
                         mw_viking_vs_other_periods_p=rnd(mannwhitneyu(VIK[k], O[k], alternative="less").pvalue, 4),
                         mw_viking_vs_settlements_p=rnd(mannwhitneyu(VIK[k], samp[k], alternative="less").pvalue, 4))
R["water"]["n"] = int(len(VIK)); R["water"]["settlement_sample"] = 8000

# ------------------------------------------------------------------ silver: counts and weights
V = H[H.set_viking]
R["silver"] = dict(
    cuerdale_items=8600, cuerdale_kg_low=32, cuerdale_kg_high=40, cuerdale_found="15 May 1840",
    cuerdale_buried="between 903 and 910 (Wikipedia, Cuerdale Hoard)",
    cuerdale_hall_rival="four times larger than its nearest rival in Britain or Ireland, according to Richard Hall (quoted in Wikipedia, Cuerdale Hoard)",
    vale_of_york_items=682, cuerdale_vs_vale_of_york_items=rnd(8600 / 682, 1),
    hoards_with_coin_count=int(V.coins.notna().sum()), hoards_with_item_count=int(V.objects.notna().sum()),
    viking_coins_listed_total_excl_cuerdale=int(V.coins.fillna(0).sum()),
    items_or_coins={r.hoard: int(max(r.coins if pd.notna(r.coins) else 0, r.objects if pd.notna(r.objects) else 0))
                    for r in V.itertuples() if pd.notna(r.coins) or pd.notna(r.objects)},
    date_range=[int(V.date_sort.min()), int(V.date_sort.max())],
    by_find_century={str(k): int(v) for k, v in V.year_found.astype(str).str.extract(r"(\d{2})\d\d")[0].dropna().astype(int).add(1).value_counts().sort_index().items()},
    found_since_2000=int(V.year_found.astype(str).str.extract(r"(\d{4})")[0].dropna().astype(int).ge(2000).sum()))
tot = sum(R["silver"]["items_or_coins"].values())
R["silver"]["n_hoards_with_count"] = len(R["silver"]["items_or_coins"])
R["silver"]["cuerdale_share_of_listed_pieces"] = rnd(8600 / tot, 3); R["silver"]["listed_pieces_total"] = int(tot)

# ------------------------------------------------------------------ Cuerdale and the Ribble
cu = H[H.hoard == "Cuerdale Hoard"].iloc[0]
near = S[np.hypot(S.x - cu.x, S.y - cu.y) <= 25000].copy()
near["d_km"] = np.hypot(near.x - cu.x, near.y - cu.y) / 1000
york = TO_BNG.transform(-1.08, 53.96)
R["cuerdale"] = dict(
    lat=cu.lat, lon=cu.lon, norse_share_15km=rnd(cu.norse_share_15km, 4), norse_n_15km=int(cu.norse_n_15km),
    settle_n_15km=int(cu.settle_n_15km), pct_rank_15km=cu.norse_pct_rank_15km,
    norse_n_25km=int(near.norse.sum()), settle_n_25km=int(len(near)),
    norse_names_25km=near[near.norse].sort_values("d_km")[["name1", "d_km"]].round(1).values.tolist(),
    nearest_norse=cu.nearest_norse_name, nearest_norse_km=rnd(cu.nearest_norse_km, 1),
    tidal_km=rnd(cu.tidal_km, 1), coast_km=rnd(cu.coast_km, 1), major_river_km=rnd(cu.major_river_km, 2),
    york_km=rnd(np.hypot(cu.x - york[0], cu.y - york[1]) / 1000, 0),
    lancashire_viking_hoards=H[(H.set_viking) & H.place_text.str.contains("Lancashire")].hoard.tolist(),
    northwest_viking_hoards=H[(H.set_viking) & H.place_text.str.contains("Lancashire|Cumbria|Cheshire")].hoard.tolist())
LAN = AREA[AREA.area == "Lancashire"].iloc[0]
R["cuerdale"]["lancashire_norse"] = int(LAN.norse); R["cuerdale"]["lancashire_share"] = rnd(LAN.share, 3)
R["cuerdale"]["lancashire_settlements"] = int(LAN.settlements)
R["cuerdale"]["silverdale_warton_km"] = rnd(np.hypot(*(H[H.hoard == "Silverdale Hoard"][["x", "y"]].values[0] - H[H.hoard == "Warton Hoard"][["x", "y"]].values[0])) / 1000, 1)

# ------------------------------------------------------------------ per-hoard table and verdicts
med = float(np.median(S.ns15))
R["gb_median_share_15km"] = rnd(med, 4)


def verdict(r):
    if pd.isna(r.norse_share_15km):
        return "not located"
    if r.norse_n_15km == 0:
        return "silver without names"
    if r.norse_pct_rank_15km >= 75:
        return "silver among names"
    return "a few names"


H["verdict"] = [verdict(r) for r in H.itertuples()]
R["verdicts_viking"] = {k: int(v) for k, v in H[H.set_viking & H.in_stats].verdict.value_counts().items()}
R["silver_without_names"] = H[H.set_viking & H.in_stats & (H.verdict == "silver without names")].hoard.tolist()
R["silver_among_names"] = H[H.set_viking & H.in_stats & (H.verdict == "silver among names")].hoard.tolist()
cols = ["hoard", "country", "list_section", "set_viking", "in_stats", "date_text", "date_sort", "place_text", "lat", "lon",
        "precision", "year_found", "coins", "objects", "norse_n_15km", "settle_n_15km", "norse_share_15km", "norse_pct_rank_15km",
        "norse_share_10km", "norse_share_25km", "nearest_norse_name", "nearest_norse_km", "coast_km", "tidal_km",
        "major_river_km", "verdict"]
HM = H[cols].copy()
for c in ["norse_share_15km", "norse_share_10km", "norse_share_25km"]:
    HM[c] = HM[c].round(4)
for c in ["nearest_norse_km", "coast_km", "tidal_km", "major_river_km"]:
    HM[c] = HM[c].round(1)
HM.to_csv(os.path.join(ROOT, "data", "hoard_metrics.csv"), index=False)
R["hoards"] = json.loads(HM.to_json(orient="records"))
O[["hoard", "section", "date_text", "lat", "lon", "norse_share_15km", "coast_km", "tidal_km", "major_river_km"]].round(4).to_csv(
    os.path.join(ROOT, "data", "hoards_other_periods_gb_metrics.csv"), index=False)
json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# ------------------------------------------------------------------ compact page data
pd_ = dict(
    names=[[round(a, 4), round(b, 4), n, e] for a, b, n, e in zip(S[S.norse].lat, S[S.norse].lon, S[S.norse].name1, S[S.norse].core)],
    grid=[[round(a, 3), round(b, 3), int(n), int(k)] for a, b, n, k in zip(G.lat, G.lon, G.n, G.k)],
    other=[[round(a, 4), round(b, 4), h, s, dt] for a, b, h, s, dt in zip(O.lat, O.lon, O.hoard, O.section, O.date_text)],
    danelaw=[[b, a] for a, b in DANELAW])
json.dump(pd_, open(os.path.join(ROOT, "data", "page_data.json"), "w"), separators=(",", ":"))
print(json.dumps({k: R[k] for k in ["counts", "overlap", "areas_top", "top_cells", "cuerdale", "silver", "danelaw", "water", "names_without_silver", "lincolnshire", "rich_cells", "verdicts_viking", "silver_without_names", "silver_among_names"]}, default=str))
print(HM[HM.set_viking][["hoard", "norse_share_15km", "norse_pct_rank_15km", "nearest_norse_name", "nearest_norse_km", "tidal_km", "major_river_km", "verdict"]].to_string())
