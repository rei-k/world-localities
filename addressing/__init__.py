"""Country-profiled address compatibility and validation contracts."""

from .components import CanonicalAddress, canonicalize_components
from .contracts import LocationPrecision, ValidationLevel, ValidationResult
from .formatting import RenderedAddress, render_address
from .profiles import AddressProfile, ProfileRegistry

__all__ = [
    "AddressProfile",
    "CanonicalAddress",
    "LocationPrecision",
    "ProfileRegistry",
    "RenderedAddress",
    "ValidationLevel",
    "ValidationResult",
    "canonicalize_components",
    "render_address",
]
