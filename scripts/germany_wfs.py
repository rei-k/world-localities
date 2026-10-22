"""Acquire a reviewable, count-checked BKG DLM250 road candidate.

The ZIP contains exact original WFS JSON pages and their byte receipts. It is
locally packaged, not a ZIP published by BKG. DLM250 is generalized to 1:250000.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import http.client
import json
from pathlib import Path
import shutil
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import time
import xml.etree.ElementTree as ET
import zipfile

import western_europe_sources as shared

BASE = 'https://sgx.geodatenzentrum.de/wfs_dlm250'
TYPE = 'dlm250:objart_42003_l'
BKG_MAX_PAGE_BYTES = 16 * 1024 * 1024
TH_MAX_PAGE_BYTES = 32 * 1024 * 1024
TH_BASE = 'https://www.geoproxy.geoportal-th.de/geoproxy/services/INSPIREad_wfs'
TH_TYPES = ('AdminUnitName', 'ThoroughfareName', 'Address')


def read_http(url, maximum):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'WorldLocalities-DE/1.0'}), timeout=50) as response:
                if response.geturl() != url:
                    raise ValueError('Unexpected WFS redirect')
                data = response.read(maximum + 1)
                if len(data) > maximum:
                    raise ValueError('Oversized WFS response')
                return data
        except HTTPError as exc:
            if exc.code not in (400, 429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (URLError, TimeoutError, http.client.IncompleteRead):
            if attempt == 2:
                raise
        time.sleep(attempt + 1)


def request_url(base=BASE, feature_type=TYPE, **params):
    return base + '?' + urlencode(dict(SERVICE='WFS', VERSION='2.0.0', REQUEST='GetFeature', TYPENAMES=feature_type, **params))


def matched_count(base=BASE, feature_type=TYPE):
    url = request_url(base, feature_type, RESULTTYPE='hits')
    data = read_http(url, 1024 * 1024)
    root = ET.fromstring(data)
    if root.tag != '{http://www.opengis.net/wfs/2.0}FeatureCollection':
        raise ValueError('Expected a WFS count response')
    return int(root.attrib['numberMatched']), {'url': url, 'sha256': hashlib.sha256(data).hexdigest(),
                                              'bytes': len(data), 'response': data.decode('utf-8')}


def th_page_receipt(data, typename, offset, expected, page_size, url):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Unexpected DTD in WFS response')
    root = ET.fromstring(data)
    nodes = root.findall('{http://www.opengis.net/wfs/2.0}member/{http://inspire.ec.europa.eu/schemas/ad/4.0}' + typename)
    ids = [n.get('{http://www.opengis.net/gml/3.2}id') for n in nodes]
    expected_rows = min(page_size, expected - offset)
    if (root.tag != '{http://www.opengis.net/wfs/2.0}FeatureCollection'
            or int(root.get('numberReturned', '-1')) != expected_rows
            or len(nodes) != expected_rows or None in ids or len(ids) != len(set(ids))):
        raise ValueError('Thuringian page schema, count or identities differ')
    return {'member': f'{typename}/{offset:09}.xml.gz', 'type': typename, 'url': url,
            'offset': offset, 'original_bytes': len(data),
            'original_sha256': hashlib.sha256(data).hexdigest(), 'numberReturned': expected_rows,
            'provider_numberMatched': root.get('numberMatched'),
            'first_id': ids[0], 'last_id': ids[-1], 'timeStamp': root.get('timeStamp')}


def download_th_page(work, typename, offset, expected, page_size):
    url = request_url(TH_BASE, 'ad:' + typename, COUNT=str(page_size), STARTINDEX=str(offset))
    path = work / typename / f'{offset:09}.xml.gz'
    if path.exists():
        return th_page_receipt(gzip.decompress(path.read_bytes()), typename, offset, expected, page_size, url)
    partial = path.with_suffix('.partial')
    if partial.exists() or partial.is_symlink():
        raise ValueError('Prior Thuringian partial requires review')
    data = read_http(url, TH_MAX_PAGE_BYTES)
    receipt = th_page_receipt(data, typename, offset, expected, page_size, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with partial.open('xb') as stream:
            created = True
            stream.write(gzip.compress(data, compresslevel=6, mtime=0))
        path.hardlink_to(partial)
    finally:
        if created:
            partial.unlink(missing_ok=True)
    return receipt


def acquire_th_candidate(target, work, page_size=5000, workers=2, max_new_pages=None):
    target, work = Path(target), Path(work)
    partial = target.with_suffix('.partial')
    if target.exists() or target.is_symlink() or partial.exists() or partial.is_symlink():
        raise ValueError('Thuringian candidate output must be new')
    if not 1 <= page_size <= 5000 or not 1 <= workers <= 4:
        raise ValueError('Invalid public-service request budget')
    before = {t: matched_count(TH_BASE, 'ad:' + t) for t in TH_TYPES}
    work.mkdir(parents=True, exist_ok=True)
    jobs_spec = [(t, offset) for t in TH_TYPES for offset in range(0, before[t][0], page_size)]
    missing = sum(not (work / t / f'{offset:09}.xml.gz').exists() for t, offset in jobs_spec)
    if max_new_pages is not None:
        if missing > max_new_pages:
            raise ValueError('Required Thuringian pages exceed the explicit acquisition ceiling')
        existing = sum(p.stat().st_size for p in work.rglob('*.gz'))
        required_free = existing + 2 * missing * TH_MAX_PAGE_BYTES + 1024 * 1024 * 1024
        free = shutil.disk_usage(work).free
        if free < required_free:
            raise ValueError('Insufficient space for bounded Thuringian pages, packaging and 1 GiB reserve')
        print(json.dumps({'new_page_ceiling': max_new_pages, 'new_pages_required': missing,
                          'free_bytes': free, 'worst_case_required_free_bytes': required_free}), flush=True)
    receipts, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(download_th_page, work, t, offset, before[t][0], page_size)
                for t, offset in jobs_spec]
        for job in concurrent.futures.as_completed(jobs):
            try:
                r = job.result()
                receipts.append(r)
                print(json.dumps({'type': r['type'], 'offset': r['offset'], 'rows': r['numberReturned'],
                                  'pages_finished': len(receipts)}), flush=True)
            except Exception as exc:
                errors.append(str(exc))
    if errors:
        raise ValueError('Thuringian pages failed; verified caches can be reused: ' + '; '.join(errors))
    after = {t: matched_count(TH_BASE, 'ad:' + t) for t in TH_TYPES}
    for t in TH_TYPES:
        pages = sorted((r for r in receipts if r['type'] == t), key=lambda r: r['offset'])
        if (before[t][0] != after[t][0] or sum(r['numberReturned'] for r in pages) != before[t][0]
                or len({r['first_id'] for r in pages}) != len(pages)):
            raise ValueError('Thuringian counts changed or offsets were ignored')
    receipts.sort(key=lambda r: (TH_TYPES.index(r['type']), r['offset']))
    index = {'schema_version': 1, 'provider': 'TLBG Thuringia',
             'expected_rows': {t: before[t][0] for t in TH_TYPES},
             'before': {t: before[t][1] for t in TH_TYPES}, 'after': {t: after[t][1] for t in TH_TYPES},
             'pages': receipts, 'packaging': 'Lossless gzip of original HTTP XML bodies, in a locally constructed ZIP.',
             'pagination_caveat': 'Capabilities advertises paging false. STARTINDEX was tested and every retrieved identity must additionally pass the full audit uniqueness/count check. Feature responses report numberMatched after COUNT, so the separate hits requests are used for totals.',
             'atomic_snapshot_verified': False, 'national_completeness_verified': False, 'deliverability_in_scope': False}
    created = False
    try:
        with partial.open('xb') as out, zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED) as archive:
            created = True
            for r in receipts:
                data = (work / r['member']).read_bytes()
                if hashlib.sha256(gzip.decompress(data)).hexdigest() != r['original_sha256']:
                    raise ValueError('Thuringian cached bytes changed')
                archive.writestr(r['member'], data)
            archive.writestr('index.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
        target.hardlink_to(partial)
    finally:
        if created:
            partial.unlink(missing_ok=True)
    return {'path': target.name, 'bytes': target.stat().st_size, 'sha256': shared.sha256(target),
            'rows_by_type': index['expected_rows'], 'pages': len(receipts), 'national_completeness_verified': False}


def page_receipt(data, offset, expected, page_size, url):
    value = json.loads(data)
    expected_rows = min(page_size, expected - offset)
    if (value.get('type') != 'FeatureCollection' or value.get('numberMatched') != expected
            or value.get('numberReturned') != expected_rows or len(value['features']) != expected_rows):
        raise ValueError('WFS page limit, count or snapshot changed')
    ids = [f['properties']['objid'] for f in value['features']]
    if len(ids) != len(set(ids)) or ids != sorted(ids):
        raise ValueError('Page identity uniqueness or requested ordering differs')
    return {'member': f'pages/{offset:09}.json', 'url': url, 'offset': offset,
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'numberReturned': expected_rows, 'numberMatched': expected,
            'first_id': ids[0], 'last_id': ids[-1], 'timeStamp': value.get('timeStamp')}


def download_page(work, offset, expected, page_size):
    url = request_url(COUNT=str(page_size), STARTINDEX=str(offset), SORTBY='objid A', OUTPUTFORMAT='application/json')
    path = work / f'{offset:09}.json'
    if path.exists():
        return page_receipt(path.read_bytes(), offset, expected, page_size, url)
    partial = path.with_suffix('.partial')
    if partial.exists() or partial.is_symlink():
        raise ValueError('Prior partial requires review')
    data = read_http(url, BKG_MAX_PAGE_BYTES)
    receipt = page_receipt(data, offset, expected, page_size, url)
    created = False
    try:
        with partial.open('xb') as target:
            created = True
            target.write(data)
        path.hardlink_to(partial)
        return receipt
    finally:
        if created:
            partial.unlink(missing_ok=True)


def acquire_candidate(target, work, page_size=5000, workers=3, max_new_pages=None):
    target, work = Path(target), Path(work)
    if target.exists() or target.is_symlink() or target.with_suffix('.partial').exists():
        raise ValueError('Candidate output must be new')
    if not 1 <= page_size <= 5000 or not 1 <= workers <= 4:
        raise ValueError('Page size or concurrency outside public-service budget')
    work.mkdir(parents=True, exist_ok=True)
    expected, before = matched_count()
    receipts, errors = [], []
    offsets = list(range(0, expected, page_size))
    missing = sum(not (work / f'{offset:09}.json').exists() for offset in offsets)
    if max_new_pages is not None:
        if missing > max_new_pages:
            raise ValueError('Required new pages exceed the explicit acquisition ceiling')
        existing = sum(p.stat().st_size for p in work.glob('*.json'))
        required_free = existing + 2 * missing * BKG_MAX_PAGE_BYTES + 1024 * 1024 * 1024
        free = shutil.disk_usage(work).free
        if free < required_free:
            raise ValueError('Insufficient space for bounded new pages, packaging and 1 GiB reserve')
        print(json.dumps({'new_page_ceiling': max_new_pages, 'new_pages_required': missing,
                          'free_bytes': free, 'worst_case_required_free_bytes': required_free}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(download_page, work, offset, expected, page_size) for offset in offsets]
        for job in concurrent.futures.as_completed(jobs):
            try:
                receipt = job.result()
            except Exception as exc:
                errors.append(str(exc))
                continue
            receipts.append(receipt)
            print(json.dumps({'offset': receipt['offset'], 'rows': receipt['numberReturned'],
                              'pages_finished': len(receipts)}, sort_keys=True), flush=True)
    if errors:
        raise ValueError('Some WFS pages failed; verified page files can be reused: ' + '; '.join(errors))
    receipts.sort(key=lambda r: r['offset'])
    if sum(r['numberReturned'] for r in receipts) != expected:
        raise ValueError('Page-count sum differs')
    if any(a['last_id'] >= b['first_id'] for a, b in zip(receipts, receipts[1:])):
        raise ValueError('Page boundaries overlap or requested ordering is unstable')
    after_count, after = matched_count()
    if after_count != expected:
        raise ValueError('Provider count changed during acquisition')
    index = {'schema_version': 1, 'provider': 'BKG', 'feature_type': TYPE, 'expected_rows': expected,
             'before': before, 'after': after, 'pages': receipts,
             'counts_semantics': 'Complete retrieved published DLM250 road layer; not all physical roads.',
             'all_physical_roads_complete': False, 'deliverability_in_scope': False}
    partial = target.with_suffix('.partial')
    created = False
    try:
        with partial.open('xb') as output, zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            created = True
            for receipt in receipts:
                data = (work / f'{receipt["offset"]:09}.json').read_bytes()
                if hashlib.sha256(data).hexdigest() != receipt['sha256']:
                    raise ValueError('Downloaded page changed before packaging')
                archive.writestr(receipt['member'], data)
            archive.writestr('index.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
        target.hardlink_to(partial)
    finally:
        if created:
            partial.unlink(missing_ok=True)
    return {'path': target.name, 'bytes': target.stat().st_size, 'sha256': shared.sha256(target),
            'rows': expected, 'pages': len(receipts), 'national_completeness_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--product', choices=('dlm250-roads', 'th-addresses'), default='dlm250-roads')
    parser.add_argument('--max-new-pages', type=int, help='Reject acquisition beyond this many uncached pages and verify a worst-case disk-space budget')
    args = parser.parse_args()
    if args.product == 'th-addresses':
        result = acquire_th_candidate(args.output, args.work_dir, workers=args.workers, max_new_pages=args.max_new_pages)
    else:
        result = acquire_candidate(args.output, args.work_dir, workers=args.workers, max_new_pages=args.max_new_pages)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
