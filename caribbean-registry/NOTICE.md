# Attribution and reuse

Gazetteer and alternate-name records are derived from GeoNames, https://www.geonames.org/, downloaded from https://download.geonames.org/export/dump/ and its alternatenames/ subdirectory. The original 27 country extracts were acquired on 2026-10-01; Cuba (CU) was acquired on 2026-10-18. Per-country source dates, URLs, byte sizes, and SHA-256 checksums are stored in `countries/CC/metadata.json`. GeoNames data is licensed under Creative Commons Attribution 4.0 International: https://creativecommons.org/licenses/by/4.0/ . Commercial use is permitted with attribution. Source terms and column definitions: https://download.geonames.org/export/dump/readme.txt . GeoNames does not endorse this derivative.

Changes: retain every A/P-class entity in all 28 UN M49 Caribbean source country extracts; preserve all 19 source fields; add IDs, classifications, exact-code parent references and quality flags; retain alternateNamesV2 records whose geonameid exists in that entity scope; distinguish non-language tags; export deterministic gzip CSV. Postal rows are an additional projection of explicit post-tagged alternate records, never an inferred join.

Country/area scope and English scope names follow the United Nations Statistics Division M49 Caribbean grouping, https://unstats.un.org/unsd/methodology/m49/. Statistical grouping does not establish sovereignty or territorial status. Country codes and source language metadata are cross-referenced with the GeoNames `countryInfo.txt` snapshot whose checksum is recorded in `scope.json`.

The data remains CC BY 4.0 and is not relicensed as MIT. Python code adapts the source-preserving GeoNames builder used by the world-localities Africa registry under its MIT license. No CSC/ODbL administrative catalogue has been merged into this dataset.

Coordinates are source reference points. No current legal hierarchy, municipality completeness, native/English label completeness, postal completeness or deliverability is certified. No street or premise address data is included.
