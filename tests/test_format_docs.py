import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs/FORMATS.md").read_text(encoding="utf-8")


class FormatDocTests(unittest.TestCase):
    def test_every_event_field_is_documented(self):
        for field in ("id", "kind", "timestamp", "actor", "payload"):
            self.assertIn(field, DOC, field)

    def test_exit_codes_are_documented(self):
        for code in ("0", "2"):
            self.assertRegex(DOC, r"`%s`" % code)


if __name__ == "__main__":
    unittest.main()
