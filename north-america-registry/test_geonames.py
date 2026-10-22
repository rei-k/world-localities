"""Country-level integrity, language-provenance, and identity regressions."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('northern_geonames_build', ROOT / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class NorthernGeoNamesTests(unittest.TestCase):
    def test_three_country_packs_have_pinned_source_and_payload_integrity(self):
        reports = {row['country']: row for row in build.verify_manifest(ROOT)}
        self.assertEqual(set(reports), {'BM', 'GL', 'PM'})
        expected = {'BM': (43, 31), 'GL': (281, 255), 'PM': (16, 13)}
        for country, (entities, localities) in expected.items():
            self.assertEqual(reports[country]['entities'], entities)
            self.assertEqual(reports[country]['localities'], localities)
            self.assertEqual(reports[country]['integrity'], 'passed')
            self.assertEqual(reports[country]['entity_replay'], 'exact')

    def test_source_identifiers_language_tags_and_partial_claims_stay_explicit(self):
        languages = {'BM': {'en', 'pt'}, 'GL': {'kl', 'da', 'en'}, 'PM': {'fr'}}
        for country, bases in languages.items():
            metadata = json.loads((ROOT / 'countries' / country / 'metadata.json').read_text())
            self.assertEqual(metadata['country']['id'], 'country:' + country)
            self.assertEqual(metadata['source_file']['retrieved_on'], '2026-10-18')
            self.assertEqual(metadata['license'], 'CC-BY-4.0')
            self.assertRegex(metadata['source_file']['sha256'], r'^[0-9a-f]{64}$')
            self.assertFalse(metadata['current_official_hierarchy_verified'])
            self.assertFalse(metadata['label_coverage']['complete_native_and_english_coverage'])
            self.assertFalse(metadata['postal_coverage']['completeness_verified'])
            self.assertFalse(metadata['postal_coverage']['deliverability_verified'])
            source_bases = {value.split('-')[0] for value in metadata['country']['source_language_codes']}
            self.assertEqual(source_bases, bases)
            self.assertGreater(metadata['label_coverage']['entities_with_attested_english'], 0)
            self.assertIn('und', metadata['label_coverage']['language_counts'])

    def test_greenland_unresolved_hierarchy_is_reported_not_guessed(self):
        metadata = json.loads((ROOT / 'countries/GL/metadata.json').read_text())
        self.assertEqual(metadata['counts']['unresolved_parents'], 36)
        self.assertEqual(metadata['counts']['ambiguous_parents'], 0)
        report = build.verify_one('GL', ROOT)
        self.assertEqual(report['localities'], 255)


if __name__ == '__main__':
    unittest.main()
