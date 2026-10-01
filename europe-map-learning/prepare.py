#!/usr/bin/env python3
"""Join real locality points to full-resolution, checksum-pinned ADM1 maps."""
import argparse
import csv
import gzip
import hashlib
import json
import math
import sys
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'europe-registry'))
from build import country_rows

COUNTRIES = {'AT': 'AUT', 'DE': 'DEU', 'CH': 'CHE'}
PROJECTION = Transformer.from_crs('EPSG:4326', 'EPSG:3035', always_xy=True).transform
INVERSE = Transformer.from_crs('EPSG:3035', 'EPSG:4326', always_xy=True).transform
SEED = 'map-pilot-v1'
BASE_RADIUS_M = 100.0  # Assumed uncertainty for this exercise, NOT measured GPS accuracy.


def digest(value):
    return hashlib.sha256(str(value).encode()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_jsonl(path, rows):
    data = ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(data.encode(), compresslevel=9, mtime=0))


def normalize(name):
    text = unicodedata.normalize('NFKD', name).casefold()
    return ''.join(c for c in text if c.isalnum())


def spatial_split(latitude, longitude):
    tile = f'{math.floor(latitude * 4)}:{math.floor(longitude * 4)}'
    bucket = int(digest(SEED + ':split:' + tile)[:8], 16) % 100
    return tile, 'train' if bucket < 70 else 'validation' if bucket < 85 else 'test'


def verdict(evidence):
    """Snapshot consistency oracle; no statement about current legal boundaries."""
    maps = evidence['map_regions']
    if len(maps) != 1 or evidence['registry_region'] != maps[0]:
        return 'REVIEW'
    if evidence['boundary_distance_m'] is None:
        return 'REVIEW'
    if evidence['boundary_distance_m'] <= evidence['assumed_radius_m']:
        return 'REVIEW'
    return 'MATCH' if evidence['claimed_region'] == maps[0] else 'CONFLICT'


def reward(action, truth):
    if action == truth:
        return 1.0
    if action == 'REVIEW':
        return -0.25
    return -2.0  # Penalize unsupported confident decisions more than abstention.


def map_evidence(point, polygons, tree, names):
    hits = sorted(int(i) for i in tree.query(point, predicate='intersects'))
    regions = sorted(names[i] for i in hits)
    # Distance in the metric Europe LAEA projection; not survey-grade/geodesic.
    distance = float(polygons[hits[0]].boundary.distance(point)) if len(hits) == 1 else None
    return regions, None if distance is None else round(distance, 3)


def crosswalk(features, admins, country):
    result = []
    for feature in features:
        p = feature['properties']
        if country == 'CH':
            matches = [r for r in admins if r['admin1_code'] == p['shapeISO'].split('-')[1]]
            method = 'verified_canton_code_equal'
        else:
            target = normalize(p['shapeName'])
            matches = [r for r in admins if target in {
                normalize(s) for s in [r['name'], r['asciiname']] + r['alternatenames'].split(',')
            }]
            method = 'unique_normalized_name_or_alias'
        if len(matches) != 1:
            raise ValueError(f'Non-unique ADM1 crosswalk: {country} {p}')
        r = matches[0]
        result.append(dict(country=country, map_iso=p['shapeISO'], map_name=p['shapeName'],
                           shape_id=p['shapeID'], geonames_id=r['id'], geonames_name=r['name'],
                           geonames_admin1_code=r['admin1_code'], method=method))
    if len({r['geonames_id'] for r in result}) != len(admins):
        raise ValueError('Crosswalk must cover every ADM1 exactly once')
    return result


def prepare(cache, per_region):
    sources = json.loads((ROOT / 'sources.json').read_text())
    audits, tasks, crosswalk_rows, preview_features = [], [], [], []
    counts = {}
    for country, iso3 in COUNTRIES.items():
        source = sources['boundaries'][country]
        path = cache / f'{iso3}.geojson'
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(source['url'], timeout=120) as response:
                path.write_bytes(response.read())
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f'Boundary checksum mismatch: {path}')
        registry = ROOT.parent / 'europe-registry'
        metadata_path = registry / 'countries' / country / 'metadata.json'
        if hashlib.sha256(metadata_path.read_bytes()).hexdigest() != sources['gazetteer'][country]['metadata_sha256']:
            raise ValueError('Registry metadata changed; deliberately refresh source manifest first')
        metadata = json.loads(metadata_path.read_text())
        for filename, info in metadata['files'].items():
            if hashlib.sha256((metadata_path.parent / filename).read_bytes()).hexdigest() != info['sha256']:
                raise ValueError(f'Registry part checksum mismatch: {country}/{filename}')
        rows = list(country_rows(registry, country))
        admins = [r for r in rows if r['feature_code'] == 'ADM1']
        features = json.loads(path.read_text())['features']
        links = crosswalk(features, admins, country)
        crosswalk_rows.extend(links)
        gn_to_iso = {r['geonames_id']: r['map_iso'] for r in links}
        names = [r['map_iso'] for r in links]
        polygons = [transform(PROJECTION, shape(f['geometry'])) for f in features]
        if not all(p.is_valid and not p.is_empty for p in polygons):
            raise ValueError('Invalid source polygon: manual review required; do not silently repair')
        tree = STRtree(polygons)
        for feature, poly in zip(features, polygons):
            props = dict(feature['properties'], snapshot_year=source['year'], source=source['provider'],
                         license=source['license'], preview_only=True, simplification_tolerance_m=300)
            preview_features.append(dict(type='Feature', properties=props,
                geometry=mapping(transform(INVERSE, poly.simplify(300, preserve_topology=True)))))
        grouped = defaultdict(list)
        for r in rows:
            if r['feature_class'] == 'P' and r['address_candidate'] == '1':
                grouped[r['state_id']].append(r)
        selected = []
        for state_id, group in sorted(grouped.items()):
            selected.extend(sorted(group, key=lambda r: digest(SEED + ':sample:' + r['id']))[:per_region])
        counts[country] = dict(eligible_localities=sum(map(len, grouped.values())), sampled=len(selected),
                               mapped_regions=len(links), boundary_year=source['year'])
        for r in selected:
            lat, lon = float(r['latitude']), float(r['longitude'])
            maps, distance = map_evidence(Point(*PROJECTION(lon, lat)), polygons, tree, names)
            tile, split = spatial_split(lat, lon)
            audit = dict(locality_id=r['id'], name=r['name'], country=country, latitude=lat,
                         longitude=lon, registry_region=gn_to_iso.get(r['state_id']),
                         registry_state_id=r['state_id'], map_regions=maps, boundary_distance_m=distance,
                         boundary_year=source['year'], tile=tile, split=split)
            natural = dict(audit, claimed_region=audit['registry_region'], assumed_radius_m=BASE_RADIUS_M)
            audit['snapshot_verdict'] = verdict(natural)
            audits.append(audit)
            variants = [('original_claim_assumed_100m', natural)]
            if len(maps) == 1:
                wrong = sorted(x for x in names if x != maps[0])
                wrong_claim = wrong[int(digest(r['id'])[:8], 16) % len(wrong)]
                variants.append(('synthetic_wrong_region', dict(natural, claimed_region=wrong_claim)))
                # Hypothetical location uncertainty reaches the real polygon boundary.
                variants.append(('synthetic_uncertainty_crosses_boundary', dict(natural,
                                assumed_radius_m=round(distance + 250, 3))))
            for variant, task in variants:
                task.update(task_id=r['id'] + ':' + variant, variant=variant,
                            radius_is_synthetic=True, gold=verdict(task))
                tasks.append(task)
        print(json.dumps({'country': country, **counts[country]}, ensure_ascii=False), flush=True)
    tasks.sort(key=lambda r: r['task_id'])
    audits.sort(key=lambda r: r['locality_id'])
    out = ROOT / 'data'
    out.mkdir(exist_ok=True)
    with (out / 'adm1_crosswalk.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(crosswalk_rows[0]))
        writer.writeheader()
        writer.writerows(crosswalk_rows)
    write_jsonl(out / 'audit.jsonl.gz', audits)
    for split in ['train', 'validation', 'test']:
        write_jsonl(out / f'{split}.jsonl.gz', [r for r in tasks if r['split'] == split])
    (out / 'map-preview.geojson').write_text(json.dumps(
        dict(type='FeatureCollection', features=preview_features), ensure_ascii=False, separators=(',', ':')) + '\n')
    split_counts = {s: dict(tasks=sum(r['split'] == s for r in tasks),
                    localities=sum(r['split'] == s for r in audits),
                    tiles=len({r['tile'] for r in audits if r['split'] == s}),
                    labels=dict(Counter(r['gold'] for r in tasks if r['split'] == s)))
                    for s in ['train', 'validation', 'test']}
    report = dict(countries=counts, localities=len(audits), tasks=len(tasks),
                  crosswalk_regions=len(crosswalk_rows), splits=split_counts,
                  snapshot_verdicts=dict(Counter(r['snapshot_verdict'] for r in audits)),
                  sampling='SHA256-ranked current populated-place candidates, up to requested count per source ADM1 (plus an unresolved-state bucket); not population representative',
                  per_region_limit=per_region, seed=SEED, tile_degrees=0.25,
                  boundary_distance_projection='EPSG:3035', assumed_default_uncertainty_m=BASE_RADIUS_M,
                  geometry_used_for_labels='full resolution; preview geometry NEVER used for labels',
                  split_limitation='Shared ADM1s across splits; adjacent tiles may be close. No held-out-country generalization claim.')
    write_json(out / 'preparation.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, default=ROOT / '.cache')
    p.add_argument('--per-region', type=int, default=100)
    args = p.parse_args()
    prepare(args.cache, args.per_region)
