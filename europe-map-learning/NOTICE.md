# Attribution and source-specific terms

This experiment combines independent data sources. It does not replace their licences
with a single blanket licence. Keep this notice with redistributed data and maps.
Exact input URLs, hashes, boundary IDs, years and original metadata are in `sources.json`.

## Locality names and points

GeoNames, https://www.geonames.org/, retrieved 2026-09-29.
Creative Commons Attribution 4.0: https://creativecommons.org/licenses/by/4.0/.
Changes: selection of populated-place candidates, geographic projection and point-in-polygon
linkage, appended model features, hypothetical region claims and uncertainty radii.
Original registry values are retained; this experiment does not edit the source registry.

## Boundary distribution

geoBoundaries / William & Mary geoLab, https://www.geoboundaries.org/.
Archive reference `9469f09` from its API, with independent SHA256 pinning.
Use the metadata's `gjDownloadURL` for the source dataset URI. geoBoundaries is the
distributor; the following country-specific original source terms remain applicable.

### Austria — AT, represented year 2017

Provider: geoBoundaries and Federal Office for Metrology and Survey, Austria.
The source metadata identifies Creative Commons Attribution-ShareAlike 2.0:
https://creativecommons.org/licenses/by-sa/2.0/.
The AT boundary adaptations in `data/map-preview.geojson`, `map.html` and
`results/map-overview.svg`, and AT boundary-derived contributions in the training/audit
data, are offered under the same CC BY-SA 2.0 terms. Keep attribution and share-alike terms
when adapting these components. This does not relicense independent Swiss or German data.

### Germany — DE, represented year 2021

Provider: Federal Agency for Cartography and Geodesy (Bundesamt für Kartographie und Geodäsie).
Data licence Germany – Attribution – Version 2.0:
https://www.govdata.de/dl-de/by-2-0.
Dataset URI: https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/DEU/ADM1/geoBoundaries-DEU-ADM1.geojson.

### Switzerland — CH, represented year 2022

Source reference: Federal Office of Topography swisstopo (©swisstopo).
Original metadata identifies the swisstopo licence. Current official terms:
https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices.
The terms allow use, processing and redistribution with source attribution.
The legacy terms URL supplied with the snapshot is also preserved in `sources.json`.

## Boundary processing and interpretation

Grounding: project full-resolution WGS84 coordinates to EPSG:3035 and perform geometric
intersection and distance-to-boundary checks. Invalid polygons would stop preprocessing;
none were silently repaired in this run. Preview only: simplify in EPSG:3035 with 300m
tolerance, preserving per-feature topology, then convert to WGS84 and an SVG Mercator display.
Preview shapes may have seams; original geometry, not preview shapes, defines labels.

Different snapshot years are deliberately disclosed. Neither learned predictions nor
geometry matches establish present-day legal status, official addresses or deliverability.
OpenStreetMap links are optional external inspection links. OSM data/tiles are not copied
into the training files or automatically fetched by the HTML.
