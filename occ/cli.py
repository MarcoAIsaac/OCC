"""CLI entrypoint for OCC."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="occ",
        description="OCC command-line interface",
    )
    subparsers = parser.add_subparsers(dest="command")

    verify_parser = subparsers.add_parser("verify", help="Run verification checks")
    verify_parser.set_defaults(func=cmd_verify)

    return parser


def cmd_verify(_: argparse.Namespace) -> int:
    print("OCC verify: OK")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0

    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
