#!/usr/bin/env python3
"""
Dual-Core Vector Memory CLI
Unified interface for LanceDB semantic search, trust gating, candidate staging, and instinct sync.
"""

import argparse
import json
import sys
from pathlib import Path

# Add package directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory.config import DEFAULT_TABLE, PROJECT_TABLE, DEFAULT_LIMIT
from memory.db import get_table_stats, initialize_tables
from memory.search import search
from memory.save import save
from memory.candidate_gate import record_candidate, confirm_candidate, load_candidates
from memory.sync_instincts import sync_instincts

def format_search_results(results: list, json_output: bool = False):
    if json_output:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("\nNo matching memories found exceeding the score threshold.")
        return

    print(f"\nFound {len(results)} memory record(s):\n")
    for idx, r in enumerate(results, 1):
        print(f"[#{idx}] {r['title']}")
        print(f"  Table:    {r['table']} | Type: {r['memory_type']} ({r['category']})")
        print(f"  Rank:     {r['rank_score']:.4f} (Sim: {r['similarity']:.4f} | Trust: {r['trust_score']} | Freshness: {r['freshness_weight']})")
        print(f"  ID:       {r['id']}")
        if r.get("metadata"):
            print(f"  Metadata: {json.dumps(r['metadata'])}")
        content = r["content"]
        snippet = content if len(content) <= 300 else content[:297] + "..."
        print(f"  Content:  {snippet.strip()}")
        print()

def main():
    parser = argparse.ArgumentParser(
        prog="memory-cli",
        description="Dual-Core Vector Memory CLI (LanceDB + Ollama + Trust Gate)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: search
    p_search = subparsers.add_parser("search", help="Execute semantic vector search")
    p_search.add_argument("query", help="Text to search for")
    p_search.add_argument("-t", "--table", default=DEFAULT_TABLE, help=f"Target table (default: {DEFAULT_TABLE}, or 'project_memory', 'all')")
    p_search.add_argument("-l", "--limit", type=int, default=DEFAULT_LIMIT, help="Max results to return")
    p_search.add_argument("-c", "--category", help="Filter by category")
    p_search.add_argument("-m", "--min-score", type=float, default=0.0, help="Minimum rank score threshold")
    p_search.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: save
    p_save = subparsers.add_parser("save", help="Save/upsert a memory record")
    p_save.add_argument("title", help="Title or summary of memory")
    p_save.add_argument("content", help="Main body content of memory")
    p_save.add_argument("-t", "--table", default=PROJECT_TABLE, help=f"Target table (default: {PROJECT_TABLE})")
    p_save.add_argument("-c", "--category", default="general", help="Category tag")
    p_save.add_argument("--id", help="Optional explicit record ID")
    p_save.add_argument("--meta", help="Optional JSON string of metadata")
    p_save.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: stats
    p_stats = subparsers.add_parser("stats", help="View row counts and table statistics")
    p_stats.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: candidates
    p_cand = subparsers.add_parser("candidates", help="List provisional candidates staged at the gate")
    p_cand.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: record-candidate
    p_rec = subparsers.add_parser("record-candidate", help="Stage or reinforce a provisional technical candidate")
    p_rec.add_argument("title", help="Error title or solution summary")
    p_rec.add_argument("content", help="Solution or workaround content")
    p_rec.add_argument("-c", "--category", default="episodic", help="Category")
    p_rec.add_argument("-d", "--domain", default="error-handling", help="Domain tag")
    p_rec.add_argument("-t", "--table", default=PROJECT_TABLE, help="Target LanceDB table")
    p_rec.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: confirm-candidate
    p_conf = subparsers.add_parser("confirm-candidate", help="Manually promote a candidate to LanceDB")
    p_conf.add_argument("candidate_id", help="Candidate ID to confirm")
    p_conf.add_argument("-t", "--table", help="Target LanceDB table")
    p_conf.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: sync-instincts
    p_sync = subparsers.add_parser("sync-instincts", help="Sync qualified CLv2 instincts (confidence >= 0.70)")
    p_sync.add_argument("--threshold", type=float, default=0.70, help="Confidence threshold (default: 0.70)")
    p_sync.add_argument("-t", "--table", default=PROJECT_TABLE, help="Target table")
    p_sync.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: init
    p_init = subparsers.add_parser("init", help="Initialize LanceDB memory tables")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "search":
            results = search(
                query=args.query,
                table=args.table,
                limit=args.limit,
                category=args.category,
                min_score=args.min_score,
            )
            format_search_results(results, args.json)

        elif args.command == "save":
            meta = {}
            if args.meta:
                try:
                    meta = json.loads(args.meta)
                except Exception:
                    meta = {"raw": args.meta}
            res = save(
                title=args.title,
                content=args.content,
                table=args.table,
                category=args.category,
                metadata=meta,
                id=args.id,
            )
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"[Success] Memory saved with ID '{res['id']}' into table '{res['table']}' ({res['category']}).")

        elif args.command == "stats":
            stats = get_table_stats()
            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print("\n=== LanceDB Vector Memory Tables ===")
                for s in stats:
                    print(f"  * {s['name']}: {s['count']} record(s)")
                print()

        elif args.command == "candidates":
            candidates = load_candidates()
            if args.json:
                print(json.dumps(candidates, indent=2))
            else:
                print(f"\n=== Provisional Staged Candidates ({len(candidates)}) ===")
                if not candidates:
                    print("  (No provisional candidates currently staged)")
                for c in candidates:
                    state_icon = "[CONFIRMED]" if c.get("trust_state") == "confirmed" else "[UNCONFIRMED]"
                    print(f"  {state_icon} {c.get('id')} - {c.get('title')}")
                    print(f"    Reinforcements: {c.get('reinforcement_count', 1)} | Sightings: {len(c.get('sightings', []))}")
                    print(f"    Content: {c.get('content')[:120]}...")
                print()

        elif args.command == "record-candidate":
            res = record_candidate(
                title=args.title,
                content=args.content,
                category=args.category,
                domain=args.domain,
                table=args.table,
            )
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"\n{res['message']}\n")

        elif args.command == "confirm-candidate":
            res = confirm_candidate(args.candidate_id, args.table)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"\n{res['message']}\n")

        elif args.command == "sync-instincts":
            res = sync_instincts(threshold=args.threshold, table=args.table)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print("\n=== Instinct Trust Gate Sync ===")
                print(f"  Scanned:  {res['scanned']} instinct file(s)")
                print(f"  Promoted: {res['promoted']} (confidence >= {res['threshold']})")
                print(f"  Held:     {res['held']} (confidence < {res['threshold']})")
                if res.get("message"):
                    print(f"  Notice:   {res['message']}")
                print()

        elif args.command == "init":
            initialize_tables()
            print("[Success] LanceDB tables initialized.")

    except Exception as err:
        print(f"\n[Error] {err}\n", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
