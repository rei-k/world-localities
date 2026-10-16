"""Country-profiled address compatibility and validation contracts."""

from .components import CanonicalAddress, canonicalize_components
from .central_asia import CentralAsiaRegistry, render_central_asia_address
from .central_europe import CentralEuropeRegistry, render_central_europe_address
from .contracts import LocationPrecision, ValidationLevel, ValidationResult
from .east_asia import (
    BilingualAddressResult,
    EastAsiaRegistry,
    LocalizedAddress,
    MissingLocalizedComponents,
    canonicalize_localized_components,
    render_bilingual_address,
    select_localized_components,
)
from .eastern_europe import EasternEuropeRegistry, render_eastern_europe_address
from .formatting import RenderedAddress, render_address
from .localized import (
    PostcodeRegionalAddressRegistry,
    RegionalAddressRegistry,
    render_regional_bilingual_address,
)
from .northern_africa import (
    NorthernAfricaRegistry,
    render_northern_africa_address,
)
from .northern_europe import NorthernEuropeRegistry, render_northern_europe_address
from .oceania import OceaniaRegistry, render_oceania_address
from .profiles import AddressProfile, ProfileRegistry
from .south_asia import SouthAsiaRegistry, render_south_asia_address
from .southern_europe import SouthernEuropeRegistry, render_southern_europe_address
from .southeast_asia import SoutheastAsiaRegistry, render_southeast_asia_address
from .western_asia import WesternAsiaRegistry, render_western_asia_address
from .western_europe import WesternEuropeRegistry, render_western_europe_address

__all__ = [
    "AddressProfile",
    "CanonicalAddress",
    "BilingualAddressResult",
    "CentralAsiaRegistry",
    "CentralEuropeRegistry",
    "EastAsiaRegistry",
    "EasternEuropeRegistry",
    "LocalizedAddress",
    "LocationPrecision",
    "MissingLocalizedComponents",
    "NorthernAfricaRegistry",
    "NorthernEuropeRegistry",
    "OceaniaRegistry",
    "PostcodeRegionalAddressRegistry",
    "ProfileRegistry",
    "RegionalAddressRegistry",
    "RenderedAddress",
    "SoutheastAsiaRegistry",
    "SouthAsiaRegistry",
    "SouthernEuropeRegistry",
    "ValidationLevel",
    "ValidationResult",
    "WesternAsiaRegistry",
    "WesternEuropeRegistry",
    "canonicalize_components",
    "canonicalize_localized_components",
    "render_address",
    "render_bilingual_address",
    "render_central_asia_address",
    "render_central_europe_address",
    "render_eastern_europe_address",
    "render_northern_africa_address",
    "render_northern_europe_address",
    "render_oceania_address",
    "render_regional_bilingual_address",
    "render_south_asia_address",
    "render_southern_europe_address",
    "render_southeast_asia_address",
    "render_western_asia_address",
    "render_western_europe_address",
    "select_localized_components",
]
