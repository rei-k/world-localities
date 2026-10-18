# Northern America locality sources (UN M49 021)

This directory is a **source-preserving quality layer**, not a claim that every
name, boundary, street, address, or postal code is covered. In UN M49,
Northern America (021) has five countries/areas: Bermuda (BM), Canada (CA),
Greenland (GL), Saint Pierre and Miquelon (PM), and the United States (US).
The larger *North America* (003) also includes Central America and the
Caribbean. See the [official UN M49 list](https://unstats.un.org/unsd/methodology/m49/overview/).

## Source status, 2026-10-18

| M49 country/area | Locality rows in source layer | Source entities | Layer and limits |
|---|---:|---:|---|
| US | 68,744 (1,231 US-PR rows are Caribbean in M49) | 68,744 | Preserved 2026 Census snapshot, 52 region files |
| CA | 5,054 | 5,054 | Preserved Statistics Canada 2025 census subdivision snapshot, 13 province/territory files |
| BM | 31 | 43 | GeoNames CC BY 4.0 country extract; partial gazetteer |
| GL | 255 | 281 | GeoNames CC BY 4.0 country extract; partial gazetteer |
| PM | 13 | 16 | GeoNames CC BY 4.0 country extract; partial gazetteer |

The M49 view contains **72,866 source locality rows** after excluding US-PR
from the US source total and adding the three GeoNames locality counts. For
BM/GL/PM, the GeoNames packs retain 340 A/P source entities: 299 populated
place features, 36 administrative subdivisions, and five other administrative
features. Greenland has 36 unresolved parent references, retained as
unresolved instead of guessed. Four `post` alternate-name observations are
stored as source tags; they do not verify a territory's postal system.

The country packages were retrieved from GeoNames on 2026-10-18. Each metadata
file pins the country ZIP SHA-256 and byte size; entity, alternate-name,
administrative preview and postal projection files have their own checksums.
Identifiers remain `gn:<geonameid>` and `gn-alt:<alternateNameId>`. Parent
links are assigned only from exact source administrative-code tuples; missing
or ambiguous links remain explicit. Primary `name`/`asciiname` have no language
tag. Language-tagged variants stay linked by exact GeoNames ID, and no English
translation is inferred from ASCII spelling.

The original [18-name administrative seed catalogue](admin-seeds.json) is
retained as a separate layer: Bermuda's nine parishes and two municipalities,
Greenland's five municipalities, and Saint Pierre and Miquelon's two French
communes (`97501`, `97502`). Seed records are not merged into GeoNames rows and
cannot validate postal or street addresses. The query result returns them in
`administrative_seeds` separately from `results`.

## Official source candidates and rights

- **Bermuda:** the Government's public GIS service exposes an address layer and
  building features. Its service metadata names the Government Survey Section,
  Land Title Registry Office and Fugro BKS, but an open redistribution licence
  was not found. The address/building data were not copied into this repository.
  See the [service metadata](https://gis.planning.gov.bm/arcgis/rest/services/Final_Layers_Separated_for_Online_Map_Viewer/MapServer/layers).
- **Greenland:** NunaGIS describes a countrywide Place Names Register with
  about 33,000 official-use names and boundaries, maintained with the Greenland
  Place Names Board. The public ArcGIS service exposes Kalaallisut, Danish and
  international name fields plus municipal codes. The reviewed public pages
  did not state a redistribution licence, so the records were not copied.
  Obtain reuse terms from the responsible authority before replacing or
  augmenting the CC BY GeoNames layer. See [NunaGIS web services](https://nunagis.gl/en/web-services/)
  and its [public register layer](https://kort.nunagis.gl/refserver/rest/services/PlacenamesRegister/PlacenamesRegisterPublic/MapServer/0).
- **Saint Pierre and Miquelon:** the two official commune names and INSEE COG
  identifiers are held separately in the seed catalogue. A complete, openly
  reusable locality gazetteer was not identified in this review.
- **United States:** the preserved Census snapshot excludes other US Island
  Areas. The 2026 Gazetteer does not make those areas complete.

These are source acquisition gaps, not missing settlements. The partial
GeoNames packs provide a usable baseline while official-source rights,
hierarchies, and crosswalks remain under review.

## Read localities

Run at the repository root with Python 3.11+ standard library:

    python north-america-registry/build.py verify
    python north-america-registry/query.py --country US --region US-CA --text San --limit 10
    python north-america-registry/query.py --country CA --region CA-NS --text Shelburne
    python north-america-registry/query.py --country GL --text Nuuk
    python north-america-registry/query.py --country GL --candidate-only --limit 10
    python north-america-registry/query.py --country US --region US-PR --include-cross-region-pr

For a GeoNames country, `--region` accepts the stable ID of an ADM1 row, such
as `gn:<geonameid>` returned as `state_id`. The query preserves the source
feature code, parent relation and candidates, primary source name, and up to
20 language-tagged aliases. Its address-candidate flag is only the GeoNames
source role; it is not a deliverability finding.

The default US view omits US-PR from Northern America. The explicit override
preserves inspection of source data; it does **not** make Puerto Rico part of
UN M49 Northern America. The Caribbean GeoNames PR layer remains independent.
**Do not add both layers as unique localities.**

`name-overrides.json` corrects one proven display defect: Canada `CA-NS` is
mistakenly labelled "New Scotia" in the preserved country index. The
presentation layer displays **Nova Scotia**, backed by [Statistics Canada
2025](https://www150.statcan.gc.ca/n1/pub/72-212-x/2025001/sect4-eng.htm).
The original country files, index, manifests, and hashes are unchanged.

## Reproduce and verify

To rebuild the three GeoNames packs, download `BM.zip`, `GL.zip`, `PM.zip`, and
their country-specific alternate-name archives from
`https://download.geonames.org/export/dump/`, then run:

    python north-america-registry/build.py build --inputs /path/to/source-files --retrieved-on YYYY-MM-DD --prepared-on YYYY-MM-DD
    python north-america-registry/build.py verify
    python -m unittest discover -s north-america-registry -p 'test_*.py' -v

The checked-in source archive checksums detect rolling upstream changes; a
later download can differ. Raw ZIPs are not included. The shipped records
retain original GeoNames fields for offline transform replay. Data are
GeoNames, CC BY 4.0; code is MIT. This package verifies integrity and exact
transformation replay, not legal hierarchy, accuracy, freshness, postal
assignment, or deliverability.

## Follow-up quality targets

1. Resolve official source reuse terms for Bermuda and Greenland and record any
   official-to-GeoNames ID crosswalk only when supported by source evidence.
2. Obtain a reusable full locality source for Saint Pierre and Miquelon and
   validate its commune codes against INSEE.
3. Independently attest official/local-language and English labels; preserve
   source language tags and avoid generated translations.
4. Acquire exact postal authority crosswalks; never treat source `post` tags,
   Census ZCTAs or Canadian CSDs as verified delivery zones.
5. Add licensed street, house-range, premise and subpremise sources only with
   separate evidence and coverage reports.

See [the Americas orchestration layer](../americas-registry/README.md) and the
[four-source review](../americas-registry/MISSING_SOURCES_REVIEW_20261018.md).
