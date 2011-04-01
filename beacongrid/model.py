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
