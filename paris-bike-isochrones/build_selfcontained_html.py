import json, math, time, urllib.request, io, base64
import numpy as np
from PIL import Image
from skimage.measure import find_contours

BASE = "/workspace/isochrones_paris"
D = np.load(f"{BASE}/durations.npy")
meta = json.load(open(f"{BASE}/meta.json"))
gj = json.load(open(f"{BASE}/isochrones_bike_92_rue_des_poissonniers.geojson"))
lats = np.array(meta["lats"]); lons = np.array(meta["lons"])
lon0, lat0 = meta["origin"]
Dm = D / 60.0
Z = 14

allpts = [tuple(gj["properties"]["origin_coords"])]
for f in gj["features"]:
    for ring in f["geometry"]["coordinates"]:
        allpts += [tuple(p) for p in ring]
xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
mx = 111320.0 * math.cos(math.radians(lat0)); my = 110540.0
margin = 0.8
lon_min = min(xs) - margin * 1000 / mx; lon_max = max(xs) + margin * 1000 / mx
lat_min = min(ys) - margin * 1000 / my; lat_max = max(ys) + margin * 1000 / my

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
TILES = ["https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
         "https://tile.openstreetmap.org/{z}/{x}/{y}.png"]
canvas = Image.new("RGB", (W, H), (240, 240, 240))
ok = 0
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        for t in TILES:
            try:
                req = urllib.request.Request(t.format(z=Z, x=tx, y=ty),
                                             headers={"User-Agent": "vibe-isochrone-map/1.0 (one-off static map render)"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    img = Image.open(io.BytesIO(r.read())).convert("RGB")
                canvas.paste(img, ((tx - tx0) * 256, (ty - ty0) * 256))
                ok += 1
                break
            except Exception:
                pass
        time.sleep(0.12)
crop = canvas.crop((int(px0f) - tx0 * 256, int(py1f) - ty0 * 256, int(px1f) - tx0 * 256, int(py0f) - ty0 * 256))
CW, CH = crop.size
crop.save(f"{BASE}/basemap_crop.png")
print("basemap crop", crop.size, "tiles", ok)

def lonlat_to_px(lon, lat):
    x, y = deg2px(lon, lat, Z)
    return x - px0f, y - py1f

def grid_to_px(r, c):
    return lonlat_to_px(lons[int(round(c))] if False else lons[0] + c * (lons[1] - lons[0]),
                        lats[0] + r * (lats[1] - lats[0]))

LEVELS = [5, 10, 15, 20, 25, 30]
FILL = {5: "#ffffcc", 10: "#c7e9b4", 15: "#7fcdbb", 20: "#41b6c4", 25: "#1d91c0", 30: "#225ea8"}

svg_paths = []
for lv in LEVELS:
    segs = find_contours(Dm, lv)
    parts = []
    best = None
    for seg in segs:
        pts = [grid_to_px(r, c) for r, c in seg]
        if len(pts) < 2:
            continue
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
        parts.append(d)
        length = sum(math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1))
        if best is None or length > best[0]:
            best = (length, pts[len(pts)//2])
    if parts:
        svg_paths.append(f'<path d="{" ".join(parts)}" fill="{FILL[lv]}" fill-opacity="0.38" stroke="black" stroke-width="3" stroke-linejoin="round"/>')
        if best:
            svg_paths.append(f'<text x="{best[1][0]:.1f}" y="{best[1][1]:.1f}" font-size="34" font-weight="bold" fill="black" stroke="white" stroke-width="6" paint-order="stroke" text-anchor="middle">{lv} min</text>')

ox, oy = lonlat_to_px(lon0, lat0)
star = []
for k in range(10):
    ang = -math.pi / 2 + k * math.pi / 5
    rad = 26 if k % 2 == 0 else 11
    star.append(f"{ox + rad*math.cos(ang):.1f},{oy + rad*math.sin(ang):.1f}")
svg_paths.append(f'<polygon points="{" ".join(star)}" fill="red" stroke="black" stroke-width="3"/>')
svg_paths.append(f'<text x="{ox+34:.1f}" y="{oy-20:.1f}" font-size="30" font-weight="bold" fill="black" stroke="white" stroke-width="6" paint-order="stroke">92 rue des Poissonniers</text>')

landmarks = [("Gare du Nord", 2.3553, 48.8809), ("Barbès-Rochechouart", 2.3488, 48.8834),
             ("Sacré-Cœur", 2.3431, 48.8867), ("Opéra", 2.3317, 48.8706),
             ("Châtelet", 2.3470, 48.8584), ("République", 2.3637, 48.8676),
             ("Bastille", 2.3694, 48.8532), ("Montparnasse", 2.3219, 48.8422)]
for name, lon, lat in landmarks:
    x, y = lonlat_to_px(lon, lat)
    if 0 < x < CW and 0 < y < CH:
        svg_paths.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#222"/><text x="{x+10:.1f}" y="{y+8:.1f}" font-size="24" fill="#222" stroke="white" stroke-width="4" paint-order="stroke">{name}</text>')

sb = 2000.0 / mx  # 2 km in degrees lon
sx, sy = 0.03 * CW, CH - 0.05 * CH
sx2 = sx + (deg2px(lon_min + sb, lat_min, Z)[0] - px0f)
svg_paths.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{sx2:.1f}" y2="{sy:.1f}" stroke="black" stroke-width="7"/><text x="{(sx+sx2)/2:.1f}" y="{sy-14:.1f}" font-size="26" font-weight="bold" text-anchor="middle" stroke="white" stroke-width="5" paint-order="stroke">2 km</text>')
nx, ny = CW - 0.05 * CW, 0.06 * CH
svg_paths.append(f'<text x="{nx:.1f}" y="{ny:.1f}" font-size="40" font-weight="bold" text-anchor="middle">N</text><line x1="{nx:.1f}" y1="{ny+10:.1f}" x2="{nx:.1f}" y2="{ny+70:.1f}" stroke="black" stroke-width="6" marker-end="url(#arr)"/>')

b64 = base64.b64encode(open(f"{BASE}/basemap_crop.png", "rb").read()).decode()
legend = "".join(f'<span style="white-space:nowrap;margin-right:12px"><span style="display:inline-block;width:14px;height:14px;background:{FILL[lv]};border:1px solid #000;vertical-align:middle"></span> {lv} min</span>' for lv in LEVELS)

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Isochrones vélo — 92 rue des Poissonniers, Paris (hors-ligne)</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#eee}}
header{{padding:10px 16px;background:#fff;border-bottom:1px solid #ccc}}
h1{{font-size:18px;margin:0 0 6px}}
#legend{{font-size:14px}}
#viewport{{position:relative;width:100%;height:82vh;overflow:hidden;background:#ddd;cursor:grab}}
#stage{{position:absolute;left:0;top:0;transform-origin:0 0}}
#stage img{{display:block;width:{CW}px;height:{CH}px;user-select:none;-webkit-user-drag:none}}
#stage svg{{position:absolute;left:0;top:0;width:{CW}px;height:{CH}px}}
footer{{padding:6px 16px;font-size:12px;color:#555;background:#fff}}
</style></head><body>
<header><h1>Isochrones vélo depuis 92 rue des Poissonniers, 75018 Paris</h1>
<div id="legend">{legend} &nbsp;·&nbsp; molette = zoom, glisser = pan</div></header>
<div id="viewport"><div id="stage">
<img src="data:image/png;base64,{b64}" alt="fond de carte Paris">
<svg viewBox="0 0 {CW} {CH}" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="4" refY="2" orient="auto"><path d="M0,0 L4,4 L0,4 Z" fill="black" transform="rotate(90 2 2)"/></marker></defs>
{chr(10).join(svg_paths)}
</svg>
</div></div>
<footer>Fond de carte © OpenStreetMap contributors, © CARTO (tuiles z14 intégrées, aucune requête externe, aucune clé API). Temps de trajet: OSRM profil vélo / OpenStreetMap, grille 41×41.</footer>
<script>
var vp=document.getElementById('viewport'), st=document.getElementById('stage');
var s=Math.min(vp.clientWidth/{CW}, vp.clientHeight/{CH}), tx=0, ty=0;
function apply(){{st.style.transform='translate('+tx+'px,'+ty+'px) scale('+s+')';}}
apply();
var drag=null;
vp.addEventListener('wheel',function(e){{e.preventDefault();
  var f=e.deltaY<0?1.2:1/1.2, ns=Math.min(Math.max(s*f,Math.min(vp.clientWidth/{CW},vp.clientHeight/{CH})*0.5),8);
  var r=vp.getBoundingClientRect(), mxp=e.clientX-r.left, myp=e.clientY-r.top;
  tx=mxp-(mxp-tx)*ns/s; ty=myp-(myp-ty)*ns/s; s=ns; apply();}},{{passive:false}});
vp.addEventListener('mousedown',function(e){{drag={{x:e.clientX,y:e.clientY,tx:tx,ty:ty}};vp.style.cursor='grabbing';}});
window.addEventListener('mousemove',function(e){{if(!drag)return;tx=drag.tx+e.clientX-drag.x;ty=drag.ty+e.clientY-drag.y;apply();}});
window.addEventListener('mouseup',function(){{drag=null;vp.style.cursor='grab';}});
</script></body></html>"""
open(f"{BASE}/isochrones_bike_92_rue_des_poissonniers.html", "w").write(html)
print("html bytes:", len(html))
