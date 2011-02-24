"""BeaconGrid command-line interface.

Run as ``python -m beacongrid <command> [options]``.

Commands
--------
  replay     Replay a session against a revised policy and emit a dossier.
  diff       Print only the diverging decisions between original and revised.
  coverage   Report rule coverage for a policy over a session.
  inspect    Summarize a session: frames, decisions, and the original policy.
  validate   Load a session or policy and confirm it parses cleanly.

All commands accept ``--json`` to emit machine-readable output on stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .coverage import compute_coverage
from .loader import LoadError, load_policy, load_session
from .replay import replay_session
from .scoring import select_action


def _emit(obj: object, as_json: bool, text: str) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, sort_keys=True))
    else:
        print(text)


def cmd_replay(args: argparse.Namespace) -> int:
    session = load_session(args.session)
    revised = load_policy(args.policy)
    dossier = replay_session(session, revised)
    _emit(dossier.to_dict(), args.json, dossier.summary())
