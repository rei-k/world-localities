"""Read the pinned Thuringian INSPIRE pages without remote reference requests."""
from collections import Counter
import gzip
import hashlib
import io
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

AD = '{http://inspire.ec.europa.eu/schemas/ad/4.0}'
GN = '{http://inspire.ec.europa.eu/schemas/gn/4.0}'
GML = '{http://www.opengis.net/gml/3.2}'
WFS = '{http://www.opengis.net/wfs/2.0}'
XLINK = '{http://www.w3.org/1999/xlink}'


def source_tree(node):
    """Namespace-qualified values/attributes, independent of serializer prefixes."""
    return [node.tag, dict(node.attrib), node.text, [source_tree(c) for c in node]]


def names(node):
    result = []
    for name in node.iter(GN + 'GeographicalName'):
        language = name.findtext(GN + 'language')
        for spelling in name.iter(GN + 'SpellingOfName'):
            result.append({'language': language, 'text': spelling.findtext(GN + 'text'),
                           'script': spelling.findtext(GN + 'script')})
    if not result or any(n['text'] is None for n in result):
        raise ValueError('Missing INSPIRE name spelling')
    return result


def documents(archive, index, typename, guard):
    for page in (p for p in index['pages'] if p['type'] == typename):
        with archive.open(page['member']) as compressed, gzip.GzipFile(fileobj=compressed) as stream:
            data = stream.read(page['original_bytes'] + 1)
        if len(data) != page['original_bytes'] or hashlib.sha256(data).hexdigest() != page['original_sha256']:
            raise ValueError('Original Thuringian HTTP body differs')
        stack, count, root = [], 0, None
        for event, node in ET.iterparse(guard(io.BytesIO(data)), events=('start', 'end')):
            if event == 'start':
                stack.append(node)
                if root is None:
                    root = node
                    if node.tag != WFS + 'FeatureCollection':
                        raise ValueError('Expected INSPIRE FeatureCollection')
                continue
            if len(stack) == 3 and stack[-2].tag == WFS + 'member':
                if node.tag != AD + typename:
                    raise ValueError('Unexpected INSPIRE feature type')
                count += 1
                yield page['member'], count, node
                stack[-2].remove(node)
            if node.tag == WFS + 'member' and len(stack) > 1:
                stack[-2].remove(node)
            stack.pop()
        if count != page['numberReturned'] or int(root.get('numberReturned', '-1')) != count:
            raise ValueError('INSPIRE page was truncated or its count differs')


def records(source, archive, metadata, emit, coords, guard):
    import json
    index = json.loads(archive.read('index.json'))
    expected = source['expected_rows']
    if index['expected_rows'] != expected:
        raise ValueError('Thuringian acquisition index differs from manifest')
    if set(archive.namelist()) != {'index.json'} | {p['member'] for p in index['pages']}:
        raise ValueError('Unexpected or missing INSPIRE page members')
    references, counts = {}, Counter()
    for typ in ('AdminUnitName', 'ThoroughfareName'):
        for member, ordinal, node in documents(archive, index, typ, guard):
            identity = node.get(GML + 'id')
            spellings = names(node)
            if not identity or identity in references:
                raise ValueError('Duplicate or missing INSPIRE reference identifier')
            references[identity] = spellings[0]['text']
            counts[typ] += 1
            suffix = identity.removeprefix(typ + '_')
            municipality = suffix[:8] if typ == 'ThoroughfareName' and re.fullmatch('[0-9]{13}', suffix) else None
            yield emit(source, member, ordinal, {'xml': source_tree(node)},
                       'street' if typ == 'ThoroughfareName' else 'administrative_name_reference', identity,
                       state='TH', name=spellings[0]['text'], street=spellings[0]['text'] if typ == 'ThoroughfareName' else None,
                       street_names=spellings, street_code=suffix[8:] if municipality else None,
                       municipality_code=municipality, source_administrative_code=municipality,
                       administrative_code_rule='INSPIRE_identifier_suffix' if municipality else None)
    for member, ordinal, node in documents(archive, index, 'Address', guard):
        identity = node.get(GML + 'id')
        if not identity:
            raise ValueError('Missing INSPIRE address identifier')
        counts['Address'] += 1
        refs = [urlsplit(c.get(XLINK + 'href', '')).fragment for c in node.findall(AD + 'component')]
        missing = [r for r in refs if r not in references]
        municipalities = [r.removeprefix('AdminUnitName_') for r in refs if re.fullmatch('AdminUnitName_[0-9]{8}', r)]
        streets = [r for r in refs if r.startswith('ThoroughfareName_')]
        municipality = municipalities[0] if len(municipalities) == 1 else None
        street_id = streets[0] if len(streets) == 1 else None
        designators = []
        for d in node.iter(AD + 'LocatorDesignator'):
            typ = d.find(AD + 'type')
            if typ is None:
                raise ValueError('Missing locator designator type')
            designators.append({'type': typ.get(XLINK + 'href'), 'value': d.findtext(AD + 'designator')})
        numbers = [d['value'] for d in designators if (d['type'] or '').endswith('/addressNumber')]
        additions = [d['value'] for d in designators if (d['type'] or '').endswith('/addressNumberExtension')]
        positions = []
        for position in node.iter(AD + 'GeographicPosition'):
            point = position.find('.//' + GML + 'Point')
            if point is None or point.get('srsName') != 'urn:ogc:def:crs:EPSG::25832':
                raise ValueError('Unexpected INSPIRE position CRS or geometry')
            pos = point.findtext(GML + 'pos').split()
            if len(pos) != 2:
                raise ValueError('Expected a 2D INSPIRE position')
            positions.append({'coordinate': coords(*pos, 'EPSG:25832'),
                              'default': position.findtext(AD + 'default')})
        defaults = [p for p in positions if p['default'] == 'true']
        chosen = positions[0] if len(positions) == 1 else defaults[0] if len(defaults) == 1 else None
        yield emit(source, member, ordinal, {'xml': source_tree(node)}, 'address', identity,
                   state='TH', municipality_code=municipality, source_administrative_code=municipality,
                   administrative_code_rule='INSPIRE_AdminUnitName_identifier_suffix',
                   municipality_name=references.get('AdminUnitName_' + municipality) if municipality else None,
                   street=references.get(street_id), street_code=street_id.removeprefix('ThoroughfareName_')[8:] if street_id else None,
                   number=numbers[0] if len(numbers) == 1 else None,
                   number_addition=additions[0] if len(additions) == 1 else None,
                   number_designators=designators, source_component_ids=refs,
                   missing_references=missing, coordinates=chosen['coordinate'] if chosen else None,
                   source_positions=positions)
    if dict(counts) != expected:
        raise ValueError('Retrieved INSPIRE type totals differ from separate provider hits')
    metadata.update(feature_counts=dict(counts), expected_rows=expected,
                    pages=len(index['pages']), atomic_snapshot_verified=False)
