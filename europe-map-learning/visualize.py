#!/usr/bin/env python3
"""Build a standalone geographic map from actual boundary and point coordinates."""
import gzip
import html
import json
import math
from pathlib import Path

from prepare import ROOT
from predict import decide, load_model


def xy(lon, lat):
    return [(lon - 5) * 65, (1.2 - math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))) * 65 * 180 / math.pi - 150]


def main():
    geometry = json.loads((ROOT / 'data/map-preview.geojson').read_text())
    with gzip.open(ROOT / 'data/audit.jsonl.gz', 'rt') as f:
        audit = list(map(json.loads, f))
    model = load_model()
    points = []
    for row in audit:
        e = dict(row, claimed_region=row['registry_region'], assumed_radius_m=100)
        d = decide(model, e)
        display = {k: row[k] for k in ['locality_id', 'name', 'country', 'latitude', 'longitude',
                   'registry_region', 'map_regions', 'boundary_distance_m', 'boundary_year', 'split', 'snapshot_verdict']}
        points.append(dict(display, x=round(xy(row['longitude'], row['latitude'])[0], 2),
                           y=round(xy(row['longitude'], row['latitude'])[1], 2),
                           learned_prediction=d['learned_prediction'], guarded_prediction=d['guarded_prediction']))
    paths = []
    for f in geometry['features']:
        coords = f['geometry']['coordinates']
        polys = [coords] if f['geometry']['type'] == 'Polygon' else coords
        path = ''.join('M' + 'L'.join(','.join(f'{v:.2f}' for v in xy(*coord)) for coord in ring) + 'Z'
                       for poly in polys for ring in poly)
        p = f['properties']
        paths.append(f'<path d="{path}" fill-rule="evenodd" class="region" data-country="{p["shapeGroup"]}" '
                     f'><title>{html.escape(p["shapeISO"] + " · " + p["shapeName"] + " · " + p["snapshot_year"])}</title></path>')
    metrics = json.loads((ROOT / 'results/metrics.json').read_text())
    prep = json.loads((ROOT / 'data/preparation.json').read_text())
    payload = json.dumps(points, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    template = (ROOT / 'map-template.html').read_text()
    page = template.replace('__PATHS__', ''.join(paths)).replace('__POINTS__', payload)
    page = page.replace('__COUNT__', f'{len(points):,}').replace('__TASKS__', f'{prep["tasks"]:,}')
    page = page.replace('__ACCURACY__', f'{metrics["selected_test"]["accuracy"] * 100:.2f}%')
    (ROOT / 'map.html').write_text(page)
    # Export a lightweight SVG as an immediately viewable geographic overview.
    circles = ''.join(f'<circle cx="{r["x"]}" cy="{r["y"]}" r="{2.5 if r["snapshot_verdict"] == "REVIEW" else 1.2}" '
                      f'fill="{"#c15327" if r["snapshot_verdict"] == "REVIEW" else "#247c78"}" opacity=".75"/>' for r in points)
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -150 850 1200"><style>.region{fill:#e4ecee;stroke:#718b96;stroke-width:.6} text{font-family:sans-serif}</style>'
    svg += '<rect x="0" y="-150" width="850" height="1200" fill="#f7faf9"/>'
    svg += '<text x="24" y="-100" font-size="30" fill="#183647">Europe · map-linked learning</text>'
    svg += f'<text x="24" y="-65" font-size="17" fill="#476571">{len(points):,} real places · 51 ADM1 regions · AT / DE / CH</text>'
    svg += ''.join(paths) + circles
    svg += '<text x="24" y="995" font-size="13">GeoNames · geoBoundaries · BEV Austria · BKG Germany · swisstopo</text>'
    svg += '<text x="24" y="1020" font-size="13">Boundary snapshots: 2017 / 2021 / 2022 · orange: needs review · display simplified</text></svg>'
    (ROOT / 'results/map-overview.svg').write_text(svg)
    print(json.dumps(dict(html_bytes=len(page.encode()), points=len(points), regions=len(paths))))


if __name__ == '__main__':
    main()
