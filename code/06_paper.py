"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23873001 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Where_the_Asylums_Were"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert R["open"]["before1800"] == 9 and len(R["listed"]["grade1"]) == 3                          # "Nine places", "three are Grade I"
assert R["since1961"]["median_close"] - 1961 >= 20                                                 # "two to four decades later"
assert R["curve"]["peak_first"] >= 1950 and R["curve"]["peak_last"] <= 1985                        # "from the 1950s to the early 1980s"
assert 30 <= R["listed"]["pct"] <= 36                                                              # "a third of the articles"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


s = R["source"]
rows = [("Articles found", s["pages"]), ("General and other hospitals (dropped)", s["drop_general"]), ("Not hospital articles (dropped)", s["drop_nothospital"]),
        ("People, organisations, units and group articles (dropped)", s["drop_org"]), ("Duplicate of the same site (merged)", s["drop_merged"]),
        ("Places kept", s["kept"]), ("of which located", s["located"]), ("of which with an opening year", R["open"]["n"]), ("of which with a closing year", R["close"]["n"]),
        ("of which with a stated size", R["beds"]["n"]), ("of which still open", R["kinds"]["open_now"])]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{From Wikipedia articles to places.}\\label{tab:select}\\begin{tabular}{lr}\\toprule Step & Articles\\\\\\midrule\n"
      + "".join(f"{tex(a)} & {b:,}\\\\\n" for a, b in rows) + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(b['title'])} & {tex(b['county'] or '')} & {b['opened'] or ''} & {b['closed'] or ''} & {b['beds']:,} & {'infobox' if b['src'] == 'infobox' else 'text'}\\\\\n" for b in R["beds"]["top"])
TB = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The fifteen largest stated sizes (beds or patients at some date), with source.}\\label{tab:big}"
      "\\begin{tabular}{llrrrl}\\toprule Place & County & Opened & Closed & Size & Source\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_SELECT}}", TS).replace("{{TABLE_BIG}}", TB)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
