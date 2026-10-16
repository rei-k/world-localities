"""Validate the repository's registry catalog and stable directory boundaries."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = Path(__file__).with_name("registry_catalog.json")
ROLES = {"official_overlay", "regional_coordinator", "regional_registry"}


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalog(root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    catalog = load_catalog()
    if catalog.get("schema_version") != 1 or catalog.get("package") != "localities":
        raise ValueError("unsupported registry catalog")

    paths: set[str] = set()
    for registry in catalog.get("registries", []):
        relative = PurePosixPath(registry["path"])
        if relative.is_absolute() or len(relative.parts) != 1 or relative.name in paths:
            raise ValueError("invalid or duplicate registry path")
        if registry.get("role") not in ROLES or not registry.get("scope"):
            raise ValueError(f"invalid registry entry: {relative}")
        directory = root / relative
        if not directory.is_dir() or not (directory / "README.md").is_file():
            raise ValueError(f"missing registry or README: {relative}")
        paths.add(relative.name)

    consumers: set[str] = set()
    for component in catalog.get("shared_components", []):
        module_path = root.joinpath(*component["module"].split(".")).with_suffix(".py")
        if not module_path.is_file():
            raise ValueError(f"missing shared component: {component['module']}")
        for name in component.get("consumers", []):
            relative = PurePosixPath(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe shared-component consumer")
            if name in consumers or not (root / relative).is_file():
                raise ValueError(f"missing or duplicate consumer: {name}")
            consumers.add(name)

    return {
        "status": "passed",
        "registry_count": len(paths),
        "shared_component_count": len(catalog["shared_components"]),
        "consumer_count": len(consumers),
    }


if __name__ == "__main__":
    print(json.dumps(validate_catalog(), sort_keys=True))
