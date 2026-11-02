"""Shared paths, groupings and helpers for the asylums project ("Where the asylums were").

Raw inputs (read in place from raw/, never modified; nothing is fetched by these scripts):
  raw/wp_pages.json      English Wikipedia, 659 articles found by walking the categories Psychiatric hospitals in the
                         United Kingdom, Former psychiatric hospitals in the United Kingdom and Defunct hospitals in
                         England, Scotland and Wales, three levels deep. For each: revision id, page categories, the
                         category it was found in ('incats'), Wikidata id, API coordinates (often missing) and 'head',
                         the first 6,000 characters of its wikitext (infobox and lead). Retrieved 2026. CC BY-SA 4.0.
  raw/wp_articles.json   English Wikipedia, parsed HTML and revision ids of context articles (Lunacy Act 1845, County
                         Asylums Act 1808, Lunatic asylum, Bethlem Royal Hospital, Psychiatric hospital, Care in the
                         Community, Water tower, Colney Hatch, Epsom Cluster, Severalls, Whittingham, Lancaster Moor,
                         List of hospitals in England, Mental Health Act 1959, Mental Treatment Act 1930, Madhouses Act
                         1774, Enoch Powell) and some category member lists. CC BY-SA 4.0. Used for facts quoted in the
                         text, credited.
  raw/wd_*.tsv           Wikidata (QLever TSV), UK items that are instances of a subclass of psychiatric hospital
                         (Q1774898): main (label, coordinates, inception, dissolved, enwiki), type, her (heritage
                         designation), arch (architect), adm (located in), nhle (Historic England list entry), alias,
                         status, beds. CC0.
  /home/claude/newdata/raw/geo/counties_uk.geojson   England ceremonial counties, Welsh preserved counties, Scottish
                         council areas, Northern Ireland (ONS / OSNI, Open Government Licence).
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_10m_populated_places_simple.geojson
                         Natural Earth (public domain): coastline of Britain, Ireland and France; towns.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("AS_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("AS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("AS_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("ASTMP", "/dev/shm/asylums"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "asylums"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23873001"                # filled in by the publisher
DOI_URL = "https://doi.org/10.5281/zenodo.23873001"        # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/asylums/"          # filled in by the publisher
RETRIEVED = "2026"
TITLE = "Where the asylums were"
PAPER_TITLE = "Where the Asylums Were: Britain's County Asylums and Psychiatric Hospitals, from the 1808 Act to Care in the Community"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
LAST_YEAR = 2026

# What happened to each place, read from the article (see 01_clean.py for the keyword rules). Order = legend order.
FATES = [("health", "Still a hospital or health site", "#2F6F8F"),
         ("homes", "Converted to homes", "#C0603A"),
         ("other", "Other new use", "#7C8A3A"),
         ("demolished", "Demolished", "#5E5A55"),
         ("derelict", "Derelict or empty", "#9A4E8C"),
         ("unknown", "Not stated", "#B7AFA3")]
FATE_LABEL = {k: l for k, l, _ in FATES}
FATE_COL = {k: c for k, _, c in FATES}
NATIONS = ["England", "Wales", "Scotland", "Northern Ireland", "Isle of Man", "Channel Islands"]

# The Epsom cluster (Wikipedia, "Epsom Cluster"): five London County Council asylums on the Horton estate.
EPSOM = ["Manor Hospital, Epsom", "Horton Hospital", "Long Grove Hospital", "St Ebba's Hospital", "West Park Hospital, Epsom"]
LONDON = (51.5074, -0.1278)    # Charing Cross, for the London ring


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    if f == "word": return NUMW.get(int(v), f"{int(v):,}")
    if f == "Word": w = NUMW.get(int(v), f"{int(v):,}"); return w[0].upper() + w[1:]
    raise ValueError(f)


NUMW = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "eleven", 12: "twelve"}


def fill(text, R, keep=("IMG", "DOI", "DOI_URL", "BLOG_URL", "TABLE_"), f=fmt):
    """Replace {{path|format}} tokens with values from results.json, leaving the publisher's placeholders."""
    neg = "|".join(re.escape(k) + (r"\}\}" if not k.endswith("_") and k != "IMG" else "") for k in keep)
    return re.sub(r"\{\{(?!" + neg + r")([^}|]+)(\|(\w+))?\}\}", lambda m: f(get(R, m.group(1)), m.group(3)), text)


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))
