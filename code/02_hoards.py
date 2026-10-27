"""Step 2. Choose the Viking Age hoards, locate them, cross-check with Wikidata, and write data/hoards.csv.

Inclusion rule (stated on the page):
  * "Viking" set: every row of the "Viking hoards" tables in the Wikipedia lists of hoards in Great
    Britain and in Ireland (the lists' own label for hoards "associated with the Viking culture").
  * "Viking Age" set: the Viking set plus any row in another section of the same lists whose
    sortable date (the year the list itself uses to sort the table) is 793 to 1066 inclusive.
    793 is the raid on Lindisfarne and 1066 the battle of Stamford Bridge, the conventional ends of
    the Viking Age in Britain.
  * One duplicate is merged: the list's "Herefordshire hoard" row is the same find as its "Eye
    Hoard" row (both: Eye near Leominster, found 2015, about 300 coins, 31 recovered).

Baseline: data/hoards_other_periods_gb.csv holds every other located row of the Great Britain list
(Neolithic to post-medieval), used as a "where do hoards get found and listed" comparison.

Location: the {{Coord}} given in the list row (most are village-level points from Wikimapia, as the
list's own coordinate template says). Rows with no coordinate are located from the stated find place,
matched to an OS Open Names populated place in the stated county, or (Talnotrie) from Wikidata.
Each hoard records its location source and precision.

Counts: coins, objects and weights are transcribed by hand from each row's "Contents" cell, only
where the list states a number (see COUNTS below). Cuerdale's weight is from the Wikipedia article on
the Cuerdale Hoard.

Run: python3 02_hoards.py
"""
import json, math, os, re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
ALL = pd.read_csv(os.path.join(ROOT, "work", "hoard_rows_all.csv"))
WD = json.load(open(os.path.join(HERE, "..", "..", "_data2", "wikidata", "hoards.json")))
OSN = os.path.join(HERE, "..", "..", "osnames_gb.tsv")

LIST_URL = {"GB": "https://en.wikipedia.org/wiki/List_of_hoards_in_Great_Britain",
            "IE": "https://en.wikipedia.org/wiki/List_of_hoards_in_Ireland"}

# find places for rows with no {{Coord}}: (OS Open Names name1, county) or a Wikidata item
GEOCODE = {
    "Ashdon Hoard": ("os", "Ashdon", "Essex", "find place 'Ashdon' in the list; OS Open Names village"),
    "Bolton Percy hoard": ("os", "Bolton Percy", "North Yorkshire", "find place 'Bolton Percy' in the list; OS Open Names village"),
    "Bucklesham Hoard": ("os", "Bucklesham", "Suffolk", "find place 'Bucklesham' in the list; OS Open Names village"),
    "Hexham Hoard": ("os", "Hexham", "Northumberland", "hoard named after Hexham (place cell blank); OS Open Names town"),
    "Kirkoswald Hoard": ("os", "Kirkoswald", "Westmorland and Furness", "find place 'Kirkoswald, Cumbria' in the list; OS Open Names village"),
    "Storr Rock Hoard": ("os", "The Storr", "Highland", "list gives only 'Isle of Skye'; placed at OS Open Names 'The Storr' from the hoard's name (approximate)"),
    "Talnotrie Hoard": ("wd", "Q108615901", None, "list gives 'near Talntrie' with no coordinate; Wikidata Q108615901 coordinate (CC0)"),
}
UNLOCATED = {"Galloway Hoard": "find site withheld: the list gives only Kirkcudbrightshire, and the Wikipedia article on the hoard says 'near Balmaghie' on undisclosed glebe land; not mapped"}
PRECISION_NOTE = {"Watlington Hoard": "the list's coordinate is the town, not the find site, which it says is unknown"}

# hand transcription from the list's Contents cell (None = not stated)
COUNTS = {
    "Ainsbrook Hoard": dict(objects=130, approx=True),
    "Ashdon Hoard": dict(coins=71),
    "Bedale Hoard": dict(objects=48, note="sum of the listed pieces: 1 pommel, 4 gold hoops, 6 rivets, 4 collars and neck-rings, 1 arm-ring, 1 ring fragment, 1 brooch, 29 ingots", ingots=29),
    "Bryn Maelgwyn Hoard": dict(coins=204),
    "Cuerdale Hoard": dict(objects=8600, weight_kg_low=32, weight_kg_high=40, note="'more than 8,600 items'; weight 32 to 40 kg, mostly bullion (Wikipedia, Cuerdale Hoard)"),
    "Eye Hoard": dict(coins=300, approx=True, note="about 300 coins; only 31 recovered"),
    "Furness Hoard": dict(coins=92),
    "Galloway Hoard": dict(objects=100, approx=True, note="'over 100' gold and silver items"),
    "Goldsborough Hoard": dict(coins=39),
    "Huxley Hoard": dict(objects=22),
    "Silverdale Hoard": dict(objects=201, coins=27, ingots=14),
    "Skaill Hoard": dict(objects=100, approx=True, note="'over 100 items'"),
    "Vale of York Hoard; (Harrogate Hoard)": dict(coins=617, objects=682, note="'more than 617 silver coins, and 65 other items'"),
    "Warton Hoard": dict(coins=3, weight_g=116.49, note="3 dirhams plus 6 pieces of cut silver weighing 116.49 g"),
    "Watlington Hoard": dict(coins=210, approx=True, ingots=15),
    "Mullaghboden Hoard": dict(coins=11),
    "Appledore Hoard": dict(coins=502, note="490 pennies (1997) and 12 (1998)"),
    "Bamburgh Hoard": dict(coins=384),
    "Beeston Tor Hoard": dict(coins=49),
    "Bolton Percy hoard": dict(coins=4000, approx=True),
    "Brantham Hoard": dict(coins=90),
    "Bucklesham Hoard": dict(coins=99),
    "Harkirke (or Harkirk) Hoard": dict(coins=300, approx=True),
    "Hexham Hoard": dict(coins=8000, approx=True),
    "Ipswich Hoard (1863)": dict(coins=150),
    "Kirkoswald Hoard": dict(coins=542),
    "Lenborough Hoard": dict(coins=5251, note="5,251 and a half coins"),
    "Pentney Hoard": dict(objects=6),
    "St Leonard's Place Hoard": dict(coins=10000, approx=True),
    "Trewhiddle Hoard": dict(coins=114),
    "West Yorkshire Hoard": dict(objects=5),
}


def hav(a, b, c, d):
    t = math.pi / 180; h = math.sin((c - a) * t / 2) ** 2 + math.cos(a * t) * math.cos(c * t) * math.sin((d - b) * t / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


osn = pd.read_csv(OSN, sep="\t", usecols=["name1", "type", "local_type", "lat", "lon", "county", "district"], dtype=str, keep_default_na=False)
wd = {}
for r in WD:
    lon, lat = map(float, r["c"][6:-1].split())
    wd.setdefault(r["h"], dict(label=r["hLabel"], lat=lat, lon=lon, enwiki=r.get("enwiki", "")))

d = ALL.copy()
d["set_viking"] = d.section.str.contains("Viking")
d["set_age"] = d.set_viking | d.date_sort.between(793, 1066)
d = d[d.set_age].copy()
d = d[d.hoard != "Herefordshire hoard"]  # duplicate of Eye Hoard
out = []
for r in d.itertuples():
    lat, lon, src, prec = r.lat, r.lon, "", ""
    if pd.notna(lat):
        src = f"coordinate in the {'Great Britain' if r.country == 'GB' else 'Ireland'} list row"
        prec = "village level (list coordinate)"
    elif r.hoard in GEOCODE:
        kind, key, county, note = GEOCODE[r.hoard]
        if kind == "os":
            m = osn[(osn.name1 == key) & ((osn.county == county) | (osn.district == county))]
            assert len(m) == 1, (r.hoard, len(m))
            lat, lon = float(m.lat.iloc[0]), float(m.lon.iloc[0])
        else:
            lat, lon = wd[key]["lat"], wd[key]["lon"]
        src = note; prec = "approximate (place name)" if "approximate" in note else ("Wikidata coordinate" if kind == "wd" else "village level (geocoded)")
    elif r.hoard in UNLOCATED:
        src = UNLOCATED[r.hoard]; prec = "not located"
    if r.hoard in PRECISION_NOTE:
        prec += "; " + PRECISION_NOTE[r.hoard]
    # Wikidata cross-check: nearest Wikidata hoard with a similar label
    base = re.sub(r"[;(].*", "", r.hoard).replace("Hoard", "").replace("hoard", "").strip().lower()
    wq, wdist = "", None
    for q, w in wd.items():
        key = next((t for t in base.split() if len(t) > 3), "")
        if key and re.search(r"\b" + re.escape(key) + r"\b", w["label"].lower()):
            if pd.notna(lat):
                dist = hav(lat, lon, w["lat"], w["lon"])
                if dist < 60:
                    wq, wdist = q, round(dist, 2)
    c = COUNTS.get(r.hoard, {})
    out.append(dict(
        hoard=re.sub(r";\s*\(", " (", r.hoard), country=r.country, list_section=r.section,
        set_viking=bool(r.set_viking), set_viking_age=True, date_text=r.date_text, date_sort=int(r.date_sort),
        place_text=r.place_text if r.hoard != "Galloway Hoard" else "Kirkcudbrightshire",
        lat=round(lat, 5) if pd.notna(lat) else None, lon=round(lon, 5) if pd.notna(lon) else None,
        location_source=src, precision=prec, year_found=r.year_found,
        museum=r.location if r.hoard != "Galloway Hoard" else "National Museum of Scotland, Edinburgh",
        contents=r.contents if r.hoard != "Galloway Hoard" else "over 100 gold and silver items, including armbands, a Christian cross, brooches, ingots and an exceptionally large Carolingian pot",
        coins=c.get("coins"), objects=c.get("objects"), ingots=c.get("ingots"), approx=c.get("approx", False),
        weight_g=c.get("weight_g"), weight_kg_low=c.get("weight_kg_low"), weight_kg_high=c.get("weight_kg_high"),
        count_note=c.get("note", ""), in_stats=bool(pd.notna(lat) and "approximate" not in prec and r.country == "GB"),
        wikidata=wq, wikidata_offset_km=wdist,
        source=LIST_URL[r.country] + (" (and https://en.wikipedia.org/wiki/Cuerdale_Hoard)" if r.hoard == "Cuerdale Hoard" else ""),
        article=f"https://en.wikipedia.org/wiki/{str(r.article).replace(' ', '_')}" if isinstance(r.article, str) and r.article else ""))
o = pd.DataFrame(out).sort_values("date_sort")
# Cells the parser cannot read cleanly: the Galloway row's place template contains '||', which shifts its
# cells (year found is 2014 in the list); two rows carry a note, not a museum, in the location column.
o.loc[o.hoard == "Galloway Hoard", "year_found"] = "2014"
o.loc[o.hoard == "Hexham Hoard", "museum"] = "not given in the list"
o.loc[o.hoard == "Bucklesham Hoard", "museum"] = "not given in the list (it notes the hoard was sold at auction)"
o["museum"] = o.museum.fillna("not given in the list").replace({"unknown": "not known (list)"})
for c in ("date_text", "place_text", "year_found", "museum", "contents", "count_note"):  # no dashes in visible text
    o[c] = o[c].astype(str).str.replace("\u2013", " to ", regex=False).str.replace("\u2014", ", ", regex=False).replace({"nan": ""})
o.to_csv(os.path.join(ROOT, "data", "hoards.csv"), index=False)

# Baseline: every other located hoard in the Great Britain list (all periods outside the Viking Age set).
# These show where hoards of any date have been found and reported, so they carry the same biases of
# farming, building, detecting and recording as the Viking hoards.
base = ALL[(ALL.country == "GB") & ALL.lat.notna() & ~ALL.hoard.isin(d.hoard) & (ALL.hoard != "Herefordshire hoard")]
base = base[["hoard", "section", "date_text", "date_sort", "place_text", "lat", "lon", "year_found"]].copy()
for c in ("date_text", "place_text", "year_found"):
    base[c] = base[c].astype(str).str.replace("\u2013", " to ", regex=False).replace({"nan": ""})
base["source"] = LIST_URL["GB"] + " (coordinate in the list row)"
base.to_csv(os.path.join(ROOT, "data", "hoards_other_periods_gb.csv"), index=False)
print(len(base), "baseline hoards of other periods;", base.section.value_counts().to_dict())
print(o[["hoard", "country", "set_viking", "date_sort", "lat", "lon", "precision", "wikidata", "wikidata_offset_km"]].to_string())
print(len(o), "hoards;", int(o.set_viking.sum()), "in the Viking tables")
