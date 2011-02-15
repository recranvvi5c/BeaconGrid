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
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    session = load_session(args.session)
    revised = load_policy(args.policy)
    dossier = replay_session(session, revised)
    if args.json:
        print(json.dumps([d.to_dict() for d in dossier.divergences], indent=2))
        return 0
    if not dossier.divergences:
        print("no divergences — revised policy reproduces every original route")
        return 0
    print(f"{len(dossier.divergences)} diverging decision(s):")
    for div in dossier.divergences:
        print(f"  step {div.step:>3} [{div.kind}]")
        print(f"      {div.original_action_id} -> {div.replay_action_id}")
        print(f"      {div.detail}")
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    session = load_session(args.session)
    policy = load_policy(args.policy) if args.policy else session.policy
    breakdowns = []
    for decision in session.decisions:
        frames = session.frames_for(decision)
        _, bd = select_action(decision, policy, frames)
        breakdowns.append(bd)
    report = compute_coverage(policy, breakdowns)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0
    print(f"coverage for policy {report.policy_id}@{report.version}")
    print(f"  ratio   : {report.coverage_ratio():.1%}")
    print(f"  fired   : {', '.join(report.fired_rules) or '(none)'}")
    print(f"  veto    : {', '.join(report.veto_rules) or '(none)'}")
    print(f"  dormant : {', '.join(report.dormant_rules) or '(none)'}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    session = load_session(args.session)
    if args.json:
        print(json.dumps(session.to_dict(), indent=2, sort_keys=True))
        return 0
    print(f"session {session.session_id} (agent={session.agent})")
    print(f"  created  : {session.created}")
    print(f"  policy   : {session.policy.policy_id}@{session.policy.version}"
          f" ({len(session.policy.rules)} rules)")
    print(f"  frames   : {len(session.frames)}")
    print(f"  decisions: {len(session.decisions)}")
    for d in sorted(session.decisions, key=lambda x: x.step):
        print(f"    step {d.step:>3}: {len(d.candidates)} candidates, "
              f"chose {d.chosen_action_id}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        if args.kind == "session":
            obj = load_session(args.path)
            print(f"OK: session {obj.session_id} parsed ({len(obj.decisions)} decisions)")
        else:
            obj = load_policy(args.path)
            print(f"OK: policy {obj.policy_id}@{obj.version} parsed ({len(obj.rules)} rules)")
        return 0
    except LoadError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="beacongrid",
        description="BeaconGrid — Agent Decision Replay Studio",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    p_replay = sub.add_parser("replay", help="replay a session against a revised policy")
    p_replay.add_argument("session", help="path to a session JSON file")
