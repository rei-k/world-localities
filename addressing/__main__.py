"""Command line interface for worldwide address profiles and rendering."""

from __future__ import annotations

import argparse
import json

from .central_asia import CentralAsiaRegistry, render_central_asia_address
from .formatting import render_address
from .east_asia import EastAsiaRegistry, render_bilingual_address
from .profiles import ProfileRegistry
from .south_asia import SouthAsiaRegistry, render_south_asia_address
from .southeast_asia import SoutheastAsiaRegistry, render_southeast_asia_address
from .western_asia import WesternAsiaRegistry, render_western_asia_address
from .western_europe import WesternEuropeRegistry, render_western_europe_address


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify", help="verify all compiled country profiles")
    commands.add_parser("east-asia", help="report native/English East Asia coverage")
    commands.add_parser(
        "southeast-asia", help="report native/English Southeast Asia coverage"
    )
    commands.add_parser(
        "south-asia", help="report native/English Southern Asia coverage"
    )
    commands.add_parser(
        "central-asia", help="report native/English Central Asia coverage"
    )
    commands.add_parser(
        "western-asia", help="report native/English Western Asia coverage"
    )
    commands.add_parser(
        "western-europe", help="report native/English Western Europe coverage"
    )
    profile = commands.add_parser("profile", help="show a selected profile")
    render = commands.add_parser("render", help="render structured address JSON")
    for command in (profile, render):
        command.add_argument("--country", required=True)
        command.add_argument("--language")
        command.add_argument("--international", action="store_true")
    render.add_argument("--components-json", required=True)
    bilingual = commands.add_parser(
        "render-bilingual", help="render strict native and English East Asia output"
    )
    bilingual.add_argument("--country", required=True)
    bilingual.add_argument("--native-language")
    bilingual.add_argument("--components-json", required=True)
    bilingual.add_argument("--allow-incomplete", action="store_true")
    southeast = commands.add_parser(
        "render-southeast-asia",
        help="render strict native and English Southeast Asia output",
    )
    southeast.add_argument("--country", required=True)
    southeast.add_argument("--native-language")
    southeast.add_argument("--components-json", required=True)
    southeast.add_argument("--allow-incomplete", action="store_true")
    south = commands.add_parser(
        "render-south-asia",
        help="render strict native and English Southern Asia output",
    )
    south.add_argument("--country", required=True)
    south.add_argument("--native-language")
    south.add_argument("--components-json", required=True)
    south.add_argument("--allow-incomplete", action="store_true")
    central = commands.add_parser(
        "render-central-asia",
        help="render strict native and English Central Asia output",
    )
    central.add_argument("--country", required=True)
    central.add_argument("--native-language")
    central.add_argument("--components-json", required=True)
    central.add_argument("--allow-incomplete", action="store_true")
    western = commands.add_parser(
        "render-western-asia",
        help="render strict native and English Western Asia output",
    )
    western.add_argument("--country", required=True)
    western.add_argument("--native-language")
    western.add_argument("--components-json", required=True)
    western.add_argument("--allow-incomplete", action="store_true")
    western_europe = commands.add_parser(
        "render-western-europe",
        help="render strict native and English Western Europe output",
    )
    western_europe.add_argument("--country", required=True)
    western_europe.add_argument("--native-language")
    western_europe.add_argument("--components-json", required=True)
    western_europe.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    registry = ProfileRegistry()
    if args.command == "verify":
        print(json.dumps(registry.report(), sort_keys=True))
        return
    if args.command == "east-asia":
        print(json.dumps(EastAsiaRegistry().report(), sort_keys=True))
        return
    if args.command == "southeast-asia":
        print(json.dumps(SoutheastAsiaRegistry().report(), sort_keys=True))
        return
    if args.command == "south-asia":
        print(json.dumps(SouthAsiaRegistry().report(), sort_keys=True))
        return
    if args.command == "central-asia":
        print(json.dumps(CentralAsiaRegistry().report(), sort_keys=True))
        return
    if args.command == "western-asia":
        print(json.dumps(WesternAsiaRegistry().report(), sort_keys=True))
        return
    if args.command == "western-europe":
        print(json.dumps(WesternEuropeRegistry().report(), sort_keys=True))
        return
    if args.command == "render-bilingual":
        components = json.loads(args.components_json)
        if not isinstance(components, dict):
            parser.error("--components-json must contain a JSON object")
        result = render_bilingual_address(
            components,
            args.country,
            native_language=args.native_language,
            strict=not args.allow_incomplete,
            registry=registry,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return
    if args.command == "render-southeast-asia":
        components = json.loads(args.components_json)
        if not isinstance(components, dict):
            parser.error("--components-json must contain a JSON object")
        result = render_southeast_asia_address(
            components,
            args.country,
            native_language=args.native_language,
            strict=not args.allow_incomplete,
            registry=registry,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return
    if args.command == "render-south-asia":
        components = json.loads(args.components_json)
        if not isinstance(components, dict):
            parser.error("--components-json must contain a JSON object")
        result = render_south_asia_address(
            components,
            args.country,
            native_language=args.native_language,
            strict=not args.allow_incomplete,
            registry=registry,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return
    if args.command == "render-central-asia":
        components = json.loads(args.components_json)
        if not isinstance(components, dict):
            parser.error("--components-json must contain a JSON object")
        result = render_central_asia_address(
            components,
            args.country,
            native_language=args.native_language,
            strict=not args.allow_incomplete,
            registry=registry,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return
    if args.command == "render-western-asia":
        components = json.loads(args.components_json)
        if not isinstance(components, dict):
            parser.error("--components-json must contain a JSON object")
        result = render_western_asia_address(
            components,
            args.country,
            native_language=args.native_language,
            strict=not args.allow_incomplete,
            registry=registry,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return
    if args.command == "render-western-europe":
        components = json.loads(args.components_json)
        if not isinstance(components, dict):
            parser.error("--components-json must contain a JSON object")
        result = render_western_europe_address(
            components,
            args.country,
            native_language=args.native_language,
            strict=not args.allow_incomplete,
            registry=registry,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
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
