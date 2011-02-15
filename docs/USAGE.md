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
