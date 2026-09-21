"""Deterministic policy scoring for candidate actions.

The scorer is the heart of BeaconGrid. Given a policy, a decision, and the
context frames visible at that decision, it computes a numeric score for each
candidate action and records exactly which rules fired. Determinism matters:
the same inputs must always produce the same score and the same selection so
that a replay is reproducible and auditable.

Scoring algorithm
------------------
For each candidate action the engine walks every rule in the policy:

1. Evaluate the rule's ``when`` predicates against the action and context.
2. If *all* predicates match, the rule "fires".
3. A firing ``veto`` rule marks the candidate disqualified.
4. A firing non-veto rule adds ``weight`` to the running score. Context-tag
   rules additionally scale their weight by the maximum salience of the
   matching frames, so a highly salient signal counts for more.

The selected action is the highest-scoring non-vetoed candidate. Ties are
broken by the policy's ``tie_break`` strategy (``lowest_cost``, ``lowest_risk``,
or ``first`` — declaration order).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .model import Action, ContextFrame, Decision, Policy, PolicyRule


@dataclass
class ScoreBreakdown:
    """The full scoring trace for a single candidate action."""

    action_id: str
    score: float = 0.0
    vetoed: bool = False
    fired: List[Tuple[str, float]] = field(default_factory=list)
    veto_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "action_id": self.action_id,
            "score": round(self.score, 6),
            "vetoed": self.vetoed,
            "fired": [{"rule_id": r, "delta": round(w, 6)} for r, w in self.fired],
            "veto_rules": list(self.veto_rules),
        }


def _predicate_matches(
    key: str,
    value: str,
    action: Action,
    frames: Sequence[ContextFrame],
) -> Tuple[bool, float]:
    """Return (matched, salience_scale) for a single predicate."""

    if key == "tool":
        return action.tool == value, 1.0
    if key == "tag":
        return value in action.tags, 1.0
    if key == "intent_contains":
        return value.lower() in action.intent.lower(), 1.0
    if key == "context_tag":
        salient = [f.salience for f in frames if value in f.tags]
        if salient:
            return True, max(salient)
        return False, 1.0
    if key == "max_risk":
        try:
            return action.risk > float(value), 1.0
        except ValueError:
            return False, 1.0
    if key == "max_cost":
        try:
            return action.cost > float(value), 1.0
        except ValueError:
            return False, 1.0
    # Unknown predicate keys never match; this keeps forward-compatible
    # policies from silently granting weight.
    return False, 1.0


def _rule_fires(
    rule: PolicyRule,
    action: Action,
    frames: Sequence[ContextFrame],
) -> Tuple[bool, float]:
    """Evaluate every predicate in a rule. All must match for the rule to fire."""

    scale = 1.0
    for key, value in rule.when:
        matched, sal = _predicate_matches(key, value, action, frames)
        if not matched:
            return False, 1.0
        scale = min(scale, sal) if key == "context_tag" else scale
        if key == "context_tag":
            scale = sal
    return True, scale


def score_action(
    action: Action,
    policy: Policy,
    frames: Sequence[ContextFrame],
) -> ScoreBreakdown:
    """Score a single action under a policy with the given context frames."""

    breakdown = ScoreBreakdown(action_id=action.action_id)
    for rule in policy.rules:
        fired, scale = _rule_fires(rule, action, frames)
        if not fired:
            continue
        if rule.veto:
            breakdown.vetoed = True
            breakdown.veto_rules.append(rule.rule_id)
            continue
        delta = rule.weight * scale
        breakdown.score += delta
        breakdown.fired.append((rule.rule_id, delta))
    return breakdown


def _tie_break_key(action: Action, strategy: str) -> Tuple[float, str]:
    if strategy == "lowest_risk":
        return (action.risk, action.action_id)
    if strategy == "first":
        return (0.0, action.action_id)
    # default: lowest_cost
    return (action.cost, action.action_id)


def select_action(
    decision: Decision,
    policy: Policy,
    frames: Sequence[ContextFrame],
) -> Tuple[Optional[str], Dict[str, ScoreBreakdown]]:
    """Return the selected action id and the full breakdown map for a decision."""

    breakdowns: Dict[str, ScoreBreakdown] = {}
    for candidate in decision.candidates:
        breakdowns[candidate.action_id] = score_action(candidate, policy, frames)

    eligible = [
        c for c in decision.candidates if not breakdowns[c.action_id].vetoed
    ]
    if not eligible:
        return None, breakdowns

    best_score = max(breakdowns[c.action_id].score for c in eligible)
    top = [c for c in eligible if breakdowns[c.action_id].score == best_score]
    if len(top) == 1:
        return top[0].action_id, breakdowns

    if policy.tie_break == "first":
        # Preserve declaration order among the tied candidates.
        order = {c.action_id: i for i, c in enumerate(decision.candidates)}
        top.sort(key=lambda c: order[c.action_id])
        return top[0].action_id, breakdowns

    top.sort(key=lambda c: _tie_break_key(c, policy.tie_break))
    return top[0].action_id, breakdowns
