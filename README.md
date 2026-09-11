# Demographics Dashboard

Interactive demographics dashboard built from the "Mistralers Demographics Data" Google Sheet
([spreadsheet](https://docs.google.com/spreadsheets/d/1Cdl9IOKeC9ZtIxeEsFkMML6xysrtgu5umdnst41v3xs/edit?gid=0#gid=0)).

## Features

- **Age distribution** – histogram with 5-year age buckets, plus mean/median age.
- **Gender split** – overall donut chart and per-department stacked bars.
- **Department groups** – Engineering & Infra, Science, Solutions (GTM), Business (GTM), Support, and Other (Product, Legal, Finance, HR, Marketing, Comms, Arthur Staff, Executive).
- Client-side filtering: click a department group card to filter every chart; click again to clear.

## Run

No build step or dependencies. The dashboard is a single static page.

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

(or just open `index.html` directly in a browser)

## Data

Data was exported from the source Google Sheet on Sep 11, 2025 and is embedded in
`data.js` (no personal names, emails, or exact birth dates are exposed — only
aggregated age buckets and gender counts per department).

## Files

- `index.html` – dashboard UI (Chart.js via CDN)
- `data.js` – aggregated demographics data
- `styles.css` – dashboard styling
