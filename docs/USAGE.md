# Using BeaconGrid

This guide walks through replaying the bundled example with both the command
line and the Python API, and explains how to read the output.

## Prerequisites

- Python 3.11+ for the reference runtime, or Go 1.24+ for the `grid` runtime.
- No third-party packages are required.

From the repository root:

```bash
python -m beacongrid --help
```

## The example

Two files under `examples/` drive every command in this guide:

- `session.json` — a recorded support-triage session under the `triage-baseline@3`
  policy, containing three decisions.
- `revised_policy.json` — a stricter `triage-revised@4` policy that adds vetoes and
  reweights preferences.

## Inspect a session first

Before replaying, look at what you recorded:

```bash
python -m beacongrid inspect examples/session.json
```

```text
session sess-support-triage-014 (agent=triage-copilot)
  created  : 2026-08-30T09:41:00Z
  policy   : triage-baseline@3 (5 rules)
  frames   : 3
  decisions: 3
    step   1: 3 candidates, chose a-escalate
    step   2: 2 candidates, chose a-close
    step   3: 2 candidates, chose a-discount
```

## Replay against a revised policy

```bash
python -m beacongrid replay examples/session.json examples/revised_policy.json
```

The summary reports the headline numbers and lists every diverging step with its
classified kind. Add `--json` to get the full dossier for programmatic use:

```bash
python -m beacongrid --json replay examples/session.json examples/revised_policy.json > dossier.json
```

## See only what changed

```bash
python -m beacongrid diff examples/session.json examples/revised_policy.json
```

```text
3 diverging decision(s):
  step   1 [tool_switch]
      a-escalate -> a-kb
      route moved from tool 'human_escalate' to 'kb_search'
  ...
```

If the revised policy reproduces every original route, `diff` prints a single line
confirming there are no divergences and exits `0`.

## Check policy coverage

```bash
python -m beacongrid coverage examples/session.json examples/revised_policy.json
```

Coverage tells you which rules fired, which vetoed, and which never matched. Omit
the policy argument to analyze the session's own embedded policy instead.

## Validate a file

```bash
python -m beacongrid validate session examples/session.json
python -m beacongrid validate policy  examples/revised_policy.json
```

A malformed or wrong-schema file prints `INVALID: ...` to stderr and exits `2`.

## The Python API

```python
from beacongrid import load_session, load_policy, replay_session

session = load_session("examples/session.json")
revised = load_policy("examples/revised_policy.json")
dossier = replay_session(session, revised)

print(dossier.summary())

for delta in dossier.deltas:
    if delta.diverged:
        print(delta.step, delta.original_action_id, "->", delta.replay_action_id)

print("dormant rules:", dossier.coverage.dormant_rules)
```

You can also drive scoring directly:

```python
from beacongrid.scoring import select_action

decision = session.decisions[0]
frames = session.frames_for(decision)
selected, breakdowns = select_action(decision, revised, frames)
print("selected:", selected)
for action_id, bd in breakdowns.items():
    print(action_id, bd.score, "vetoed" if bd.vetoed else "")
```

## The Go runtime

```bash
cd grid
go run ./cmd/grid replay   ../examples/session.json ../examples/revised_policy.json
go run ./cmd/grid diff      ../examples/session.json ../examples/revised_policy.json
go run ./cmd/grid coverage  ../examples/session.json ../examples/revised_policy.json --json
```

The Go CLI accepts the same arguments and the same `--json` flag, and produces
results identical to the Python runtime.

## Wiring replay into CI

Commit a session and a policy, then fail a build when behavior changes
unexpectedly by diffing the JSON dossier against a committed baseline. See
`ROADMAP.md` for the direction of first-class CI helpers.
