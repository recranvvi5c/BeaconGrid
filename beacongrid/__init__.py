"""BeaconGrid — Agent Decision Replay Studio.

BeaconGrid ingests a recorded agent session — its context frames, the policy
that was active at decision time, the candidate tool actions that were scored,
and the action the agent actually chose — then *replays* every decision against
a revised policy. The replay engine produces decision deltas, route divergence
summaries, policy coverage reports, and a shareable replay dossier.

The public surface is deliberately small and dependency-free. Everything is
built on the Python standard library so a session can be replayed anywhere a
3.11 interpreter runs.

Typical usage::

    from beacongrid import load_session, load_policy, replay_session

    session = load_session("examples/session.json")
    revised = load_policy("examples/revised_policy.json")
    dossier = replay_session(session, revised)
    print(dossier.summary())
"""

from .model import (
    Action,
    ContextFrame,
    Decision,
    Policy,
    PolicyRule,
    Session,
)
from .loader import (
    LoadError,
    load_policy,
    load_session,
)
from .replay import (
    DecisionDelta,
    ReplayDossier,
    ReplayEngine,
    RouteDivergence,
    replay_session,
)
from .coverage import CoverageReport, compute_coverage
from .scoring import ScoreBreakdown, score_action

__version__ = "1.0.0"

__all__ = [
    "Action",
    "ContextFrame",
    "Decision",
    "Policy",
    "PolicyRule",
    "Session",
    "LoadError",
    "load_policy",
    "load_session",
    "DecisionDelta",
    "ReplayDossier",
    "ReplayEngine",
    "RouteDivergence",
    "replay_session",
    "CoverageReport",
    "compute_coverage",
    "ScoreBreakdown",
    "score_action",
    "__version__",
]
