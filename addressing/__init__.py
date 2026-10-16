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
from .profiles import AddressProfile, ProfileRegistry

__all__ = [
    "AddressProfile",
    "CanonicalAddress",
    "BilingualAddressResult",
    "EastAsiaRegistry",
    "LocalizedAddress",
    "LocationPrecision",
    "MissingLocalizedComponents",
    "ProfileRegistry",
    "RenderedAddress",
    "ValidationLevel",
    "ValidationResult",
    "canonicalize_components",
    "canonicalize_localized_components",
    "render_address",
    "render_bilingual_address",
    "select_localized_components",
]
