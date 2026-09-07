"""Command-line interface for subnetcalc."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import Subnet

_ROWS = (
    ("CIDR", "cidr"),
    ("Network", "network"),
    ("Broadcast", "broadcast"),
    ("Netmask", "netmask"),
    ("Wildcard", "wildcard"),
    ("First host", "first_host"),
    ("Last host", "last_host"),
    ("Usable hosts", "usable_hosts"),
    ("Total addresses", "total_addresses"),
    ("Class", "class"),
    ("Private (RFC 1918)", "private"),
)


def _format_table(data: dict) -> str:
    width = max(len(label) for label, _ in _ROWS)
    lines = [f"{label:<{width}} : {data[key]}" for label, key in _ROWS]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subnetcalc",
        description="IPv4 subnet calculator with no dependencies.",
    )
    parser.add_argument(
        "cidr",
        help="network in CIDR form, e.g. 192.168.1.0/24 or 10.0.0.0/255.0.0.0",
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="emit JSON instead of a table"
    )
    parser.add_argument(
        "-s",
        "--split",
        type=int,
        metavar="N",
        help="divide the block into at least N equal subnets",
    )
    parser.add_argument(
        "-c",
        "--contains",
        metavar="IP",
        help="check whether IP belongs to the network and exit 0/1",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        subnet = Subnet.parse(args.cidr)
    except ValueError as exc:
        parser.error(str(exc))

    if args.contains is not None:
        try:
            inside = subnet.contains(args.contains)
        except ValueError as exc:
            parser.error(str(exc))
        print(f"{args.contains} is {'in' if inside else 'NOT in'} {subnet.as_dict()['cidr']}")
        return 0 if inside else 1

    if args.split is not None:
        try:
            pieces = subnet.split(args.split)
        except ValueError as exc:
            parser.error(str(exc))
        if args.json:
            print(json.dumps([p.as_dict() for p in pieces], indent=2))
        else:
            for piece in pieces:
                info = piece.as_dict()
                print(
                    f"{info['cidr']:<20} {info['first_host']} - {info['last_host']}"
                    f"  ({info['usable_hosts']} hosts)"
                )
        return 0

    data = subnet.as_dict()
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(_format_table(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
