"""Pinned German administrative, street and numbered-location observations.

Read original state deliveries, explicitly labelled mirrors and ALKIS-derived
tables separately. Published-source coverage is not physical-world completeness.
Python standard library only; no expansion of house-number ranges.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sqlite3
import struct
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile

import western_europe_sources as shared
import germany_inspire

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'releases/hierarchy/western-europe/germany/sources.json'
STATES = {'01': 'SH', '02': 'HH', '03': 'NI', '04': 'HB', '05': 'NW',
          '06': 'HE', '07': 'RP', '08': 'BW', '09': 'BY', '10': 'SL',
          '11': 'BE', '12': 'BB', '13': 'MV', '14': 'SN', '15': 'ST', '16': 'TH'}
FORMATS = {'gv100_zip', 'hk_csv_zip', 'derived_csv_zip', 'bremen_dbf_zip',
           'hamburg_gml_zip', 'gazetteer_geojson_gzip', 'bkg_roads_geojson_zip', 'inspire_th_zip'}
PROVENANCE = {'official_direct', 'official_archive', 'official_mirror', 'third_party_derived'}
HK_FIELDS = ['nba', 'oid', 'qua', 'landschl', 'land', 'regbezschl', 'regbez',
             'kreisschl', 'kreis', 'gmdschl', 'gmd', 'ottschl', 'ott',
             'strschl', 'str', 'hnr', 'adz', 'zone', 'ostwert', 'nordwert',
             'postplz', 'postonm', 'postonmzus', 'postott', 'poststr', 'aud']
GV_KINDS = {'10': 'state', '20': 'regional_division', '30': 'planning_region',
            '40': 'county', '50': 'municipal_association', '60': 'municipality'}
FORMAT_KINDS = {'gv100_zip': set(GV_KINDS.values()),
                'hk_csv_zip': {'address'}, 'derived_csv_zip': {'address'},
                'bremen_dbf_zip': {'address'}, 'hamburg_gml_zip': {'address'},
                'gazetteer_geojson_gzip': {'street'},
                'bkg_roads_geojson_zip': {'road_segment'},
                'inspire_th_zip': {'address', 'street', 'administrative_name_reference'}}
IMPLEMENTATION_SHA256 = shared.sha256(__file__)
IMPLEMENTATION_FILES = {str(Path(p).relative_to(ROOT)): shared.sha256(p) for p in
                        (__file__, germany_inspire.__file__, shared.__file__)}


def load_manifest(path=DEFAULT_MANIFEST):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if (value.get('schema_version') != 1 or value.get('country') != 'DE'
            or value.get('region') != 'western-europe'
            or value.get('national_completeness_verified') is not False
            or value.get('deliverability_in_scope') is not False):
        raise ValueError('Invalid German source manifest or scope')
    if sorted(value['states']) != sorted(STATES.values()):
        raise ValueError('The ledger must include all 16 states')
    if not value['sources']:
        raise ValueError('Empty source manifest')
    for field in ('id', 'path'):
        pins = value['sources'] + value.get('evidence', [])
        if len({p[field] for p in pins}) != len(pins):
            raise ValueError('Duplicate pin ' + field)
    for pin in value['sources'] + value.get('evidence', []):
        shared.source_path(Path('.'), pin)
        if (pin.get('country') != 'DE' or type(pin['bytes']) is not int or pin['bytes'] <= 0
                or not re.fullmatch('[0-9a-f]{64}', pin['sha256'])):
            raise ValueError('Invalid source byte pin')
    for source in value['sources']:
        if (source['format'] not in FORMATS or source['provenance'] not in PROVENANCE
                or not source['states'] or not set(source['states']) <= set(STATES.values())):
            raise ValueError('Invalid source format or provenance')
        if not source.get('licence') or not source.get('licence_url'):
            raise ValueError('Missing source terms')
    return value


def selected_sources(manifest, state=None, kind=None):
    if state is not None and state not in STATES.values():
        raise ValueError('Unknown German state')
    return [s for s in manifest['sources'] if (state is None or state in s['states'])
            and (kind is None or kind in FORMAT_KINDS[s['format']])]


def obs(source, member, ordinal, raw, kind, identity, **values):
    return shared.observation(source, member, ordinal, raw, kind, identity,
                              provenance=source['provenance'], **values)


def code(value, width):
    # Never repair an integer-parsed or unknown provider code by silently padding.
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{' + str(width) + '}', value):
        raise ValueError('Invalid or unpadded administrative code: ' + repr(value))
    return value


def coordinates(x, y, crs):
    for v in (x, y):
        if not isinstance(v, str) or not math.isfinite(float(v)):
            raise ValueError('Non-finite source coordinate')
    return {'x': x, 'y': y, 'crs': crs}


def hk_record(source, member, ordinal, raw):
    normalized = dict(raw)
    if 'kreissch' in raw:
        if 'kreisschl' in raw:
            raise ValueError('Ambiguous Hessian county field')
        normalized['kreisschl'] = raw['kreissch']
    shared.require(normalized, *HK_FIELDS[1:20])
    land = code(raw['landschl'], 2)
    state = STATES[land]
    if state not in source['states']:
        raise ValueError('Source belongs to another state')
    ags = land + code(raw['regbezschl'], 1) + code(normalized['kreisschl'], 2) + code(raw['gmdschl'], 3)
    identity = raw['oid']
    if not re.fullmatch('DE[A-Za-z0-9]{14}', identity):
        raise ValueError('Invalid HK registry identifier')
    if raw['zone'] not in ('32', '33'):
        raise ValueError('Unknown UTM zone')
    # Berlin HK uses the Gemeinde position for the 12 boroughs. Keep that
    # publisher code and expose the city-state municipality separately.
    municipality = '11000000' if state == 'BE' else ags
    return obs(source, member, ordinal, raw, 'address', identity, state=state,
               municipality_code=municipality, source_administrative_code=ags,
               administrative_code_rule='Berlin_city_state' if state == 'BE' else 'HK_AGS_components',
               municipality_name=raw['land'] if state == 'BE' else raw['gmd'],
               source_administrative_name=raw['gmd'], locality_name=raw['ott'],
               street_code=raw['strschl'], street=raw['str'],
               number=raw['hnr'], number_addition=raw['adz'],
               postcode=raw.get('postplz', ''), quality=raw['qua'],
               source_date=raw.get('aud', ''),
               coordinates=coordinates(raw['ostwert'], raw['nordwert'], 'EPSG:258' + raw['zone']),
               **({'borough_code': ags, 'borough_name': raw['gmd']} if state == 'BE' else {}))


def csv_records(source, archive):
    member = source['member']
    with archive.open(member) as binary, io.TextIOWrapper(binary, encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, delimiter=source['delimiter'])
        if source['header']:
            fields = next(reader)
            if len(fields) != len(set(fields)):
                raise ValueError('Duplicate CSV header')
        else:
            fields = source['columns']
        if len(fields) != len(set(fields)):
            raise ValueError('Duplicate normalized CSV header')
        for ordinal, cells in enumerate(reader, 1):
            if len(cells) != len(fields):
                raise ValueError(f'CSV width changed: {member}:{ordinal}')
            raw = dict(zip(fields, cells))
            if source['format'] == 'hk_csv_zip':
                yield hk_record(source, member, ordinal, raw)
                continue
            mapping = source['mapping']
            values = {name: raw[field] for name, field in mapping.items()}
            state = source['states'][0]
            values.update(state=state, municipality_code=None,
                          coordinates=coordinates(raw[source['x']], raw[source['y']], source['crs']))
            identity = raw.get(source.get('identity_field', '')) or None
            if state == 'SL':
                # The mirror retains original ALKIS codes and coordinates as
                # well as its transformed WGS84 columns. Preserve both.
                ags = code(raw['LAN'], 2) + code(raw['RBZ'], 1) + code(raw['KRS'], 2) + code(raw['GMD'], 3)
                values.update(municipality_code=ags, source_administrative_code=ags,
                              original_coordinates=coordinates(raw['XCOORD'], raw['YCOORD'], 'EPSG:4647'))
            yield obs(source, member, ordinal, raw, 'address', identity, **values)


def gv_record(source, member, ordinal, line):
    if len(line) != 220 or line[:2] not in GV_KINDS:
        raise ValueError('Unexpected GV100 record type or width')
    stamp = line[2:10]
    reference_date = date.fromisoformat(stamp[:4] + '-' + stamp[4:6] + '-' + stamp[6:8]).isoformat()
    typ, ags, association = line[:2], line[10:18], line[18:22]
    kind, state = GV_KINDS[typ], STATES[code(ags[:2], 2)]
    widths = {'10': 2, '20': 3, '30': 4, '40': 5, '50': 5, '60': 8}
    unit_code = code(ags[:widths[typ]], widths[typ])
    if typ == '50':
        unit_code += code(association, 4)
    unit_id = typ + ':' + unit_code
    values = dict(state=state, record_type=typ, name=line[22:72].rstrip(),
                  administrative_seat=line[72:122].rstrip(), reference_date=reference_date,
                  unit_code=unit_code, text_code=line[122:124],
                  municipality_code=ags if typ == '60' else None,
                  raw_ags_field=ags, raw_association_field=association)
    if typ == '60':
        code(ags, 8)
        values.update(ars=ags[:5] + code(association, 4) + ags[5:],
                      is_municipality_free_area=line[122:124] in ('65', '66'),
                      administrative_seat_postcode=line[165:170])
    return obs(source, member, ordinal, {'line': line}, kind, unit_id, **values)


def dbf_rows(stream):
    header = stream.read(32)
    if len(header) != 32:
        raise ValueError('Truncated DBF header')
    count, offset, width = struct.unpack_from('<IHH', header, 4)
    if offset < 33 or (offset - 33) % 32:
        raise ValueError('Invalid DBF header length')
    descriptors = stream.read(offset - 32)
    if len(descriptors) != offset - 32 or descriptors[-1:] != b'\r':
        raise ValueError('Truncated DBF fields')
    fields = [(descriptors[i:i + 11].split(b'\0')[0].decode('ascii'), descriptors[i + 16])
              for i in range(0, offset - 33, 32)]
    if width != 1 + sum(n for _, n in fields) or len(fields) != len({f for f, _ in fields}):
        raise ValueError('Invalid DBF record width or repeated fields')
    for ordinal in range(1, count + 1):
        b = stream.read(width)
        if len(b) != width or b[:1] != b' ':
            raise ValueError('Truncated or deleted DBF row requires review')
        cursor, raw = 1, {}
        for field, length in fields:
            raw[field] = b[cursor:cursor + length].decode('utf-8').strip()
            cursor += length
        yield ordinal, raw
    if stream.read() not in (b'', b'\x1a'):
        raise ValueError('Unexpected trailing DBF records')


def bremen_records(source, archive):
    with archive.open(source['inner_member']) as stream, tempfile.SpooledTemporaryFile(max_size=32 * 1024 * 1024) as temp:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            temp.write(block)
        temp.seek(0)
        with zipfile.ZipFile(temp) as inner:
            member = source['member']
            with inner.open(member) as dbf, inner.open(source['point_member']) as shp:
                header = shp.read(100)
                if len(header) != 100 or struct.unpack('>I', header[:4])[0] != 9994 or struct.unpack('<I', header[32:36])[0] != 1:
                    raise ValueError('Expected a Point shapefile')
                for ordinal, raw in dbf_rows(dbf):
                    h = shp.read(8)
                    if len(h) != 8 or struct.unpack('>2I', h) != (ordinal, 10):
                        raise ValueError('SHP and DBF ordinals differ')
                    b = shp.read(20)
                    if len(b) != 20 or struct.unpack('<I', b[:4])[0] != 1:
                        raise ValueError('Missing address Point')
                    x, y = struct.unpack('<2d', b[4:])
                    ags = code(raw['lan'], 2) + code(raw['rbz'], 1) + code(raw['krs'], 2) + code(raw['gmd'], 3)
                    if raw['lan'] != '04' or raw['crs'] != 'ETRS89_UTM32':
                        raise ValueError('Unexpected Bremen state or CRS')
                    yield obs(source, source['inner_member'] + '!' + member, ordinal, raw, 'address', raw['uuid'],
                              state='HB', municipality_code=ags, source_administrative_code=ags,
                              municipality_name=raw['onm'], street_code=raw['sss'], street=raw['stn'],
                              number=raw['hnr'], number_addition=raw['adz'], postcode=raw['plz'],
                              quality=raw['qua'], source_end=raw['ende'],
                              coordinates=coordinates(repr(x), repr(y), 'EPSG:25832'))
                if shp.read():
                    raise ValueError('Unexpected extra SHP points')
            if inner.testzip() is not None:
                raise ValueError('Nested ZIP CRC mismatch')


class XMLGuard:
    def __init__(self, stream):
        self.stream, self.tail = stream, b''

    def read(self, size=-1):
        b = self.stream.read(size)
        combined = (self.tail + b).upper()
        if b'<!DOCTYPE' in combined or b'<!ENTITY' in combined:
            raise ValueError('DTD/entity declarations are not supported')
        self.tail = combined[-16:]
        return b


def hamburg_records(source, archive):
    fme, gml = '{http://www.safe.com/gml/fme}', '{http://www.opengis.net/gml}'
    with archive.open(source['member']) as stream:
        stack, ordinal = [], 0
        for event, node in ET.iterparse(XMLGuard(stream), events=('start', 'end')):
            if event == 'start':
                stack.append(node)
                continue
            if node.tag == fme + 'adressen':
                ordinal += 1
                raw = {c.tag[len(fme):]: c.text or '' for c in node if c.tag.startswith(fme)}
                points = node.findall('.//' + gml + 'Point')
                if len(points) != 1 or points[0].get('srsName') != 'EPSG:25832':
                    raise ValueError('Unexpected Hamburg address geometry')
                pos = points[0].find(gml + 'pos').text.split()
                if len(pos) != 2:
                    raise ValueError('Expected two-dimensional position')
                yield obs(source, source['member'], ordinal, raw, 'address', node.get(gml + 'id'),
                          state='HH', municipality_code='02000000', municipality_name='Hamburg',
                          street_code=raw['strasse'], street=raw['strname'], number=raw['hausnr'],
                          number_addition=raw['zusatz'], postcode=raw['plz'],
                          coordinates=coordinates(*pos, 'EPSG:25832'))
                if len(stack) > 1:
                    stack[-2].remove(node)
            # Remove each completed featureMember; otherwise empty members
            # accumulate on the root of a state-wide GML file.
            if node.tag == fme + 'featureMember' and len(stack) > 1:
                stack[-2].remove(node)
            stack.pop()


def json_features(stream, metadata):
    """Incremental, strict root-object/FeatureCollection reader, bounded per feature."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Repeated JSON object field')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('Non-finite JSON constant: ' + value)

    decoder = json.JSONDecoder(object_pairs_hook=pairs, parse_constant=constant)
    buffer, eof = '', False

    def fill():
        nonlocal buffer, eof
        b = stream.read(65536)
        eof = not b
        buffer += b

    def space():
        nonlocal buffer
        while True:
            buffer = buffer.lstrip()
            if buffer or eof:
                return
            fill()

    def char(expected):
        nonlocal buffer
        space()
        if not buffer.startswith(expected):
            raise ValueError('Malformed GeoJSON punctuation')
        buffer = buffer[len(expected):]

    def value():
        nonlocal buffer
        while True:
            space()
            try:
                v, stop = decoder.raw_decode(buffer)
                # raw_decode can accept only the prefix of a number at a
                # buffer boundary (123 / 123e+4). Wait for its delimiter.
                if (stop == len(buffer) or buffer[stop] not in ' \t\r\n,]}:') and not eof:
                    fill()
                    continue
                buffer = buffer[stop:]
                return v
            except json.JSONDecodeError as exc:
                if eof or len(buffer) > 32 * 1024 * 1024:
                    raise ValueError('Truncated or oversized GeoJSON value') from exc
                fill()

    char('{')
    keys = set()
    while True:
        key = value()
        if not isinstance(key, str) or key in keys:
            raise ValueError('Duplicate or invalid GeoJSON root key')
        keys.add(key)
        char(':')
        if key == 'features':
            char('[')
            space()
            if not buffer.startswith(']'):
                while True:
                    feature = value()
                    if not isinstance(feature, dict) or feature.get('type') != 'Feature':
                        raise ValueError('Expected GeoJSON Feature')
                    yield feature
                    space()
                    if buffer.startswith(']'):
                        break
                    char(',')
            char(']')
        else:
            metadata[key] = value()
        space()
        if buffer.startswith('}'):
            char('}')
            break
        char(',')
    space()
    if buffer or stream.read(1) or 'features' not in keys or metadata.get('type') != 'FeatureCollection':
        raise ValueError('Trailing data or invalid FeatureCollection')


def bkg_records(source, archive, metadata):
    index = json.loads(archive.read('index.json'))
    if index['feature_type'] != 'dlm250:objart_42003_l' or index['expected_rows'] != source['expected_rows']:
        raise ValueError('BKG index and manifest differ')
    pages, count = [], 0
    if set(archive.namelist()) != {'index.json'} | {p['member'] for p in index['pages']}:
        raise ValueError('Unexpected or missing BKG pages')
    for page in index['pages']:
        data = archive.read(page['member'])
        if len(data) != page['bytes'] or hashlib.sha256(data).hexdigest() != page['sha256']:
            raise ValueError('Original BKG response page differs')
        receipt, returned = {}, 0
        for ordinal, feature in enumerate(json_features(io.StringIO(data.decode('utf-8')), receipt), 1):
            raw = feature['properties']
            if (raw['land'] != 'DE' or raw['objart'] != '42003' or raw['modellart'] != 'DLM250'
                    or feature['geometry']['type'] not in ('LineString', 'MultiLineString')):
                raise ValueError('Unexpected BKG road object')
            returned += 1
            yield obs(source, page['member'], ordinal, raw, 'road_segment', raw['objid'],
                      state='DE', name=raw.get('znm'), road_reference=raw.get('bez'),
                      geometry_reference={'member': page['member'], 'ordinal': ordinal,
                                          'type': feature['geometry']['type'], 'crs': 'EPSG:25832',
                                          'bbox': feature.get('bbox')},
                      map_scale_denominator=250000, all_physical_roads_complete=False)
        if (returned != page['numberReturned'] or receipt.get('numberReturned') != returned
                or receipt.get('numberMatched') != source['expected_rows']
                or receipt.get('crs') != {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:EPSG::25832'}}):
            raise ValueError('BKG page CRS or declared counts differ')
        count += returned
        pages.append({'member': page['member'], 'rows': returned})
    if count != source['expected_rows']:
        raise ValueError('BKG page counts do not cover the complete published layer')
    metadata.update(feature_counts={'road_segment': count}, pages=pages, expected_rows=source['expected_rows'])


def records(source, root, metadata=None):
    path = shared.source_path(root, source)
    if source['format'] == 'gazetteer_geojson_gzip':
        import gzip
        receipt = {} if metadata is None else metadata
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            for ordinal, feature in enumerate(json_features(stream, receipt), 1):
                raw = feature['properties']
                state = STATES[code(raw['landschluessel'], 2)]
                if state not in source['states']:
                    raise ValueError('Gazetteer state differs')
                yield obs(source, source['member'], ordinal, raw, 'street', str(feature['id']),
                          state=state, street=raw['strassenname'], street_code=raw['strassenschluessel'],
                          municipality_code='11000000' if state == 'BE' else raw['gemeindeschluessel'],
                          source_administrative_code=raw['gemeindeschluessel'],
                          geometry_reference={'member': source['member'], 'ordinal': ordinal,
                                              'type': feature['geometry']['type']})
        return
    with zipfile.ZipFile(path) as archive:
        if source['format'] in ('hk_csv_zip', 'derived_csv_zip'):
            yield from csv_records(source, archive)
        elif source['format'] == 'gv100_zip':
            with archive.open(source['member']) as binary, io.TextIOWrapper(binary, encoding='utf-8-sig', newline='') as stream:
                for ordinal, line in enumerate(stream, 1):
                    yield gv_record(source, source['member'], ordinal, line.rstrip('\r\n'))
        elif source['format'] == 'bremen_dbf_zip':
            yield from bremen_records(source, archive)
        elif source['format'] == 'hamburg_gml_zip':
            yield from hamburg_records(source, archive)
        elif source['format'] == 'bkg_roads_geojson_zip':
            yield from bkg_records(source, archive, {} if metadata is None else metadata)
        elif source['format'] == 'inspire_th_zip':
            yield from germany_inspire.records(source, archive, {} if metadata is None else metadata, obs, coordinates, XMLGuard)
        else:
            raise ValueError('Unsupported German source')


def administrative_reference(source, root):
    rows = list(records(source, root))
    index = {r['source_id']: r for r in rows}
    if len(rows) != len(index):
        raise ValueError('Duplicate administrative identifiers')
    missing = []
    for row in rows:
        typ, c, land = row['record_type'], row['unit_code'], row['raw_ags_field'][:2]
        if typ == '10':
            parent = None
        elif typ == '20':
            parent = '10:' + land
        elif typ == '30':
            parent = '20:' + c[:3]
        elif typ == '40':
            parent = ('30:' + c[:4] if '30:' + c[:4] in index else
                      '20:' + c[:3] if '20:' + c[:3] in index else '10:' + land)
        elif typ == '50':
            # These two GV placeholder associations name the joint DE/LU
            # territory and MV coastal waters, outside an enumerated county.
            parent = ('10:' + land if c in ('070009999', '130009999') else '40:' + c[:5])
        else:
            parent = '50:' + c[:5] + row['raw_association_field']
        row['parent_id'] = parent
        row['parent_link_rule'] = ('GV100_special_state_bucket' if typ == '50' and c in ('070009999', '130009999')
                                   else 'GV100_code_layout')
        if parent is not None and parent not in index:
            missing.append({'id': row['source_id'], 'parent_id': parent})
    return rows, {'reference_date': sorted({r['reference_date'] for r in rows}),
                  'record_type_counts': dict(Counter(r['record_type'] for r in rows)),
                  'municipalities': sum(r['kind'] == 'municipality' and not r['is_municipality_free_area'] for r in rows),
                  'municipality_free_areas': sum(r.get('is_municipality_free_area', False) for r in rows),
                  'unresolved_parent_references': missing,
                  'municipalities_by_state': dict(Counter(r['state'] for r in rows if r['kind'] == 'municipality' and not r['is_municipality_free_area']))}


def analyze(source, root, municipalities, temp_dir=None):
    path = shared.verify_pin(source, root)
    counts, missing, municipality_counts, dates, qualities, missing_refs, municipality_addresses, municipality_streets = (Counter() for _ in range(8))
    digest, metadata, streets = hashlib.sha256(), {}, set()
    with tempfile.TemporaryDirectory(prefix='germany-audit-', dir=temp_dir) as work:
        db = sqlite3.connect(str(Path(work) / 'identities.sqlite'))
        db.executescript('PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; CREATE TABLE ids (id TEXT PRIMARY KEY) WITHOUT ROWID;')
        for row in records(source, root, metadata):
            digest.update((shared.canonical(row) + '\n').encode('utf-8'))
            counts[row['kind']] += 1
            state = row['state']
            counts['state:' + state] += 1
            if row['source_id'] is not None:
                cur = db.execute('INSERT OR IGNORE INTO ids VALUES (?)', (row['source_id'],))
                if not cur.rowcount:
                    counts['repeated_source_id_observations'] += 1
            else:
                counts['without_registry_id'] += 1
            if row['kind'] not in ('address', 'street'):
                continue
            missing_refs.update(row.get('missing_references', []))
            ags = row.get('municipality_code')
            if ags:
                municipality_counts[ags] += 1
                (municipality_addresses if row['kind'] == 'address' else municipality_streets)[ags] += 1
                if ags not in municipalities:
                    missing[ags] += 1
            else:
                counts['without_municipality_code'] += 1
            if row['kind'] == 'address':
                if row.get('number') and row['number'] != '0':
                    counts['numbered_address_observations'] += 1
                else:
                    counts['without_assigned_number'] += 1
                for key in ('street', 'number_addition', 'postcode'):
                    if not row.get(key):
                        counts['without_' + key] += 1
                source_place = row.get('municipality_name') or row.get('locality_name') or ''
                streets.add((state, ags, source_place, row.get('street_code', ''), row['street']))
                dates[row.get('source_date', '') or '(not provided per row)'] += 1
                qualities[row.get('quality', '') or '(not provided)'] += 1
        counts['unique_source_ids'] = db.execute('SELECT count(*) FROM ids').fetchone()[0]
        db.close()
    if source['format'] == 'gazetteer_geojson_gzip':
        import gzip
        kind = 'street'
        if metadata.get('numberReturned') != counts[kind] or metadata.get('numberMatched') != counts[kind]:
            raise ValueError('Bulk response is incomplete')
        expected_crs = 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
        if metadata.get('crs') != expected_crs:
            raise ValueError('Unexpected bulk-response CRS')
        raw_digest, raw_bytes = hashlib.sha256(), 0
        with gzip.open(path, 'rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                raw_digest.update(block)
                raw_bytes += len(block)
        if (raw_bytes != source['original_response_bytes']
                or raw_digest.hexdigest() != source['original_response_sha256']):
            raise ValueError('Original HTTP-response bytes differ after decompression')
        metadata = {k: metadata[k] for k in ('numberMatched', 'numberReturned', 'timeStamp', 'crs')}
    else:
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError('ZIP CRC mismatch')
    if source['format'] in ('bkg_roads_geojson_zip', 'inspire_th_zip') and counts['repeated_source_id_observations']:
        raise ValueError('Repeated identifiers cannot establish full WFS layer acquisition')
    result = {'id': source['id'], 'source_sha256': source['sha256'], 'provenance': source['provenance'],
              'canonical_rows_sha256': digest.hexdigest(), 'counts': dict(counts),
              'address_derived_street_keys': len(streets), 'municipality_observation_counts': dict(sorted(municipality_counts.items())),
              'municipality_address_counts': dict(sorted(municipality_addresses.items())),
              'municipality_street_counts': dict(sorted(municipality_streets.items())),
              'unresolved_component_references': dict(sorted(missing_refs.items())),
              'unknown_municipality_codes': dict(sorted(missing.items())), 'source_date_counts': dict(sorted(dates.items())),
              'coordinate_quality_counts': dict(sorted(qualities.items())), 'source_integrity': 'PASS'}
    if metadata:
        result['provider_response_receipt'] = metadata
    if source.get('municipality_counts_member'):
        with zipfile.ZipFile(path) as z:
            expected = {}
            for _, raw in shared.csv_rows(z, source['municipality_counts_member']):
                ags = raw['landschl'] + raw['regbezschl'] + raw['kreisschl'] + raw['gmdschl']
                if ags in expected:
                    raise ValueError('Duplicate provider municipality total')
                expected[ags] = int(raw['count'])
            if expected != dict(municipality_counts):
                raise ValueError('Provider municipality totals differ from all parsed rows')
        result['provider_municipality_totals'] = {'status': 'PASS', 'municipalities': len(expected), 'observations': sum(expected.values()),
                                                  'independent_national_denominator': False}
    return result


def audit(manifest, root, state=None, temp_dir=None):
    admin = next(s for s in manifest['sources'] if s['format'] == 'gv100_zip')
    shared.verify_pin(admin, root)
    admin_rows, reference = administrative_reference(admin, root)
    municipalities = {r['municipality_code']: r for r in admin_rows if r['kind'] == 'municipality'}
    reports = []
    for source in selected_sources(manifest, state):
        result = analyze(source, root, municipalities, temp_dir)
        reports.append(result)
        print(shared.canonical({'source': source['id'], 'counts': result['counts'], 'status': 'VALIDATED'}), flush=True)
    for evidence in manifest.get('evidence', []):
        shared.verify_pin(evidence, root)
    if any(shared.sha256(ROOT / p) != pin for p, pin in IMPLEMENTATION_FILES.items()):
        raise ValueError('Implementation changed during the audit')
    return {'schema_version': 1, 'region': 'western-europe', 'country': 'DE', 'status': 'PASS',
            'implementation_sha256': IMPLEMENTATION_SHA256,
            'implementation_files': IMPLEMENTATION_FILES,
            'manifest_sha256': hashlib.sha256(shared.canonical(manifest).encode()).hexdigest(),
            'administrative_reference': reference, 'source_reports': reports,
            'evidence_pins_verified': len(manifest.get('evidence', [])),
            'national_completeness_verified': False, 'deliverability_in_scope': False,
            'counts_semantics': 'Source observations; identifiers, snapshots and derivations stay separate. No physical-road or assigned-number completeness inference.'}


def replay(manifest, root, accepted, state=None, temp_dir=None):
    if (accepted['implementation_sha256'] != shared.sha256(__file__)
            or accepted['manifest_sha256'] != hashlib.sha256(shared.canonical(manifest).encode()).hexdigest()):
        raise ValueError('Implementation or manifest differs from accepted audit')
    if accepted.get('implementation_files') != IMPLEMENTATION_FILES:
        raise ValueError('An imported reader differs from the accepted audit')
    actual = audit(manifest, root, state, temp_dir)
    old = {r['id']: r for r in accepted['source_reports']}
    for row in actual['source_reports']:
        if old.get(row['id']) != row:
            raise ValueError('Source-row replay differs: ' + row['id'])
    if accepted['administrative_reference'] != actual['administrative_reference']:
        raise ValueError('Administrative replay differs')
    return {**actual, 'source_row_replay': 'PASS'}


def acquire(manifest, root, state=None):
    recovered = []
    for pin in selected_sources(manifest, state) + manifest.get('evidence', []):
        path = shared.source_path(root, pin)
        if path.exists():
            shared.verify_pin(pin, root)
            recovered.append(pin['id'])
            continue
        if path.is_symlink():
            raise ValueError('Existing source symlink needs review')
        url = pin.get('requested_url')
        if not url or urlsplit(url).scheme != 'https':
            raise ValueError('Restore packaged bytes for locally constructed or unavailable source: ' + pin['id'])
        partial = path.with_name(path.name + '.partial')
        if partial.exists() or partial.is_symlink():
            raise ValueError('Prior incomplete source needs review')
        created = False
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urlopen(Request(url, headers={'User-Agent': 'WorldLocalities-DE/1.0'}), timeout=50) as response:
                if response.geturl() != pin['final_url']:
                    raise ValueError('Unexpected source redirect')
                with partial.open('xb') as output:
                    created, count = True, 0
                    for block in iter(lambda: response.read(1024 * 1024), b''):
                        count += len(block)
                        if count > pin['bytes']:
                            raise ValueError('New snapshot needs a new pin')
                        output.write(block)
            if partial.stat().st_size != pin['bytes'] or shared.sha256(partial) != pin['sha256']:
                raise ValueError('Pinned bytes were not recovered')
            path.hardlink_to(partial)
            recovered.append(pin['id'])
        finally:
            if created:
                partial.unlink(missing_ok=True)
    return {'status': 'PINNED_BYTES_RECOVERED', 'sources': recovered,
            'national_completeness_verified': False, 'deliverability_in_scope': False}


def search(manifest, root, state=None, text='', number=None, kind=None, limit=20, offset=0):
    if not 1 <= limit <= 200 or offset < 0:
        raise ValueError('Invalid pagination')
    matches, skipped = [], 0
    for source in selected_sources(manifest, state, kind):
        shared.verify_pin(source, root)
        for row in records(source, root):
            if state is not None and row['state'] != state:
                continue
            if kind is not None and row['kind'] != kind:
                continue
            if number is not None and row.get('number') != number:
                continue
            if text and text.casefold() not in shared.canonical(row).casefold():
                continue
            if skipped < offset:
                skipped += 1
                continue
            matches.append(row)
            if len(matches) > limit:
                break
        if len(matches) > limit:
            break
    more = len(matches) > limit
    return {'country': 'DE', 'results': matches[:limit], 'has_more': more,
            'next_offset': offset + limit if more else None,
            'national_completeness_verified': False, 'deliverability_in_scope': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inventory', 'administration', 'audit', 'replay', 'search', 'acquire'))
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--country', choices=('DE',))
    parser.add_argument('--state', choices=sorted(STATES.values()))
    parser.add_argument('--data-root', type=Path)
    parser.add_argument('--accepted', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--temp-dir', type=Path)
    parser.add_argument('--text', default='')
    parser.add_argument('--number')
    parser.add_argument('--kind')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--offset', type=int, default=0)
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.command == 'inventory':
            result = {**manifest, 'sources': selected_sources(manifest, args.state)}
        else:
            if args.data_root is None:
                raise ValueError('--data-root is required')
            if args.command == 'administration':
                source = next(s for s in manifest['sources'] if s['format'] == 'gv100_zip')
                shared.verify_pin(source, args.data_root)
                rows, reference = administrative_reference(source, args.data_root)
                result = {'country': 'DE', 'units': [r for r in rows if args.state is None or r['state'] == args.state],
                          'reference': reference, 'national_completeness_verified': False,
                          'deliverability_in_scope': False}
            elif args.command == 'audit':
                result = audit(manifest, args.data_root, args.state, args.temp_dir)
            elif args.command == 'replay':
                if args.accepted is None:
                    raise ValueError('--accepted is required')
                result = replay(manifest, args.data_root, json.loads(args.accepted.read_text()), args.state, args.temp_dir)
            elif args.command == 'acquire':
                result = acquire(manifest, args.data_root, args.state)
            else:
                result = search(manifest, args.data_root, args.state, args.text, args.number, args.kind, args.limit, args.offset)
        rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output:
            args.output.write_text(rendered, encoding='utf-8')
        else:
            print(rendered, end='')
    except (OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile, struct.error, ET.ParseError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
