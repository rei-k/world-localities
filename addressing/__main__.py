"""Command line interface for worldwide address profiles and rendering."""

from __future__ import annotations

import argparse
import json

from .formatting import render_address
from .profiles import ProfileRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify", help="verify all compiled country profiles")
    profile = commands.add_parser("profile", help="show a selected profile")
    render = commands.add_parser("render", help="render structured address JSON")
    for command in (profile, render):
        command.add_argument("--country", required=True)
        command.add_argument("--language")
        command.add_argument("--international", action="store_true")
    render.add_argument("--components-json", required=True)
    args = parser.parse_args()
    registry = ProfileRegistry()
    if args.command == "verify":
        print(json.dumps(registry.report(), sort_keys=True))
        return
    selected = registry.select(
        args.country, language=args.language, international=args.international
    )
    if args.command == "profile":
        print(
            json.dumps(
                {
                    "key": selected.key,
                    "country_code": selected.country_code,
                    "language": selected.language,
                    "inherited_from": selected.inherited_from,
                    "config": selected.config,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return
    components = json.loads(args.components_json)
    if not isinstance(components, dict):
        parser.error("--components-json must contain a JSON object")
    result = render_address(
        components,
        args.country,
        language=args.language,
        international=args.international,
        registry=registry,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
