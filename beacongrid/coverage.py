"""Policy coverage analysis.

Coverage answers a question every policy author eventually asks: *which of my
rules actually did anything?* BeaconGrid tracks, across every candidate of
every decision, whether each rule fired, contributed weight, or issued a veto.

The report surfaces:
  - ``fired_rules``: rules that matched at least one candidate
  - ``dormant_rules``: rules that never matched — candidates for pruning
  - ``veto_rules``: rules that disqualified at least one candidate
  - per-rule hit counts and total weight contributed

Coverage is computed as a byproduct of a replay so it always reflects the
revised policy the dossier was generated against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .model import Policy
from .scoring import ScoreBreakdown


@dataclass
class RuleStat:
    rule_id: str
    hits: int = 0
    vetoes: int = 0
    total_weight: float = 0.0

    def to_dict(self) -> Dict[str, object]:
