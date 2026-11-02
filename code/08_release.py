"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23873001, https://doi.org/10.5281/zenodo.23873001 and https://blog.tristanhotham.com/2026/10/31/asylums/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Where_the_Asylums_Were"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
A = pd.read_csv(f"{DATA}/asylums.csv").set_index("wikipedia_title")
top = R["beds"]["top"]
assert all(1600 <= t["beds"] <= 2000 for t in top[5:12]) and len(top[5:12]) == 7                  # "seven more at 1,600 to 2,000"
assert top[3]["beds"] == top[4]["beds"] and {top[3]["title"], top[4]["title"]} == {"Friern Hospital", "Claybury Hospital"}
assert all(A.loc[t, "fate"] == "homes" for t in ("Friern Hospital", "Claybury Hospital", "Warley Hospital", "Bexley Hospital", "Exminster Hospital"))
assert "apartments" in A.loc["Exminster Hospital", "fate_text"]
assert R["london"]["ring_homes_pct"] > 50                                                            # "most of the ring is now housing"
assert R["open_by_year"][0]["open"] < 10                                                             # "from under 10"
assert {c[0] for c in R["london"]["ring_counties"]} == {"Surrey", "Hertfordshire", "Kent", "Essex", "Greater London"}

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23873001"}, set(re.findall(r"\{\{[^|}]+\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "haunted"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s, o, c, fc = R["source"], R["open"], R["close"], R["fates_closed"]
meta = {"title": "Where the asylums were: the rise, fall and afterlife of Britain's county asylums",
        "slug": "asylums",
        "excerpt": f"I mapped {s['located']} of Britain's asylums and psychiatric hospitals from Wikipedia. Most were built between 1845 and 1914, almost none closed until the 1980s, and of the closed sites whose fate is known, {round(fc['homes_of_known_pct'])}% are now homes.",
        "seo_description": f"A map of {s['located']} British asylums and psychiatric hospitals: two waves of building, {c['dec1990s']} closures in the 1990s, and what the sites are now.",
        "tags": ["asylums", "psychiatric hospitals", "history", "maps", "data visualisation", "mental health history", "Care in the Community", "Wikipedia"],
        "header_alt": f"Title card reading 'Where the asylums were', with 'asylums' in brick red, on pale paper beside a map of Britain and Northern Ireland dotted with {s['located']} coloured circles for asylums and psychiatric hospitals, clustered around London and the industrial North. Text: most opened between 1845 and 1914; {c['dec1990s']} closed in the 1990s alone; two in three closed sites with a stated fate are now homes."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/asylums_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "raw"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"asylums/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"asylums/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "asylums/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("``", "\"").replace("''", "\"")
zmeta = {"title": PAPER_TITLE,
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Data derived from English Wikipedia (CC BY-SA 4.0); the place table in the data and code archive is released under CC BY-SA 4.0, the paper under CC BY 4.0.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["asylums", "psychiatric hospitals", "history of psychiatry", "deinstitutionalisation", "Care in the Community", "Lunacy Act 1845", "historic buildings", "Wikipedia", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://en.wikipedia.org/wiki/Category:Former_psychiatric_hospitals_in_the_United_Kingdom", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
