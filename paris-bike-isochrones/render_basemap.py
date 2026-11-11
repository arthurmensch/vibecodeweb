import json, math, time, urllib.request, io
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = "/workspace/isochrones_paris"
D = np.load(f"{BASE}/durations.npy")
meta = json.load(open(f"{BASE}/meta.json"))
gj = json.load(open(f"{BASE}/isochrones_bike_92_rue_des_poissonniers.geojson"))
lats = np.array(meta["lats"]); lons = np.array(meta["lons"])
lon0, lat0 = meta["origin"]
Dm = D / 60.0
Z = 14

allpts = [tuple(gj["properties"]["origin_coords"])]  # lon, lat
for f in gj["features"]:
    for ring in f["geometry"]["coordinates"]:
        allpts += [tuple(p) for p in ring]
xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
mx = 111320.0 * math.cos(math.radians(lat0)); my = 110540.0
margin = 0.8  # km
lon_min = min(xs) - margin * 1000 / mx
lon_max = max(xs) + margin * 1000 / mx
lat_min = min(ys) - margin * 1000 / my
lat_max = max(ys) + margin * 1000 / my

def deg2px(lon, lat, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n * 256.0
    y = (1.0 - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n * 256.0
    return x, y

px0f, py1f = deg2px(lon_min, lat_max, Z)
px1f, py0f = deg2px(lon_max, lat_min, Z)
tx0, ty0 = int(px0f // 256), int(py1f // 256)
tx1, ty1 = int(px1f // 256), int(py0f // 256)
W, H = (tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256
print(f"tiles {tx1-tx0+1}x{ty1-ty0+1} = {(tx1-tx0+1)*(ty1-ty0+1)}, canvas {W}x{H}px at z{Z}")

TILES = ["https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
         "https://tile.openstreetmap.org/{z}/{x}/{y}.png"]
canvas = Image.new("RGB", (W, H), (240, 240, 240))
ok = fail = 0
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        got = False
        for t in TILES:
            try:
                req = urllib.request.Request(t.format(z=Z, x=tx, y=ty),
                                             headers={"User-Agent": "vibe-isochrone-map/1.0 (one-off static map render)"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    img = Image.open(io.BytesIO(r.read())).convert("RGB")
                canvas.paste(img, ((tx - tx0) * 256, (ty - ty0) * 256))
                got = True
                ok += 1
                break
            except Exception as e:
                last = e
        if not got:
            fail += 1
            print("tile fail", tx, ty, last)
        time.sleep(0.12)
print("tiles ok/fail:", ok, fail)
crop = canvas.crop((int(px0f) - tx0 * 256, int(py1f) - ty0 * 256, int(px1f) - tx0 * 256, int(py0f) - ty0 * 256))
print("cropped:", crop.size)

fig, ax = plt.subplots(figsize=(14, 13))
ax.imshow(crop, extent=[lon_min, lon_max, lat_min, lat_max], interpolation="bilinear", zorder=0)
ax.set_aspect(1.0 / math.cos(math.radians(lat0)))

levels = [5, 10, 15, 20, 25, 30]
cf = ax.contourf(lons, lats, Dm, levels=[0] + levels + [40], cmap="YlGnBu", alpha=0.55, zorder=2)
cs = ax.contour(lons, lats, Dm, levels=levels, colors="black", linewidths=2.0, zorder=3)
ax.clabel(cs, fmt="%d min", fontsize=13, inline=True)

landmarks = [("Gare du Nord", 2.3553, 48.8809), ("Barbès-Rochechouart", 2.3488, 48.8834),
             ("Sacré-Cœur", 2.3431, 48.8867), ("Opéra", 2.3317, 48.8706),
             ("Châtelet", 2.3470, 48.8584), ("République", 2.3637, 48.8676),
             ("Bastille", 2.3694, 48.8532), ("Montparnasse", 2.3219, 48.8422)]
for name, lon, lat in landmarks:
    if lon_min < lon < lon_max and lat_min < lat < lat_max:
        ax.annotate(name, (lon, lat), fontsize=10, color="#333", zorder=5,
                    xytext=(4, 4), textcoords="offset points")

ax.plot(lon0, lat0, marker="*", ms=26, color="red", mec="black", mew=1.2, zorder=6)
ax.annotate("92 rue des Poissonniers", (lon0, lat0), fontsize=13, fontweight="bold",
            xytext=(10, -16), textcoords="offset points", zorder=6,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="red", alpha=0.9))

sb_km = 2.0
dlon = sb_km * 1000 / mx
x_sb = lon_min + 0.02 * (lon_max - lon_min)
y_sb = lat_min + 0.03 * (lat_max - lat_min)
ax.plot([x_sb, x_sb + dlon], [y_sb, y_sb], color="black", lw=4, solid_capstyle="butt", zorder=6)
ax.text(x_sb + dlon / 2, y_sb + 0.0015 * (lat_max - lat_min), f"{sb_km:.0f} km",
        ha="center", fontsize=12, fontweight="bold", zorder=6,
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
ax.annotate("N", (lon_max - 0.03 * (lon_max - lon_min), lat_max - 0.04 * (lat_max - lat_min)),
            fontsize=16, fontweight="bold", ha="center", zorder=6,
            arrowprops=dict(arrowstyle="-|>", color="black", lw=2), xytext=(0, -22), textcoords="offset points")

ax.set_xlim(lon_min, lon_max); ax.set_ylim(lat_min, lat_max)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.set_title("Isochrones vélo depuis 92 rue des Poissonniers, Paris 18e\n5–30 min à vélo (OSRM profil vélo / OpenStreetMap)",
             fontsize=17, fontweight="bold")
ax.text(0.995, 0.005, "Fond de carte © OpenStreetMap contributors, © CARTO · temps: OSRM vélo",
        transform=ax.transAxes, ha="right", fontsize=9, color="#555",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75))
fig.tight_layout()
out = f"{BASE}/isochrones_bike_92_rue_des_poissonniers.png"
fig.savefig(out, dpi=220)
print("saved", out)
