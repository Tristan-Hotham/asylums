"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, o, c, cv, fc, lo, ep, B, L, NM = R["source"], R["open"], R["close"], R["curve"], R["fates_closed"], R["london"], R["epsom"], R["beds"], R["listed"], R["names"]
N = lambda v: f"{round(v):,}"
P = lambda v: f"{round(v)}%"
readme = f"""# Where the asylums were

A map and analysis of Britain's county lunatic asylums and later psychiatric hospitals, built from English Wikipedia: where they were, when they opened after the County Asylums Act 1808 and the Lunacy Act 1845, how big they grew, when they closed after Enoch Powell's 1961 Water Tower speech and Care in the Community, and what the sites are now. {N(s['kept'])} places, {N(s['located'])} located. A companion to "What's left of the workhouse?".

**This is not a complete list of Britain's asylums.** It covers places that have an English Wikipedia article in the categories walked, read by simple published rules.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Coverage: {N(s['pages'])} Wikipedia articles found; {N(s['kept'])} kept as asylums, psychiatric hospitals or institutions for people with learning disabilities ({N(s['drop_general'])} general hospitals and {N(s['drop_nothospital'])} non-hospital articles dropped); {N(s['located'])} located: {R['nations']['England']} in England, {R['nations']['Scotland']} in Scotland, {R['nations']['Wales']} in Wales, {R['nations']['Northern Ireland']} in Northern Ireland, {R['nations']['Isle of Man']} on the Isle of Man.
- Openings: two waves, peaking in the {o['peak_dec']}s ({o['peak_n']}) and the 1900s ({o['dec1900s']}), with a lull in the 1880s ({o['dec1880s']}). {P(o['y1845_1914_pct'])} of places with an opening year opened between 1845 and 1914.
- Closures: {c['before1961']} of {c['n']} dated closures came before 1961 and {c['y1961_1979']} between 1961 and 1979; {c['dec1980s']} in the 1980s, {c['dec1990s']} in the 1990s, {c['dec2000s']} in the 2000s. {P(c['y1980_1999_pct'])} closed between 1980 and 1999. The number open peaked at {cv['peak_n']} ({cv['peak_first']} to {cv['peak_last']}) and is {cv['y2026']} today. Median life of a Victorian asylum: {R['gap']['vic_median_life']} years.
- Size: the largest stated is Whittingham, Lancashire, {N(B['top'][0]['beds'])} patients in 1939; {B['over1000']} places state 1,000 or more.
- Clusters: {lo['ring_vic']} asylums opened 1830 to 1939 lie 10 to 40 km from Charing Cross, {lo['inner_vic']} within 10 km; the five Epsom hospitals opened {ep['opened_min']} to {ep['opened_max']} within {ep['max_km']} km of each other.
- Now: of {fc['n']} places no longer open, {fc['homes']} ({P(R['fates_closed_pct']['homes'])}) are homes, {fc['other']} another use, {fc['demolished']} demolished, {fc['derelict']} derelict, {fc['unknown']} not stated. Of those with a stated fate, {P(fc['homes_of_known_pct'])} are homes. {L['n']} articles ({P(L['pct'])}) report a listed building.
- Names: {NM['asylum_any']} articles record an "asylum" name, {NM['mental_hospital']} a "mental hospital" name; where a single year is given for the "mental hospital" name, {NM['mh_years_1920_1939']} of {NM['mh_years_n']} fall in 1920 to 1939.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/counties.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/asylums.csv` | All {N(s['kept'])} places: Wikipedia title and revision, other names, nation, county, coordinates, opened and closed years with their source, status, stated beds with the phrase, fate with the phrase that set it, listed status, learning disability flag, distance to the nearest big town and to Charing Cross, selection rule. **CC BY-SA 4.0** (derived from Wikipedia). |
| `data/excluded.csv` | The {N(s['dropped'])} articles dropped, with the reason. CC BY-SA 4.0. |
| `data/by_decade.csv`, `data/open_by_year.csv` | Openings and closures by decade; places open, opened and closed each year. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/land.json`, `data/counties.json`, `data/cities.json` | Page data and outlines. |
| `raw/` | The inputs: Wikipedia article heads and context articles (CC BY-SA 4.0), the Wikidata extract (CC0, not used, see below). |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, and `qa.js`, the browser check. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Selection: an article is kept if it describes a single place and its lead's first two sentences, its infobox type or speciality, or a psychiatric hospital category plus its text call it an asylum, psychiatric or mental hospital, or institution for people with learning disabilities. People, NHS trusts, tribunals, units within another hospital, the Epsom Cluster overview and one general hospital (checked by hand) are dropped; one duplicate site is merged.
- Fields: coordinates from the coord template (or the API); years from the infobox, then the lead, then the text ("the hospital closed in"), then establishment categories; a present-tense lead with no closing year means still open. Size: infobox beds or the largest capacity the text states.
- Fate: keyword rules on the lead, then on the rest of the opening text, in the order still a hospital, homes, other use, derelict, demolished; the triggering phrase is kept in the data.
- Wikidata: the extract supplied was built on Q1774898, the class for clinics; none of its {s['wd_items']} items matched an article here, so it is not used.

## Caveats

- Not every asylum has a Wikipedia article in these categories; Wales and Northern Ireland are thin.
- Only the first 6,000 characters of each article were available, so later history, including fate, is often missing ({fc['unknown']} closed sites have none).
- Years, sizes and fates are what the articles say, read by rules; sizes are capacities at different dates.
- Distances use present-day town populations (Natural Earth).

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read from `raw/` and `/home/claude/newdata/raw/geo/` (paths in `code/common.py`). Intermediate files go to `/dev/shm/asylums/work` (set `ASTMP` to change).

```
python3 code/01_clean.py        # select articles, read years, beds, names, fates, listed status
python3 code/02_geo.py          # coastline, counties and towns
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html (checks facts stated in words)
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- English Wikipedia contributors: articles in the categories walked and the context articles (County Asylums Act 1808, Lunacy Act 1845, Lunatic asylum, Madhouses Act 1774, Mental Treatment Act 1930, Mental Health Act 1959, Care in the Community, Enoch Powell, Epsom Cluster, Colney Hatch Lunatic Asylum, Whittingham Hospital, Bethlem Royal Hospital), revisions of 2026 (ids in `data/results.json` and `data/asylums.csv`). CC BY-SA 4.0.
- Wikidata (CC0): supplied but not used.
- Natural Earth coastline and populated places (public domain). ONS and OSNI county outlines (Open Government Licence).
- Optional base map tiles on the page: Esri.

## Licence

Code: MIT. Text, figures and derived summary data (results.json, by_decade.csv, open_by_year.csv): CC BY 4.0. The table derived from Wikipedia (`data/asylums.csv`, `data/excluded.csv`, `data/site.json`) and the raw Wikipedia files: CC BY-SA 4.0. Wikidata: CC0. See `LICENSE`.

## Citation

Hotham, T. (2026) Where the asylums were: Britain's county asylums and psychiatric hospitals, from the 1808 Act to Care in the Community. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.

The text of the page, paper and blog post, the figures, and the derived summary
data (data/results.json, data/by_decade.csv, data/open_by_year.csv) are released
under CC BY 4.0.

The place table and the other files derived from English Wikipedia
(data/asylums.csv, data/excluded.csv, data/site.json) and the raw Wikipedia
files in raw/ are released under CC BY-SA 4.0, as Wikipedia's licence requires.
Credit: English Wikipedia contributors.

The Wikidata extract in raw/ is CC0. Natural Earth is public domain. County
outlines: ONS and OSNI, Open Government Licence v3.0.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Where Britain's asylums were: {s['located']} asylums and psychiatric hospitals mapped. Most were built between 1845 and 1914, almost none closed until the 1980s, and two in three closed sites with a stated fate are now homes

## Body

I mapped the asylums and psychiatric hospitals that have an English Wikipedia article, {N(s['kept'])} places ({N(s['located'])} with coordinates), and read their opening and closing years, stated size and present use from the articles with simple published rules. Building came in two waves, peaking in the {o['peak_dec']}s ({o['peak_n']} opened) and the 1900s ({o['dec1900s']}). The number open reached {cv['peak_n']} and barely moved for decades: Enoch Powell's 1961 "Water Tower" speech called for them to go, but only {c['y1961_1979']} closed in the next twenty years. Then {c['dec1980s']} closed in the 1980s and {c['dec1990s']} in the 1990s. London ringed itself with them: {lo['ring_vic']} sit 10 to 40 km out, {lo['inner_vic']} inside 10 km. The biggest stated was Whittingham near Preston, {N(B['top'][0]['beds'])} patients in 1939. Of closed sites whose fate the article states, {P(fc['homes_of_known_pct'])} are now homes. Caveats: not every asylum has an article, only the opening text of each article was read, and {fc['unknown']} closed sites have no stated fate. Interactive map with a time slider: {PAGE}

## Source comment

Source: English Wikipedia articles in the categories Psychiatric hospitals in the UK, Former psychiatric hospitals in the UK and Defunct hospitals in England, Scotland and Wales (CC BY-SA 4.0, revisions of 2026), plus the articles on the 1808 and 1845 Acts, the Mental Treatment Act 1930, Care in the Community and Enoch Powell. Coastline and towns: Natural Earth; counties: ONS and OSNI.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "haunted"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
