# Silver and Names

The Vikings left two kinds of trace in Britain: buried silver and place names. This study puts {{counts.hoards_viking_gb|int}} Viking hoards from Wikipedia's lists of hoards against every settlement in the Ordnance Survey's gazetteer ({{counts.settlements|int}}, of which {{counts.norse_core|int}} carry a Norse element such as -by, -thorpe, -thwaite or -toft) and asks whether the two maps agree, and where there is silver without names, or names without silver.

**Interactive version:** https://tristan-hotham.github.io/viking-silver/

This repository holds the interactive page, the data and the analysis code for the data study *Silver and Names: Viking hoards and Norse place names in Britain* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23677169

## Headline results

- Around the {{counts.vik_in_stats|int}} Viking hoards located to village level in Britain, {{overlap.r15.viking_mean|pct1}} of settlements within 15 km have a Norse name, {{overlap.r15.viking_vs_settlements_gb.ratio|f1}} times the {{overlap.r15.viking_vs_settlements_gb.random_mean|pct1}} around a random settlement (20,000 random draws, one-sided p = {{overlap.r15.viking_vs_settlements_gb.p_one_sided|f3}}). The result holds at 10 km ({{overlap.r10.viking_vs_settlements_gb.ratio|f1}} times) and 25 km ({{overlap.r25.viking_vs_settlements_gb.ratio|f1}} times).
- The {{counts.other_periods_baseline|int}} hoards of other periods in the Great Britain list average {{overlap.r15.other_periods_mean|pct1}} ({{overlap.r15.other_periods_vs_settlements_gb.ratio|f1}} times random). Viking hoards are more Norse than these (one-sided rank test p = {{overlap.r15.mw_viking_vs_other_periods_p|f3}}).
- {{danelaw.viking.inside|int}} of {{danelaw.viking.n|int}} English Viking hoards lie north and east of the approximate Danelaw line, with {{danelaw.norse_names.share|pct0}} of Norse names and {{danelaw.settlements.share|pct0}} of all English settlements. The two outside, Watlington and Eye, are late 9th century hoards with coins of Alfred and Ceolwulf II.
- Silver without names: five Viking hoards (Ashdon, Talnotrie, Eye, Watlington, Bryn Maelgwyn) have no Norse-named settlement within 15 km.
- Names without silver: Lincolnshire has {{lincolnshire.norse|int}} Norse-named settlements ({{lincolnshire.share_of_england_norse|pct0}} of England's) and no Viking hoard in the lists. The ten 10 km squares with the most Norse names, all in Lincolnshire and Leicestershire, are {{top_cells_km.min|int}} to {{top_cells_km.max|int}} km from the nearest listed Viking hoard.
- Viking hoards are not especially coastal: median {{water.tidal_km.viking_median|f1}} km to tidal water against {{water.tidal_km.settlements_median|f1}} km for settlements.
- Cuerdale (found 1840 by the Ribble near Preston; more than 8,600 items, 32 to 40 kg) is {{silver.cuerdale_share_of_listed_pieces|pct0}} of all pieces counted in the listed Viking hoards, yet only {{cuerdale.norse_n_15km|int}} of {{cuerdale.settle_n_15km|int}} settlements within 15 km of it have Norse names.

## Files

- `index.html`: the interactive page (Leaflet map with layer toggles and hoard popups, charts).
- `header.png`: social card.
- `data/hoards.csv`: the {{counts.hoards_all|int}} Viking Age hoards (the lists' "Viking hoards" tables plus other rows dated 793 to 1066), with list section, date, find place, coordinates, how and from what source each was located, museum, contents, counts of coins, items and ingots where the list states them, Wikidata cross-check, source and article URLs.
- `data/hoard_metrics.csv`: the same hoards with the Norse share of settlements within 10, 15 and 25 km, percentile among all settlements, nearest Norse-named settlement, distances to coast, tidal water and major rivers, and a verdict.
- `data/hoards_other_periods_gb.csv` and `data/hoards_other_periods_gb_metrics.csv`: the {{counts.other_periods_baseline|int}} other located hoards in the Great Britain list (the baseline).
- `data/norse_names.csv`: every OS Open Names settlement with a Norse element (core set, and the broad set with -holme and -garth), with coordinates, type, area and element.
- `data/grid10km.csv`: settlements and Norse names per 10 km British National Grid square, with distance to the nearest Viking hoard.
- `data/areas.csv`: Norse names, settlements and hoards per OS Open Names county or unitary area.
- `data/page_data.json`: compact data for the page.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_parse_hoards.py` (parse the list wikitext), `02_hoards.py` (select, locate and cross-check hoards), `03_names.py` (Norse elements; `python3 03_names.py test` runs the rule tests), `04_analysis.py` (all statistics), `05_build_site.py` (page and README), `06_header.py` (social card), `07_release_figs.py` (paper and blog figures), `08_paper.py` (paper PDF via xelatex). `geo_utils.py` decodes OS Open Rivers geometry. Large shared inputs (OS Open Names, OS Open Rivers, Wikipedia wikitext, Wikidata extract) are read from the parent folder and are not included.

## Method in brief

**Hoards.** Every row of the "Viking hoards" tables in Wikipedia's List of hoards in Great Britain and List of hoards in Ireland, the lists' own label for hoards associated with Viking culture ({{counts.hoards_viking_tables|int}} hoards after merging one duplicate). A wider "Viking Age" set adds every other row whose sortable date in the list is 793 to 1066 ({{counts.hoards_viking_age_extra|int}} more). Hoards are placed at the coordinate in the list row (village level); rows without one are placed from the stated find place in OS Open Names, or from Wikidata (Talnotrie). The Galloway Hoard's find spot is withheld and is not mapped; Storr Rock is placed only approximately and is left out of the tests; the Irish hoards are mapped but not tested, because the place-name data cover Great Britain only.

**Names.** OS Open Names populated places, split into words, matched as whole words to -by, -thorpe, -thwaite, -toft, kirk-, -scale and, in Orkney, Shetland, Highland and the Western Isles, -ster, -bister and -bost. To avoid false friends kirk counts only in England, -by in Scotland only in Orkney, Shetland, Highland and Dumfries and Galloway, and Welsh look-alikes are excluded. Element meanings are taken only from: Wikipedia, *List of generic forms in place names in the British Isles* and *Toponymy of England*; the Survey of English Place-Names entry for Scaleby, Cumberland; and the Shetland Amenity Trust note on -bister. A broad set adds -holme and -garth, which those sources give as Norse or English/Welsh.

**Tests.** The share of settlements within 10, 15 and 25 km of each hoard that carry a Norse element, against 20,000 random draws of the same number of settlements, and against hoards of other periods (Mann-Whitney). Distances to the coast (Natural Earth 1:10m land), tidal water (coast plus OS Open Rivers tidal rivers) and major rivers (named watercourses at least 50 km long). The Danelaw line is the approximate tracing used in the companion study [Beck, brook or burn](https://tristan-hotham.github.io/dale-down-fell-beck/).

**Caveats.** The hoards are the notable ones listed on Wikipedia, not every find; most points are village-level; OS Open Names is a modern map; agreement between silver and names does not separate Viking activity from where land has been disturbed and searched.

## How to rerun

Python 3 with pandas, numpy, scipy, shapely, pyproj (and Playwright for the header). From `code/`: `python3 01_parse_hoards.py && python3 02_hoards.py && python3 03_names.py && python3 04_analysis.py && python3 05_build_site.py`. Inputs expected one folder up: `_data2/wikipedia_wikitext.json`, `_data2/wikidata/hoards.json`, `osnames_gb.tsv`, `osrivers/Data/oprvrs_gb.gpkg`, and the Natural Earth land extract used by the lighthouse project.

## Sources and licence

- Hoards: Wikipedia contributors, *List of hoards in Great Britain*, *List of hoards in Ireland* and *Cuerdale Hoard*, https://en.wikipedia.org (CC BY-SA 4.0). Cross-check: Wikidata (CC0).
- Place names and rivers: Contains OS data © Crown copyright and database right 2026. OS Open Names and OS Open Rivers, Ordnance Survey, Open Government Licence v3.0.
- Element meanings: Wikipedia, *List of generic forms in place names in the British Isles* and *Toponymy of England* (CC BY-SA 4.0); Survey of English Place-Names (English Place-Name Society), Scaleby, https://epns.nottingham.ac.uk/browse/Cumberland/Scaleby/532847f8b47fc408f900102a-Scaleby ; Shetland Amenity Trust (2020), Place name of the week: Bisters, https://www.shetlandamenity.org/place-name-of-the-week-bisters
- Coastline: Natural Earth (public domain).
- Base map tiles on the page: Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community. Map library: Leaflet.

Because the hoard data derive from Wikipedia (CC BY-SA 4.0), the derived data and the page text are released under CC BY-SA 4.0; please keep the Ordnance Survey copyright statement when reusing the data. Code is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) *Silver and Names: Viking hoards and Norse place names in Britain*. Zenodo. https://doi.org/10.5281/zenodo.23677169

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
