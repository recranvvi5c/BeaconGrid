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
