"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, land.json, towns) is embedded; data/counties.json is loaded by the
page. Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted
before </body>. 10.5281/zenodo.23873001 and https://blog.tristanhotham.com/2026/10/31/asylums/ stay as placeholders for the publisher."""
import json
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
D = pd.read_pickle(f"{WORK}/places2.pkl")
T = {r.title: r for r in D.itertuples()}
O, CL, CV, F, FC, L, NM, B = R["open"], R["close"], R["curve"], R["fates"], R["fates_closed"], R["listed"], R["names"], R["beds"]

# facts stated in words (page, blog, paper, collage)
assert O["peak_dec"] == 1860 and O["c1900_peak_dec"] == 1900 and O["trough_dec"] == 1880       # two waves, a lull in the 1880s
assert O["dec1890s"] > O["dec1880s"] and O["dec1900s"] > O["dec1880s"]
assert CL["peak_dec"] == 1990 and CL["y1961_1979"] <= 3 and CL["before1961"] <= 6                  # "almost nothing closed" in the twenty years after 1961
assert CV["y1980"] >= CV["y1961"] - 2                                                               # "still" as many in 1980
assert B["top"][0]["title"] == "Whittingham Hospital" and B["top"][1]["title"] == "Prestwich Hospital" and "1903" in B["top"][1]["phrase"]
assert T["Whittingham Hospital"].county == "Lancashire" and T["Prestwich Hospital"].county == "Greater Manchester"
assert R["london"]["ring_counties"][0][0] == "Surrey" and R["london"]["ring_counties"][1][0] == "Greater London" and len(R["london"]["ring_counties"]) == 5
assert R["epsom"]["n"] == 5 and R["epsom"]["still_open"] == 1 and [r for r in R["epsom"]["rows"] if r[2] is None][0][0] == "St Ebba's Hospital"
assert sorted(L["grade1"]) == ["Bootham Park Hospital", "Grove Place", "Holloway Sanatorium"] and "Hampshire" in T["Grove Place"].lead
assert T["Banstead Hospital"].fate == "other" and "Prison" in T["Banstead Hospital"].fate_text and T["Parc Hospital"].fate == "other" and "Prison" in T["Parc Hospital"].fate_text
assert "Princess Park Manor" in T["Friern Hospital"].lead and "Virginia Park" in T["Holloway Sanatorium"].lead and "Wadsley Park Village" in T["Middlewood Hospital"].lead
assert all(T[t].fate == "homes" for t in ("Friern Hospital", "Holloway Sanatorium", "Middlewood Hospital"))
assert T["Exminster Hospital"].names[1:4] == ["Devon County Lunatic Asylum", "Devon Mental Hospital", "Exe Vale Hospital"]
assert "Colney Hatch" in " ".join(T["Friern Hospital"].names) or "Colney Hatch" in T["Friern Hospital"].lead
assert R["kinds"]["ld"] >= 10 and R["nations"]["Northern Ireland"] < 10 and R["nations"]["Wales"] < 20       # "thinly covered"
assert R["town"]["y1845_1914"]["over5_pct"] > R["town"]["y1948_"]["over5_pct"]
assert R["source"]["wd_matched"] == 0 and R["source"]["wd_health_centres"] > R["source"]["wd_items"] / 2      # "most were community health centres"
assert FC["homes"] > FC["other"] + FC["demolished"] + FC["derelict"]                                          # "Mostly homes" (of the known)
assert R["open"]["before1800"] == 9 and R["open"]["first_title"] == "Bethlem Royal Hospital"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23873001", "https://blog.tristanhotham.com/2026/10/31/asylums/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*LAND*/", open(f"{DATA}/land.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "haunted", "spooky", "creepy"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
