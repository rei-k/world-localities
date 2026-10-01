# South America locality and administrative gazetteer

Source-preserving GeoNames country extracts retrieved on 2026-10-01. This is a gazetteer baseline, not a verified current register of all municipalities, postal addresses, or deliverable destinations. All source A/P features are retained with no population cutoff, including historical and abandoned features. Feature classes other than A/P are excluded and counted in each country's metadata.

## Verified publication totals

This publication contains **14 of 16 UN M49 South America countries/areas**. Argentina (AR) and Paraguay (PY) remain pending and have no country payloads, projections, reconstruction parts or country-level data reports in this subset.

- 14 published countries/areas; 241,514 source entity identities
- 12,419 administrative rows; 228,964 populated-place rows; 131 other A-class rows
- 289,202 alternate-name/value observations linked by source ID
- 553 unresolved direct-parent references retained explicitly
- Subset integrity and exact derived-column replay passed; 21 data/reconstruction/scope regression tests passed

Counts cover only the published subset and are source identities, not deduplicated real-world municipality or postal-address totals. English and local-language coverage remains incomplete; see `summary.json` and country metadata.

## Scope and files

UN M49 intermediate region 005, South America, defines the scope. The full M49 scope has 16 areas. This publication includes BO, BR, BV, CL, CO, EC, FK, GF, GS, GY, PE, SR, UY, VE; AR and PY are pending. Bouvet Island, the Falkland Islands (Malvinas), French Guiana, and South Georgia and the South Sandwich Islands are included according to that statistical classification. This is not a sovereignty determination. Source country assignments and secondary country codes are preserved without reinterpretation.

- `scope.json`: sourced country/area profiles and any separate external coverage
- `countries/CC/entities.csv.gz`: all retained administrative, populated-place, and other A-class rows, with all 19 original GeoNames fields
- `countries/CC/admin1.csv`: duplicate display projection of ADM1 entities; do not count twice
- `countries/CC/alternate-values.csv.gz`: all alternate-name/value observations whose GeoNames entity ID is in the country's retained entity set
- `countries/CC/metadata.json`: URLs, retrieval date, source hashes, counts, output hashes, label coverage and unresolved hierarchy counts
- `coverage.csv`, `manifest.json`, `verification.json`: country counts, publication inventory and integrity results
- `schema.json`: exact entity and alias columns and meaning
- `sources/geonames-readme.txt`: upstream schema and attribution statement
- `sources/source-inventory.json`: source-input byte hashes and reuse provenance

The manifest explicitly reports what is prepared; the M49 scope itself is not proof of official administrative completeness. Bouvet Island has no A/P locality or ADM1–5 record in this extract; its source territory feature is retained, rather than inventing a settlement or state. Country profiles are reference anchors and are not added to entity counts.

## Identity and hierarchy

`gn:<geonameid>` is a stable source identity; `gn-alt:<alternateNameId>` is an alternate-value source identity. `country:CC` is a country/area profile reference. These are not cross-source reconciled real-world IDs. Source country and administrative codes remain strings, preserving leading zeroes, and must not be assumed to be ISO 3166-2 codes.

Direct parents are resolved only by unique, exact, complete source administrative-code tuples. An absent intermediate parent stays unresolved; an ADM1 match is retained separately in `state_id`, without substituting it as the direct parent. No name-similarity or coordinate-proximity join is used. Historical administrative entities cannot parent active administrative records or settlements. `country_scope_only` means only country membership was available, not direct administrative governance.

The source ADM1–5 hierarchy has different meanings across countries. Its rows must not all be called municipal governments. The source can be outdated, incomplete or inconsistent with legal boundaries; current official hierarchy has not been independently certified. Population zero may mean unknown. Coordinates are source reference points, not boundaries or entrances.

## Language and postal values

The primary `name` and flat `alternatenames` fields have no source language tags. Their language remains undetermined; `asciiname` is an ASCII rendering and is never labeled as an English translation.

Language-tagged observations are in `alternate-values.csv.gz`. All source flags and date ranges are preserved, as are special source values such as `post`, `link`, and `wkdt`. A `language_name` value is source-attested for its stated language. The country-language coverage count compares exact source language tags to the source `countryInfo.txt` language list. This is not a claim that every name is indigenous or officially approved. A name can have multiple alternatives in one language; none is silently selected as authoritative.

The metadata's `current_english_name_entities` and `current_country_language_name_entities` count names that are not marked historic and have no end-period. These are source-filter counts, not independent confirmation that a name is legally current. Missing English/local-language names remain missing; no translation, transliteration or language guess is substituted. Label coverage is materially incomplete and is disclosed per country.

Postal values are only rows explicitly tagged `post` by GeoNames and linked to the exact source entity ID. There is no name-based postal join, no fabricated postcode, no street address or Address1 field, and no postal deliverability validation.

## Large-file publication and automatic reconstruction

Six large compressed files are distributed as ordered raw binary chunks of at most 512 KiB under `.parts/`. `split_manifest.json` records original paths, byte counts, full SHA-256/Git blob hashes and each ordered part's byte count and SHA-256. These chunks are not separate gzip streams; exact concatenation restores the original compressed bytes without recompression or data changes. The original large files are intentionally absent from the published tree. All smaller compressed files are unchanged.

`query.py` automatically materializes the requested country; `build.py verify` automatically materializes every country before validating it. You can also run `python materialize.py --country BR`. This is offline and requires no extra packages. The clean publication-only copy was tested with all six oversized originals absent: automatic query and full-pack verification rebuilt exact original bytes, and all 21 data/reconstruction/scope regression tests passed. See `publication_verification.json`. A writable checkout is needed for the reconstructed files. Use a writable copy if the installed package is read-only. The original canonical metadata and integrity hashes remain valid.

Reconstruction rejects path traversal, symlink paths, missing/corrupt/wrong-size parts, invalid aggregate sizes, checksum mismatches, and mismatched existing outputs. Existing correct files are reused. A temporary output is fully verified before an exclusive link creates the destination; existing output is never overwritten.

## Use and reproduce

Python 3.11+ and the standard library are sufficient:

```sh
python query.py --country UY --text Montevideo --limit 10
python query.py --country PE --kind admin_subdivision --level 1
python build.py verify
python -m unittest -v test_registry
```

To rebuild, download each selected `CC.zip` from `https://download.geonames.org/export/dump/`, each country alias archive from `https://download.geonames.org/export/dump/alternatenames/CC.zip` to `CC-alternatenames.zip`, plus `countryInfo.txt` and the UN M49 overview HTML as `m49.html`. Then run:

```sh
python build.py build --inputs /path/to/inputs --retrieved-on YYYY-MM-DD
python build.py verify
```

`--countries UY BO` limits regeneration to chosen published-country files. AR and PY are explicitly excluded from this publication and rejected by its build/query entry points. Source URLs are mutable daily exports; the recorded hashes identify the retrieved bytes. Raw selected entity columns and all included alternate-value source columns survive in the shipped CSVs. Integrity verification replays all entity-derived columns exactly, checks file hashes, unique source IDs, country scope, references, acyclic hierarchy and alias linkage. Deterministic gzip excludes timestamps and filenames. Re-compression may depend on Python/zlib versions.

## Related layers and licensing

The destination's official IBGE Brazil municipal layer is a separate dataset. Do not merge same-named gazetteer settlements and official municipalities automatically, and do not add their counts as distinct real-world localities. No official layer is copied or overwritten here.

GeoNames data and derived CSVs: Creative Commons Attribution 4.0. Source: https://www.geonames.org/ and https://download.geonames.org/export/dump/. License: https://creativecommons.org/licenses/by/4.0/. Changes are the A/P selection, country packaging, typed identities, administrative-code linkage and validation metadata. GeoNames provides the data as-is, without completeness or accuracy warranty. Code is MIT; see `LICENSE` and `NOTICE.md`.
