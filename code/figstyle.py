"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the paper and brick palette, fate colours, and the outline of Britain and Ireland (data/land.json,
data/counties.json) in the British National Grid (EPSG:27700)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#66625B", "axes.labelcolor": "#22211F",
                     "xtick.color": "#66625B", "ytick.color": "#66625B"})
BG, FG, MUT, LAND, RULE, SEA, COAST = "#F5F2EB", "#22211F", "#66625B", "#E7E1D3", "#DCD5C7", "#EEF1F0", "#B9B2A3"
HOT, COOL, INK, GOLD = "#A8442A", "#2F6F8F", "#2C3A3A", "#B8862B"
FCOL = FATE_COL; FLAB = FATE_LABEL; FKEYS = [k for k, _, _ in FATES]

PJ = Transformer.from_crs(4326, 27700, always_xy=True)
LANDJ = jload(f"{DATA}/land.json")
CTJ = jload(f"{DATA}/counties.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


def _shapes(fc):
    out = []
    for f in fc["features"]:
        for ring in rings(f["geometry"]):
            x, y = PJ.transform(ring[:, 0], ring[:, 1]); out.append((f["properties"], np.column_stack([x, y])))
    return out


LANDS = _shapes(LANDJ); CTS = _shapes(CTJ)
EXT = (-120e3, 680e3, -20e3, 1000e3)        # Britain and Northern Ireland in BNG metres (x0, x1, y0, y1)


def isles(ax, ext=EXT, land=LAND, counties=True, lw=.35, cc="#FFFFFF"):
    for p, xy in LANDS:
        ax.add_patch(MPoly(xy, closed=True, fc=land if p.get("uk") or p.get("iso") == "IRL" else "#ECE7DC", ec=COAST, lw=.4, zorder=1))
    if counties:
        for p, xy in CTS:
            ax.add_patch(MPoly(xy, closed=True, fc="none", ec=cc, lw=lw, zorder=1.5))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def proj(lon, lat):
    return PJ.transform(np.asarray(lon), np.asarray(lat))


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def rad(beds, k=1.0):
    """Marker size (points^2) for a stated size; places with none get a small fixed dot."""
    return np.where(np.isnan(beds), 9 * k, np.maximum(16, beds * .055) * k)
