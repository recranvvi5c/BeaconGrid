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
        return {
            "rule_id": self.rule_id,
            "hits": self.hits,
            "vetoes": self.vetoes,
            "total_weight": round(self.total_weight, 6),
        }


@dataclass
class CoverageReport:
    policy_id: str
    version: str
    stats: Dict[str, RuleStat] = field(default_factory=dict)

    @property
    def fired_rules(self) -> List[str]:
        return sorted(r for r, s in self.stats.items() if s.hits > 0)

    @property
    def dormant_rules(self) -> List[str]:
        return sorted(
            r for r, s in self.stats.items() if s.hits == 0 and s.vetoes == 0
        )

    @property
    def veto_rules(self) -> List[str]:
        return sorted(r for r, s in self.stats.items() if s.vetoes > 0)

    def coverage_ratio(self) -> float:
        if not self.stats:
            return 0.0
        active = sum(1 for s in self.stats.values() if s.hits or s.vetoes)
        return round(active / len(self.stats), 6)

    def to_dict(self) -> Dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "coverage_ratio": self.coverage_ratio(),
            "fired_rules": self.fired_rules,
            "dormant_rules": self.dormant_rules,
            "veto_rules": self.veto_rules,
            "rule_stats": [s.to_dict() for s in self.stats.values()],
        }


def compute_coverage(
    policy: Policy,
    breakdowns: List[Dict[str, ScoreBreakdown]],
) -> CoverageReport:
    """Aggregate rule activity across every decision's scoring breakdowns."""

    report = CoverageReport(policy_id=policy.policy_id, version=policy.version)
    for rule in policy.rules:
        report.stats[rule.rule_id] = RuleStat(rule_id=rule.rule_id)

    for decision_map in breakdowns:
        for breakdown in decision_map.values():
            for rule_id, delta in breakdown.fired:
                stat = report.stats.setdefault(rule_id, RuleStat(rule_id=rule_id))
                stat.hits += 1
                stat.total_weight += delta
            for rule_id in breakdown.veto_rules:
                stat = report.stats.setdefault(rule_id, RuleStat(rule_id=rule_id))
                stat.vetoes += 1
    return report
