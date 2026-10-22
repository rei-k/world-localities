#!/usr/bin/env python3
"""Build and verify the non-official GeoNames supplement for M49 Northern America."""
import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from localities import geonames as core

COUNTRIES = ('BM', 'GL', 'PM')
ALT_RAW = 'alternate_name_id geonameid language name is_preferred is_short is_colloquial is_historic from to'.split()
ALT_FIELDS = ['id', 'entity_id', 'record_kind'] + ALT_RAW
SPECIAL = {'post': 'postal_code', 'link': 'link', 'wkdt': 'wikidata_id', 'iata': 'iata',
           'icao': 'icao', 'faac': 'faac', 'abbr': 'abbreviation', 'phon': 'phonetic',
           'unlc': 'unlocode', 'tcid': 'transport_canada_id'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def alt_rows(path, country, entity_ids):
    with zipfile.ZipFile(path) as archive:
        data = archive.read(country + '.txt').decode('utf-8')
    retained, total, unmatched = [], 0, 0
    for line in data.splitlines():
        values = line.split('\t')
        total += 1
        if len(values) != 10:
            raise ValueError('alternateNamesV2 schema changed')
        row = dict(zip(ALT_RAW, values))
        if 'gn:' + row['geonameid'] not in entity_ids:
            unmatched += 1
            continue
        if any(row[key] not in ('', '1') for key in
               ('is_preferred', 'is_short', 'is_colloquial', 'is_historic')):
            raise ValueError('invalid alternate-name flags')
        if not row['alternate_name_id'].isdigit() or not row['name']:
            raise ValueError('invalid alternate-name identity or label')
        retained.append(dict(id='gn-alt:' + row['alternate_name_id'],
                             entity_id='gn:' + row['geonameid'],
                             record_kind=SPECIAL.get(row['language'], 'name'), **row))
    retained.sort(key=lambda row: int(row['alternate_name_id']))
    if len({row['id'] for row in retained}) != len(retained):
        raise ValueError('duplicate alternate-name ID')
    return retained, total, unmatched


def file_info(data, payload, rows):
    return {'rows': rows, 'bytes': len(payload), 'sha256': digest(payload),
            'uncompressed_sha256': digest(data)}


def build_one(country, inputs, output, scope, retrieved_on):
    profile = next(row for row in scope['countries'] if row['country'] == country)
    country_meta = {key: profile[key] for key in
                    ('id', 'country', 'alpha3', 'm49', 'name_en', 'region', 'region_m49',
                     'geonames_country_name', 'geonames_id', 'source_language_codes')}
    raw_path = inputs / (country + '.zip')
    raw = list(core.source_rows(raw_path, country))
    retained = core.build_rows([row for row in raw if row['feature_class'] in ('A', 'P')], country)
    source_meta = {
        'url': core.SOURCE_URL + country + '.zip', 'retrieved_on': retrieved_on,
        'sha256': digest(raw_path.read_bytes()), 'bytes': raw_path.stat().st_size,
        'source_rows': len(raw), 'retained_rows': len(retained),
        'discarded_feature_classes': dict(Counter(
            row['feature_class'] for row in raw if row['feature_class'] not in ('A', 'P')))
    }
    stats = core.write_country(retained, country, output, source_meta, country_meta,
                               registry_root=output)
    directory = output / 'countries' / country
    alternate_path = inputs / (country + '-alternates.zip')
    aliases, total, unmatched = alt_rows(alternate_path, country,
                                         {row['id'] for row in retained})
    metadata = read_json(directory / 'metadata.json')
    metadata['alternate_names_source'] = {
        'url': core.SOURCE_URL + 'alternatenames/' + country + '.zip',
        'retrieved_on': retrieved_on, 'sha256': digest(alternate_path.read_bytes()),
        'bytes': alternate_path.stat().st_size, 'source_rows': total,
        'retained_direct_id_rows': len(aliases), 'discarded_not_in_entity_scope': unmatched
    }
    alias_data = core.csv_bytes(aliases, ALT_FIELDS)
    alias_payload = core.compressed(alias_data)
    (directory / 'alternate-names.csv.gz').write_bytes(alias_payload)
    metadata['auxiliary_files'] = {
        'alternate-names.csv.gz': file_info(alias_data, alias_payload, len(aliases))
    }
    labels = [row for row in aliases if row['record_kind'] == 'name']
    english = {row['entity_id'] for row in labels
               if row['language'] == 'en' or row['language'].startswith('en-')}
    languages = {value.split('-')[0] for value in country_meta['source_language_codes']}
    local = {row['entity_id'] for row in labels
             if row['language'].split('-')[0] in languages}
    metadata['label_coverage'] = {
        'source_language_tagged_name_rows': sum(bool(row['language']) for row in labels),
        'untagged_name_rows': sum(not row['language'] for row in labels),
        'entities_with_attested_english': len(english),
        'entities_with_attested_country_language': len(local),
        'entities_without_attested_english': len(retained) - len(english),
        'country_language_reference': 'GeoNames countryInfo language codes; not independently verified official/native-language status',
        'language_counts': dict(sorted(Counter(row['language'] or 'und' for row in labels).items())),
        'complete_native_and_english_coverage': False,
        'asciiname_is_english_translation': False,
        'generated_translations': 0
    }
    postal = [row for row in aliases if row['record_kind'] == 'postal_code']
    if postal:
        postal_data = core.csv_bytes(postal, ALT_FIELDS)
        postal_payload = core.compressed(postal_data)
        (directory / 'postal-links.csv.gz').write_bytes(postal_payload)
        metadata['auxiliary_files']['postal-links.csv.gz'] = file_info(
            postal_data, postal_payload, len(postal))
    metadata['postal_coverage'] = {
        'direct_source_id_rows': len(postal),
        'relation': 'GeoNames alternate-name post tag linked by exact geonameid; not postal-authority confirmation',
        'completeness_verified': False, 'deliverability_verified': False,
        'note': 'Subset projection of alternate-names.csv.gz; do not add to alias counts. No name/proximity matching.'
    }
    metadata['auxiliary_record_kind_counts'] = dict(
        sorted(Counter(row['record_kind'] for row in aliases).items()))
    metadata['scope_note'] = (
        'Partial GeoNames source gazetteer only. Official Greenland/Bermuda/France administrative or '
        'address completeness is not established; primary names have no language tag, and the '
        'government-attested administrative seeds remain a separate evidence layer.'
    )
    core.write_json(directory / 'metadata.json', metadata)
    return dict(stats, entities=len(retained), alternate_rows=len(aliases),
                postal_rows=len(postal), english_entities=len(english))


def verify_one(country, output=ROOT):
    directory = output / 'countries' / country
    metadata = read_json(directory / 'metadata.json')
    if metadata['country']['country'] != country or metadata['license'] != 'CC-BY-4.0':
        raise ValueError(country + ': source scope or license mismatch')
    if metadata['source_file']['url'] != core.SOURCE_URL + country + '.zip':
        raise ValueError(country + ': source URL mismatch')
    if not re.fullmatch(r'[0-9a-f]{64}', metadata['source_file']['sha256']):
        raise ValueError(country + ': missing source archive checksum')
    entity_info = metadata['files']['entities.csv.gz']
    payload = (directory / 'entities.csv.gz').read_bytes()
    data = gzip.decompress(payload)
    if digest(payload) != entity_info['sha256'] or digest(data) != entity_info['uncompressed_sha256']:
        raise ValueError(country + ': entity checksum mismatch')
    if len(payload) != entity_info['bytes']:
        raise ValueError(country + ': entity byte count mismatch')
    rows = list(csv.DictReader(data.decode('utf-8').splitlines()))
    if len(rows) != entity_info['rows'] or len({row['id'] for row in rows}) != len(rows):
        raise ValueError(country + ': entity row count or identity mismatch')
    if any(row['id'] != 'gn:' + row['geonameid'] or row['country_code'] != country for row in rows):
        raise ValueError(country + ': source-country identity mismatch')
    if rows != core.build_rows([{key: row[key] for key in core.RAW} for row in rows], country):
        raise ValueError(country + ': entity transform replay mismatch')
    indexed = {row['id']: row for row in rows}
    for row in rows:
        for field in ('parent_candidates_json', 'state_candidates_json'):
            candidates = json.loads(row[field])
            if any(identity not in indexed for identity in candidates):
                raise ValueError(country + ': dangling source candidate')
        if row['parent_id'] and not row['parent_id'].startswith('country:') and row['parent_id'] not in indexed:
            raise ValueError(country + ': dangling resolved parent')
        if row['state_id'] and row['state_id'] not in indexed:
            raise ValueError(country + ': dangling state reference')
        if row['state_id'] and indexed[row['state_id']]['admin_level'] != '1':
            raise ValueError(country + ': state reference is not an ADM1 entity')
        visited, parent_id = {row['id']}, row['parent_id']
        while parent_id in indexed:
            if parent_id in visited:
                raise ValueError(country + ': cyclic parent chain')
            visited.add(parent_id)
            parent_id = indexed[parent_id]['parent_id']
    if sum(row['address_candidate'] == '1' for row in rows) != metadata['counts']['address_candidates']:
        raise ValueError(country + ': address-candidate count mismatch')
    if sum(row['kind'] == 'locality' for row in rows) != metadata['counts']['locality_rows']:
        raise ValueError(country + ': locality count mismatch')
    preview = (directory / 'admin1.csv').read_bytes()
    expected_preview = core.csv_bytes(row for row in rows if row['admin_level'] == '1')
    if preview != expected_preview or digest(preview) != metadata['preview_files']['admin1.csv']['sha256']:
        raise ValueError(country + ': ADM1 preview mismatch')
    auxiliary = {}
    for filename, info in metadata['auxiliary_files'].items():
        compressed = (directory / filename).read_bytes()
        decompressed = gzip.decompress(compressed)
        if digest(compressed) != info['sha256'] or digest(decompressed) != info['uncompressed_sha256']:
            raise ValueError(country + ': auxiliary checksum mismatch: ' + filename)
        parsed = list(csv.DictReader(decompressed.decode('utf-8').splitlines()))
        if len(parsed) != info['rows'] or len({row['id'] for row in parsed}) != len(parsed):
            raise ValueError(country + ': auxiliary row/identity mismatch: ' + filename)
        for row in parsed:
            if row['entity_id'] not in indexed or row['id'] != 'gn-alt:' + row['alternate_name_id']:
                raise ValueError(country + ': invalid alternate-name foreign key')
            if row['record_kind'] != SPECIAL.get(row['language'], 'name'):
                raise ValueError(country + ': alternate-name kind mismatch')
        auxiliary[filename] = parsed
    aliases = auxiliary.get('alternate-names.csv.gz', [])
    postal = [row for row in aliases if row['record_kind'] == 'postal_code']
    if postal != auxiliary.get('postal-links.csv.gz', []):
        raise ValueError(country + ': postal projection differs from source tags')
    if len(aliases) != metadata['alternate_names_source']['retained_direct_id_rows']:
        raise ValueError(country + ': alternate-name count mismatch')
    return {'country': country, 'entities': len(rows), 'localities': metadata['counts']['locality_rows'],
            'alternate_rows': len(aliases), 'postal_rows': len(postal), 'integrity': 'passed',
            'entity_replay': 'exact'}


def summarize(output=ROOT, prepared_on='2026-10-18'):
    ready = [country for country in COUNTRIES
             if (output / 'countries' / country / 'metadata.json').is_file()]
    reports = [verify_one(country, output) for country in ready]
    rows, aliases = set(), set()
    coverage = []
    for country in ready:
        metadata = read_json(output / 'countries' / country / 'metadata.json')
        for filename, seen in (('entities.csv.gz', rows), ('alternate-names.csv.gz', aliases)):
            ids = {row['id'] for row in core.read_csv(output / 'countries' / country / filename)}
            if seen.intersection(ids):
                raise ValueError('duplicate identity across Northern source countries')
            seen.update(ids)
        coverage.append(dict(metadata['counts'],
                             entities=metadata['files']['entities.csv.gz']['rows'],
                             alternate_rows=metadata['alternate_names_source']['retained_direct_id_rows'],
                             postal_rows=metadata['postal_coverage']['direct_source_id_rows'],
                             english_entities=metadata['label_coverage']['entities_with_attested_english']))
    if coverage:
        coverage_data = core.csv_bytes(coverage, list(coverage[0]))
        (output / 'coverage.csv').write_bytes(coverage_data)
    totals = {key: sum(row[key] for row in coverage)
              for key in coverage[0] if isinstance(coverage[0][key], int)} if coverage else {}
    countries = [{'country': country,
                  'metadata_sha256': digest((output / 'countries' / country / 'metadata.json').read_bytes())}
                 for country in ready]
    scope_data = (output / 'scope.json').read_bytes()
    manifest = {
        'schema_version': 1, 'region': 'Northern America', 'region_m49': '021',
        'scope_count': 3, 'prepared_count': len(ready), 'prepared_countries': ready,
        'missing_countries': sorted(set(COUNTRIES) - set(ready)), 'totals': totals,
        'countries': countries, 'scope_sha256': digest(scope_data),
        'coverage_sha256': digest((output / 'coverage.csv').read_bytes()) if coverage else None,
        'license': 'CC-BY-4.0', 'prepared_on': prepared_on,
        'coverage_claim': 'Three partial GeoNames country extracts; official locality, administrative, postal, street and address completeness remain unverified.'
    }
    core.write_json(output / 'manifest.json', manifest)
    core.write_json(output / 'verification.json', {
        'schema_version': 1, 'countries': len(reports), 'entity_rows': len(rows),
        'alternate_rows': len(aliases), 'errors': 0, 'reports': reports,
        'limits': ['Integrity and source-code replay are verified; official hierarchy and source accuracy are not.',
                   'Postal tags are direct GeoNames observations, not address deliverability.']
    })
    return manifest


def verify_manifest(output=ROOT, selected=None):
    scope = read_json(output / 'scope.json')
    expected = {row['country'] for row in scope['countries']
                if row['status'] == 'published_geonames_source'}
    manifest = read_json(output / 'manifest.json')
    if manifest['region_m49'] != '021' or digest((output / 'scope.json').read_bytes()) != manifest['scope_sha256']:
        raise ValueError('Northern source manifest scope mismatch')
    if digest((output / 'coverage.csv').read_bytes()) != manifest['coverage_sha256']:
        raise ValueError('Northern source coverage checksum mismatch')
    entries = {row['country']: row for row in manifest['countries']}
    if set(entries) != expected or set(manifest['prepared_countries']) != expected:
        raise ValueError('Northern source manifest country set mismatch')
    chosen = selected or sorted(expected)
    reports = []
    with (output / 'coverage.csv').open(encoding='utf-8', newline='') as handle:
        coverage = {row['country']: row for row in csv.DictReader(handle)}
    totals = {}
    for country in chosen:
        if country not in entries:
            raise ValueError(country + ': missing Northern source manifest entry')
        raw = (output / 'countries' / country / 'metadata.json').read_bytes()
        if digest(raw) != entries[country]['metadata_sha256']:
            raise ValueError(country + ': metadata checksum mismatch')
        metadata = json.loads(raw.decode('utf-8'))
        row = coverage[country]
        for field in metadata['counts']:
            if row.get(field) != str(metadata['counts'][field]):
                raise ValueError(country + ': coverage metric mismatch: ' + field)
        for field, value in (
            ('entities', metadata['files']['entities.csv.gz']['rows']),
            ('alternate_rows', metadata['alternate_names_source']['retained_direct_id_rows']),
            ('postal_rows', metadata['postal_coverage']['direct_source_id_rows']),
            ('english_entities', metadata['label_coverage']['entities_with_attested_english'])
        ):
            if row.get(field) != str(value):
                raise ValueError(country + ': coverage metric mismatch: ' + field)
            totals[field] = totals.get(field, 0) + value
        reports.append(verify_one(country, output))
    if selected is None:
        for field, value in totals.items():
            if manifest['totals'].get(field) != value:
                raise ValueError('Northern source manifest total mismatch: ' + field)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify', 'summarize'))
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT)
    parser.add_argument('--country', nargs='+')
    parser.add_argument('--retrieved-on', default='2026-10-18')
    parser.add_argument('--prepared-on', default='2026-10-18')
    args = parser.parse_args()
    if args.command == 'build':
        if args.inputs is None:
            parser.error('--inputs required')
        scope = read_json(args.output / 'scope.json')
        for country in args.country or COUNTRIES:
            if country not in COUNTRIES:
                parser.error('unsupported country: ' + country)
            print(json.dumps(build_one(country, args.inputs, args.output, scope,
                                       args.retrieved_on), ensure_ascii=False), flush=True)
        result = summarize(args.output, args.prepared_on)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    elif args.command == 'verify':
        print(json.dumps({'reports': verify_manifest(args.output, args.country)}, ensure_ascii=False), flush=True)
    else:
        scope = read_json(args.output / 'scope.json')
        print(json.dumps(summarize(args.output, args.prepared_on), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
