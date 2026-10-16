#!/usr/bin/env python3
"""Compatibility entry point for the shared GeoNames transformation core."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from localities import geonames as _shared

RAW = _shared.RAW
DERIVED = _shared.DERIVED
FIELDS = _shared.FIELDS
CURRENT_PLACES = _shared.CURRENT_PLACES
SOURCE_URL = _shared.SOURCE_URL
M49_URL = _shared.M49_URL
jdump = _shared.jdump
sha = _shared.sha
write_json = _shared.write_json
csv_bytes = _shared.csv_bytes
compressed = _shared.compressed
read_csv = _shared.read_csv
source_rows = _shared.source_rows
level = _shared.level
code_key = _shared.code_key
build_rows = _shared.build_rows


def freshness_issues(country, adm1_count):
    return _shared.freshness_issues(country, adm1_count, ROOT)


def write_country(rows, country, output, source_meta, country_meta):
    return _shared.write_country(
        rows,
        country,
        output,
        source_meta,
        country_meta,
        registry_root=ROOT,
    )
