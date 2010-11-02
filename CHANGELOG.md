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
