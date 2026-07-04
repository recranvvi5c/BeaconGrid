# Changelog

All notable changes to BeaconGrid are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-02

The first stable release. Both runtimes replay sessions at parity.

### Added

- Typed, frozen data model for sessions, policies, context frames, decisions,
  and candidate actions (`beacongrid/session@1`, `beacongrid/policy@1`).
- Dependency-free JSON loader with schema-prefix and major-version validation
  and a single `LoadError` exception surface.
- Deterministic policy scorer with six predicates (`tool`, `tag`,
  `intent_contains`, `context_tag`, `max_risk`, `max_cost`), additive weights,
  absolute vetoes, and salience-scaled context matching.
- Total tie-break strategies: `lowest_cost` (default), `lowest_risk`, `first`.
- Replay engine producing per-decision deltas with full scoring breakdowns.
- Route divergence classification: `tool_switch`, `veto_shift`, `reweight`,
  `all_vetoed`, each with a human-readable detail.
- Policy coverage analysis: fired, dormant, and veto rules with per-rule hit
  counts, veto counts, and total contributed weight.
- Shareable `beacongrid/dossier@1` output with text and JSON rendering.
- Python CLI (`python -m beacongrid`) with `replay`, `diff`, `coverage`,
  `inspect`, and `validate` commands, all supporting `--json`.
- Go module `grid` mirroring the reference, with a `cmd/grid` CLI at parity.
- Runnable support-triage example under `examples/`.
- Documentation: README, usage guide, format reference, architecture, and design
  notes.

[1.0.0]: https://github.com/beacongrid/beacongrid/releases/tag/v1.0.0
