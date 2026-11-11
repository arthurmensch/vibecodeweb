# Paris bike isochrones — 92 rue des Poissonniers

Isochrones (reachable-area contours) by **bike** from **92 rue des Poissonniers, 75018 Paris**
(`48.892422, 2.352321`, official BAN geocode), at 5 / 10 / 15 / 20 / 25 / 30 minutes.

## Files

- `isochrones_bike_92_rue_des_poissonniers.png` — static map, 3080×2860 px, on a real basemap (CARTO Voyager / OSM raster tiles, zoom 14) with labeled 5–30 min contours, landmarks, scale bar, north arrow
- `isochrones_bike_92_rue_des_poissonniers.html` — interactive map, **fully self-contained** (basemap embedded as base64 image + SVG isochrone overlay; no external requests, no API key). Wheel = zoom, drag = pan. Open the file directly in any browser
- `isochrones_bike_92_rue_des_poissonniers.geojson` — isochrone polygons (`properties.minutes`, `properties.area_km2`)
- `summary.json` — area per travel time
- `compute_isochrones.py`, `render.py`, `render_basemap.py`, `build_selfcontained_html.py` — reproducible pipeline

## Method & data source

Travel times come from the **OSRM public demo server, bike profile, over OpenStreetMap data**
(`router.project-osrm.org/table/v1/bike`, one source → 41×41 destination grid covering ±7 km).
Note: Google Maps Platform APIs were not reachable from the generating session (no Maps API
key/connector), so Google Maps data could not be used; OSRM/OSM is the open equivalent.
OSRM bike speeds are optimistic (~20 km/h effective); Google Maps bike estimates are typically
30–50% longer.

## Reachable area

| Time | Area |
|---|---|
| 5 min | 3.0 km² |
| 10 min | 34.8 km² |
| 15 min | 113.5 km² |
| 20 min | 164.0 km² |
| 25 min | 193.0 km² |
| 30 min | 203.2 km² |

Spot checks (OSRM bike): Gare du Nord 3.1 km / 9 min, Châtelet 6.0 km / 17 min,
République 4.4 km / 13 min, La Défense 10.4 km / 17 min, Montparnasse 10.8 km / 24 min.
