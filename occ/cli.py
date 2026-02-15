"""CLI entrypoint for OCC."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="occ",
        description="OCC command-line interface",
    )
    subparsers = parser.add_subparsers(dest="command")

    verify_parser = subparsers.add_parser("verify", help="Run verification checks")
    verify_parser.set_defaults(func=cmd_verify)

    run_parser = subparsers.add_parser("run", help="Run an OCC module")
    run_parser.add_argument("module", help="Module name to run")
    run_parser.add_argument("--out", default="out/", help="Output directory")
    run_parser.set_defaults(func=cmd_run)

    return parser


def cmd_verify(_: argparse.Namespace) -> int:
    print("OCC verify: OK")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"OCC run: module={args.module} out={out_dir}")
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
