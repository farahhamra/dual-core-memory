import unittest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add package directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.config import resolve_table_name, DEFAULT_TABLE, PROJECT_TABLE
from memory.search import (
    resolve_taxonomy_category,
    compute_trust_score,
    compute_freshness_weight,
)

class TestMemoryLogic(unittest.TestCase):
    def test_table_name_resolution(self):
        self.assertEqual(resolve_table_name(None), DEFAULT_TABLE)
        self.assertEqual(resolve_table_name("default"), DEFAULT_TABLE)
        self.assertEqual(resolve_table_name("default_memory"), DEFAULT_TABLE)
        self.assertEqual(resolve_table_name("project"), PROJECT_TABLE)
        self.assertEqual(resolve_table_name("project_memory"), PROJECT_TABLE)
        self.assertEqual(resolve_table_name("custom-table"), "custom_table")

    def test_taxonomy_category_resolution(self):
        # Metadata override
        self.assertEqual(resolve_taxonomy_category("general", {"memory_type": "procedural"}), "procedural")
        self.assertEqual(resolve_taxonomy_category("general", {"memory_type": "episodic"}), "episodic")
        self.assertEqual(resolve_taxonomy_category("general", {"memory_type": "declarative"}), "declarative")

        # Inferred from category name
        self.assertEqual(resolve_taxonomy_category("pattern"), "procedural")
        self.assertEqual(resolve_taxonomy_category("learned-instinct"), "procedural")
        self.assertEqual(resolve_taxonomy_category("error-handling"), "episodic")
        self.assertEqual(resolve_taxonomy_category("workaround"), "episodic")
        self.assertEqual(resolve_taxonomy_category("schema"), "declarative")
        self.assertEqual(resolve_taxonomy_category("unknown"), "declarative")

    def test_trust_score_computation(self):
        # Declarative is invariant 1.0
        self.assertEqual(compute_trust_score("declarative"), 1.0)

        # Procedural uses confidence score
        self.assertEqual(compute_trust_score("procedural", {"confidence": 0.95}), 0.95)
        self.assertEqual(compute_trust_score("procedural", {"confidence": 0.70}), 0.70)
        self.assertEqual(compute_trust_score("procedural", {}), 0.85)

        # Episodic trust depends on gate confirmation state
        self.assertEqual(compute_trust_score("episodic", {"trust_state": "unconfirmed"}), 0.5)
        self.assertEqual(compute_trust_score("episodic", {"trust_state": "confirmed"}), 1.0)
        self.assertEqual(compute_trust_score("episodic", {}), 1.0)

    def test_freshness_weight_decay(self):
        # Declarative and procedural have flat 1.0 freshness
        self.assertEqual(compute_freshness_weight("declarative", None), 1.0)
        self.assertEqual(compute_freshness_weight("procedural", "2020-01-01T00:00:00Z"), 1.0)

        # Episodic freshly created is ~1.0
        now_iso = datetime.now(timezone.utc).isoformat()
        self.assertAlmostEqual(compute_freshness_weight("episodic", now_iso), 1.0, places=2)

        # Episodic 30 days old should decay to ~0.50 (half-life = 30 days)
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        half_life_freshness = compute_freshness_weight("episodic", thirty_days_ago)
        self.assertAlmostEqual(half_life_freshness, 0.50, delta=0.03)

        # Episodic 60 days old should decay to ~0.25 (two half-lives)
        sixty_days_ago = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        two_half_lives = compute_freshness_weight("episodic", sixty_days_ago)
        self.assertAlmostEqual(two_half_lives, 0.25, delta=0.03)

if __name__ == "__main__":
    unittest.main()
