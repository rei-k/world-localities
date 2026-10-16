"""Country-profiled address compatibility and validation contracts."""

from .components import CanonicalAddress, canonicalize_components
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
from .formatting import RenderedAddress, render_address
from .localized import RegionalAddressRegistry, render_regional_bilingual_address
from .profiles import AddressProfile, ProfileRegistry
from .southeast_asia import SoutheastAsiaRegistry, render_southeast_asia_address

__all__ = [
    "AddressProfile",
    "CanonicalAddress",
    "BilingualAddressResult",
    "EastAsiaRegistry",
    "LocalizedAddress",
    "LocationPrecision",
    "MissingLocalizedComponents",
    "ProfileRegistry",
    "RegionalAddressRegistry",
    "RenderedAddress",
    "SoutheastAsiaRegistry",
    "ValidationLevel",
    "ValidationResult",
    "canonicalize_components",
    "canonicalize_localized_components",
    "render_address",
    "render_bilingual_address",
    "render_regional_bilingual_address",
    "render_southeast_asia_address",
    "select_localized_components",
]
