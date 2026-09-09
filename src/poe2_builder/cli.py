from __future__ import annotations

import argparse
import json
from pathlib import Path

from .fetch import fetch_sources
from .importer import build_database
from .validation import snipe_summary, validate_database


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="PoE2 real-data importer")
    result.add_argument("--cache-dir", type=Path, default=Path(".cache/sources"))
    result.add_argument("--database", type=Path, default=Path("data/poe2.db"))
    commands = result.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download pinned real-data sources")
    fetch.add_argument("--force", action="store_true")
    commands.add_parser("build", help="build SQLite from verified source files")
    commands.add_parser("validate", help="validate Checkpoint 1 acceptance criteria")
    commands.add_parser("snipe", help="show queryable Snipe vertical-slice data")
    commands.add_parser("all", help="fetch, build, validate, and show Snipe data")
    return result


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> None:
    args = parser().parse_args()
    if args.command in {"fetch", "all"}:
        print(fetch_sources(args.cache_dir, force=getattr(args, "force", False)))
    if args.command in {"build", "all"}:
        print_json(build_database(args.cache_dir, args.database))
    if args.command in {"validate", "all"}:
        print_json(validate_database(args.database))
    if args.command in {"snipe", "all"}:
        print_json(snipe_summary(args.database))


if __name__ == "__main__":
    main()

