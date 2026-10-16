import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from localities import geonames, materialize
from localities.layout import load_catalog, validate_catalog


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositoryLayout(unittest.TestCase):
    def test_catalog_matches_existing_registry_boundaries(self):
        report = validate_catalog(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["registry_count"], 10)
        self.assertEqual(report["shared_component_count"], 2)

    def test_catalog_paths_are_unique(self):
        catalog = load_catalog()
        paths = [entry["path"] for entry in catalog["registries"]]
        self.assertEqual(len(paths), len(set(paths)))

    def test_geonames_compatibility_entries_use_shared_transform(self):
        for index, relative in enumerate(
            [
                "caribbean-registry/geonames_core.py",
                "south-america-registry/geonames_core.py",
            ]
        ):
            module = load_module(f"compat_geonames_{index}", ROOT / relative)
            self.assertIs(module.build_rows, geonames.build_rows)
            self.assertIs(module.read_csv, geonames.read_csv)
            self.assertEqual(module.ROOT, (ROOT / relative).parent)

    def test_materialize_compatibility_entries_use_shared_restore(self):
        for index, relative in enumerate(
            [
                "caribbean-registry/materialize.py",
                "central-america-registry/materialize.py",
                "south-america-registry/materialize.py",
            ]
        ):
            module = load_module(f"compat_materialize_{index}", ROOT / relative)
            self.assertIs(module.restore, materialize.restore)
            self.assertIs(module.manifest, materialize.manifest)
            self.assertEqual(module.ROOT, (ROOT / relative).parent)

    def test_ensure_file_validates_existing_managed_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = b"verified bytes"
            target = root / "countries" / "XX" / "entities.csv.gz"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"corrupt bytes")
            manifest = {
                "files": [
                    {
                        "country": "XX",
                        "path": "countries/XX/entities.csv.gz",
                        "bytes": len(expected),
                        "sha256": hashlib.sha256(expected).hexdigest(),
                        "parts": [],
                    }
                ]
            }
            (root / "split_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "existing output differs"):
                materialize.ensure_file(target, root)


if __name__ == "__main__":
    unittest.main()
