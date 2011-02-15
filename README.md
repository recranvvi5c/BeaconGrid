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
