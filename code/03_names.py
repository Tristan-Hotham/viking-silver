"""Step 3. Find Norse-derived elements in the names of settlements in OS Open Names (GB).

Features used: every OS Open Names record of type populatedPlace (local types City, Town, Village,
Hamlet, Other Settlement and Suburban Area). Each name is lower-cased and split into tokens on
spaces and hyphens ("Kirkby-in-Ashfield" -> kirkby, in, ashfield); a rule must match a whole token.

Element meanings are taken only from cited sources:
  W1   = Wikipedia, "List of generic forms in place names in the British Isles" (by/bie, thorpe, thwaite,
         toft, kirk, ster, holm/holme, garth)
  W2   = Wikipedia, "Toponymy of England" (by, thorpe, thwaite, toft)
  EPNS = Survey of English Place-Names, entry for Scaleby, Cumberland ("near the shielings", v. skali)
         https://epns.nottingham.ac.uk/browse/Cumberland/Scaleby/532847f8b47fc408f900102a-Scaleby
  SAT  = Shetland Amenity Trust, "Place name of the week: Bisters" (2020): -bister "from the Old Norse
         bolstadr meaning a farm or dwelling place"  https://www.shetlandamenity.org/place-name-of-the-week-bisters

Two sets:
  core  = elements the sources give as Old Norse only (by, thorpe, thwaite, toft, kirk, scale, and the
          Scottish farm words -ster, -bister and -bost, counted together as "ster")
  broad = core plus elements the sources give as Old Norse OR another language (holme: ON or OE;
          garth: ON or Welsh), used only as a sensitivity check.

Where a rule is limited to one area it is to avoid known false friends found in an audit of every
Scottish and Welsh match and of samples of English ones:
  * kirk counts only in England (Scots kirk = church, as in Falkirk and Kirkcaldy);
  * -by counts in England, and in Scotland only in Orkney, Shetland, Highland (Caithness) and Dumfries
    and Galloway; the Scots spelling -bie only in Dumfries and Galloway (Lockerbie, Canonbie). This
    drops Gaelic or Scots look-alikes such as Abercrombie, Rescobie and Stronchrubie, and Welsh
    Llangibby and Pontwalby;
  * -ster and -bister count only in Orkney, Shetland and Highland, and never inside -chester, -caster,
    -minster or Gaelic -allister (Gortonallister, Badfallister); -setter is left out because I found
    no citable gloss for it;
  * -bost (W1: Old Norse, farm; Leurbost) counts only in Orkney, Shetland, Highland and the Western Isles;
  * -scale and -garth count only in England.
Writes data/norse_names.csv (matched settlements) and work/settlements.csv (all settlements, with a
core/broad flag). Run: python3 03_names.py   (python3 03_names.py test runs the rule tests only)
"""
import os, re, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
OSN = os.path.join(HERE, "..", "..", "osnames_gb.tsv")

NORSE_SCOT = {"Orkney Islands", "Shetland Islands", "Highland", "Dumfries and Galloway"}
NORTH_ISLES = {"Orkney Islands", "Shetland Islands", "Highland"}
RULES = [  # key, label, set, regex on a token, areas (country or Scottish council; None = all), exclusions, meaning, source
    dict(key="by", label="-by", set="core", rx=r"[a-z]{2,}by", where={"England"} | NORSE_SCOT, exclude={"abby", "hobby", "lobby"},
         meaning="settlement, village (ON by, byr)", source="W1; W2"),
    dict(key="by", label="-by", set="core", rx=r"[a-z]{3,}bie", where={"Dumfries and Galloway"}, exclude=set(),
         meaning="settlement, village (W1 lists Lockerbie under by / bie)", source="W1"),
    dict(key="thorpe", label="-thorpe", set="core", rx=r".*thorpe?s?", where=None, exclude=set(),
         meaning="secondary settlement, satellite farm (ON thorp)", source="W1; W2"),
    dict(key="thwaite", label="-thwaite", set="core", rx=r".*thwaite?s?", where=None, exclude=set(),
         meaning="clearing, paddock, parcel of land (ON thveit)", source="W1; W2"),
    dict(key="toft", label="-toft", set="core", rx=r".*tofts?", where=None, exclude=set(),
         meaning="homestead (ON toft)", source="W1; W2"),
    dict(key="kirk", label="kirk-", set="core", rx=r"kirk.*|.*kirk", where={"England"}, exclude={"dunkirk"},
         meaning="church (ON)", source="W1"),
    dict(key="scale", label="-scale", set="core", rx=r"scales?|.{2,}scales?", where={"England"}, exclude=set(),
         meaning="shieling, summer hut (ON skali)", source="EPNS"),
    dict(key="ster", label="-ster / -bister", set="core", rx=r".*bister|.{2,}ster", where=NORTH_ISLES,
         exclude={"easter", "wester", "lister", "webster", "dempster", "foster", "forster"},
         exclude_rx=r".*(chester|caster|minster|allister|setter)", meaning="farm (ON)", source="W1; SAT"),
    dict(key="ster", label="-bost", set="core", rx=r".{2,}bost", where=NORTH_ISLES | {"Na h-Eileanan Siar"}, exclude=set(),
         meaning="farm (ON)", source="W1"),
    dict(key="holme", label="-holme", set="broad", rx=r".*(holme|hulme|holm)s?", where=None, exclude=set(),
         meaning="island; also holly (ON or OE)", source="W1"),
    dict(key="garth", label="-garth", set="broad", rx=r".*garth", where={"England"}, exclude=set(),
         meaning="enclosure, small summit or ridge (ON or Welsh)", source="W1"),
]
CORE_KEYS = ["by", "thorpe", "thwaite", "toft", "kirk", "scale", "ster"]


def tokens(name):
    s = name.lower().replace("’", "'")
    s = re.sub(r"\(.*?\)", " ", s)
    return [t.strip(".,;:!?\"'") for t in re.split(r"[\s\-]+", s) if t.strip(".,;:!?\"'")]


def element(name, country, only=None, area=""):
    """First matching rule key for this name (core rules are tried first)."""
    toks = tokens(name)
    for r in RULES:
        if only and r["set"] != only:
            continue
        if r["where"] and country not in r["where"] and area not in r["where"]:
            continue
        for t in toks:
            if t in r["exclude"] or (r.get("exclude_rx") and re.fullmatch(r["exclude_rx"], t)):
                continue
            if re.fullmatch(r["rx"], t):
                return r["key"]
    return None


TESTS = [("Grimsby", "England", "by"), ("Kirkby-in-Ashfield", "England", "by"), ("Lockerbie", "Scotland", "by", "Dumfries and Galloway"),
         ("Abercrombie", "Scotland", None, "Fife"), ("Tenby", "Wales", None), ("Llangibby", "Wales", None),
         ("Gortonallister", "Scotland", None, "Highland"), ("Isbister", "Scotland", "ster", "Shetland Islands"),
         ("Housetter", "Scotland", None, "Shetland Islands"), ("Leurbost", "Scotland", "ster", "Na h-Eileanan Siar"), ("Kittybrewster", "Scotland", None, "Aberdeen City"), ("Scunthorpe", "England", "thorpe"), ("Thorpe le Soken", "England", "thorpe"),
         ("Bassenthwaite", "England", "thwaite"), ("Lowestoft", "England", "toft"), ("Ormskirk", "England", "kirk"),
         ("Falkirk", "Scotland", None), ("Dunkirk", "England", None), ("Seascale", "England", "scale"),
         ("Portinscale", "England", "scale"), ("Scrabster", "Scotland", "ster", "Highland"), ("Easter Ross", "Scotland", None),
         ("Chester", "England", None), ("Leicester", "England", None), ("Levenshulme", "England", "holme"),
         ("Aysgarth", "England", "garth"), ("Preston", "England", None), ("Clitheroe", "England", None)]

if __name__ == "__main__":
    T = [t + ("",) * (4 - len(t)) for t in TESTS]
    bad = [(n, c, e, element(n, c, area=a)) for n, c, e, a in T if element(n, c, area=a) != e]
    print("rule tests:", "all pass" if not bad else bad)
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        sys.exit()
    d = pd.read_csv(OSN, sep="\t", dtype=str, keep_default_na=False)
    d = d[d.type == "populatedPlace"].copy()
    for c in ("lat", "lon"): d[c] = d[c].astype(float)
    for c in ("x", "y"): d[c] = d[c].astype(int)
    d["area"] = d.county.where(d.county != "", d.district).map(lambda c: c.split(" - ")[-1].strip() if " - " in c else c)
    d["core"] = [element(n, c, "core", a) or "" for n, c, a in zip(d.name1, d.country, d.area)]
    d["broad"] = [element(n, c, area=a) or "" for n, c, a in zip(d.name1, d.country, d.area)]
    keep = ["name1", "local_type", "lat", "lon", "x", "y", "area", "country", "core", "broad"]
    d[keep].to_csv(os.path.join(ROOT, "work", "settlements.csv"), index=False)
    m = d[d.broad != ""][keep].rename(columns={"name1": "name", "core": "element_core", "broad": "element_broad"})
    m.to_csv(os.path.join(ROOT, "data", "norse_names.csv"), index=False)
    print(len(d), "settlements;", (d.core != "").sum(), "core Norse;", (d.broad != "").sum(), "broad")
    print(d[d.core != ""].core.value_counts().to_string())
    print(d[d.broad != ""].broad.value_counts().to_string())
    print(d.groupby("country").apply(lambda g: (g.core != "").mean()).round(4).to_string())
