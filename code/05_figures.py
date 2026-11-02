"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json and data/asylums.csv."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from figstyle import *

R = jload(f"{DATA}/results.json")
assert 62 <= R["fates_closed"]["homes_of_known_pct"] <= 70 and R["open"]["y1845_1914_pct"] > 50   # "two in three", "most"
A = pd.read_csv(f"{DATA}/asylums.csv")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
HALO = [pe.withStroke(linewidth=3.2, foreground=SEA)]
HALOB = [pe.withStroke(linewidth=3.2, foreground=BG)]
L = A[A.lat.notna()].copy()
L["x"], L["y"] = proj(L.lon.values, L.lat.values)
ORDER = {k: i for i, k in enumerate(FKEYS)}


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def dots(ax, D, k=1.0, z=3):
    D = D.sort_values("beds", ascending=False, na_position="last")
    ax.scatter(D.x, D.y, s=rad(D.beds.values.astype(float), k), c=[FCOL[f] for f in D.fate], ec="#FFFFFF", lw=.6, alpha=.9, zorder=z)


def fate_legend(fig, loc, anchor, ncol=3, fs=10):
    h = [Line2D([], [], ls="", marker="o", ms=9, mfc=FCOL[k], mec="#fff", label=FLAB[k]) for k in FKEYS]
    fig.legend(handles=h, loc=loc, bbox_to_anchor=anchor, ncol=ncol, frameon=False, fontsize=fs)


# ---------- map of Britain ----------
fig = plt.figure(figsize=(12, 13.2), facecolor=BG); ax = fig.add_axes([0, .07, 1, .86]); ax.set_facecolor(SEA)
ax.add_patch(plt.Rectangle((EXT[0], EXT[2]), EXT[1] - EXT[0], EXT[3] - EXT[2], fc=SEA, ec="none", zorder=0))
isles(ax); dots(ax, L, k=1.7)
for nm, lon, lat, dx, dy, ha in (("London", -0.13, 51.51, 12e3, -14e3, "left"), ("Manchester", -2.24, 53.48, 9e3, -12e3, "left"), ("Glasgow", -4.25, 55.86, -8e3, 9e3, "right"),
                                 ("Birmingham", -1.9, 52.48, -8e3, -12e3, "right"), ("Leeds", -1.55, 53.8, 9e3, 6e3, "left"), ("Edinburgh", -3.19, 55.95, 8e3, 8e3, "left"),
                                 ("Cardiff", -3.18, 51.48, -8e3, -14e3, "right"), ("Belfast", -5.93, 54.6, -8e3, 8e3, "right")):
    x, y = proj(lon, lat); ax.scatter([x], [y], s=14, c=FG, marker="s", zorder=6); ax.text(x + dx, y + dy, nm, ha=ha, fontsize=10.5, color=FG, fontweight="medium", path_effects=HALOB, zorder=6)
fig.text(.03, .965, f"{R['source']['located']} asylums and psychiatric hospitals in English Wikipedia, coloured by what the site is now", fontsize=13, color=FG)
fig.text(.03, .945, "Circle area: the largest number of beds or patients the article states; small dots: none stated. Squares: cities", fontsize=10.5, color=MUT)
fate_legend(fig, "lower center", (.5, .005), ncol=3, fs=10.5)
both(fig, "map")

# ---------- decades ----------
D = pd.DataFrame(R["decades"])
fig = plt.figure(figsize=(12, 6), facecolor=BG); ax = fig.add_axes([.07, .1, .9, .78]); ax.set_facecolor(BG)
ax.bar(D.dec + 5, D.opened, width=8, color=COOL, label="opened")
ax.bar(D.dec + 5, -D.closed, width=8, color=HOT, label="closed")
ax.axhline(0, color=FG, lw=1); spines(ax); ax.set_xlim(1797, 2033)
ax.set_yticks([-80, -60, -40, -20, 0, 20, 40]); ax.set_yticklabels(["80", "60", "40", "20", "0", "20", "40"])
ax.grid(axis="y", color=RULE); ax.set_axisbelow(True); ax.set_ylabel("places, by decade")
o, c = R["open"], R["close"]
ax.text(o["peak_dec"] + 5, o["peak_n"] + 2, f"{o['peak_n']} in the {o['peak_dec']}s", ha="center", fontsize=10.5)
ax.text(1905, o["dec1900s"] + 2, f"{o['dec1900s']} in the 1900s", ha="center", fontsize=10.5)
ax.text(c["peak_dec"] - 1, -c["peak_n"] + 2, f"{c['peak_n']} closed\nin the {c['peak_dec']}s", ha="right", va="bottom", fontsize=10.5)
for yr, t in ((1808, "1808 Act"), (1845, "1845 Acts"), (1961, "Powell's\nspeech, 1961")):
    ax.axvline(yr, color=MUT, ls=":", lw=1); ax.text(yr + 1.5, -6 if yr != 1961 else -40, t, fontsize=9.5, color=MUT, va="top")
fig.legend(loc="upper left", bbox_to_anchor=(.07, .99), ncol=2, frameon=False, fontsize=10.5)
fig.text(.97, .955, f"{o['before1800']} that opened before 1800 not shown", ha="right", fontsize=9.5, color=MUT)
both(fig, "decades")

# ---------- open per year ----------
OY = pd.DataFrame(R["open_by_year"]).set_index("y"); cv = R["curve"]
fig = plt.figure(figsize=(12, 5.6), facecolor=BG); ax = fig.add_axes([.07, .11, .9, .78]); ax.set_facecolor(BG)
ax.fill_between(OY.index, 0, OY.open, color=COOL, alpha=.15, lw=0); ax.plot(OY.index, OY.open, color=COOL, lw=2.4)
spines(ax); ax.set_xlim(1800, 2026); ax.set_ylim(0, 225); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True); ax.set_ylabel("open that year")
for yr, t, yy in ((1845, "1845\nLunacy Act", 150), (1930, "1930 Mental\nTreatment Act", 120), (1961, "1961\nWater Tower\nspeech", 120), (1990, "1990 NHS and\nCommunity\nCare Act", 150)):
    ax.axvline(yr, color=MUT, ls=":", lw=1); ax.text(yr - 1.5, yy, t, fontsize=9.5, color=MUT, ha="right", va="top")
ax.text(1977, cv["peak_n"] + 6, f"{cv['peak_n']} open, {cv['peak_first']} to {cv['peak_last']}", ha="center", fontsize=10.5)
ax.text(2024, cv["y2026"] - 8, f"{cv['y2026']} today", ha="right", va="top", fontsize=10.5)
ax.text(1900, cv["y1900"] + 8, f"{cv['y1900']} in 1900", ha="right", fontsize=10.5)
fig.text(.07, .95, f"Asylums and psychiatric hospitals open each year, of the {cv['n']} in the data with dates", fontsize=12, color=FG)
both(fig, "open")

# ---------- fates ----------
FC = R["fates_closed"]; n = FC["n"]
fig = plt.figure(figsize=(12, 5), facecolor=BG); ax = fig.add_axes([.27, .12, .66, .74]); ax.set_facecolor(BG)
ks = [k for k in FKEYS if k != "health"]
vals = [FC[k] for k in ks]
ax.barh(range(len(ks))[::-1], vals, color=[FCOL[k] for k in ks], height=.66)
for i, (k, v) in enumerate(zip(ks, vals)):
    ax.text(v + 1.2, len(ks) - 1 - i, f"{v} ({round(100 * v / n)}%)", va="center", fontsize=11)
ax.set_yticks(range(len(ks))[::-1]); ax.set_yticklabels([FLAB[k] for k in ks], fontsize=11.5); ax.tick_params(axis="y", length=0)
ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.set_xlim(0, max(vals) * 1.22)
fig.text(.03, .93, f"What the {n} closed sites are now, as their Wikipedia article states it ({R['fates']['health']} more are still open)", fontsize=12, color=FG)
both(fig, "fates")

# ---------- biggest ----------
T = R["beds"]["top"][:12]
fig = plt.figure(figsize=(12, 6.2), facecolor=BG); ax = fig.add_axes([.28, .06, .64, .82]); ax.set_facecolor(BG)
nm = [t["title"].replace(" Hospital", "").replace(", Epsom", " (Epsom)") for t in T][::-1]; v = [t["beds"] for t in T][::-1]
ax.barh(nm, v, color=INK, height=.68)
for i, t in enumerate(T[::-1]):
    ax.text(t["beds"] + 30, i, f"{t['beds']:,}  {t['county'] if isinstance(t['county'], str) else ''}", va="center", fontsize=10, color=FG)
ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=11); ax.set_xlim(0, 4600)
fig.text(.03, .93, "The biggest: the largest number of beds or patients each article states", fontsize=12, color=FG)
both(fig, "biggest")

# ---------- London ring and Epsom ----------
LE = (480e3, 590e3, 130e3, 230e3)
fig = plt.figure(figsize=(12, 11), facecolor=BG); ax = fig.add_axes([0, .06, 1, .88])
ax.add_patch(plt.Rectangle((LE[0], LE[2]), LE[1] - LE[0], LE[3] - LE[2], fc=SEA, zorder=0))
isles(ax, ext=LE, lw=.8, cc="#FFFFFF")
cx, cy = proj(*LONDON[::-1])
for r, ls in ((10e3, "-"), (40e3, "--")):
    th = np.linspace(0, 2 * np.pi, 200); ax.plot(cx + r * np.cos(th), cy + r * np.sin(th), color=MUT, lw=1, ls=ls, zorder=2)
ax.text(cx + 40e3 * np.cos(np.radians(52)) + 1500, cy + 40e3 * np.sin(np.radians(52)) + 1500, "40 km from Charing Cross", fontsize=10, color=MUT, path_effects=HALO, rotation=-38, zorder=6)
ax.text(cx, cy - 10e3 - 3500, "10 km", fontsize=10, color=MUT, ha="center", path_effects=HALO, zorder=6)
dots(ax, L, k=3.2)
ax.scatter([cx], [cy], marker="+", s=120, color=FG, zorder=7); ax.text(cx - 2000, cy - 3200, "Charing Cross", ha="right", fontsize=10, color=FG, path_effects=HALOB, zorder=7)
ex, ey = proj(R["epsom"]["lon"], R["epsom"]["lat"])
ax.text(ex - 2500, ey - 7500, "EPSOM CLUSTER\nfive hospitals within\n%.1f km" % R["epsom"]["max_km"], fontsize=10.5, color=FG, ha="right", fontweight="medium", path_effects=HALOB, zorder=7)
for t, dx, dy, ha in (("Friern Hospital", 2500, 2000, "left"), ("Claybury Hospital", 2500, 1500, "left"), ("Cane Hill Hospital", 2500, -2500, "left"), ("Napsbury Hospital", 2500, 1800, "left"),
                      ("Warley Hospital", -2500, 2200, "right"), ("Bexley Hospital", 0, -4500, "center"), ("Holloway Sanatorium", -2500, 1800, "right"), ("Leavesden Hospital", -2500, 1800, "right")):
    r = L[L.wikipedia_title == t]
    if len(r): ax.text(float(r.x.iloc[0]) + dx, float(r.y.iloc[0]) + dy, t.replace(" Hospital", ""), ha=ha, fontsize=9.5, color=FG, path_effects=HALOB, zorder=7)
lo = R["london"]
fig.text(.03, .965, f"London's ring: {lo['ring_vic']} asylums opened 1830 to 1939 lie 10 to 40 km from Charing Cross, {lo['inner_vic']} within 10 km", fontsize=12.5, color=FG)
fate_legend(fig, "lower center", (.5, .0), ncol=3, fs=10.5)
both(fig, "london")

# ---------- names (paper only) ----------
NM = R["names"]; kn = R["source"]["kept"]
rows = [("any name with \"asylum\"", NM["asylum_any"], HOT), ("\"lunatic asylum\" or similar", NM["lunatic_asylum"], HOT), ("\"mental hospital\"", NM["mental_hospital"], GOLD),
        ("institution or colony", NM["institution"], GOLD), ("\"psychiatric hospital\"", NM["psychiatric_hospital"], COOL), ("today's title starts with \"St\"", NM["saint_titles"], COOL)]
fig = plt.figure(figsize=(12, 4.6), facecolor=BG); ax = fig.add_axes([.3, .08, .62, .8]); ax.set_facecolor(BG)
ax.barh([r[0] for r in rows][::-1], [r[1] for r in rows][::-1], color=[r[2] for r in rows][::-1], height=.66)
for i, r in enumerate(rows[::-1]): ax.text(r[1] + 1.5, i, f"{r[1]} ({round(100 * r[1] / kn)}%)", va="center", fontsize=10.5)
ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=11); ax.set_xlim(0, 175)
fig.text(.03, .93, f"Names the {kn} articles record, from the title, the infobox and the text", fontsize=12, color=FG)
both(fig, "names", blog=False)

# ---------- distance to town (paper only) ----------
TW = R["town"]; eras = [("before 1845", TW["pre1845"]), ("1845 to 1914", TW["y1845_1914"]), ("1915 to 1947", TW["y1915_1947"]), ("1948 onwards", TW["y1948_"])]
fig = plt.figure(figsize=(12, 4.4), facecolor=BG); ax = fig.add_axes([.2, .14, .74, .72]); ax.set_facecolor(BG)
yy = np.arange(len(eras))[::-1]
ax.barh(yy + .18, [e[1]["over5_pct"] for e in eras], height=.34, color=COOL, label="more than 5 km")
ax.barh(yy - .18, [e[1]["over15_pct"] for e in eras], height=.34, color=INK, label="more than 15 km")
for y, (n_, e) in zip(yy, eras):
    ax.text(e["over5_pct"] + 1, y + .18, f"{round(e['over5_pct'])}%", va="center", fontsize=10); ax.text(e["over15_pct"] + 1, y - .18, f"{round(e['over15_pct'])}%", va="center", fontsize=10)
ax.set_yticks(yy); ax.set_yticklabels([f"opened {n_}\n({e['n']} places)" for n_, e in eras], fontsize=10.5); ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 105); spines(ax); ax.set_xlabel("share of places this far from the nearest town of 100,000 or more today")
ax.legend(loc="lower right", frameon=False, fontsize=10)
both(fig, "town", blog=False)

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.56, .02, .42, .96]); isles(ax, ext=(-60e3, 660e3, 0, 990e3), lw=.25); dots(ax, L, k=.6)
fig.text(.04, .88, "Where the", fontproperties=DISP, fontsize=52, color=FG, va="top")
fig.text(.04, .72, "asylums", fontproperties=DISP, fontsize=66, color=HOT, va="top")
fig.text(.04, .53, "were", fontproperties=DISP, fontsize=52, color=FG, va="top")
fig.text(.04, .36, f"{R['source']['located']} asylums and psychiatric hospitals mapped.\nMost opened between 1845 and 1914; {R['close']['dec1990s']} closed\nin the 1990s alone. Two in three closed sites\nwith a stated fate are now homes.", fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.4)
fig.text(.04, .05, "maps.tristanhotham.com/asylums", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
