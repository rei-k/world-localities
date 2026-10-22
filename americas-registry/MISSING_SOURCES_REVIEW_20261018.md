# Formerly missing Americas locality sources: review on 2026-10-18

## Result

The four missing M49 country/areas now have source gazetteer packs built from
GeoNames. The source-pack inventory is **57/57**, but the added layers are
partial gazetteers. This does not establish complete official municipalities,
localities, roads, house numbers, postal codes, translations or deliverability.

GeoNames publishes per-country extracts and alternate-name files, updated as a
rolling public service under CC BY 4.0. Each integration preserves the source
country identifiers, parent candidates, original names and language-tagged
alternate-name records. Primary GeoNames `name` and `asciiname` values do not
carry language tags; ASCII names are not treated as English translations.
Unresolved parent relationships remain unresolved. The original 18
government-attested administrative seed names for BM/GL/PM remain a separate
layer and are excluded from locality counts.

| M49 area | GeoNames raw rows | Packaged A/P entities | Locality features | Unresolved parents | Other source records |
|---|---:|---:|---:|---:|---|
| BM Bermuda | 677 | 43 | 31 | 0 | 370 linked alternate-name/reference rows |
| GL Greenland | 7,573 | 281 | 255 | 36 | 2,468 linked alternate-name/reference rows; 2 `post` tags |
| PM Saint Pierre and Miquelon | 522 | 16 | 13 | 0 | 200 linked alternate-name/reference rows; 2 `post` tags |
| CU Cuba | 46,767 | 16,270 | 16,083 | 58 | 19,580 linked alternate-name/reference rows |

`entities` includes A/P feature rows, not only populated places. `Locality
features` counts P-class rows. Direct `post` tags are stored separately and do
not establish postal-authority coverage.

## Source archive checksums

All files below were retrieved on 2026-10-18. Source and output checksums are
also recorded in each `countries/CC/metadata.json` and pinned by its region
manifest.

| Area | GeoNames entity source SHA-256 | Alternate-name source SHA-256 | Derived entity payload SHA-256 |
|---|---|---|---|
| BM | `fac21dc4235c3d522519ef2c71fd32906ca3336314385088dee5f27cf6871c6e` | `74fce6cbc9b92c1da03cd56f83089564714fc1463417c08bab5d08c5894bbfb9` | `fadabf599c0f2a57408f29f3fbc21272daa29a1ceae37d7ada23dd26cc06dd88` |
| GL | `e27333700814bfd58b3503f85bd9a7b4e273487d23f7cd96bf063b7305e19f32` | `f4212175e849f36557583c4d10c011e46a982398c145022c674498b680b4cde8` | `660b52cd9bc50754264aa0390c21a30bc4b920b6c8fd32904d35395fd5b0e1f7` |
| PM | `b883bafe4643fdc01deb881694a694c45d09e6dc62af27762cf824cbe9d59e91` | `fbbd03d1eb99f19905038931daaebe3a76bea5d1d784b561eb199b93fda375fd` | `ebc71566cb4ac384680d9c9e868ba1e1e03e4aec0b129fe29acfe1d6493ac547` |
| CU | `e312287eb3f50d17207a5884802d16ff90a58d388ad702371c725cadce2223ba` | `2f3a8f627e6657a5be6158f27db05296256973869d6db710dd6d3c42c80e7b81` | `01a682ebcea55b4aa0c666cb290101a2c001bf6891cd9f42da7c7654faa06488` |

## Official data reviewed and not copied

- **Bermuda:** the Government of Bermuda GIS service exposes addresses,
  buildings and survey-related map layers. Its service metadata includes
  Government Survey Section, Land Title Registry Office and Fugro BKS
  copyright attribution. A clear open redistribution licence was not found in
  the reviewed service metadata, so the raw layers were not copied. If the
  government supplies reuse terms, the address and road sources can be reviewed
  for a separate, source-specific integration. [Service metadata](https://gis.planning.gov.bm/arcgis/rest/services/Final_Layers_Separated_for_Online_Map_Viewer/MapServer/layers).
- **Greenland:** NunaGIS describes a public Place Names Register with about
  33,000 names and defined boundaries, authorized for official use by the
  Greenland Place Names Board. Its public ArcGIS layer exposes official,
  previous, variant, Danish and international names and municipality codes.
  The reviewed pages did not specify data redistribution terms. The records
  were not downloaded into this repository. Reuse terms from Oqaasileriffik,
  Asiaq or the relevant data owner are needed before the full official layer
  can be published; this is the largest remaining source-coverage opportunity.
  [NunaGIS web services](https://nunagis.gl/en/web-services/) ·
  [Public register layer](https://kort.nunagis.gl/refserver/rest/services/PlacenamesRegister/PlacenamesRegisterPublic/MapServer/0) ·
  [Place Names Committee](https://oqaasileriffik.gl/en/place-names/).
- **Saint Pierre and Miquelon:** INSEE provides the two French commune names
  and identifiers `97501` (Miquelon-Langlade) and `97502` (Saint-Pierre),
  retained in the seed catalogue. A complete, explicitly reusable locality
  gazetteer for the territory was not identified in this review. The GeoNames
  pack is the available source layer while the official boundary/locality
  dataset and reuse terms remain to be confirmed. [INSEE department 975
  source](https://www.insee.fr/fr/statistiques/fichier/8680702/dep975.pdf).
- **Cuba:** GeoNames lists Cuba's national data provider as `one_cu`,
  Oficina Nacional de Estadísticas, Cuba, but a directly downloadable,
  redistributable ONEI locality extract was not identified in this review. The
  GeoNames country file is included as an open fallback, not as the official
  national dataset. The official-data wait condition remains until a usable
  ONEI source, licence, vintage and identifiers can be pinned.
  [GeoNames Cuba source page](https://www.geonames.org/countries/CU/cuba.html).

The official source pages above provide evidence for named layers and
administrative facts, not blanket permission to redistribute their datasets.
No unsupported data was imported to fill those gaps.

## Reproduction and validation

From the repository root, using Python 3.11+ standard library:

    python north-america-registry/build.py verify
    python caribbean-registry/build.py verify
    python -m unittest discover -s north-america-registry -p 'test_*.py' -v
    python -m unittest discover -s caribbean-registry -p 'test_caribbean.py' -v
    python americas-registry/audit.py --mode audit
    python americas-registry/quality_cycle.py --area northern-america --area caribbean

Before Caribbean verification, materialize the split Dominican Republic file:

    python -m localities materialize --registry caribbean --country DO

Payload verification covers checksums, row counts, stable country-specific
IDs, code-based parent relations and candidates, alias foreign keys, postal
projections, and exact transform replay. The review does not download official
sources or certify national hierarchy, licence completeness, translation,
street/address coverage or delivery.
