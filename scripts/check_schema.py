"""Validate the committed examples against the documented session and policy shape."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_EVENT = ("id", "kind", "timestamp")


def fail(message: str) -> int:
    print("schema check failed: " + message)
    return 1


def main() -> int:
    session = json.loads((ROOT / "examples/session.json").read_text(encoding="utf-8"))
    if "events" not in session or not isinstance(session["events"], list) or not session["events"]:
        return fail("session.json needs a non-empty events list")
    for index, event in enumerate(session["events"]):
        missing = [k for k in REQUIRED_EVENT if k not in event]
        if missing:
            return fail("session.json event %d is missing %s" % (index, ", ".join(missing)))
    policy = json.loads((ROOT / "examples/revised_policy.json").read_text(encoding="utf-8"))
    weights = policy.get("weights")
    if not isinstance(weights, dict) or not weights:
        return fail("revised_policy.json needs a non-empty weights mapping")
    for name, weight in weights.items():
        if not isinstance(weight, (int, float)) or weight < 0:
            return fail("weight %s must be a non-negative number" % name)
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        return fail("weights sum to %.6f, expected 1.0" % total)
    print("examples ok: %d events, %d weights" % (len(session["events"]), len(weights)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
