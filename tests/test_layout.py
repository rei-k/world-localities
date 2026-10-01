"""Repository navigation and independent-source contracts after directory migration."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
LAYERS = {row['id']: row for row in CATALOG['layers']}


class DirectoryLayoutTests(unittest.TestCase):
    def test_unique_root_relative_catalog_paths(self):
        self.assertEqual(len(LAYERS), len(CATALOG['layers']))
        self.assertEqual(len({x['path'] for x in LAYERS.values()}), len(LAYERS))
        for item in LAYERS.values():
            for key in ('path', 'readme', 'scope', 'manifest', 'schema', 'coverage'):
                if key not in item:
                    continue
                relative = Path(item[key])
                self.assertFalse(relative.is_absolute())
                self.assertNotIn('..', relative.parts)
                self.assertTrue((ROOT / relative).exists(), item[key])
            self.assertEqual(len(item['countries']), len(set(item['countries'])))

    def test_all_continents_share_one_root(self):
        self.assertEqual({x['region'].split('/')[0] for x in LAYERS.values()},
                         {'africa', 'asia', 'europe', 'oceania', 'americas'})
        legacy = ['africa', 'asia', 'europe', 'oceania', 'official',
                  'central-america', 'caribbean', 'south-america']
        for name in legacy:
            self.assertFalse((ROOT / (name + '-registry')).exists())

    def test_americas_geography_and_layer_separation(self):
        self.assertEqual(LAYERS['americas.northern.official']['countries'], ['CA', 'US'])
        self.assertEqual(LAYERS['americas.central.official']['countries'], ['MX'])
        self.assertEqual(LAYERS['americas.southern.official']['countries'], ['BR'])
        self.assertNotIn('americas.northern.gazetteer', LAYERS)
        self.assertIn('PR', LAYERS['americas.caribbean.gazetteer']['countries'])
        self.assertTrue((ROOT / 'regions/americas/northern/official/US/US-PR.csv').exists())
        self.assertTrue((ROOT / 'regions/americas/southern/gazetteer/countries/BR').is_dir())
        self.assertTrue((ROOT / 'regions/americas/southern/official/BR').is_dir())

    def test_partial_scope_stays_explicit(self):
        expected = {'central': (6, {'CR', 'MX'}),
                    'caribbean': (27, {'CU'}),
                    'southern': (14, {'AR', 'PY'})}
        for region, (count, missing) in expected.items():
            layer = LAYERS[f'americas.{region}.gazetteer']
            self.assertEqual(len(layer['countries']), count)
            self.assertEqual(set(layer['not_published']), missing)
            for country in missing:
                self.assertFalse((ROOT / layer['path'] / 'countries' / country).exists())

    def test_asia_official_is_not_gazetteer(self):
        self.assertEqual(LAYERS['asia.official']['countries'], ['JP', 'TW'])
        self.assertEqual(len(LAYERS['asia.gazetteer']['countries']), 52)
        self.assertNotEqual(LAYERS['asia.official']['path'], LAYERS['asia.gazetteer']['path'])

    def test_training_inputs_use_new_paths(self):
        path = ROOT / 'training/asia/plan.json'
        plan = json.loads(path.read_text(encoding='utf-8'))
        for value in plan['official_inputs'].values():
            target = (path.parent / value).resolve()
            self.assertTrue(target.is_relative_to(ROOT))
            self.assertTrue(target.is_file())
            self.assertIn('regions/asia/official/', target.as_posix())

    def test_eurostat_has_an_explicit_official_root(self):
        path = ROOT / 'regions/europe/official/eurostat.py'
        spec = importlib.util.spec_from_file_location('layout_eurostat', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.ROOT, path.parent)
        self.assertEqual(module._CORE.ROOT, ROOT / 'regions/europe/gazetteer')
        self.assertTrue((module.ROOT / 'eurostat-lau/manifest.json').is_file())

    def test_source_map_only_routes_destinations(self):
        mapping = json.loads((ROOT / 'regions/americas/official/provenance/source-map.json').read_text())
        self.assertEqual(len(mapping['files']), 151)
        self.assertEqual(len({x['destination_path'] for x in mapping['files']}), 151)
        for item in mapping['files']:
            self.assertTrue(item['source_path'].startswith('address-foundation/'))
            self.assertTrue(item['source_url'].startswith('https://github.com/rei-k/world-address/'))
            self.assertTrue(item['destination_path'].startswith('regions/americas/'))
            self.assertNotIn('..', Path(item['destination_path']).parts)
            self.assertRegex(item['source_git_blob_sha1'], r'^[0-9a-f]{40}$')
            self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')


if __name__ == '__main__':
    unittest.main()
