"""Core data model for BeaconGrid sessions and policies.

The model is intentionally frozen and hashable where practical so that replay
results are reproducible and comparable. Every structure carries an explicit
``from_dict`` classmethod so JSON payloads map cleanly onto typed objects
without a third-party validation library.

Schema versions
----------------
Sessions and policies both carry a ``schema`` string of the form
``beacongrid/session@1`` or ``beacongrid/policy@1``. The loader validates the
prefix and major version; unknown minor fields are preserved on the raw record
so forward-compatible payloads survive a round trip.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class SchemaError(ValueError):
    """Raised when a record fails structural validation."""


def _require(record: Dict[str, Any], key: str, kind: str) -> Any:
    if key not in record:
        raise SchemaError(f"{kind}: missing required field '{key}'")
    return record[key]


@dataclass(frozen=True)
class ContextFrame:
    """A single observation available to the agent at decision time.

    Frames model whatever the agent could see: a user turn, a retrieved
    document, a tool result, or an environment signal. ``salience`` is a
    0..1 float the replay engine uses to weight context-sensitive rules.
    """

    frame_id: str
    kind: str
    content: str
    salience: float = 0.5
    tags: Tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, record: Dict[str, Any]) -> "ContextFrame":
        return cls(
            frame_id=str(_require(record, "frame_id", "context_frame")),
            kind=str(_require(record, "kind", "context_frame")),
            content=str(record.get("content", "")),
            salience=float(record.get("salience", 0.5)),
            tags=tuple(str(t) for t in record.get("tags", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "kind": self.kind,
            "content": self.content,
            "salience": self.salience,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class Action:
    """A candidate tool action the agent could take at a decision point."""

    action_id: str
    tool: str
    intent: str
    args: Tuple[Tuple[str, str], ...] = ()
    risk: float = 0.0
    cost: float = 0.0
    tags: Tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, record: Dict[str, Any]) -> "Action":
        raw_args = record.get("args", {}) or {}
        args = tuple(sorted((str(k), str(v)) for k, v in raw_args.items()))
        return cls(
            action_id=str(_require(record, "action_id", "action")),
            tool=str(_require(record, "tool", "action")),
            intent=str(record.get("intent", "")),
            args=args,
            risk=float(record.get("risk", 0.0)),
            cost=float(record.get("cost", 0.0)),
            tags=tuple(str(t) for t in record.get("tags", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "tool": self.tool,
            "intent": self.intent,
            "args": {k: v for k, v in self.args},
            "risk": self.risk,
            "cost": self.cost,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class Decision:
    """A single decision point within a session.

    ``candidates`` are the actions offered to the agent. ``chosen_action_id``
    is what the original policy selected. ``context_frame_ids`` links the
    decision to the frames that were visible when it was made.
    """

    decision_id: str
    step: int
    prompt: str
    candidates: Tuple[Action, ...]
    chosen_action_id: str
    context_frame_ids: Tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, record: Dict[str, Any]) -> "Decision":
        candidates = tuple(
            Action.from_dict(a) for a in _require(record, "candidates", "decision")
        )
        return cls(
            decision_id=str(_require(record, "decision_id", "decision")),
            step=int(_require(record, "step", "decision")),
            prompt=str(record.get("prompt", "")),
            candidates=candidates,
            chosen_action_id=str(_require(record, "chosen_action_id", "decision")),
            context_frame_ids=tuple(
                str(f) for f in record.get("context_frame_ids", [])
            ),
        )

    def candidate(self, action_id: str) -> Optional[Action]:
        for action in self.candidates:
            if action.action_id == action_id:
                return action
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "step": self.step,
            "prompt": self.prompt,
            "candidates": [a.to_dict() for a in self.candidates],
            "chosen_action_id": self.chosen_action_id,
            "context_frame_ids": list(self.context_frame_ids),
        }


@dataclass(frozen=True)
class PolicyRule:
    """A single scoring rule inside a policy.

    Rules are declarative. The scoring engine evaluates each rule against a
    candidate action plus the decision's context and adds ``weight`` to the
    action's score when the rule matches. A rule with ``veto=True`` disqualifies
    a matching action outright regardless of accumulated score.

    Supported ``when`` predicates:
      - ``tool``: exact tool name match
      - ``tag``: candidate carries this tag
      - ``intent_contains``: substring match against the action intent
      - ``context_tag``: any linked context frame carries this tag
      - ``max_risk``: matches when candidate risk exceeds the given float
      - ``max_cost``: matches when candidate cost exceeds the given float
    """

    rule_id: str
    when: Tuple[Tuple[str, str], ...]
    weight: float = 0.0
    veto: bool = False
    note: str = ""

    @classmethod
    def from_dict(cls, record: Dict[str, Any]) -> "PolicyRule":
        raw_when = _require(record, "when", "policy_rule")
        when = tuple(sorted((str(k), str(v)) for k, v in raw_when.items()))
        return cls(
            rule_id=str(_require(record, "rule_id", "policy_rule")),
            when=when,
            weight=float(record.get("weight", 0.0)),
            veto=bool(record.get("veto", False)),
            note=str(record.get("note", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "when": {k: v for k, v in self.when},
            "weight": self.weight,
            "veto": self.veto,
            "note": self.note,
        }


@dataclass(frozen=True)
class Policy:
    """A named, versioned collection of scoring rules."""

    policy_id: str
    version: str
    rules: Tuple[PolicyRule, ...]
    tie_break: str = "lowest_cost"

    @classmethod
    def from_dict(cls, record: Dict[str, Any]) -> "Policy":
        rules = tuple(
            PolicyRule.from_dict(r) for r in _require(record, "rules", "policy")
        )
        return cls(
            policy_id=str(_require(record, "policy_id", "policy")),
            version=str(record.get("version", "0")),
            rules=rules,
            tie_break=str(record.get("tie_break", "lowest_cost")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "beacongrid/policy@1",
            "policy_id": self.policy_id,
            "version": self.version,
            "tie_break": self.tie_break,
            "rules": [r.to_dict() for r in self.rules],
        }


@dataclass(frozen=True)
class Session:
    """A recorded agent session ready for replay."""

    session_id: str
    agent: str
    created: str
    policy: Policy
    frames: Tuple[ContextFrame, ...]
    decisions: Tuple[Decision, ...]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, record: Dict[str, Any]) -> "Session":
        frames = tuple(
            ContextFrame.from_dict(f) for f in record.get("frames", [])
        )
        decisions = tuple(
            Decision.from_dict(d) for d in _require(record, "decisions", "session")
        )
        return cls(
            session_id=str(_require(record, "session_id", "session")),
            agent=str(record.get("agent", "unknown")),
            created=str(record.get("created", "")),
            policy=Policy.from_dict(_require(record, "policy", "session")),
            frames=frames,
            decisions=decisions,
            metadata=dict(record.get("metadata", {})),
        )

    def frame_index(self) -> Dict[str, ContextFrame]:
        return {f.frame_id: f for f in self.frames}

    def frames_for(self, decision: Decision) -> List[ContextFrame]:
        index = self.frame_index()
        return [index[fid] for fid in decision.context_frame_ids if fid in index]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "beacongrid/session@1",
            "session_id": self.session_id,
            "agent": self.agent,
            "created": self.created,
            "policy": self.policy.to_dict(),
            "frames": [f.to_dict() for f in self.frames],
            "decisions": [d.to_dict() for d in self.decisions],
            "metadata": self.metadata,
        }
