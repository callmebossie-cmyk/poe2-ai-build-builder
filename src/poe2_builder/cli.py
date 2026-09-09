from __future__ import annotations

import argparse
import json
from pathlib import Path

from .fetch import fetch_sources
from .database import connect
from .directions import BuildDirectionService, OfflineDeterministicProvider, QualityMode
from .graph import PassiveGraph, PathNotFoundError
from .importer import build_database
from .retrieval import BuildIntent, CandidateRetriever
from .ollama_provider import OllamaProvider
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
    graph = commands.add_parser("graph-demo", help="find the nearest projectile passive from a class start")
    graph.add_argument("--class-name", default="Ranger")
    retrieve = commands.add_parser("retrieve", help="build a bounded, explainable candidate context")
    retrieve.add_argument("--skill", default="Snipe")
    retrieve.add_argument("--playstyle", default="Fast")
    retrieve.add_argument("--goal", default="Mapping")
    retrieve.add_argument("--budget", default="Cheap")
    directions = commands.add_parser("directions-contract-demo", help="run the offline build-direction contract test")
    directions.add_argument("--skill", default="Snipe")
    directions.add_argument("--playstyle", default="Fast")
    directions.add_argument("--goal", default="Mapping")
    directions.add_argument("--budget", default="Cheap")
    directions.add_argument("--quality", choices=[mode.value for mode in QualityMode], default=QualityMode.BALANCED.value)
    ollama = commands.add_parser("directions-ollama", help="run live build directions through local Ollama")
    ollama.add_argument("--model", default="qwen3:8b")
    ollama.add_argument("--endpoint", default="http://127.0.0.1:11434/api/chat")
    ollama.add_argument("--skill", default="Snipe")
    ollama.add_argument("--playstyle", default="Fast")
    ollama.add_argument("--goal", default="Mapping")
    ollama.add_argument("--budget", default="Cheap")
    ollama.add_argument("--quality", choices=[mode.value for mode in QualityMode], default=QualityMode.BALANCED.value)
    ollama.add_argument("--output", type=Path)
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
    if args.command == "graph-demo":
        passive_graph = PassiveGraph.from_database(args.database)
        start = passive_graph.class_start(args.class_name)
        db = connect(args.database)
        try:
            targets = [
                row[0]
                for row in db.execute(
                    "SELECT DISTINCT node_id FROM passive_stats WHERE lower(text) LIKE '%projectile%'"
                )
            ]
        finally:
            db.close()
        paths = []
        for target in targets:
            try:
                paths.append(passive_graph.shortest_path(start, target))
            except PathNotFoundError:
                continue
        if not paths:
            raise PathNotFoundError(f"No reachable projectile passive from {args.class_name}")
        path = min(paths, key=lambda candidate: (candidate.point_cost, candidate.nodes[-1]))
        print_json(
            {
                "class": args.class_name,
                "start": start,
                "target": path.nodes[-1],
                "target_name": passive_graph.names[path.nodes[-1]],
                "point_cost": path.point_cost,
                "nodes": path.nodes,
                "connected_component_size": passive_graph.component_size(start),
            }
        )
    if args.command == "retrieve":
        intent = BuildIntent(args.skill, args.playstyle, args.goal, args.budget)
        print_json(CandidateRetriever(args.database).retrieve(intent))
    if args.command == "directions-contract-demo":
        intent = BuildIntent(args.skill, args.playstyle, args.goal, args.budget)
        service = BuildDirectionService(args.database, OfflineDeterministicProvider())
        print_json(service.generate(intent, QualityMode(args.quality)))
    if args.command == "directions-ollama":
        intent = BuildIntent(args.skill, args.playstyle, args.goal, args.budget)
        service = BuildDirectionService(
            args.database,
            OllamaProvider(model=args.model, endpoint=args.endpoint),
            max_attempts=3,
        )
        result = service.generate(intent, QualityMode(args.quality))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print_json(result)


if __name__ == "__main__":
    main()
