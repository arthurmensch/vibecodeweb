import json, math, time, urllib.request
import numpy as np

ORIGIN = (2.352321, 48.892422)  # lon, lat — 92 Rue des Poissonniers, 75018 Paris (BAN id 75118_7564_00092)
lon0, lat0 = ORIGIN
NLAT, NLON = 41, 41
DLAT, DLON = 0.065, 0.092
CHUNK = 140
LEVELS_MIN = [5, 10, 15, 20, 25, 30]

lats = np.linspace(lat0 - DLAT, lat0 + DLAT, NLAT)
lons = np.linspace(lon0 - DLON, lon0 + DLON, NLON)
pts = [(lon, lat) for lat in lats for lon in lons]  # row-major: idx = i*NLON + j

def fetch(url, tries=4):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vibe-isochrone-research/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(2 + 3 * k)
    raise RuntimeError(f"fetch failed: {url[:80]}... {last}")

import os
CACHE = "/workspace/isochrones_paris/durations.npy"
if os.path.exists(CACHE):
    D = np.load(CACHE)
    meta = json.load(open("/workspace/isochrones_paris/meta.json"))
    n_unreach = meta["n_unreachable"]
    print("loaded cached grid", D.shape, flush=True)
else:
    durations = [None] * len(pts)
    snapped = [None] * len(pts)
    for c in range(0, len(pts), CHUNK):
        chunk = pts[c:c + CHUNK]
        coords = [ORIGIN] + chunk
        url = ("https://router.project-osrm.org/table/v1/bike/"
               + ";".join(f"{lo:.6f},{la:.6f}" for lo, la in coords)
               + "?sources=0&destinations=all")
        data = fetch(url)
        assert data.get("code") == "Ok", data
        row = data["durations"][0]
        dests = data["destinations"][1:]
        for k in range(len(chunk)):
            durations[c + k] = row[k + 1]
            snapped[c + k] = dests[k]["location"]
        print(f"chunk {c//CHUNK+1}: {len(chunk)} pts ok", flush=True)
        time.sleep(1)

    D = np.array([np.nan if d is None else float(d) for d in durations]).reshape(NLAT, NLON)
    n_unreach = int(np.isnan(D).sum())
    D = np.nan_to_num(D, nan=7200.0)
    np.save(CACHE, D)
    json.dump({"origin": ORIGIN, "lats": lats.tolist(), "lons": lons.tolist(),
               "n_unreachable": n_unreach}, open("/workspace/isochrones_paris/meta.json", "w"))
print("grid", D.shape, "min/median/max(min):", D.min()/60, np.median(D)/60, D.max()/60, "unreachable:", n_unreach)

from skimage.measure import find_contours
from shapely.geometry import LineString, Point, mapping, shape
from shapely.ops import unary_union
import rasterio.features

dlat = lats[1] - lats[0]
dlon = lons[1] - lons[0]

def rc_to_lonlat(r, c):
    return (lons[0] + c * dlon, lats[0] + r * dlat)

# meter projection around origin for area stats
mx = 111320.0 * math.cos(math.radians(lat0))
my = 110540.0
def pix_to_xy(x, y):
    lon, lat = lons[0] + (x - 0.5) * dlon, lats[0] + (y - 0.5) * dlat
    return ((lon - lon0) * mx, (lat - lat0) * my)

features = []
summary = {}
origin_pt_xy = Point(0, 0)
for m in LEVELS_MIN:
    t = m * 60.0
    mask = (D <= t).astype("uint8")
    geoms = [shape(g) for g, v in rasterio.features.shapes(mask, mask=mask) if v == 1]
    merged = unary_union(geoms).buffer(0)
    polys = [merged] if merged.geom_type == "Polygon" else list(merged.geoms)
    from shapely.geometry import Polygon as Poly
    kept_xy = []
    for p in polys:
        pts_xy = [pix_to_xy(x, y) for x, y in p.exterior.coords]
        holes_xy = [[pix_to_xy(x, y) for x, y in ring.coords] for ring in p.interiors]
        q = Poly(pts_xy, holes_xy)
        if q.covers(origin_pt_xy):
            kept_xy.append(q)
    merged_xy = unary_union(kept_xy) if kept_xy else None
    if merged_xy is None:
        print(f"level {m} min: no polygon containing origin?!", flush=True)
        continue
    area_km2 = merged_xy.area / 1e6
    # back to lon/lat for geojson
    inv = lambda x, y: (lon0 + x / mx, lat0 + y / my)
    ext = [ [round(v, 6) for v in inv(x, y)] for x, y in merged_xy.exterior.coords ]
    holes = [ [ [round(v, 6) for v in inv(x, y)] for x, y in ring.coords ] for ring in merged_xy.interiors ]
    features.append({"type": "Feature",
                     "properties": {"minutes": m, "area_km2": round(area_km2, 2)},
                     "geometry": {"type": "Polygon", "coordinates": [ext] + holes}})
    summary[m] = {"area_km2": round(area_km2, 2)}
    print(f"level {m:2d} min: area {area_km2:.2f} km2, rings ext pts {len(ext)}", flush=True)

gj = {"type": "FeatureCollection",
      "properties": {"origin": "92 rue des Poissonniers, 75018 Paris",
                     "origin_coords": ORIGIN, "mode": "bicycle", "source": "OSRM bike profile / OpenStreetMap"},
      "features": features}
json.dump(gj, open("/workspace/isochrones_paris/isochrones_bike_92_rue_des_poissonniers.geojson", "w"))
json.dump(summary, open("/workspace/isochrones_paris/summary.json", "w"), indent=1)
print("DONE", summary)
