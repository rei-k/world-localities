"""Strict domestic-language and English address selection for Oceania."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Mapping

from .localized import (
    BilingualAddressResult,
    RegionalAddressRegistry,
    render_regional_bilingual_address,
)
from .profiles import ProfileRegistry


CONFIG_PATH = Path(__file__).with_name("oceania_profiles.json")
COUNTRIES = {
    "AS",
    "AU",
    "CC",
    "CK",
    "CX",
    "FJ",
    "FM",
    "GU",
    "HM",
    "KI",
    "MH",
    "MP",
    "NC",
    "NF",
    "NR",
    "NU",
    "NZ",
    "PF",
    "PG",
    "PN",
    "PW",
    "SB",
    "TK",
    "TO",
    "TV",
    "UM",
    "VU",
    "WF",
    "WS",
}


class OceaniaRegistry(RegionalAddressRegistry):
    """Address policies for every UN M49 Oceania country or territory."""

    def __init__(self, path: Path = CONFIG_PATH):
        super().__init__(
            path,
            region_name="Oceania",
            expected_countries=COUNTRIES,
        )
        self.locality_registry = self.payload["locality_registry"]
        self._verify_postcode_policies()

    def _verify_postcode_policies(self) -> None:
        for country_code, policy in self.countries.items():
            if "postcode_pattern" not in policy:
                raise ValueError(f"postcode policy missing: {country_code}")
            pattern = policy["postcode_pattern"]
            if pattern is not None:
                re.compile(str(pattern))
            if not isinstance(policy.get("postcode_required"), bool):
                raise ValueError(f"postcode requirement missing: {country_code}")

    def validate_postcode(self, country_code: str, postcode: str | None) -> bool:
        """Check syntax only; this does not assert that a code was assigned."""

        policy = self.get(country_code)
        if postcode is None or not postcode.strip():
            return not policy["postcode_required"]
        pattern = policy["postcode_pattern"]
        if pattern is None:
            return False
        return re.fullmatch(str(pattern), postcode.strip(), re.IGNORECASE) is not None


def render_oceania_address(
    components: Mapping[str, str | None | Mapping[str, str | None]],
    country_code: str,
    *,
    native_language: str | None = None,
    strict: bool = True,
    registry: ProfileRegistry | None = None,
    oceania: OceaniaRegistry | None = None,
) -> BilingualAddressResult:
    return render_regional_bilingual_address(
        components,
        country_code,
        region=oceania or OceaniaRegistry(),
        native_language=native_language,
        strict=strict,
        registry=registry,
    )


__all__ = ["OceaniaRegistry", "render_oceania_address"]
