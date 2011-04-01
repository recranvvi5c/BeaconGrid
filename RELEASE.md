# Releasing BeaconGrid

BeaconGrid ships two runtimes that must always agree. A release is not done until
the Python package and the Go module replay the bundled example to identical
results and both carry the same version story. This document is the checklist a
maintainer follows to cut a release.

## Versioning

BeaconGrid follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- **MAJOR** — a change to the on-disk schemas (`beacongrid/session@1`,
  `beacongrid/policy@1`, `beacongrid/dossier@1`) or to scoring semantics that
  alters selected actions for previously valid inputs.
- **MINOR** — new predicates, new CLI commands, or new tie-break strategies that
  leave existing dossiers byte-compatible.
- **PATCH** — bug fixes and documentation that do not change any dossier.

The canonical version lives in `pyproject.toml` (`[project].version`). The Go
module is versioned by its git tag.

## Pre-release checklist

Run from the repository root. Both runtimes must pass before tagging.

1. **Confirm dependency-free.** No third-party imports have crept into either
   runtime; `pyproject.toml` `dependencies` stays empty and `grid/go.mod` has no
   `require` block.

2. **Compile-check both runtimes.**
   ```bash
   python -m compileall beacongrid
   cd grid && go build ./... && go vet ./... && cd ..
   ```

3. **Verify cross-runtime parity on the bundled example.** The two dossiers must
   be identical:
   ```bash
   python -m beacongrid --json replay examples/session.json examples/revised_policy.json > /tmp/py.json
   (cd grid && go run ./cmd/grid replay ../examples/session.json ../examples/revised_policy.json --json) > /tmp/go.json
   diff /tmp/py.json /tmp/go.json
   ```
   A non-empty diff is a release blocker: the runtimes have drifted.
