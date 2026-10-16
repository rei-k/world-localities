#!/usr/bin/env python3
"""Compatibility entry point for the shared split-file materializer."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from localities import materialize as _shared

safe_path = _shared.safe_path
sha_file = _shared.sha_file
restore = _shared.restore
manifest = _shared.manifest
materialize_country = _shared.materialize_country


def ensure_file(path, root=ROOT):
    return _shared.ensure_file(path, root)


if __name__ == "__main__":
    _shared.main(ROOT)
