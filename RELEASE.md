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

4. **Smoke-test every command** on both runtimes: `replay`, `diff`, `coverage`,
   `inspect`, `validate`. Confirm exit code `0` on the example and `2` on a
   deliberately malformed file.

5. **Update `CHANGELOG.md`.** Move entries out of any unreleased section into a
   dated version heading and add the release link at the bottom.

6. **Reconcile `ROADMAP.md`.** Anything shipped in this release moves from
   *Planned* to *Shipped* as a `[x]` item.

7. **Bump the version** in `pyproject.toml`.

## Cutting the release

1. Commit the version bump and changelog on a release branch; open a PR.
2. After merge, tag `main`:
   ```bash
   git tag -a v<version> -m "BeaconGrid v<version>"
   git push origin v<version>
   ```
   The tag serves both runtimes — it is the Go module version and the Python
   release marker.
3. Build the Python distribution from the clean, tagged tree:
   ```bash
   python -m build
   ```
4. Publish the GitHub release from the tag, pasting the matching `CHANGELOG.md`
   section as the release notes.

## Post-release

- Verify a fresh clone at the tag replays the example identically in both
  runtimes.
- Open the next `## [Unreleased]` section in `CHANGELOG.md`.
- Announce the release and link the dossier-parity check output for the record.

## Rollback

Because a dossier is fully self-describing and scoring is deterministic, a bad
release is diagnosable by replaying an archived session and diffing the dossier
against the one committed under the previous tag. If a release regresses behavior,
yank the affected Python artifact, advise users to pin the prior tag for the Go
module, and ship a corrective PATCH once the diverging dossier is reproduced.
