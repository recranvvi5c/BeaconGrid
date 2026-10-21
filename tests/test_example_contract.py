import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ExampleContractTests(unittest.TestCase):
    def test_session_example_carries_the_documented_keys(self):
        session = json.loads((ROOT / "examples/session.json").read_text(encoding="utf-8"))
        self.assertIn("events", session)
        self.assertIsInstance(session["events"], list)
        self.assertTrue(session["events"])
        first = session["events"][0]
        for key in ("id", "kind", "timestamp"):
            self.assertIn(key, first)

    def test_policy_example_weights_are_non_negative_and_sum_to_one(self):
        policy = json.loads((ROOT / "examples/revised_policy.json").read_text(encoding="utf-8"))
        weights = policy.get("weights", {})
        self.assertTrue(weights)
        for name, w in weights.items():
            self.assertGreaterEqual(w, 0.0, name)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
