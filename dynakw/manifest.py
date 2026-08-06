"""Command line access to the capability report.

For consumers that are not running in this process::

    python -m dynakw.manifest --format json > dynakw_capabilities.json

and for reading at a terminal::

    python -m dynakw.manifest
    python -m dynakw.manifest --pattern '*SET_*'
    python -m dynakw.manifest --describe '*MAT_ELASTIC_FLUID'
"""

import argparse
import json
import sys

from dynakw import __version__
from dynakw.core.introspect import (
    KeywordNotSupported,
    capability_manifest,
    describe_keyword,
    supported_keywords,
)


def _format_summary(pattern=None) -> str:
    """One line per keyword: name, card count and what can be done with it."""
    specs = supported_keywords(pattern)
    if not specs:
        return f"No keywords match {pattern!r}."

    width = max(len(s.keyword) for s in specs)
    lines = [f"dynakw {__version__} — {len(specs)} keywords", ""]
    lines.append(f"{'KEYWORD'.ljust(width)}  CARDS  BUILD  NOTE")

    for s in specs:
        if s.schema_driven:
            note = "schema-driven"
        elif s.custom_write:
            note = "custom parse and write" if s.custom_parse else "custom write"
        else:
            note = "custom parse"
        lines.append(
            f"{s.keyword.ljust(width)}  {len(s.cards):>5}  "
            f"{'yes' if s.can_build else 'no':<5}  {note}")

    lines.append("")
    lines.append("BUILD = a cards dict shaped by the schemas writes correctly.")
    return "\n".join(lines)


def _format_detail(name: str) -> str:
    """The cards and fields of one concrete keyword variant."""
    spec = describe_keyword(name)

    out = [spec.keyword]
    if spec.aliases:
        out.append(f"  also: {', '.join(spec.aliases)}")
    if spec.description:
        out.append(f"  {spec.description}")
    if spec.manual_section:
        out.append(f"  manual: {spec.manual_section}")
    out.append(f"  parse: {'yes' if spec.can_parse else 'no'}   "
               f"build: {'yes' if spec.can_build else 'no'}")

    if not spec.cards:
        out.append("")
        out.append("  No card structure — the block is kept as raw text.")
        return "\n".join(out)

    for card in spec.cards:
        out.append("")
        flags = []
        if card.repeating:
            flags.append("repeating")
        if card.dynamic:
            flags.append("dynamic")
        suffix = f"  [{', '.join(flags)}]" if flags else ""
        out.append(f"  {card.name}{suffix}")
        if card.description:
            out.append(f"    {card.description}")
        if card.condition_doc:
            out.append(f"    Applies: {card.condition_doc}")

        name_w = max(len(f.name) for f in card.fields)
        for f in card.fields:
            bits = [f"{f.type}{f.width}"]
            if f.required:
                bits.append("required")
            if f.units:
                bits.append(f.units)
            if not f.stored:
                bits.append("not stored")
            out.append(f"      {f.name.ljust(name_w)}  "
                       f"{('(' + ', '.join(bits) + ')').ljust(24)} "
                       f"{f.description}")
            if f.choices:
                for value, meaning in f.choices.items():
                    out.append(f"      {' ' * name_w}    {value}: {meaning}")

    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m dynakw.manifest",
        description="Report which LS-DYNA keywords dynakw implements.")
    parser.add_argument(
        "--describe", metavar="KEYWORD",
        help="Show the cards and fields of one keyword variant, "
             "e.g. '*MAT_ELASTIC_FLUID'.")
    parser.add_argument(
        "--pattern", metavar="GLOB",
        help="Only keywords matching this fnmatch pattern, e.g. '*SET_*'.")
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="Output format (default: text).")
    args = parser.parse_args(argv)

    try:
        if args.describe:
            if args.format == "json":
                print(json.dumps(describe_keyword(args.describe).to_dict(),
                                 indent=2))
            else:
                print(_format_detail(args.describe))
        elif args.format == "json":
            print(json.dumps(capability_manifest(args.pattern), indent=2))
        else:
            print(_format_summary(args.pattern))
    except KeywordNotSupported as exc:
        print(exc, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
