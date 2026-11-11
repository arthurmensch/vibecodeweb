import json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection

D = np.load("/workspace/isochrones_paris/durations.npy")
meta = json.load(open("/workspace/isochrones_paris/meta.json"))
gj = json.load(open("/workspace/isochrones_paris/isochrones_bike_92_rue_des_poissonniers.geojson"))
lats = np.array(meta["lats"]); lons = np.array(meta["lons"])
lon0, lat0 = meta["origin"]
mx = 111320.0 * math.cos(math.radians(lat0)); my = 110540.0
X, Y = np.meshgrid((lons - lon0) * mx / 1000.0, (lats - lat0) * my / 1000.0)  # km
Dm = D / 60.0

fig, ax = plt.subplots(figsize=(11, 10))
levels = [0, 5, 10, 15, 20, 25, 30, 35]
cf = ax.contourf(X, Y, Dm, levels=levels, cmap="YlGnBu", alpha=0.85)
cs = ax.contour(X, Y, Dm, levels=[5, 10, 15, 20, 25, 30], colors="black", linewidths=1.4)
ax.clabel(cs, fmt="%d min", fontsize=10)
colors = {5: "#08306b", 10: "#08589f", 15: "#2b8cbe", 20: "#4eb3d3", 25: "#7bccc4", 30: "#a8ddb5"}
for f in gj["features"]:
    m = f["properties"]["minutes"]
    ring = np.array(f["geometry"]["coordinates"][0])
    xy = np.column_stack([(ring[:, 0] - lon0) * mx / 1000.0, (ring[:, 1] - lat0) * my / 1000.0])
    ax.plot(xy[:, 0], xy[:, 1], color=colors[m], lw=2.2, label=f"{m} min ({f['properties']['area_km2']} km²)")
ax.plot(0, 0, marker="*", ms=22, color="red", mec="black", label="92 rue des Poissonniers")
ax.set_aspect("equal")
ax.set_xlabel("km est"); ax.set_ylabel("km nord")
ax.set_title("Isochrones vélo — 92 rue des Poissonniers, Paris 18e\n(durées OSRM profil vélo / OpenStreetMap, grille 41×41)")
ax.legend(loc="upper left", fontsize=9)
cb = fig.colorbar(cf, ax=ax, shrink=0.8); cb.set_label("minutes à vélo")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("/workspace/isochrones_paris/isochrones_bike_92_rue_des_poissonniers.png", dpi=170)
print("png saved")

html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Isochrones vélo — 92 rue des Poissonniers, Paris</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{height:100%;margin:0}#info{position:absolute;top:10px;left:60px;z-index:1000;background:#fff;padding:8px 12px;border-radius:6px;font:13px sans-serif;box-shadow:0 1px 5px rgba(0,0,0,.3)}</style>
</head><body><div id="map"></div><div id="info"><b>Isochrones vélo depuis 92 rue des Poissonniers, 75018 Paris</b><br>OSRM profil vélo / OpenStreetMap — 5 à 30 min</div>
<script>
var gj = __GEOJSON__;
var map = L.map('map').setView([48.892422, 2.352321], 12);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
var colors = {5:'#08306b',10:'#08589f',15:'#2b8cbe',20:'#4eb3d3',25:'#41ab5d',30:'#a8ddb5'};
var layer = L.geoJSON(gj,{style:function(f){var m=f.properties.minutes;return{color:colors[m]||'#333',weight:2,fillColor:colors[m]||'#ccc',fillOpacity:0.25};},
 onEachFeature:function(f,l){l.bindPopup(f.properties.minutes+' min — '+f.properties.area_km2+' km²');}}).addTo(map);
L.circleMarker([48.892422,2.352321],{radius:9,color:'red',fillColor:'red',fillOpacity:1}).addTo(map).bindPopup('<b>92 rue des Poissonniers, 75018 Paris</b>');
map.fitBounds(layer.getBounds());
</script></body></html>"""
html = html.replace("__GEOJSON__", json.dumps(gj))
open("/workspace/isochrones_paris/isochrones_bike_92_rue_des_poissonniers.html", "w").write(html)
print("html saved")

# ASCII map for chat
nlat, nlon = D.shape
rows, cols = 26, 52
chars = " .:-=+*#%@"
out = []
for r in range(rows):
    line = ""
    for c in range(cols):
        i = int((rows - 1 - r) / (rows - 1) * (nlat - 1))
        j = int(c / (cols - 1) * (nlon - 1))
        v = Dm[i, j]
        k = min(int(v / 30 * (len(chars) - 1)), len(chars) - 1)
        line += chars[k]
    out.append(line)
# mark origin
oi = int(round((1 - (lat0 - lats[0]) / (lats[-1] - lats[0])) * (rows - 1)))
oj = int(round((lon0 - lons[0]) / (lons[-1] - lons[0]) * (cols - 1)))
line = out[oi]; out[oi] = line[:oj] + "O" + line[oj+1:]
open("/workspace/isochrones_paris/ascii_map.txt", "w").write("\n".join(out))
print("\n".join(out))
