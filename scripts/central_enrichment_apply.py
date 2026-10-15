#!/usr/bin/env python3
"""One-time, exact-match integration patch; removed after successful import QA."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(relative, old, new):
    path = ROOT / relative
    text = path.read_text(encoding='utf-8')
    if new in text and old not in text:
        return
    if text.count(old) != 1:
        raise ValueError(f'{relative}: expected one exact patch target, found {text.count(old)}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


replace('americas-registry/audit.py', 'import argparse\n', 'import argparse\nimport importlib.util\n')
old = '    sources["MX"] = official_snapshot(root, "MX")\n'
new = old + '''    # The preserved six-country publication remains unchanged. CR is additive.
    module_path = Path(__file__).resolve().parents[1] / "central-america-registry/supplement.py"
    spec = importlib.util.spec_from_file_location("central_cr_snapshot", module_path)
    supplement = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supplement)
    cr = supplement.verify(root)
    sources["CR"] = {
        "country": "CR", "status": "published_source_layer",
        "layer": "central-america-registry/enrichment/countries/CR",
        "source_locality_rows": cr["locality_rows"],
        "in_m49_area_locality_rows": cr["locality_rows"],
        "excluded_source_locality_rows": 0,
        "unresolved_parents": cr["unresolved_parents"],
        "quality": "geonames_source_gazetteer_raw_replayed_not_official_postal_coverage"
    }
'''
replace('americas-registry/audit.py', old, new)
replace('americas-registry/audit.py', '"Expected separate MX / pending CR scope has changed"',
        '"Expected separate MX / additive CR scope has changed"')
replace('americas-registry/audit.py',
        '    return sources, ["MX: separate INEGI official snapshot; not part of 6-country GeoNames package"]',
        '''    return sources, [
        "MX: separate INEGI official snapshot; not part of 6-country GeoNames package",
        "CR: additive source gazetteer with raw replay; original six-country snapshot is unchanged",
        "CR: source ADM2 count is 82; separate government CodeSystem has 84 entries and is not a verified GeoNames crosswalk"
    ]''')

anchor = '            checked_official.append(cc)\n'
addition = '''    if area == 'central-america':
        central = imported('central_payload_quality', ROOT / 'central-america-registry/quality.py')
        payload_report = central.verify_all(root)
        v.require(payload_report['status'] == 'passed',
                  'Central America payload validation failed: ' + str(payload_report['failed_countries']))
        government = imported('central_canton_codes', ROOT / 'central-america-registry/government_codes.py')
        government.verify(root)
        # Record all new source and derived bytes actually validated by the runner.
        for folder in ('central-america-registry/enrichment', 'central-america-registry/government-reference/CR'):
            manifest = v.decode_json(record(folder + '/manifest.json'))
            for filename in sorted(manifest['files']):
                record(folder + '/' + filename)
        record('central-america-registry/locale_manifest.json')
        for cc in central.BASE:
            folder = 'central-america-registry/countries/' + cc
            for metadata_name in ('metadata.json', 'locale_metadata.json'):
                metadata = v.decode_json(record(folder + '/' + metadata_name))
                for filename in sorted(metadata['files']):
                    record(folder + '/' + filename)
'''
replace('americas-registry/quality_cycle.py', anchor, anchor + addition)
replace('americas-registry/quality_cycle.py',
        "'regional_gazetteer_payload_checks': 'not_run' if area != 'northern-america' else 'not_applicable',",
        "'regional_gazetteer_payload_checks': ('passed_hashes_and_derived_replay_CR_raw_replay' if area == 'central-america' else 'not_run' if area != 'northern-america' else 'not_applicable'),")
replace('americas-registry/quality_cycle.py',
        "'regional_check_scope': 'pinned country metadata and country-level metrics, not compressed payload contents',",
        "'regional_check_scope': ('Seven Central America gazetteer payloads: hashes, derived columns and ID references; CR raw ZIP replay and government CodeSystem replay. Legacy six-country raw ZIP replay is not run.' if area == 'central-america' else 'pinned country metadata and country-level metrics, not compressed payload contents'),")

replace('tests/test_americas_unified.py',
        'self.assertEqual(self.report["source_country_area_count"], 52)',
        'self.assertEqual(self.report["source_country_area_count"], 53)')
replace('tests/test_americas_unified.py', '[2, 7, 27, 16]', '[2, 8, 27, 16]')
replace('tests/test_americas_unified.py', '[["BM", "GL", "PM"], ["CR"], ["CU"], []]',
        '[["BM", "GL", "PM"], [], ["CU"], []]')
replace('tests/test_americas_unified.py',
        'self.assertIn("CR", area["pending_country_area_codes"])',
        'self.assertNotIn("CR", area["pending_country_area_codes"])')
replace('tests/test_americas_integrity.py',
        "self.assertEqual(result['source_country_area_count'], 52)",
        "self.assertEqual(result['source_country_area_count'], 53)")

path = ROOT / 'README.md'
text = path.read_text(encoding='utf-8')
text = text.replace('52/57', '53/57').replace('52 / 57', '53 / 57')
section = '''
## 中央アメリカの追加強化（2026-10-15）

[中央アメリカ強化記録](central-america-registry/ENRICHMENT_20261015.md)に、
コスタリカ6,465地名・行政地物と6,182言語付き名称の追加、政府公開84カントンコード表、
8か国共通検索、全ペイロード検査を整理した。国別出典レイヤーは中央アメリカ8/8、
アメリカ大陸53/57。住所・郵便番号・全自治体の完全網羅ではない。

新しい入口は `python central-america-registry/query_enriched.py --country CR --text 'San Jose' --language es`、
実データ検査は `python central-america-registry/quality.py`。
'''
if '## 中央アメリカの追加強化（2026-10-15）' not in text:
    text = text.rstrip() + '\n' + section
path.write_text(text, encoding='utf-8')

path = ROOT / 'central-america-registry/README.md'
text = path.read_text(encoding='utf-8')
note = '''> **2026-10-15 現行統合版:** コスタリカの追加レイヤーとメキシコの別出典を含め、中央アメリカ8/8か国を参照できるようになりました。
> [追加内容・検証範囲](ENRICHMENT_20261015.md)、`query_enriched.py`、`quality.py`を参照してください。
> 以下の6か国版の説明と既存manifest/coverageは、変更していない保存済み原本の説明です。

'''
if not text.startswith(note):
    text = note + text
path.write_text(text, encoding='utf-8')

path = ROOT / 'americas-registry/README.md'
text = path.read_text(encoding='utf-8').replace('52 / 57', '53 / 57').replace('52/57', '53/57')
lines = text.splitlines()
for i, line in enumerate(lines):
    if line.startswith('| 2 |') and 'Central America' in line:
        lines[i] = '| 2 | [Central America](../central-america-registry/ENRICHMENT_20261015.md) | 013 | 8 / 8: six preserved GeoNames packs + Costa Rica supplement + separate INEGI Mexico | None for source country layers |'
text = '\n'.join(lines) + '\n'
text += '\nCentral America now validates actual gazetteer payloads and the pinned Costa Rica raw archives through `quality_cycle.py`; the legacy six-country raw ZIP replay is still a separate task. The government 84-canton CodeSystem remains separate from the 82 ADM2 records in the Costa Rica GeoNames snapshot.\n'
path.write_text(text, encoding='utf-8')
print('Applied exact Central America integration patches; preserved original country data.')
