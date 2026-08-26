"""The replay engine: re-run every decision against a revised policy.

Replay is the studio's headline capability. It takes a recorded session — whose
decisions were made under an *original* policy — and evaluates each decision
again under a *revised* policy. Where the revised selection differs from what
the agent actually chose, BeaconGrid emits a decision delta and classifies the
route divergence.

Outputs
-------
``ReplayDossier`` bundles everything needed to review or share a replay:
  - one :class:`DecisionDelta` per decision
  - a list of :class:`RouteDivergence` records (only the diverging decisions)
  - a :class:`CoverageReport` for the revised policy
  - headline statistics and a human-readable summary

The dossier serializes to a single JSON document via :meth:`ReplayDossier.to_dict`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .coverage import CoverageReport, compute_coverage
from .model import Policy, Session
from .scoring import ScoreBreakdown, select_action


@dataclass
class DecisionDelta:
    """The replay outcome for one decision."""

    decision_id: str
    step: int
    original_action_id: str
    replay_action_id: Optional[str]
    diverged: bool
    original_score: float
    replay_score: float
    breakdown: Dict[str, ScoreBreakdown] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "step": self.step,
            "original_action_id": self.original_action_id,
            "replay_action_id": self.replay_action_id,
            "diverged": self.diverged,
            "original_score": round(self.original_score, 6),
            "replay_score": round(self.replay_score, 6),
            "breakdown": {k: v.to_dict() for k, v in self.breakdown.items()},
        }


@dataclass
class RouteDivergence:
    """A classified explanation of why a decision diverged on replay."""

    decision_id: str
    step: int
    kind: str
    detail: str
    original_action_id: str
    replay_action_id: Optional[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "step": self.step,
            "kind": self.kind,
            "detail": self.detail,
            "original_action_id": self.original_action_id,
            "replay_action_id": self.replay_action_id,
        }


@dataclass
class ReplayDossier:
    """The complete, shareable result of a replay."""

    session_id: str
    agent: str
    original_policy: str
    revised_policy: str
    deltas: List[DecisionDelta] = field(default_factory=list)
    divergences: List[RouteDivergence] = field(default_factory=list)
    coverage: Optional[CoverageReport] = None

    @property
    def divergence_rate(self) -> float:
        if not self.deltas:
            return 0.0
        return round(len(self.divergences) / len(self.deltas), 6)

    def summary(self) -> str:
        lines = [
            f"BeaconGrid replay dossier — session {self.session_id}",
            f"  agent            : {self.agent}",
            f"  original policy  : {self.original_policy}",
            f"  revised policy   : {self.revised_policy}",
            f"  decisions        : {len(self.deltas)}",
            f"  divergences      : {len(self.divergences)}",
            f"  divergence rate  : {self.divergence_rate:.1%}",
        ]
        if self.coverage:
            lines.append(
                f"  policy coverage  : {self.coverage.coverage_ratio():.1%} "
                f"({len(self.coverage.dormant_rules)} dormant)"
            )
        for div in self.divergences:
            lines.append(
                f"    step {div.step:>3} [{div.kind}] "
                f"{div.original_action_id} -> {div.replay_action_id}"
            )
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema": "beacongrid/dossier@1",
            "session_id": self.session_id,
            "agent": self.agent,
            "original_policy": self.original_policy,
            "revised_policy": self.revised_policy,
            "decisions": len(self.deltas),
            "divergences": len(self.divergences),
            "divergence_rate": self.divergence_rate,
            "deltas": [d.to_dict() for d in self.deltas],
            "route_divergences": [d.to_dict() for d in self.divergences],
            "coverage": self.coverage.to_dict() if self.coverage else None,
        }


class ReplayEngine:
    """Replays a session against a revised policy."""

    def __init__(self, session: Session, revised_policy: Policy) -> None:
        self.session = session
        self.revised_policy = revised_policy

    def _classify(
        self,
        original_action_id: str,
        replay_action_id: Optional[str],
        breakdown: Dict[str, ScoreBreakdown],
        session,
        decision,
    ) -> RouteDivergence:
        """Classify a divergence into a route kind with a human explanation."""

        if replay_action_id is None:
            return RouteDivergence(
                decision_id=decision.decision_id,
                step=decision.step,
                kind="all_vetoed",
                detail="every candidate was disqualified by a veto rule",
                original_action_id=original_action_id,
                replay_action_id=None,
            )

        orig_bd = breakdown.get(original_action_id)
        if orig_bd and orig_bd.vetoed:
            return RouteDivergence(
                decision_id=decision.decision_id,
                step=decision.step,
                kind="veto_shift",
                detail=(
                    "the originally chosen action is now vetoed by rules "
                    + ", ".join(orig_bd.veto_rules)
                ),
                original_action_id=original_action_id,
                replay_action_id=replay_action_id,
            )

        orig_tool = decision.candidate(original_action_id)
        new_tool = decision.candidate(replay_action_id)
        if orig_tool and new_tool and orig_tool.tool != new_tool.tool:
            kind = "tool_switch"
            detail = f"route moved from tool '{orig_tool.tool}' to '{new_tool.tool}'"
        else:
            kind = "reweight"
            detail = "revised weights promoted a different candidate of the same tool"
        return RouteDivergence(
            decision_id=decision.decision_id,
            step=decision.step,
            kind=kind,
            detail=detail,
            original_action_id=original_action_id,
            replay_action_id=replay_action_id,
        )

    def run(self) -> ReplayDossier:
        dossier = ReplayDossier(
            session_id=self.session.session_id,
            agent=self.session.agent,
            original_policy=f"{self.session.policy.policy_id}@{self.session.policy.version}",
            revised_policy=f"{self.revised_policy.policy_id}@{self.revised_policy.version}",
        )
        all_breakdowns: List[Dict[str, ScoreBreakdown]] = []

        for decision in sorted(self.session.decisions, key=lambda d: d.step):
            frames = self.session.frames_for(decision)
            replay_action_id, breakdown = select_action(
                decision, self.revised_policy, frames
            )
            all_breakdowns.append(breakdown)

            original_id = decision.chosen_action_id
            orig_score = breakdown.get(original_id)
            replay_score = breakdown.get(replay_action_id) if replay_action_id else None
            diverged = replay_action_id != original_id

            delta = DecisionDelta(
                decision_id=decision.decision_id,
                step=decision.step,
                original_action_id=original_id,
                replay_action_id=replay_action_id,
                diverged=diverged,
                original_score=orig_score.score if orig_score else 0.0,
                replay_score=replay_score.score if replay_score else 0.0,
                breakdown=breakdown,
            )
            dossier.deltas.append(delta)

            if diverged:
                dossier.divergences.append(
                    self._classify(
                        original_id,
                        replay_action_id,
                        breakdown,
                        self.session,
                        decision,
                    )
                )

        dossier.coverage = compute_coverage(self.revised_policy, all_breakdowns)
        return dossier


def replay_session(session: Session, revised_policy: Policy) -> ReplayDossier:
    """Convenience wrapper around :class:`ReplayEngine`."""

    return ReplayEngine(session, revised_policy).run()
