"""r/dataisbeautiful collage for asylums: 2400 x 3200 px, light background. Numbers from data/results.json.
Map labels sit on open sea or on the paper, with a halo; each is checked against the land (buffered), every circle
and every other label, and a leader line may not cross another label."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from shapely.geometry import Polygon as SPoly, box as sbox, Point as SPt, LineString as SLS
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep

R = jload(f"{DATA}/results.json")
A = pd.read_csv(f"{DATA}/asylums.csv")
BGc, SEAc = "#F7F5F0", "#E9EFF1"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
L = A[A.lat.notna()].copy(); L["x"], L["y"] = proj(L.lon.values, L.lat.values)
o, c, cv, fc = R["open"], R["close"], R["curve"], R["fates_closed"]
assert 62 <= fc["homes_of_known_pct"] <= 70                      # "two in three"

fig = plt.figure(figsize=(12, 16), dpi=200, facecolor=BGc)
fig.text(.045, .982, "Where Britain's asylums were, and what they are now", fontproperties=DISP, fontsize=34, color=FG, va="top")
fig.text(.045, .944, f"{R['source']['located']} asylums and psychiatric hospitals in English Wikipedia. Most were built between 1845 and 1914;\n"
         f"almost none closed until the 1980s, then {c['dec1990s']} closed in the 1990s alone. Two in three closed sites\nwith a stated fate are now homes.",
         fontproperties=SERP, fontsize=14.5, color=FG, va="top", linespacing=1.45)

# ---- map
MX = (-330e3, 1080e3, -10e3, 990e3)
ax = fig.add_axes([0, .355, 1, .5]); ax.set_facecolor(SEAc)
ax.add_patch(plt.Rectangle((MX[0], MX[2]), MX[1] - MX[0], MX[3] - MX[2], fc=SEAc, ec="none", zorder=0))
isles(ax, ext=MX, lw=.3)
K = 1.5
D = L.sort_values("beds", ascending=False, na_position="last")
S = rad(D.beds.values.astype(float), K)
ax.scatter(D.x, D.y, s=S, c=[FCOL[f] for f in D.fate], ec="#FFFFFF", lw=.6, alpha=.92, zorder=3)
fig.canvas.draw(); REN = fig.canvas.get_renderer()
bb = ax.get_window_extent(REN); upp = (MX[1] - MX[0]) / bb.width      # map metres per pixel
DOTS = [SPt(x, y).buffer(np.sqrt(s) / 2 * 200 / 72 * upp + 2e3) for x, y, s in zip(D.x, D.y, S)]
DOTG = prep(unary_union(DOTS))
landp = []
for p, xy in LANDS:
    if len(xy) >= 4: landp.append(SPoly(xy).buffer(0))
LANDG = prep(unary_union(landp).buffer(9e3))
PLACED, LINES = [], []


def tbox(t):
    b = t.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[b.x0 - 6, b.y0 - 5], [b.x1 + 6, b.y1 + 5]])
    return sbox(x0, y0, x1, y1)


def place(name, text, target, prefs, ha="left", size=11, w="medium", col=FG):
    t = ax.text(0, 0, text, ha=ha, va="center", fontsize=size, color=col, fontweight=w, family=MONO, linespacing=1.2, zorder=10, path_effects=HALO)
    tx, ty = proj(*target)
    for lon0, lat0 in prefs:
        cands = [(lon0 + dx * .25, lat0 + dy * .15) for r in range(0, 14) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
        for lon, lat in cands:
            x, y = proj(lon, lat); t.set_position((float(x), float(y))); b = tbox(t)
            if not sbox(MX[0] + 1e4, MX[2] + 1e4, MX[1] - 1e4, MX[3] - 1e4).contains(b): continue
            if LANDG.intersects(b) or DOTG.intersects(b) or any(b.intersects(q) for _, q in PLACED) or any(b.intersects(l) for _, l in LINES): continue
            pb, _ = nearest_points(b, SPt(float(tx), float(ty)))
            ln = SLS([(pb.x, pb.y), (float(tx), float(ty))])
            if any(ln.intersects(q) for _, q in PLACED): continue
            PLACED.append((name, b)); LINES.append((name, ln))
            ax.plot(*ln.xy, color=FG, lw=.8, zorder=9); ax.scatter([tx], [ty], s=10, c=FG, zorder=11)
            return
    raise RuntimeError("no clean spot for " + name)


T = {r.wikipedia_title: r for r in L.itertuples()}
b0, b1 = R["beds"]["top"][0], R["beds"]["top"][1]
w_, p_ = T[b0["title"]], T[b1["title"]]
place("whit", f"WHITTINGHAM, near Preston\n{b0['beds']:,} patients in 1939,\nthe largest in Britain", (w_.lon, w_.lat), [(-5.6, 54.15)], "right")
place("prest", f"PRESTWICH, Manchester\n{b1['beds']:,} patients by 1903", (p_.lon, p_.lat), [(-5.0, 53.05)], "right")
lo, ep = R["london"], R["epsom"]
place("ring", f"LONDON'S RING\n{lo['ring_vic']} asylums built 10 to 40 km\nout, only {lo['inner_vic']} in the inner city", (0.35, 51.62), [(2.6, 52.3)], "left")
place("epsom", f"THE EPSOM CLUSTER\nfive hospitals within {ep['max_km']:.1f} km", (ep["lon"], ep["lat"]), [(0.2, 50.45)], "left")
bet = T["Bethlem Royal Hospital"]
place("bethlem", "BETHLEM, founded 1247:\nthe original 'Bedlam', still open", (bet.lon, bet.lat), [(3.3, 51.35), (1.5, 50.2), (-1.5, 50.1)], "left")
cr = T["The Crichton"]
place("crichton", "THE CRICHTON, Dumfries\nnow a university campus", (cr.lon, cr.lat), [(-5.9, 54.85)], "right")
for nm, b in PLACED:
    assert not LANDG.intersects(b) and not DOTG.intersects(b), nm
    assert not any(b.intersects(q) for n2, q in PLACED if n2 != nm), nm
for nm, l in LINES:
    assert not any(l.intersects(q) for n2, q in PLACED if n2 != nm), nm
print("labels ok", len(PLACED))

# size key and legend on the paper under the map
lax = fig.add_axes([0, .27, 1, .08]); lax.axis("off"); lax.set_xlim(0, 1); lax.set_ylim(0, 1)
ks = list(FATE_COL)
for i, k in enumerate(ks):
    x = [.05, .42, .72][i % 3]; y = .78 - (i // 3) * .34
    n = fc[k] if k != "health" else R["fates"]["health"]
    lax.scatter([x], [y], s=150, c=FCOL[k], ec="#fff", lw=.8); lax.text(x + .02, y, f"{FLAB[k]}  {n}" + ("*" if k == "derelict" and not (L.fate == "derelict").any() else ""), va="center", fontsize=12, color=FG)
lax.text(.05, .06, "Circle area: largest beds or patients the article states (key right); small dots: none stated. *No coordinates, not mapped.", fontsize=10, color=MUT, va="center")
for i, n in enumerate((500, 1500, 3000)):
    r_pt = np.sqrt(max(16, n * .055) * K) / 2
    lax.scatter([.885 + i * .04], [.47], s=max(16, n * .055) * K, facecolors="none", edgecolors=FG, lw=.9)
    lax.text(.885 + i * .04, .2, f"{n:,}", ha="center", fontsize=9, color=FG)

# ---- charts
DD = pd.DataFrame(R["decades"])
a1 = fig.add_axes([.07, .07, .4, .17]); a1.set_facecolor(BGc)
a1.bar(DD.dec + 5, DD.opened, width=8, color=COOL); a1.bar(DD.dec + 5, -DD.closed, width=8, color=HOT)
a1.axhline(0, color=FG, lw=1); spines(a1); a1.set_xlim(1797, 2033); a1.set_ylim(-88, 58)
a1.set_yticks([-80, -40, 0, 40]); a1.set_yticklabels(["80", "40", "0", "40"], fontsize=10); a1.tick_params(axis="x", labelsize=10)
a1.text(1800, 55, "opened per decade", color=COOL, fontsize=11, va="top", fontweight="medium")
a1.text(1800, -84, "closed per decade", color=HOT, fontsize=11, va="bottom", fontweight="medium")
a1.text(o["peak_dec"] + 5, o["peak_n"] + 2, f"{o['peak_n']} in the {o['peak_dec']}s", fontsize=9.5, ha="center", va="bottom")
a1.text(c["peak_dec"] - 4, -c["peak_n"] + 3, f"{c['peak_n']} in the\n{c['peak_dec']}s", fontsize=9.5, ha="right", va="bottom")
OY = pd.DataFrame(R["open_by_year"]).set_index("y")
a2 = fig.add_axes([.57, .07, .38, .17]); a2.set_facecolor(BGc)
a2.fill_between(OY.index, 0, OY.open, color=COOL, alpha=.15, lw=0); a2.plot(OY.index, OY.open, color=COOL, lw=2.2)
a2.axvline(1961, color=HOT, ls=":", lw=1.2); a2.text(1957, 40, "1961: Powell's\n'Water Tower'\nspeech", ha="right", fontsize=9.5, color=HOT)
spines(a2); a2.set_xlim(1800, 2026); a2.set_ylim(0, 225); a2.tick_params(labelsize=10)
a2.text(1802, 220, "open at once", color=COOL, fontsize=11, va="top", fontweight="medium")
a2.text(1972, cv["peak_n"] + 6, f"peak {cv['peak_n']}", ha="center", fontsize=9.5)
a2.text(2024, cv["y2026"] - 10, f"{cv['y2026']} today", ha="right", va="top", fontsize=9.5)
fig.text(.045, .012, f"Data: English Wikipedia articles in its psychiatric and defunct hospital categories (CC BY-SA 4.0), read by\npublished rules; not every asylum has an article. Coast: Natural Earth. Counties: ONS, OSNI.\n"
         "Dr Tristan Hotham · maps.tristanhotham.com/asylums", fontsize=9.5, color=MUT, linespacing=1.4)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "where_the_asylums_were.png")
fig.savefig(out, dpi=200, facecolor=BGc)
from PIL import Image
print(out, Image.open(out).size)
