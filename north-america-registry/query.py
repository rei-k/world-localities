#!/usr/bin/env python3
"""Read existing US/CA source localities through the M49 Northern America view.

No geographical name, postal code, street address or translation is generated.
M49 Northern America (021) excludes Puerto Rico; US source material can still
be inspected with an explicit cross-region override.
"""
import argparse
import csv
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = Path(__file__).resolve().parent


class QueryError(ValueError):
    """An unavailable/invalid query or a source consistency problem."""


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def _metadata(registry):
    scope = load_json(registry / "scope.json")
    corrections = load_json(registry / "name-overrides.json")
    by_country = {c["country"]: c for c in scope["countries"]}
    if len(by_country) != 5 or set(by_country) != {"BM", "CA", "GL", "PM", "US"}:
        raise QueryError("Northern America M49 country catalogue changed")
    overrides = {(x["country"], x["state_code"]): x for x in corrections["entries"]}
    if len(overrides) != len(corrections["entries"]):
        raise QueryError("duplicate presentation override")
    return scope, by_country, overrides


def administrative_seeds(registry, country, text=None, limit=20):
    data = load_json(registry / "admin-seeds.json")
    records = []
    seen = set()
    for row in data["records"]:
        identity = row["provisional_id"]
        if identity in seen:
            raise QueryError("duplicated provisional administrative seed ID")
        seen.add(identity)
        if row["evidence_id"] not in data["source_evidence"]:
            raise QueryError("administrative seed is missing source evidence")
        if row["country"] != country:
            continue
        if text and normalized(text) not in normalized(row["source_name"]):
            continue
        records.append({
            "provisional_id": identity,
            "name": row["source_name"],
            "language": row["language"],
            "kind": row["kind"],
            "official_code": row["official_code"],
            "evidence_url": data["source_evidence"][row["evidence_id"]]["url"],
            "locality_status": "administrative_seed_only",
            "postal_or_street_verified": False
        })
    return records[:limit], len(records)


def display_region_name(country, region, overrides):
    change = overrides.get((country, region["code"]))
    if change is None:
        return region["name"]
    if region["name"] != change["snapshot_name"]:
        raise QueryError("source region name changed; review display override")
    if change["status"] != "verified_presentation_correction" or not change["evidence_url"]:
        raise QueryError("unverified display correction")
    return change["display_name_en"]


def search(country, *, region=None, text=None, limit=20,
           candidate_only=False, include_cross_region_pr=False, root=ROOT):
    """Search source rows; status distinguishes missing data from empty results."""
    country = country.upper()
    region = region.upper() if region else None
    if not isinstance(limit, int) or not 1 <= limit <= 500:
        raise QueryError("limit must be an integer from 1 to 500")
    scope, countries, overrides = _metadata(root / "north-america-registry")
    profile = countries.get(country)
    if profile is None:
        raise QueryError(f"{country}: country is outside M49 Northern America (021)")
    if include_cross_region_pr and country != "US":
        raise QueryError("the Puerto Rico source exception is only valid for US")
    if profile["status"] == "pending_locality_source":
        if region:
            raise QueryError(f"{country}: no region catalogue has been loaded")
        seeds, count = administrative_seeds(root / "north-america-registry", country, text, limit)
        return {
            "country": country, "m49_region": "021", "status": "not_loaded",
            "source_layer": None, "source_locality_rows": None,
            "rows_scanned": None, "matches_found": None, "results": [],
            "administrative_seeds": seeds, "administrative_seed_matches": count,
            "administrative_seeds_truncated": count > limit,
            "limitations": [
                "Administrative seed names are evidence-backed but not a full locality gazetteer.",
                "No verified locality source has been installed; an empty locality result does not mean no places exist.",
                "Administrative seeds cannot validate postal addresses or street and unit numbers."
            ]
        }
    if profile["status"] != "preserved_official_snapshot":
        raise QueryError(f"{country}: unknown source status")

    index_path = root / profile["source_index"]
    index = load_json(index_path)
    if index["country"] != country:
        raise QueryError("country mismatch in source index")
    region_by_code = {item["code"]: item for item in index["regions"]}
    if len(region_by_code) != len(index["regions"]):
        raise QueryError("duplicate source region code")
    if region and region not in region_by_code:
        raise QueryError(f"{region}: unknown source region")
    exclusions = set(profile.get("excluded_state_codes_for_m49", []))
    if region in exclusions and not include_cross_region_pr:
        raise QueryError(f"{region}: outside M49 021; use explicit --include-cross-region-pr")
    source_dir = index_path.parent
    output, scanned, matched = [], 0, 0
    for state in index["regions"]:
        if region and state["code"] != region:
            continue
        if state["code"] in exclusions and not include_cross_region_pr:
            continue
        display = display_region_name(country, state, overrides)
        source_file = source_dir / state["file"]
        if source_file.parent != source_dir:
            raise QueryError("unsafe region file path")
        with source_file.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != index["columns"]:
                raise QueryError(f"{source_file}: unexpected CSV columns")
            for row in reader:
                if row["state_code"] != state["code"]:
                    raise QueryError(f"{source_file}: state code mismatch")
                scanned += 1
                if candidate_only and row["address_candidate"] != "1":
                    continue
                if text and normalized(text) not in normalized(row["name"]):
                    continue
                matched += 1
                if len(output) < limit:
                    output.append({
                        "id": row["id"],
                        "source_code": row["code"],
                        "name": row["name"],
                        "language": row["lang"],
                        "source_type": row["source_type"],
                        "category": row["category"],
                        "parent_id": row["parent_id"],
                        "region_code": state["code"],
                        "region_name": display,
                        "region_name_in_snapshot": state["name"],
                        "address_country": row["address_country"],
                        "address_candidate_flag": row["address_candidate"] == "1",
                        "postal_assignment_verified": False,
                        "delivery_verified": False
                    })
    return {
        "country": country, "m49_region": "021",
        "status": "source_snapshot_available",
        "source_layer": profile["source_index"],
        "source_vintage": index["vintage"],
        "source_locality_rows": index["counts"]["source_localities"],
        "excluded_source_region_codes": sorted(exclusions) if not include_cross_region_pr else [],
        "cross_region_override_used": bool(include_cross_region_pr),
        "rows_scanned": scanned, "matches_found": matched,
        "results_truncated": matched > limit, "results": output,
        "limitations": [
            "Census/statistical areas are not all independent municipalities.",
            "address_candidate is a source selection flag, not postal deliverability.",
            "No postal assignments, street/house-number validation or official translations are claimed."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", required=True, help="US, CA, BM, GL or PM")
    parser.add_argument("--region", help="e.g. US-NY or CA-QC")
    parser.add_argument("--text", help="substring match, Unicode accent-insensitive")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--candidate-only", action="store_true")
    parser.add_argument("--include-cross-region-pr", action="store_true")
    args = parser.parse_args()
    try:
        report = search(
            args.country, region=args.region, text=args.text, limit=args.limit,
            candidate_only=args.candidate_only,
            include_cross_region_pr=args.include_cross_region_pr
        )
    except (QueryError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
