"""Step 1. Parse the Wikipedia hoard lists into one table of rows.

Reads the full wikitext of "List of hoards in Great Britain" and "List of hoards in Ireland"
(CC BY-SA 4.0, downloaded to ../../_data2/wikipedia_wikitext.json) and writes
../work/hoard_rows_all.csv: one row per table row, with the list section it sits in, the sortable
date the list gives ({{sort|0905|early 10th century}} -> 905), the place text, any {{Coord}} in the
row, year of discovery, current location and contents (wiki markup stripped).

Run: python3 01_parse_hoards.py
"""
import json, os, re, csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = os.path.join(HERE, "..", "..", "_data2", "wikipedia_wikitext.json")
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
W = json.load(open(SRC))


def strip_refs(s):
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    # {{#tag:ref|...|group=note}} notes (may contain nested templates)
    while "{{#tag:ref" in s:
        i = s.find("{{#tag:ref"); depth = 0; j = i
        while j < len(s):
            if s.startswith("{{", j): depth += 1; j += 2; continue
            if s.startswith("}}", j):
                depth -= 1; j += 2
                if depth == 0: break
                continue
            j += 1
        s = s[:i] + s[j:]
    return s


def plain(s):
    s = strip_refs(s)
    s = re.sub(r"\{\{[Cc]oord\|[^}]*\}\}", "", s)
    s = re.sub(r"\{\{sort\|[^|}]*\|([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\{\{convert\|([\d.]+)\|(\w+)[^}]*\}\}", r"\1 \2", s)
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"<br\s*/?>", "; ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("'''", "").replace("''", "")
    s = re.sub(r"\s+", " ", s).strip(" ;|")
    return s


def link_target(s):
    m = re.search(r"\[\[([^\]|]*)", s)
    return m.group(1).strip() if m else ""


def coord(s):
    m = re.search(r"\{\{[Cc]oord\|(-?[\d.]+)\|(-?[\d.]+)", s)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def sortdate(s):
    m = re.search(r"\{\{sort\|(-?\d+)\|", s)
    return int(m.group(1)) if m else None


def split_cells(row):
    """A wikitable row: cells start with '|' at line start, and '||' separates cells on a line."""
    row = strip_refs(row)
    cells = []
    for line in row.split("\n"):
        if not line.startswith("|") or line.startswith("|-") or line.startswith("|}"):
            if cells and line.strip() and not line.startswith(("|-", "|}", "!")):
                cells[-1] += "\n" + line
            continue
        parts = re.split(r"\|\|", line[1:])
        cells.extend(parts)
    return [c.strip() for c in cells]


rows = []
for title, country in [("List of hoards in Great Britain", "GB"), ("List of hoards in Ireland", "IE")]:
    wt = W[title]["wt"]
    secs = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^==([^=].*?)==\s*$", wt, re.M)]
    secs.append((len(wt), "END"))
    for (a, name), (b, _) in zip(secs, secs[1:]):
        body = wt[a:b]
        for tm in re.finditer(r"\{\|(.*?)\n\|\}", body, re.S):
            tbl = tm.group(1)
            for raw in re.split(r"\n\|-[^\n]*", tbl)[1:]:
                if raw.strip().startswith("!") or not raw.strip():
                    continue
                c = split_cells(raw)
                if len(c) < 6:
                    continue
                # some rows have the image cell missing or merged; keep the 7-column reading where possible
                if len(c) == 6:
                    c.insert(1, "")
                hoard, image, date, place, found, where, contents = (c + [""] * 7)[:7]
                lat, lon = coord(raw)
                sd = sortdate(date)
                if sd is None:
                    m = re.search(r"(\d{1,2})(?:st|nd|rd|th) century", plain(date))
                    if m:  # a bare "10th century" with no sort key: mid-century, flagged
                        sd = (int(m.group(1)) - 1) * 100 + 50
                        if re.search(r"late", plain(date), re.I): sd += 25
                        if re.search(r"early", plain(date), re.I): sd -= 25
                rows.append(dict(
                    list=title, country=country, section=name, hoard=plain(hoard), article=link_target(hoard),
                    date_text=plain(date), date_sort=sd, date_has_sortkey=sortdate(date) is not None,
                    place_text=plain(place), place_link=link_target(re.sub(r"\{\{sort\|[^|]*\|", "", place)),
                    lat=lat, lon=lon, year_found=plain(found), location=plain(where), contents=plain(contents)))

out = os.path.join(ROOT, "work", "hoard_rows_all.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "rows ->", out)
