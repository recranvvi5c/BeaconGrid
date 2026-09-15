# Architecture

BeaconGrid is a small, layered system with a single data flow: untrusted JSON
enters through a loader, becomes a typed model, is scored by a deterministic
engine, and exits as a dossier. Two runtimes — Python and Go — implement the
same pipeline.

## Components

```
        JSON files / strings
                │
                ▼
        ┌───────────────┐
        │    Loader     │  parse + schema check
        └───────────────┘
                │  typed records
                ▼
        ┌───────────────┐
        │     Model     │  Session, Policy, Decision, Action, frames
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │    Scoring    │  score_action → select_action (per decision)
        └───────────────┘
                │  breakdowns
                ▼
   ┌────────────┴────────────┐
   ▼                         ▼
┌─────────┐            ┌──────────────┐
│ Replay  │            │  Coverage    │
│ engine  │────────────▶  (byproduct) │
└─────────┘            └──────────────┘
   │
   ▼
┌───────────────┐
│    Dossier    │  deltas + divergences + coverage
└───────────────┘
```

### Loader (`loader.py`, CLI loaders in `cmd/grid`)

The single choke point for untrusted input. It parses JSON from a path or an
in-memory string, asserts the `schema` discriminator matches an accepted major
version, and delegates structural mapping to the model. Every failure surfaces
as one exception type (`LoadError` in Python), so callers have a single thing to
catch.

### Model (`model.py`, `model.go`)

Frozen, typed records with explicit `from_dict` / JSON-tag mapping. No
third-party validation library — required fields raise `SchemaError`, and
argument maps are canonicalized (sorted key/value tuples in Python) so
equivalent payloads compare equal. Frozen records make replay results
reproducible and safe to share across the pipeline.

### Scoring (`scoring.py`, `scoring.go`)

The deterministic core. `score_action` walks every rule against one candidate,
recording which rules fired and any vetoes. `select_action` scores all
candidates, filters out vetoed ones, picks the highest score, and resolves ties
with the policy's tie-break strategy. Scoring is a pure function of
`(policy, decision, frames)` — no clocks, randomness, or I/O.

### Replay engine (`replay.py`, `replay.go`)

Iterates decisions in `step` order, calls `select_action` under the revised
policy, builds a `DecisionDelta` per decision, and — when the selection differs
from the original — classifies the divergence. It collects every decision's
breakdown map and hands them to coverage.

### Coverage (`coverage.py`, part of `replay.go`)

Aggregates rule activity across the breakdowns collected during a replay: hit
counts, veto counts, total weight contributed, and the derived fired/dormant/veto
partitions plus a coverage ratio.

### Dossier

The serializable output that bundles deltas, divergences, and coverage into one
`beacongrid/dossier@1` document with headline statistics and a human-readable
summary.

### CLI (`cli.py`, `cmd/grid/main.go`)

A thin dispatch layer over the library: `replay`, `diff`, `coverage`, `inspect`,
and `validate`, each with a `--json` mode.

## Data flow

1. **Load** the session (which embeds the original policy) and, separately, the
   revised policy.
2. **Order** decisions by `step`.
3. For each decision, gather its linked context frames and **score** every
   candidate under the revised policy.
4. **Select** the winning candidate; compare with the original choice to compute
   a delta and, if changed, a classified divergence.
5. **Aggregate** all breakdowns into a coverage report.
6. **Assemble** the dossier and render it as text or JSON.

## Two runtimes, one algorithm

The Go module mirrors the Python reference type-for-type and function-for-
function. Both evaluate rules in a stable order and use total tie-breaks, so a
dossier produced by one runtime matches the other. Python optimizes for
reference clarity; Go targets embedding in high-throughput services.

## Boundaries

BeaconGrid never runs an agent, calls a tool, or contacts a model. It replays
*recorded* decisions through a *deterministic* scorer. That narrow scope keeps
the system fast, auditable, and dependency-free.
