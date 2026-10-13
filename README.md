<div align="center">

<img src="docs/assets/logo.svg" alt="BeaconGrid" width="560" />

# BeaconGrid

### Agent Decision Replay Studio

*Record what your agent decided. Rewrite the policy. Replay the past. See exactly what changes.*

<img src="docs/assets/replay-flow.svg" alt="BeaconGrid replay flow" width="720" />

</div>

---

BeaconGrid is a dependency-free studio for **replaying recorded agent sessions against revised policies**. It answers the question every team shipping an autonomous agent eventually asks: *"If I change this rule, which past decisions would the agent have made differently — and why?"*

You capture a session once: the context the agent saw, the policy that was live, the candidate tool actions it scored, and the action it chose. BeaconGrid then re-runs every decision under a **revised** policy and produces a shareable **replay dossier** containing:

- **Decision deltas** — per-decision original vs. replay selection with full scoring traces.
- **Route divergence** — a classified explanation for every decision that changed course.
- **Policy coverage** — which rules actually fired, which vetoed, and which lay dormant.

There are two runtimes that produce **byte-compatible** results: a Python 3.11 reference package (`beacongrid`) and a Go module (`grid`). Both use only their respective standard libraries. Nothing to install, nothing to pin, nothing to break.

---

## Table of contents

- [Why BeaconGrid](#why-beacongrid)
- [Core concepts](#core-concepts)
- [Install](#install)
- [Quickstart](#quickstart)
- [The session format](#the-session-format)
- [The policy format](#the-policy-format)
- [The scoring model](#the-scoring-model)
- [Route divergence classification](#route-divergence-classification)
- [Policy coverage](#policy-coverage)
- [Command-line interface](#command-line-interface)
- [The replay dossier](#the-replay-dossier)
- [Python API](#python-api)
- [Go runtime](#go-runtime)
- [Determinism and reproducibility](#determinism-and-reproducibility)
- [Worked example](#worked-example)
- [Design principles](#design-principles)
- [Project layout](#project-layout)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Why BeaconGrid

Agents that call tools make chains of decisions. Each decision picks one candidate action from several, guided by a **policy** — a set of scoring rules that reward, penalize, or outright veto candidates. Policies drift constantly: you tighten a safety rule, add a veto, reweight a preference, retire a legacy path.

Every one of those edits is a bet. Without a way to replay history, you ship the bet blind and discover the consequences in production. BeaconGrid turns that bet into a measurement.

- **Regression-proof your policy changes.** Replay a corpus of real sessions before you ship. If a reweight silently reroutes 40% of refund flows through a human queue, you see it in the diff, not in the on-call channel.
- **Audit decisions after the fact.** A dossier is a complete, self-contained record: inputs, rules, scores, and outcomes. Attach it to a ticket, a compliance review, or a postmortem.
- **Prune dead rules.** Coverage reveals rules that never fired across your entire replay corpus. Dormant rules are noise; delete them with confidence.
- **Explain divergence in plain language.** Every changed route is classified — `tool_switch`, `veto_shift`, `reweight`, `all_vetoed` — with a human-readable reason.
- **Run anywhere.** No third-party packages. A session replays identically on a laptop, in CI, or inside an air-gapped review environment, in either Python or Go.

BeaconGrid does **not** run your agent, call your tools, or talk to any model. It replays *recorded* decisions through a *deterministic* scorer. That narrow scope is the point: the studio is fast, auditable, and trivially embeddable.

---

## Core concepts

| Concept | What it is |
| --- | --- |
| **Session** | A recorded run: metadata, the original policy, context frames, and an ordered list of decisions. |
| **Context frame** | One observation the agent could see at decision time (a user turn, a retrieved doc, an environment signal), carrying a `salience` weight and tags. |
| **Decision** | A single choice point: a prompt, the candidate actions, the linked context frames, and the action originally chosen. |
| **Action** | A candidate tool call with a tool name, intent, arguments, risk, cost, and tags. |
| **Policy** | A named, versioned set of scoring rules plus a tie-break strategy. |
| **Policy rule** | A declarative `when` predicate map plus a `weight`, an optional `veto`, and a note. |
| **Score breakdown** | The full trace for one candidate: final score, which rules fired, and any vetoes. |
| **Decision delta** | The replay outcome for one decision: original vs. replay action and their scores. |
| **Route divergence** | A classified explanation for a decision whose replay selection differs from the original. |
| **Coverage report** | Aggregate rule activity across a replay: fired, dormant, and veto rules with hit counts. |
| **Replay dossier** | The complete, serializable bundle of everything above. |

---

## Install

BeaconGrid has no runtime dependencies. Clone the repository and you are ready.

```bash
git clone https://github.com/beacongrid/beacongrid.git
cd beacongrid
```

### Python (3.11+)

Run the CLI straight from the source tree:

```bash
python -m beacongrid --help
```

Or install it as a console script:

```bash
pip install .
beacongrid --help
```

### Go (1.24+)

Build or run the `grid` CLI from the module directory:

```bash
cd grid
go build ./...
go run ./cmd/grid --help
```

---

## Quickstart

The repository ships a ready-to-run support-triage example under [`examples/`](examples/): a recorded session (`session.json`) and a revised policy (`revised_policy.json`).

Replay the session against the revised policy:

```bash
python -m beacongrid replay examples/session.json examples/revised_policy.json
```

```text
BeaconGrid replay dossier — session sess-support-triage-014
  agent            : triage-copilot
  original policy  : triage-baseline@3
  revised policy   : triage-revised@4
  decisions        : 3
  divergences      : 3
  divergence rate  : 100.0%
  policy coverage  : 85.7% (1 dormant)
    step   1 [tool_switch] a-escalate -> a-kb
    step   2 [tool_switch] a-close -> a-followup
    step   3 [veto_shift] a-discount -> a-defer
```

Show only what changed:

```bash
python -m beacongrid diff examples/session.json examples/revised_policy.json
```

Emit the full machine-readable dossier:

```bash
python -m beacongrid --json replay examples/session.json examples/revised_policy.json > dossier.json
```

The Go runtime accepts the same files and prints the same results:

```bash
cd grid
go run ./cmd/grid replay ../examples/session.json ../examples/revised_policy.json
```

---

## The session format

A session is a single JSON object discriminated by a `schema` field. The loader validates the schema prefix and major version before mapping the payload onto typed objects.

```json
{
  "schema": "beacongrid/session@1",
  "session_id": "sess-support-triage-014",
  "agent": "triage-copilot",
  "created": "2026-08-30T09:41:00Z",
  "metadata": { "channel": "support-inbox" },
  "policy": { "schema": "beacongrid/policy@1", "policy_id": "triage-baseline", "version": "3", "rules": [] },
  "frames": [
    {
      "frame_id": "f1",
      "kind": "user_turn",
      "content": "I was double charged and need this fixed today.",
      "salience": 0.9,
      "tags": ["billing", "urgent"]
    }
  ],
  "decisions": [
    {
      "decision_id": "d1",
      "step": 1,
      "prompt": "How should the agent respond?",
      "context_frame_ids": ["f1"],
      "chosen_action_id": "a-escalate",
      "candidates": [
        {
          "action_id": "a-kb",
          "tool": "kb_search",
          "intent": "look up the refund SOP",
          "args": { "query": "duplicate charge refund" },
          "risk": 0.1,
          "cost": 0.2,
          "tags": ["read-only"]
        }
      ]
    }
  ]
}
```

Field notes:

- `salience` is a `0..1` float. Context-tag rules scale their weight by the maximum salience of the matching frames, so a highly salient signal counts for more.
- `risk` and `cost` are free-scale floats used by rules (`max_risk`, `max_cost`) and by tie-breaks.
- `context_frame_ids` link a decision to the frames visible when it was made; unknown ids are ignored.
- Unknown top-level fields are tolerated so forward-compatible payloads survive a round trip.

---

## The policy format

A policy is a named, versioned list of rules plus a tie-break strategy. It can be embedded inside a session (the *original* policy) or supplied standalone (the *revised* policy).

```json
{
  "schema": "beacongrid/policy@1",
  "policy_id": "triage-revised",
  "version": "4",
  "tie_break": "lowest_risk",
  "rules": [
    { "rule_id": "prefer-knowledge-base", "when": { "tool": "kb_search" }, "weight": 4.0 },
    { "rule_id": "veto-unattended-refund", "when": { "tool": "issue_refund" }, "veto": true },
    { "rule_id": "reward-urgent-context", "when": { "context_tag": "urgent" }, "weight": 3.0 }
  ]
}
```

A rule fires only when **every** predicate in its `when` map matches. Supported predicates:

| Predicate | Matches when |
| --- | --- |
| `tool` | the candidate's tool name equals the value |
| `tag` | the candidate carries this tag |
| `intent_contains` | the value is a case-insensitive substring of the intent |
| `context_tag` | any linked context frame carries this tag (scales weight by salience) |
| `max_risk` | the candidate's `risk` exceeds the given float |
| `max_cost` | the candidate's `cost` exceeds the given float |

Unknown predicate keys never match. This is deliberate: a forward-compatible policy that references a predicate this build does not understand will simply not grant weight, rather than silently misbehaving.

---

## The scoring model

Scoring is deterministic and fully traced. For each candidate action, the engine walks every rule in the policy in declaration order:

1. Evaluate the rule's `when` predicates against the action and its context frames.
2. If **all** predicates match, the rule *fires*.
3. A firing `veto` rule marks the candidate disqualified and records the rule id. Vetoes short-circuit weight — a vetoed candidate cannot be selected regardless of score.
4. A firing non-veto rule adds `weight` to the running score. A `context_tag` predicate scales its rule's weight by the maximum salience among the matching frames.

The selected action is the **highest-scoring non-vetoed candidate**. Ties are resolved by the policy's `tie_break` strategy:

| Strategy | Tie-break order |
| --- | --- |
| `lowest_cost` *(default)* | lowest `cost`, then action id |
| `lowest_risk` | lowest `risk`, then action id |
| `first` | original declaration order |

Because scoring is a pure function of `(policy, decision, frames)`, the same inputs always yield the same score, the same selection, and the same trace.

---

## Route divergence classification

When the replay selection differs from what the agent originally chose, BeaconGrid classifies *why*:

| Kind | Meaning |
| --- | --- |
| `tool_switch` | the route moved to a candidate using a **different tool** |
| `veto_shift` | the originally chosen action is now **vetoed**, forcing a different route |
| `reweight` | revised weights promoted a different candidate of the **same tool** |
| `all_vetoed` | **every** candidate was disqualified; the decision has no selectable route |

Each divergence carries a human-readable `detail` string, so a reviewer scanning a diff understands the cause without reading scores.

---

## Policy coverage

Coverage answers: *which of my rules actually did anything?* Computed as a byproduct of a replay, it always reflects the revised policy the dossier was generated against.

- **fired rules** — matched at least one candidate and contributed weight.
- **veto rules** — disqualified at least one candidate.
- **dormant rules** — never matched anything; prime candidates for pruning.
- **per-rule stats** — hit count, veto count, and total weight contributed.
- **coverage ratio** — the fraction of rules that were active (fired or vetoed).

---

## Command-line interface

Both runtimes expose the same five commands. Every command accepts `--json` for machine-readable output.

| Command | Purpose |
| --- | --- |
| `replay <session> <policy>` | Replay a session against a revised policy; print the dossier. |
| `diff <session> <policy>` | Print only the diverging decisions. |
| `coverage <session> [policy]` | Report rule coverage (defaults to the session's own policy). |
| `inspect <session>` | Summarize a session: frames, decisions, and the original policy. |
| `validate session\|policy <path>` | Load a record and confirm it parses cleanly. |

Python:

```bash
python -m beacongrid replay   examples/session.json examples/revised_policy.json
python -m beacongrid diff      examples/session.json examples/revised_policy.json
python -m beacongrid coverage  examples/session.json examples/revised_policy.json
python -m beacongrid inspect   examples/session.json
python -m beacongrid validate  policy examples/revised_policy.json
```

Go:

```bash
cd grid
go run ./cmd/grid replay   ../examples/session.json ../examples/revised_policy.json
go run ./cmd/grid coverage  ../examples/session.json ../examples/revised_policy.json --json
```

Exit codes: `0` success, `2` a load or validation error (details on stderr).

---

## The replay dossier

The dossier is the canonical output — a single self-describing JSON document (`beacongrid/dossier@1`) that bundles everything needed to review or share a replay:

```json
{
  "schema": "beacongrid/dossier@1",
  "session_id": "sess-support-triage-014",
  "agent": "triage-copilot",
  "original_policy": "triage-baseline@3",
  "revised_policy": "triage-revised@4",
  "decisions": 3,
  "divergences": 3,
  "divergence_rate": 1.0,
  "deltas": [ { "decision_id": "d1", "diverged": true, "original_action_id": "a-escalate", "replay_action_id": "a-kb", "breakdown": {} } ],
  "route_divergences": [ { "step": 1, "kind": "tool_switch", "detail": "route moved from tool 'human_escalate' to 'kb_search'" } ],
  "coverage": { "coverage_ratio": 0.857143, "dormant_rules": ["legacy-macro"], "veto_rules": ["veto-autonomous-discount", "veto-unattended-refund"] }
}
```

Because every delta carries its full scoring breakdown, a dossier is completely self-contained: you can reconstruct exactly why each candidate scored what it did without the original policy in hand.

---

## Python API

The public surface is small and importable directly from the top-level package:

```python
from beacongrid import load_session, load_policy, replay_session

session = load_session("examples/session.json")
revised = load_policy("examples/revised_policy.json")

dossier = replay_session(session, revised)

print(dossier.summary())
print("divergence rate:", dossier.divergence_rate)

for delta in dossier.deltas:
    if delta.diverged:
        print(delta.decision_id, delta.original_action_id, "->", delta.replay_action_id)

for rule in dossier.coverage.dormant_rules:
    print("dormant:", rule)

# Serialize the whole thing:
import json
json.dumps(dossier.to_dict(), indent=2)
```

Lower-level building blocks are available too — `score_action`, `select_action`, `compute_coverage`, and the `ReplayEngine` class for callers that want to drive the replay loop themselves.

---

## Go runtime

The Go module `grid` mirrors the Python reference type-for-type and function-for-function. The library is importable, and `cmd/grid` provides the CLI.

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"beacongrid/grid"
)

func main() {
	sessionData, _ := os.ReadFile("examples/session.json")
	policyData, _ := os.ReadFile("examples/revised_policy.json")

	var session grid.Session
	var revised grid.Policy
	json.Unmarshal(sessionData, &session)
	json.Unmarshal(policyData, &revised)

	dossier := grid.Replay(session, revised)
	fmt.Println(dossier.Summary())
	fmt.Printf("divergence rate: %.1f%%\n", dossier.DivergenceRate*100)
}
```

Both runtimes classify divergence identically and compute the same coverage ratios, so you can record in one environment and replay in another.

---

## Determinism and reproducibility

BeaconGrid is engineered for reproducibility:

- **Pure scoring.** No clocks, no randomness, no I/O inside the scorer.
- **Stable ordering.** Decisions are replayed in `step` order; rules are evaluated in declaration order; tie-breaks are total (they always end with the action id).
- **Canonical arguments.** Action and rule argument maps are normalized so equivalent payloads compare equal.
- **Cross-runtime parity.** The Python and Go engines are held to the same algorithm; a dossier produced by one matches the other.

The practical payoff: check a session into version control, replay it in CI on every policy change, and diff the dossier. A meaningful change in behavior shows up as a change in the committed dossier.

---

## Worked example

The shipped example models a support-triage agent handling a double-charge complaint under a baseline policy, replayed against a stricter revised policy that adds vetoes for autonomous refunds and discounts and strongly boosts knowledge-base lookups.

The revised policy diverges on all three decisions:

- **Step 1** — a `tool_switch`: the baseline escalated to a human; the revised policy's heavy knowledge-base boost, combined with the urgent context signal, promotes a `kb_search` lookup instead.
- **Step 2** — a `tool_switch`: closing the ticket scored nothing under the revised policy, while a knowledge-base follow-up scored highest.
- **Step 3** — a `veto_shift`: the autonomous goodwill discount is now vetoed, so the route falls to deferring the decision to a supervisor.

Coverage reports 85.7%: six of seven rules were active, with the `legacy-macro` rule dormant — no candidate in the session carried the `macro-v1` tag, so it is a clear pruning candidate.

Walk through it step by step in [`docs/USAGE.md`](docs/USAGE.md).

---

## Design principles

- **Dependency-free by contract.** The entire system runs on the Python and Go standard libraries. This is a hard rule, not an aspiration.
- **Declarative policies.** Rules are data, not code. A policy is JSON you can diff, review, and generate.
- **Trace everything.** Every score carries the list of rules that produced it. No opaque numbers.
- **Small public surface.** A handful of loaders, one replay entry point, one dossier. Easy to learn, hard to misuse.
- **Two runtimes, one algorithm.** Python for reference clarity, Go for embedding in high-throughput services.

Read the full rationale in [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`DESIGN.md`](DESIGN.md).

---

## Project layout

```
beacongrid/
├── beacongrid/            Python reference package
│   ├── model.py           typed session/policy data model
│   ├── loader.py          JSON loading + schema validation
│   ├── scoring.py         deterministic policy scorer
│   ├── replay.py          replay engine + dossier
│   ├── coverage.py        policy coverage analysis
│   └── cli.py             command-line interface
├── grid/                  Go module (mirrors the reference)
│   ├── model.go
│   ├── scoring.go
│   ├── replay.go
│   └── cmd/grid/main.go   Go CLI
├── examples/              ready-to-run session + revised policy
├── docs/                  usage, formats, assets (SVGs)
└── root files             LICENSE, CHANGELOG, ROADMAP, etc.
```

---

## Documentation

- [`docs/USAGE.md`](docs/USAGE.md) — a guided tour of the CLI and API.
- [`docs/FORMATS.md`](docs/FORMATS.md) — the complete session, policy, and dossier schemas.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — components, data flow, and the replay pipeline.
- [`DESIGN.md`](DESIGN.md) — the decisions behind the scoring model and dual runtimes.
- [`ROADMAP.md`](ROADMAP.md) — shipped milestones and what is next.
- [`CHANGELOG.md`](CHANGELOG.md) — release history.

---

## Contributing

Contributions are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow and style, [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community expectations, and [`SECURITY.md`](SECURITY.md) to report vulnerabilities. For help, see [`SUPPORT.md`](SUPPORT.md).

---

## License

BeaconGrid is released under the Apache License 2.0. See [`LICENSE`](LICENSE).
