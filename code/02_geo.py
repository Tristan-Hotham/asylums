"""Geography: light outline files for the page and figures, and the towns used for labels and distances.
  data/land.json      coastlines of Great Britain, Ireland, the Isle of Man, the Channel Islands and northern France
                      (Natural Earth 1:10m, simplified), the page's offline base map and the figures' land
  data/counties.json  UK counties (ONS / OSNI outlines, simplified): England ceremonial counties, Welsh preserved
                      counties, Scottish council areas, Northern Ireland as one unit
  data/cities.json    Natural Earth populated places in the UK, Ireland, the Isle of Man and the Channel Islands
"""
from shapely.geometry import shape, mapping, box
from common import *


def rnd(c, k=3):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


CLIP = box(-11.0, 48.6, 2.6, 61.2)
W = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
feats = []
for f in W["features"]:
    p = f["properties"]; iso = p.get("ADM0_A3")
    if iso not in ("GBR", "IRL", "IMN", "JEY", "GGY", "FRA", "BEL", "NLD"):
        continue
    g = shape(f["geometry"]).intersection(CLIP)
    if g.is_empty:
        continue
    g = g.simplify(0.004, preserve_topology=True)
    feats.append({"type": "Feature", "properties": {"iso": iso, "uk": int(iso in ("GBR", "IMN", "JEY", "GGY"))}, "geometry": {"type": g.geom_type, "coordinates": rnd(mapping(g)["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/land.json")

C = jload(f"{GEO}/counties_uk.geojson")
cf = []
for f in C["features"]:
    g = shape(f["geometry"]).simplify(0.003, preserve_topology=True)
    cf.append({"type": "Feature", "properties": {"county": f["properties"]["county"], "nation": f["properties"]["nation"]},
               "geometry": {"type": g.geom_type, "coordinates": rnd(mapping(g)["coordinates"])}})
jsave({"type": "FeatureCollection", "features": cf}, f"{DATA}/counties.json")

P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in P["features"]:
    p = f["properties"]
    if p.get("adm0name") in ("United Kingdom", "Ireland", "Isle of Man", "Jersey", "Guernsey"):
        nm = {"Londonderry/Derry": "Derry", "Stoke": "Stoke-on-Trent", "Newcastle": "Newcastle upon Tyne"}.get(p["name"], p["name"])
        cities.append({"name": nm, "lat": round(p["latitude"], 4), "lon": round(p["longitude"], 4), "pop": int(p.get("pop_max") or 0), "country": p["adm0name"]})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("land", os.path.getsize(f"{DATA}/land.json") // 1024, "KB; counties", len(cf), os.path.getsize(f"{DATA}/counties.json") // 1024, "KB; towns", len(cities))
