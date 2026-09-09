#!/usr/bin/env python3
"""
Ranking Formula Scenario Analysis (Synthetic Stress-Testing)
Evaluates how the mathematical penalty terms (confidence damping and 30-day temporal decay)
behave when raw semantic similarity favors an unconfirmed, low-confidence, or obsolete record:
  1. Cosine Only
  2. Cosine x Trust
  3. Cosine x Freshness
  4. Cosine x Trust x Freshness (Full Dual-Core Model)

Note: This script validates the mathematical properties of the ranking formula across
constructed scenario conditions, demonstrating why cosine similarity alone is vulnerable to
distractors with high keyword overlap.
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Ensure package is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.search import (
    resolve_taxonomy_category,
    compute_trust_score,
    compute_freshness_weight,
)

def create_dataset() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)

    return [
        {
            "scenario": "1. Stale Unconfirmed Workaround",
            "query": "Prisma connection pool timeout error",
            "ground_truth_id": "target-pool-config",
            "description": "90-day-old unconfirmed hack has high semantic match (0.88) vs durable pool config (0.80).",
            "records": [
                {
                    "id": "distractor-stale-hack",
                    "title": "Hack: Restart process on timeout error",
                    "category": "workaround",
                    "metadata": {"memory_type": "episodic", "trust_state": "unconfirmed"},
                    "similarity": 0.88,
                    "date": (now - timedelta(days=90)).isoformat(),
                },
                {
                    "id": "target-pool-config",
                    "title": "Prisma Connection Pool & Timeout Settings",
                    "category": "architecture",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.80,
                    "date": (now - timedelta(days=5)).isoformat(),
                },
                {
                    "id": "noise-database-ssl",
                    "title": "PostgreSQL SSL Certificate Setup",
                    "category": "best-practice",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.45,
                    "date": (now - timedelta(days=30)).isoformat(),
                },
            ],
        },
        {
            "scenario": "2. Unconfirmed Rumor vs Verified Fix",
            "query": "Node.js EventEmitter memory leak workaround",
            "ground_truth_id": "target-verified-leak-fix",
            "description": "1-day-old unconfirmed speculation has 0.86 sim vs 2-day-old verified fix with 0.82 sim.",
            "records": [
                {
                    "id": "distractor-unconfirmed-rumor",
                    "title": "Maybe increase maxListeners to 100",
                    "category": "troubleshooting",
                    "metadata": {"memory_type": "episodic", "trust_state": "unconfirmed"},
                    "similarity": 0.86,
                    "date": (now - timedelta(days=1)).isoformat(),
                },
                {
                    "id": "target-verified-leak-fix",
                    "title": "Remove unbind handler in useEffect cleanup",
                    "category": "bug-fix",
                    "metadata": {"memory_type": "episodic", "trust_state": "confirmed", "reinforcement_count": 2},
                    "similarity": 0.82,
                    "date": (now - timedelta(days=2)).isoformat(),
                },
                {
                    "id": "noise-event-naming",
                    "title": "Event Naming Conventions",
                    "category": "convention",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.50,
                    "date": (now - timedelta(days=20)).isoformat(),
                },
            ],
        },
        {
            "scenario": "3. Low-Confidence Habit vs Proven Convention",
            "query": "React state management API integration pattern",
            "ground_truth_id": "target-proven-pattern",
            "description": "Low-confidence (0.35) suggestion has 0.85 sim vs high-confidence (0.92) standard with 0.80 sim.",
            "records": [
                {
                    "id": "distractor-tentative-habit",
                    "title": "Use global window variable for token cache",
                    "category": "pattern",
                    "metadata": {"memory_type": "procedural", "confidence": 0.35},
                    "similarity": 0.85,
                    "date": (now - timedelta(days=4)).isoformat(),
                },
                {
                    "id": "target-proven-pattern",
                    "title": "Zustand Store with HTTP Client Interceptors",
                    "category": "pattern",
                    "metadata": {"memory_type": "procedural", "confidence": 0.92},
                    "similarity": 0.80,
                    "date": (now - timedelta(days=10)).isoformat(),
                },
                {
                    "id": "noise-css-layout",
                    "title": "Flexbox Navigation Bar Component",
                    "category": "general",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.38,
                    "date": (now - timedelta(days=15)).isoformat(),
                },
            ],
        },
        {
            "scenario": "4. Expired Library Bug Workaround",
            "query": "Webpack 5 Module not found polyfill buffer",
            "ground_truth_id": "target-modern-polyfill",
            "description": "Expired workaround from 150 days ago (0.89) vs current active polyfill setup (0.81).",
            "records": [
                {
                    "id": "distractor-ancient-patch",
                    "title": "Webpack 4 node.buffer fallback hack",
                    "category": "workaround",
                    "metadata": {"memory_type": "episodic", "trust_state": "confirmed"},
                    "similarity": 0.89,
                    "date": (now - timedelta(days=150)).isoformat(),
                },
                {
                    "id": "target-modern-polyfill",
                    "title": "Webpack 5 ProvidePlugin Buffer and Process Polyfills",
                    "category": "workaround",
                    "metadata": {"memory_type": "episodic", "trust_state": "confirmed"},
                    "similarity": 0.81,
                    "date": (now - timedelta(days=2)).isoformat(),
                },
                {
                    "id": "noise-package-json",
                    "title": "NPM Scripts Convention",
                    "category": "convention",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.40,
                    "date": (now - timedelta(days=60)).isoformat(),
                },
            ],
        },
        {
            "scenario": "5. Clean Schema Retrieval (Control 1)",
            "query": "Database schema for user authentication table",
            "ground_truth_id": "target-users-ddl",
            "description": "Standard schema query with no distractors; plain cosine should succeed easily.",
            "records": [
                {
                    "id": "target-users-ddl",
                    "title": "Database Table: users (Core DB DDL)",
                    "category": "db-schema",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.88,
                    "date": (now - timedelta(days=10)).isoformat(),
                },
                {
                    "id": "unrelated-orders-ddl",
                    "title": "Database Table: orders and order_items",
                    "category": "db-schema",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.52,
                    "date": (now - timedelta(days=10)).isoformat(),
                },
                {
                    "id": "noise-logging",
                    "title": "Pino Logger Structured Formatting",
                    "category": "best-practice",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.35,
                    "date": (now - timedelta(days=10)).isoformat(),
                },
            ],
        },
        {
            "scenario": "6. Standard API Spec (Control 2)",
            "query": "REST API standard error response structure",
            "ground_truth_id": "target-rfc7807",
            "description": "Clear technical standard query; plain cosine should perform correctly.",
            "records": [
                {
                    "id": "target-rfc7807",
                    "title": "RFC 7807 Problem Details for HTTP APIs",
                    "category": "best-practice",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.85,
                    "date": (now - timedelta(days=30)).isoformat(),
                },
                {
                    "id": "unrelated-git-workflow",
                    "title": "Trunk-Based Development Git Guidelines",
                    "category": "agent-tip",
                    "metadata": {"memory_type": "procedural", "confidence": 0.85},
                    "similarity": 0.42,
                    "date": (now - timedelta(days=30)).isoformat(),
                },
            ],
        },
        {
            "scenario": "7. Temporary CLI Hack vs Multi-Stage Build Pattern",
            "query": "Docker build cache optimization slow npm install",
            "ground_truth_id": "target-docker-multistage",
            "description": "Temporary 45-day-old unconfirmed --no-cache hack (0.87) vs multi-stage cache pattern (0.81).",
            "records": [
                {
                    "id": "distractor-docker-hack",
                    "title": "Docker build --no-cache workaround",
                    "category": "workaround",
                    "metadata": {"memory_type": "episodic", "trust_state": "unconfirmed"},
                    "similarity": 0.87,
                    "date": (now - timedelta(days=45)).isoformat(),
                },
                {
                    "id": "target-docker-multistage",
                    "title": "Docker Multi-Stage Build with BuildKit Mount Cache",
                    "category": "pattern",
                    "metadata": {"memory_type": "procedural", "confidence": 0.88},
                    "similarity": 0.81,
                    "date": (now - timedelta(days=14)).isoformat(),
                },
                {
                    "id": "noise-docker-compose",
                    "title": "Local Docker Compose Services",
                    "category": "general",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.44,
                    "date": (now - timedelta(days=20)).isoformat(),
                },
            ],
        },
        {
            "scenario": "8. Deprecated Auth Endpoint vs Active Key Verification",
            "query": "JWT token verification RSA public key signature",
            "ground_truth_id": "target-rs256-verification",
            "description": "120-day-old unconfirmed legacy auth hack (0.87) vs active RS256 token verification (0.82).",
            "records": [
                {
                    "id": "distractor-legacy-secret",
                    "title": "Bypass signature check using HS256 shared secret",
                    "category": "workaround",
                    "metadata": {"memory_type": "episodic", "trust_state": "unconfirmed"},
                    "similarity": 0.87,
                    "date": (now - timedelta(days=120)).isoformat(),
                },
                {
                    "id": "target-rs256-verification",
                    "title": "JWT RS256 Asymmetric Key Verification with JWKS",
                    "category": "best-practice",
                    "metadata": {"memory_type": "procedural", "confidence": 0.90},
                    "similarity": 0.82,
                    "date": (now - timedelta(days=7)).isoformat(),
                },
                {
                    "id": "noise-cors-config",
                    "title": "CORS Origin Whitelist Configuration",
                    "category": "convention",
                    "metadata": {"memory_type": "declarative"},
                    "similarity": 0.46,
                    "date": (now - timedelta(days=40)).isoformat(),
                },
            ],
        },
    ]

def evaluate_models(dataset: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    models = {
        "Cosine Only": lambda sim, trust, fresh: sim,
        "Cosine x Trust": lambda sim, trust, fresh: sim * trust,
        "Cosine x Freshness": lambda sim, trust, fresh: sim * fresh,
        "Full Dual-Core (Sim x Trust x Fresh)": lambda sim, trust, fresh: sim * trust * fresh,
    }

    results = {name: {"p_at_1": 0.0, "mrr": 0.0, "recall_at_3": 0.0} for name in models}
    n = len(dataset)

    print("\n" + "=" * 95)
    print("DETAILED SCENARIO BREAKDOWN")
    print("=" * 95)

    for case in dataset:
        target_id = case["ground_truth_id"]
        print(f"\nScenario: {case['scenario']}")
        print(f"Query:    \"{case['query']}\"")
        print(f"Goal:     Rank target '{target_id}' as #1")

        case_results = {}
        for m_name, score_fn in models.items():
            scored_records = []
            for r in case["records"]:
                m_type = resolve_taxonomy_category(r["category"], r["metadata"])
                t_score = compute_trust_score(m_type, r["metadata"])
                f_weight = compute_freshness_weight(m_type, r["date"])
                final_score = round(score_fn(r["similarity"], t_score, f_weight), 4)

                scored_records.append({
                    "id": r["id"],
                    "title": r["title"],
                    "score": final_score,
                    "sim": r["similarity"],
                    "trust": t_score,
                    "fresh": f_weight,
                })

            scored_records.sort(key=lambda x: x["score"], reverse=True)

            # Find rank of ground truth target (1-indexed)
            target_rank = None
            for idx, item in enumerate(scored_records, 1):
                if item["id"] == target_id:
                    target_rank = idx
                    break

            if target_rank == 1:
                results[m_name]["p_at_1"] += 1.0
            if target_rank is not None:
                results[m_name]["mrr"] += 1.0 / target_rank
                if target_rank <= 3:
                    results[m_name]["recall_at_3"] += 1.0

            case_results[m_name] = {
                "rank": target_rank,
                "winner": scored_records[0]["id"],
                "winner_score": scored_records[0]["score"],
            }

        # Print comparison for this scenario
        print(f"  {'Model':<38} | {'Target Rank':<12} | {'Winner ID':<30} | {'Status'}")
        print("  " + "-" * 90)
        for m_name, cr in case_results.items():
            status = "PASS (Target #1)" if cr["rank"] == 1 else f"FAIL (Ranked #{cr['rank']})"
            print(f"  {m_name:<38} | #{cr['rank']:<11} | {cr['winner']:<30} | {status}")

    # Compute averages
    for m_name in results:
        results[m_name]["p_at_1"] = round((results[m_name]["p_at_1"] / n) * 100.0, 1)
        results[m_name]["mrr"] = round(results[m_name]["mrr"] / n, 4)
        results[m_name]["recall_at_3"] = round((results[m_name]["recall_at_3"] / n) * 100.0, 1)

    return results

def main():
    dataset = create_dataset()
    results = evaluate_models(dataset)

    print("\n" + "=" * 85)
    print("RANKING FORMULA SCENARIO ANALYSIS (N = 8 Scenarios)")
    print("=" * 85)
    print(f"{'Ranking Model':<42} | {'Precision@1':<13} | {'MRR':<10} | {'Recall@3':<10}")
    print("-" * 85)
    for model_name, metrics in results.items():
        print(
            f"{model_name:<42} | "
            f"{metrics['p_at_1']:>5.1f}%       | "
            f"{metrics['mrr']:>6.4f}   | "
            f"{metrics['recall_at_3']:>5.1f}%"
        )
    print("=" * 85)
    print("Scenario Analysis Takeaways:")
    print("  * Controls (5 & 6): Plain cosine works as expected when candidates are equally clean.")
    print("  * Distractor stress-tests (1-4, 7, 8): Plain cosine selects stale/unconfirmed records due to keyword overlap.")
    print("  * Full Formula (Sim x Trust x Freshness): Mathematically demotes stale/unconfirmed records without false penalties.\n")

if __name__ == "__main__":
    main()
