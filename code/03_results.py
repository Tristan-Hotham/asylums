"""Every number used anywhere (data/results.json), the reusable tables (data/asylums.csv, data/by_decade.csv,
data/open_by_year.csv) and the page data (data/site.json).

Definitions (see 01_clean.py for how each field is read from the articles):
  * place: an article kept by the rules in 01_clean.py (an asylum, psychiatric hospital or hospital for people with
    learning disabilities, or a later mental health unit), one row per site;
  * located: coordinates from {{coord}} in the wikitext or, failing that, the Wikipedia API;
  * opened, closed: years as the article states them; a decade is 1840 to 1849 and so on;
  * open in a year: opened in or before it and not yet closed (closed after it, or still open). Places whose article
    says they closed but gives no year are left out of the yearly count;
  * big town: a Natural Earth populated place in the UK, Ireland or the Isle of Man with a population (present day,
    pop_max) of at least 100,000; distance is great circle distance to the nearest one;
  * the London ring: places 10 to 40 km from Charing Cross; the Epsom cluster: the five hospitals Wikipedia's
    "Epsom Cluster" article names."""
import csv, collections, html as _html
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.prepared import prep
from common import *

D = pd.read_pickle(f"{WORK}/places.pkl").reset_index(drop=True)
CHK = jload(f"{WORK}/checks.json")
PG = jload(f"{RAW}/wp_pages.json")["pages"]
ART = jload(f"{RAW}/wp_articles.json")
R = {}
pc = lambda a, b: round(100 * a / b, 1) if b else None
N = len(D)

# ---------- where: nation and county ----------
CT = jload(f"{DATA}/counties.json")
CP = [(f["properties"]["county"], f["properties"]["nation"], prep(shape(f["geometry"])), shape(f["geometry"])) for f in CT["features"]]


def where(lat, lon):
    if lat is None or np.isnan(lat): return None, None
    p = Point(lon, lat)
    for c, n, pg, _ in CP:
        if pg.contains(p): return c, n
    if 54.0 < lat < 54.45 and -4.85 < lon < -4.3: return "Isle of Man", "Isle of Man"
    if 49.1 < lat < 49.8 and -2.8 < lon < -2.0: return "Jersey" if lat < 49.3 else "Guernsey", "Channel Islands"
    best = min(CP, key=lambda q: q[3].distance(p))                # on the coast, just outside a simplified outline
    return (best[0], best[1]) if best[3].distance(p) < 0.08 else (None, None)


W = [where(a, b) for a, b in zip(D.lat, D.lon)]
D["county"] = [w[0] for w in W]; D["nation"] = [w[1] for w in W]
L = D[D.lat.notna()]
assert L.nation.notna().all(), L[L.nation.isna()].title.tolist()
assert all(49 < a < 61 and -9 < b < 2.5 for a, b in zip(L.lat, L.lon))

# ---------- source and selection ----------
wd = list(csv.reader(open(f"{RAW}/wd_main.tsv", encoding="utf-8"), delimiter="\t"))[1:]
wdt = list(csv.reader(open(f"{RAW}/wd_type.tsv", encoding="utf-8"), delimiter="\t"))[1:]
qid = lambda s: re.sub(r".*/(Q\d+)>.*", r"\1", s)
wd_ids = {qid(r[0]) for r in wd}
wp_ids = {p["wikidata"] for p in PG.values()}
tc = collections.Counter(re.sub(r'^"?(.*?)"?@en$', r"\1", r[2]) for r in wdt)
R["source"] = {"pages": CHK["pages"], "n_cats": len(CHK["cats_walked"]), "kept": N, "dropped": CHK["pages"] - N,
               "drop_reasons": CHK["dropped"], "located": int(D.lat.notna().sum()), "located_pct": pc(D.lat.notna().sum(), N),
               "coord_wikitext": int((D.coord_src == "wikitext").sum()), "coord_api": int((D.coord_src == "api").sum()),
               "not_located": int(D.lat.isna().sum()), "api_coords_pages": sum(1 for p in PG.values() if p.get("coords")),
               "rule_A": int(D.rule.str.contains("A").sum()), "rule_only_B": int((D.rule == "B").sum()), "rule_only_C": int((D.rule == "C").sum()),
               "rule_all": int((D.rule == "ABC").sum()), "retrieved": RETRIEVED,
               "wd_items": len(wd_ids), "wd_matched": len(wd_ids & wp_ids), "wd_enwiki": sum(1 for r in wd if r[5]),
               "wd_types_top": tc.most_common(4), "wd_health_centres": tc.get("community health center", 0), "wd_clinic_like": sum(v for k, v in tc.items() if "clinic" in k)}
dr = R["source"]["drop_reasons"]
R["source"]["drop_general"] = dr.get("a general or other hospital (no psychiatric signal in category, infobox or lead)", 0) + dr.get("a general hospital whose site once had a lunatic ward (checked by hand)", 0)
R["source"]["drop_nothospital"] = dr.get("not a hospital article", 0)
R["source"]["drop_org"] = dr.get("an organisation, unit or group article, not a single place", 0) + dr.get("a person or other non-place article", 0)
R["source"]["drop_merged"] = sum(v for k, v in dr.items() if k.startswith("same site"))
assert R["source"]["drop_general"] + R["source"]["drop_nothospital"] + R["source"]["drop_org"] + R["source"]["drop_merged"] == R["source"]["dropped"]
assert R["source"]["wd_matched"] == 0
nat = L.nation.value_counts()
R["nations"] = {k: int(v) for k, v in nat.items()}
cty = L.county.value_counts()
R["counties_top"] = [[k, int(v)] for k, v in cty.head(12).items()]
R["n_counties"] = int(L.county.nunique())

# ---------- kinds ----------
R["kinds"] = {"ld": int(D.ld.sum()), "secure": int(D.secure.sum()), "private": int(D.private.sum()), "open_now": int(D.open_now.sum()),
              "closed": int((D.status == "closed").sum()), "status_unknown": int((D.status == "unknown").sum()),
              "closed_with_year": int(D.closed.notna().sum()), "closed_no_year": int(((D.status == "closed") & D.closed.isna()).sum())}

# ---------- openings and closures ----------
op = D[D.opened.notna()].copy(); op["opened"] = op.opened.astype(int)
cl = D[D.closed.notna()].copy(); cl["closed"] = cl.closed.astype(int)
DEC = list(range(1800, 2030, 10))
dec = []
for d in DEC:
    dec.append({"dec": d, "opened": int(((op.opened >= d) & (op.opened < d + 10)).sum()), "closed": int(((cl.closed >= d) & (cl.closed < d + 10)).sum())})
pre = int((op.opened < 1800).sum())
R["decades"] = dec
DD = pd.DataFrame(dec).set_index("dec")
o19 = DD.loc[1800:1990]
R["open"] = {"n": len(op), "pct": pc(len(op), N), "before1800": pre, "first_year": int(op.opened.min()), "first_title": op.sort_values("opened").title.iloc[0],
             "peak_dec": int(DD.opened.idxmax()), "peak_n": int(DD.opened.max()),
             "y1808_1844": int(((op.opened >= 1808) & (op.opened <= 1844)).sum()), "y1845_1889": int(((op.opened >= 1845) & (op.opened <= 1889)).sum()),
             "y1890_1914": int(((op.opened >= 1890) & (op.opened <= 1914)).sum()), "y1915_1947": int(((op.opened >= 1915) & (op.opened <= 1947)).sum()),
             "y1948_1989": int(((op.opened >= 1948) & (op.opened <= 1989)).sum()), "y1990_": int((op.opened >= 1990).sum()),
             "y1845_1914": int(((op.opened >= 1845) & (op.opened <= 1914)).sum()), "y1800_1844": int(((op.opened >= 1800) & (op.opened <= 1844)).sum()),
             "dec1840s": int(DD.loc[1840, "opened"]), "dec1850s": int(DD.loc[1850, "opened"]), "dec1860s": int(DD.loc[1860, "opened"]),
             "dec1890s": int(DD.loc[1890, "opened"]), "dec1900s": int(DD.loc[1900, "opened"]), "dec1830s": int(DD.loc[1830, "opened"]),
             "dec1810s": int(DD.loc[1810, "opened"]), "dec1820s": int(DD.loc[1820, "opened"]), "dec1870s": int(DD.loc[1870, "opened"]), "dec1880s": int(DD.loc[1880, "opened"]),
             "dec1910s": int(DD.loc[1910, "opened"]), "dec1920s": int(DD.loc[1920, "opened"]), "dec1930s": int(DD.loc[1930, "opened"]),
             "median": int(op.opened.median())}
o = R["open"]
o["y1845_1914_pct"] = pc(o["y1845_1914"], o["n"])
o["post1845_peak_dec"] = int(DD.loc[1840:1880].opened.idxmax())
o["c1900_peak_dec"] = int(DD.loc[1890:1910].opened.idxmax())
o["trough_dec"] = int(DD.loc[1870:1890].opened.idxmin())
R["close"] = {"n": len(cl), "pct_of_closed": pc(len(cl), R["kinds"]["closed"]), "peak_dec": int(DD.closed.idxmax()), "peak_n": int(DD.closed.max()),
              "dec1960s": int(DD.loc[1960, "closed"]), "dec1970s": int(DD.loc[1970, "closed"]), "dec1980s": int(DD.loc[1980, "closed"]), "dec1990s": int(DD.loc[1990, "closed"]),
              "dec2000s": int(DD.loc[2000, "closed"]), "dec2010s": int(DD.loc[2010, "closed"]), "dec2020s": int(DD.loc[2020, "closed"]),
              "y1980_1999": int(((cl.closed >= 1980) & (cl.closed <= 1999)).sum()), "before1961": int((cl.closed < 1961).sum()),
              "y1961_1979": int(((cl.closed >= 1961) & (cl.closed <= 1979)).sum()), "since2000": int((cl.closed >= 2000).sum()),
              "median": int(cl.closed.median()), "first": int(cl.closed.min()), "last": int(cl.closed.max())}
c = R["close"]
c["y1980_1999_pct"] = pc(c["y1980_1999"], c["n"]); c["since1961"] = c["n"] - c["before1961"]; c["since1961_pct"] = pc(c["since1961"], c["n"])
c["y1990s_pct"] = pc(c["dec1990s"], c["n"])
both = D[D.opened.notna() & D.closed.notna()].copy()
life = (both.closed - both.opened).astype(int)
vic = both[(both.opened >= 1808) & (both.opened <= 1914)]
vlife = (vic.closed - vic.opened).astype(int)
R["gap"] = {"n": len(both), "median_life": int(life.median()), "vic_n": len(vic), "vic_median_life": int(vlife.median()),
            "vic_over100": int((vlife >= 100).sum()), "vic_over100_pct": pc((vlife >= 100).sum(), len(vic)),
            "peak_to_peak": c["peak_dec"] - o["c1900_peak_dec"], "median_open_closed": int(both.opened.median()), "median_close_closed": int(both.closed.median()),
            "longest": [[r.title, int(r.opened), int(r.closed), int(r.closed - r.opened)] for r in both.assign(l=life).sort_values("l", ascending=False).head(5).itertuples()]}
assert o["peak_n"] == max(d["opened"] for d in dec)

# open by year: the rise and fall
YRS = list(range(1800, LAST_YEAR + 1))
ok_curve = D[D.opened.notna() & ~((D.status == "closed") & D.closed.isna())]
oy = []
for y in YRS:
    n = int(((ok_curve.opened <= y) & (ok_curve.closed.isna() | (ok_curve.closed > y))).sum())
    oy.append({"y": y, "open": n, "opened": int((op.opened == y).sum()), "closed": int((cl.closed == y).sum())})
R["open_by_year"] = oy
OY = pd.DataFrame(oy).set_index("y")
R["curve"] = {"n": len(ok_curve), "left_out": int(len(op) - len(ok_curve)), "peak_n": int(OY.open.max()), "peak_first": int(OY.open.idxmax()),
              "peak_last": int(OY.index[OY.open == OY.open.max()].max()),
              "y1845": int(OY.loc[1845, "open"]), "y1900": int(OY.loc[1900, "open"]), "y1914": int(OY.loc[1914, "open"]), "y1961": int(OY.loc[1961, "open"]),
              "y1980": int(OY.loc[1980, "open"]), "y2000": int(OY.loc[2000, "open"]), "y2026": int(OY.loc[LAST_YEAR, "open"]), "y1850": int(OY.loc[1850, "open"])}
cv = R["curve"]
cv["fall_1961_2000_pct"] = round(100 * (1 - cv["y2000"] / cv["y1961"]), 1)
# of the places open in 1961, how many have closed since, and when
o61 = ok_curve[(ok_curve.opened <= 1961) & (ok_curve.closed.isna() | (ok_curve.closed > 1961))]
R["since1961"] = {"open_1961": len(o61), "closed_since": int(o61.closed.notna().sum()), "closed_since_pct": pc(o61.closed.notna().sum(), len(o61)),
                  "still_open": int(o61.closed.isna().sum()), "median_close": int(o61.closed.dropna().median()),
                  "closed_1980_1999": int(((o61.closed >= 1980) & (o61.closed <= 1999)).sum())}
R["since1961"]["closed_1980_1999_pct"] = pc(R["since1961"]["closed_1980_1999"], R["since1961"]["closed_since"])
assert c["peak_dec"] in (1980, 1990)

# ---------- size ----------
B = D[D.beds.notna()].copy(); B["beds"] = B.beds.astype(int)
B = B.sort_values("beds", ascending=False)
R["beds"] = {"n": len(B), "pct": pc(len(B), N), "infobox": int((B.beds_src == "infobox").sum()), "text": int((B.beds_src == "text").sum()),
             "over1000": int((B.beds >= 1000).sum()), "over2000": int((B.beds >= 2000).sum()), "median": int(B.beds.median()),
             "top": [{"title": r.title, "beds": int(r.beds), "src": r.beds_src, "phrase": r.beds_text, "opened": None if pd.isna(r.opened) else int(r.opened),
                      "closed": None if pd.isna(r.closed) else int(r.closed), "county": r.county} for r in B.head(15).itertuples()]}
bt = R["beds"]["top"]
assert bt[0]["title"] == "Whittingham Hospital" and bt[0]["beds"] == 3533
vb = B[(B.opened >= 1808) & (B.opened <= 1914)]; mb = B[B.opened >= 1990]
R["beds"]["vic_n"] = len(vb); R["beds"]["vic_median"] = int(vb.beds.median()); R["beds"]["modern_n"] = len(mb); R["beds"]["modern_median"] = int(mb.beds.median()) if len(mb) else None

# ---------- clusters: Epsom and the London ring ----------
E = D[D.title.isin(EPSOM)]
assert len(E) == 5 and E.lat.notna().all(), E.title.tolist()
pairs = [gc_km(a.lat, a.lon, b.lat, b.lon) for i, a in E.iterrows() for j, b in E.iterrows() if i < j]
cen = (E.lat.mean(), E.lon.mean())
R["epsom"] = {"n": len(E), "opened_min": int(E.opened.min()), "opened_max": int(E.opened.max()), "closed_min": int(E.closed.min()) if E.closed.notna().any() else None,
              "closed_max": int(E.closed.max()) if E.closed.notna().any() else None, "max_km": round(max(pairs), 1), "beds_sum": int(E.beds.fillna(0).sum()),
              "beds_n": int(E.beds.notna().sum()), "km_london": round(float(gc_km(cen[0], cen[1], *LONDON)), 1), "lat": round(cen[0], 4), "lon": round(cen[1], 4),
              "rows": [[r.title, None if pd.isna(r.opened) else int(r.opened), None if pd.isna(r.closed) else int(r.closed), None if pd.isna(r.beds) else int(r.beds), r.fate] for r in E.sort_values("opened").itertuples()],
              "still_open": int(E.open_now.sum())}
ep = R["epsom"]
EA = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>|<sup.*?</sup>", "", ART["Epsom_Cluster"]["html"], flags=re.S)))).replace("\xa0", " ")
for s in ("five large psychiatric hospitals", "London County Council", "Horton Estate", "12,000 patients", "only five were built"):
    assert s in EA, s
D["km_london"] = [float(gc_km(a, b, *LONDON)) if not pd.isna(a) else np.nan for a, b in zip(D.lat, D.lon)]
LR = D[(D.km_london >= 10) & (D.km_london <= 40)]
LRv = LR[(LR.opened >= 1830) & (LR.opened <= 1939)]
inner = D[D.km_london < 10]
R["london"] = {"ring_n": len(LR), "ring_vic": len(LRv), "inner_n": len(inner), "inner_vic": int(((inner.opened >= 1830) & (inner.opened <= 1939)).sum()),
               "ring_beds_sum": int(LRv.beds.fillna(0).sum()), "ring_beds_n": int(LRv.beds.notna().sum()),
               "ring_counties": [[k, int(v)] for k, v in LRv.county.value_counts().items()],
               "ring_closed": int(LRv.closed.notna().sum()), "ring_homes": int((LRv.fate == "homes").sum()), "ring_median_km": round(float(LRv.km_london.median()), 1),
               "ring_closed_1980_1999": int(((LRv.closed >= 1980) & (LRv.closed <= 1999)).sum())}
lo = R["london"]
lo["ring_homes_pct"] = pc(lo["ring_homes"], lo["ring_vic"])
lo["ring_closed_pct"] = pc(lo["ring_closed"], lo["ring_vic"])
lo["ring_outside_gl"] = int(sum(v for k, v in lo["ring_counties"] if k != "Greater London"))

# ---------- fates ----------
fc = D.fate.value_counts()
R["fates"] = {k: int(fc.get(k, 0)) for k, _, _ in FATES}
R["fates_pct"] = {k: pc(fc.get(k, 0), N) for k, _, _ in FATES}
cd = D[D.status != "open"]
cfc = cd.fate.value_counts()
R["fates_closed"] = {"n": len(cd), **{k: int(cfc.get(k, 0)) for k, _, _ in FATES}}
R["fates_closed_pct"] = {k: pc(cfc.get(k, 0), len(cd)) for k, _, _ in FATES}
known = len(cd) - int(cfc.get("unknown", 0)) - int(cfc.get("health", 0))
R["fates_closed"]["known"] = known
R["fates_closed"]["homes_of_known_pct"] = pc(cfc.get("homes", 0), known)
hm = D[D.fate == "homes"]
R["fates_detail"] = {"src_lead": int((D.fate_src == "lead").sum()), "src_text": int((D.fate_src == "text").sum()),
                     "homes_with_demolition": int(hm.fate_flags.map(lambda f: "demolished" in f).sum()),
                     "homes_converted": int(hm.fate_text.str.contains(r"convert", case=False).sum()),
                     "plans_only": int(D.plans.sum()), "any_demolition": int(D.fate_flags.map(lambda f: "demolished" in f).sum())}
vicp = D[(D.opened >= 1808) & (D.opened <= 1914)]
vfc = vicp.fate.value_counts()
R["fates_vic"] = {"n": len(vicp), **{k: int(vfc.get(k, 0)) for k, _, _ in FATES}}
R["fates_vic_pct"] = {k: pc(vfc.get(k, 0), len(vicp)) for k, _, _ in FATES}

# ---------- listed ----------
ls = D[D.listed.notna()]
R["listed"] = {"n": len(ls), "pct": pc(len(ls), N), "grades": {k: int(v) for k, v in ls.listed.value_counts().items()},
               "src_text": int((ls.listed_src == "text").sum()), "src_cat": int((ls.listed_src == "category").sum()),
               "vic_n": int(vicp.listed.notna().sum()), "vic_pct": pc(vicp.listed.notna().sum(), len(vicp)),
               "modern_n": int(D[D.opened >= 1948].listed.notna().sum()), "modern_of": int((D.opened >= 1948).sum()),
               "homes_listed": int(hm.listed.notna().sum()), "homes_listed_pct": pc(hm.listed.notna().sum(), len(hm)),
               "grade1": [r.title for r in ls[ls.listed == "Grade I"].itertuples()], "catA": int((ls.listed == "Category A").sum()),
               "star": int((ls.listed == "Grade II*").sum()), "g2": int((ls.listed == "Grade II").sum())}

# ---------- distance from the nearest big town ----------
CITIES = jload(f"{DATA}/cities.json")
BIG = [c for c in CITIES if c["pop"] >= 100000 and c["country"] in ("United Kingdom", "Ireland", "Isle of Man")]
BG = np.array([[c["lat"], c["lon"]] for c in BIG])


def nearest(lat, lon):
    d = gc_km(lat, lon, BG[:, 0], BG[:, 1]); i = int(np.argmin(d)); return float(d[i]), BIG[i]["name"]


nt = [nearest(a, b) if not pd.isna(a) else (np.nan, None) for a, b in zip(D.lat, D.lon)]
D["km_town"] = [x[0] for x in nt]; D["town"] = [x[1] for x in nt]
DL = D[D.km_town.notna()]
era = {"pre1845": DL[DL.opened < 1845], "y1845_1914": DL[(DL.opened >= 1845) & (DL.opened <= 1914)], "y1915_1947": DL[(DL.opened >= 1915) & (DL.opened <= 1947)],
       "y1948_": DL[DL.opened >= 1948]}
R["town"] = {"n_big": len(BIG), "median": round(float(DL.km_town.median()), 1), "n": len(DL)}
for k, v in era.items():
    R["town"][k] = {"n": len(v), "median": round(float(v.km_town.median()), 1), "over5": int((v.km_town > 5).sum()), "over5_pct": pc((v.km_town > 5).sum(), len(v)),
                    "over15": int((v.km_town > 15).sum()), "over15_pct": pc((v.km_town > 15).sum(), len(v))}
R["town"]["vic_over5_vs_modern"] = [R["town"]["y1845_1914"]["over5_pct"], R["town"]["y1948_"]["over5_pct"]]
far = DL.sort_values("km_town", ascending=False)
R["town"]["farthest"] = [[r.title, round(r.km_town, 1), r.town] for r in far.head(5).itertuples()]

# ---------- names ----------
TERMN = ["lunatic asylum", "asylum", "institution or colony", "mental hospital", "psychiatric hospital", "mental health unit or centre", "hospital"]
anyterm = lambda t: D.terms.map(lambda x: t in x)
asy = D.terms.map(lambda x: "lunatic asylum" in x or "asylum" in x)
R["names"] = {"n_with_old": int(D.names.map(len).gt(1).sum()), "lunatic_asylum": int(anyterm("lunatic asylum").sum()), "asylum_any": int(asy.sum()),
              "mental_hospital": int(anyterm("mental hospital").sum()), "psychiatric_hospital": int(anyterm("psychiatric hospital").sum()),
              "institution": int(anyterm("institution or colony").sum()), "saint_titles": int(D.saint.sum()),
              "asylum_then_mh": int((asy & anyterm("mental hospital")).sum()), "now_hospital_title": int(D.title.str.contains(r"\bHospital\b").sum()),
              "title_asylum": int(D.title.str.contains(r"Asylum").sum())}
nm = R["names"]
nm["asylum_any_pct"] = pc(nm["asylum_any"], N); nm["mental_hospital_pct"] = pc(nm["mental_hospital"], N); nm["saint_pct"] = pc(nm["saint_titles"], N)
# years in which places took a 'Mental Hospital' name, and a saint's name, from rename sentences
mh_years = [y for rr in D.renames for a, t, y in rr if t == "mental hospital" and y]
saint_years = [y for rr in D.renames for a, t, y in rr if re.match(r"(St\.?|Saint)\s", a) and y and y >= 1900]
nm["mh_years_n"] = len(mh_years); nm["mh_years_1920_1939"] = sum(1920 <= y <= 1939 for y in mh_years)
nm["mh_years_pct"] = pc(nm["mh_years_1920_1939"], len(mh_years)); nm["mh_years_median"] = int(np.median(mh_years)) if mh_years else None
nm["mh_years_1930_1934"] = sum(1930 <= y <= 1934 for y in mh_years)
nm["saint_years_n"] = len(saint_years); nm["saint_years_1948_1965"] = sum(1948 <= y <= 1965 for y in saint_years)
nm["mh_hist"] = collections.Counter((y // 10) * 10 for y in mh_years)
nm["mh_hist"] = {str(k): int(v) for k, v in sorted(nm["mh_hist"].items())}
EX = {"Exminster Hospital": None, "Lancaster Moor Hospital": None, "Whittingham Hospital": None, "Severalls Hospital": None}
nm["examples"] = [[r.title, r.names[:4]] for r in D[D.title.isin(["Exminster Hospital", "Ballamona Hospital", "Digby Hospital", "Stone House Hospital", "Rubery Hill Hospital"])].itertuples()]

# ---------- Wikipedia context facts (quoted, CC BY-SA) ----------
def wtext(k):
    h = ART[k]["html"]; h = re.sub(r"<style.*?</style>|<sup.*?</sup>", "", h, flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h)).replace("\xa0", " "))


T = {k: wtext(k) for k, v in ART.items() if isinstance(v, dict) and "html" in v}
FACTS = {"County_Asylums_Act_1808": ["permitted, but did not compel, justices of the peace to provide establishments for the care of pauper lunatics", "Wynn's Act"],
         "Lunacy_Act_1845": ["change in the status of mentally ill people to patients", "By 1827 however only nine county asylums had opened", "County Asylums Act 1845", "Lunacy Commission"],
         "Lunatic_asylum": ["Nine counties first applied", "asylum numbers continued to increase up to the 1950s"],
         "Mental_Treatment_Act_1930": ['replaced the term "asylum" with "mental hospital"', "voluntary admission"],
         "Mental_Health_Act_1959": ["away from institutional care to that in the community", "0.4% of the population of England were housed in asylums"],
         "Enoch_Powell#Water_Tower_speech": ["There they stand, isolated, majestic, imperious, brooded over by the gigantic water-tower and chimney combined, rising unmistakable and daunting out of the countryside", "Minister of Health from 1960 to 1963"],
         "Care_in_the_Community": ["National Health Service and Community Care Act 1990", "came into effect in April 1993", "Making a Reality of Community Care", "1961 Water Tower speech"],
         "Madhouses_Act_1774": ["legal framework for regulating \"madhouses\""],
         "Whittingham_Hospital": ["largest mental hospital in Great Britain", "3533"],
         "Colney_Hatch_Lunatic_Asylum": ["longest corridor in Britain", "home to 2,500 mental patients"],
         "Bethlem_Royal_Hospital": ["Founded in 1247", "Monks Orchard in 1930", "bedlam"]}
for k, ss in FACTS.items():
    for s in ss:
        assert s in T[k], (k, s)
R["wiki"] = {"revids": {k: ART[k]["revid"] for k in T}, "powell_quote": FACTS["Enoch_Powell#Water_Tower_speech"][0] + ", the asylums which our forefathers built with such immense solidity to express the notions of their day",
             "missing": [k for k, v in ART.items() if isinstance(v, dict) and "err" in v]}
assert "the asylums which our forefathers built with such immense solidity" in T["Enoch_Powell#Water_Tower_speech"]
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG}

# ---------- clean data out ----------
FI = {k: i for i, (k, _, _) in enumerate(FATES)}
out = D.copy()
out["wikipedia_url"] = "https://en.wikipedia.org/wiki/" + out.title.str.replace(" ", "_")
out["other_names"] = out.names.map(lambda n: "; ".join(n[1:]))
out["fate_label"] = out.fate.map(FATE_LABEL)
cols = ["title", "other_names", "nation", "county", "lat", "lon", "opened", "opened_src", "closed", "closed_src", "status", "beds", "beds_src", "beds_text",
        "fate", "fate_label", "fate_src", "fate_text", "kept_buildings", "listed", "listed_src", "ld", "secure", "km_town", "town", "km_london", "rule", "wikidata", "revid", "wikipedia_url"]
out[cols].rename(columns={"title": "wikipedia_title", "ld": "learning_disability", "km_town": "km_to_town_100k", "town": "nearest_town_100k", "rule": "selection_rule"}) \
    .round({"km_town": 1, "km_london": 1, "lat": 5, "lon": 5}).to_csv(f"{DATA}/asylums.csv", index=False)
pd.DataFrame(dec).rename(columns={"dec": "decade"}).to_csv(f"{DATA}/by_decade.csv", index=False)
pd.DataFrame(oy).rename(columns={"y": "year"}).to_csv(f"{DATA}/open_by_year.csv", index=False)

# ---------- page data ----------
rows = []
for r in D.itertuples():
    rows.append([r.title, r.names[1:6], None if pd.isna(r.lat) else round(r.lat, 5), None if pd.isna(r.lon) else round(r.lon, 5),
                 None if pd.isna(r.opened) else int(r.opened), None if pd.isna(r.closed) else int(r.closed), int(r.open_now), None if pd.isna(r.beds) else int(r.beds),
                 FI[r.fate], r.county or "", r.nation or "", int(r.revid), r.listed or "", int(r.ld), r.status, r.beds_src or "",
                 None if pd.isna(r.km_town) else round(r.km_town, 1), r.town or ""])
site = {"cols": ["title", "names", "lat", "lon", "opened", "closed", "open_now", "beds", "fate", "county", "nation", "revid", "listed", "ld", "status", "beds_src", "km_town", "town"],
        "rows": rows, "fates": FATES, "epsom": EPSOM, "london": list(LONDON)}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
D.to_pickle(f"{WORK}/places2.pkl")
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "results.json", "asylums.csv")})
for k in ("source", "nations", "kinds", "open", "close", "gap", "curve", "since1961", "epsom", "london", "fates", "fates_closed", "fates_closed_pct", "fates_detail", "fates_vic_pct", "listed", "names"):
    print(k, R[k])
print("town", {k: v for k, v in R["town"].items()})
print("beds", {k: v for k, v in R["beds"].items() if k != "top"}); print([(b["title"], b["beds"], b["src"]) for b in bt])
print(R["decades"])
