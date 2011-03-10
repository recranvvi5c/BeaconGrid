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
