# Where the asylums were

A map and analysis of Britain's county lunatic asylums and later psychiatric hospitals, built from English Wikipedia: where they were, when they opened after the County Asylums Act 1808 and the Lunacy Act 1845, how big they grew, when they closed after Enoch Powell's 1961 Water Tower speech and Care in the Community, and what the sites are now. 244 places, 233 located. A companion to "What's left of the workhouse?".

**This is not a complete list of Britain's asylums.** It covers places that have an English Wikipedia article in the categories walked, read by simple published rules.

Interactive page: https://maps.tristanhotham.com/asylums/
Paper: https://doi.org/10.5281/zenodo.23873001
Blog post: https://blog.tristanhotham.com/2026/10/31/asylums/

## Headline results

- Coverage: 659 Wikipedia articles found; 244 kept as asylums, psychiatric hospitals or institutions for people with learning disabilities (355 general hospitals and 45 non-hospital articles dropped); 233 located: 171 in England, 42 in Scotland, 14 in Wales, 5 in Northern Ireland, 1 on the Isle of Man.
- Openings: two waves, peaking in the 1860s (30) and the 1900s (26), with a lull in the 1880s (10). 62% of places with an opening year opened between 1845 and 1914.
- Closures: 5 of 155 dated closures came before 1961 and 2 between 1961 and 1979; 17 in the 1980s, 83 in the 1990s, 31 in the 2000s. 64% closed between 1980 and 1999. The number open peaked at 199 (1972 to 1983) and is 69 today. Median life of a Victorian asylum: 126 years.
- Size: the largest stated is Whittingham, Lancashire, 3,533 patients in 1939; 30 places state 1,000 or more.
- Clusters: 28 asylums opened 1830 to 1939 lie 10 to 40 km from Charing Cross, 7 within 10 km; the five Epsom hospitals opened 1899 to 1921 within 2.1 km of each other.
- Now: of 173 places no longer open, 81 (47%) are homes, 17 another use, 22 demolished, 2 derelict, 51 not stated. Of those with a stated fate, 66% are homes. 83 articles (34%) report a listed building.
- Names: 141 articles record an "asylum" name, 82 a "mental hospital" name; where a single year is given for the "mental hospital" name, 21 of 33 fall in 1920 to 1939.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/counties.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/asylums.csv` | All 244 places: Wikipedia title and revision, other names, nation, county, coordinates, opened and closed years with their source, status, stated beds with the phrase, fate with the phrase that set it, listed status, learning disability flag, distance to the nearest big town and to Charing Cross, selection rule. **CC BY-SA 4.0** (derived from Wikipedia). |
| `data/excluded.csv` | The 415 articles dropped, with the reason. CC BY-SA 4.0. |
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
- Wikidata: the extract supplied was built on Q1774898, the class for clinics; none of its 213 items matched an article here, so it is not used.

## Caveats

- Not every asylum has a Wikipedia article in these categories; Wales and Northern Ireland are thin.
- Only the first 6,000 characters of each article were available, so later history, including fate, is often missing (51 closed sites have none).
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

Hotham, T. (2026) Where the asylums were: Britain's county asylums and psychiatric hospitals, from the 1808 Act to Care in the Community. Zenodo. https://doi.org/10.5281/zenodo.23873001

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
