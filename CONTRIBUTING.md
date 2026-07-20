# Contributing to BeaconGrid

Thanks for your interest in improving BeaconGrid. This guide covers how to set up,
make changes, and propose them.

## Ground rules

- **Stay dependency-free.** The Python package and the Go module must run on
  their standard libraries only. Pull requests that add runtime dependencies will
  be declined.
- **Keep the two runtimes at parity.** A change to the scoring or replay
  algorithm in one runtime must land in the other in the same pull request, with
  matching behavior.
- **Preserve determinism.** No clocks, randomness, or I/O in the scoring path.
  Ordering must remain stable and tie-breaks total.

## Development setup

```bash
git clone https://github.com/beacongrid/beacongrid.git
cd beacongrid
python -m beacongrid --help          # Python runtime
cd grid && go build ./... && cd ..   # Go runtime
```

## Making a change

1. Create a branch from `main`.
2. Make your change in both runtimes when it touches shared behavior.
3. Verify the CLIs still replay the bundled example and produce matching results:
   ```bash
   python -m beacongrid --json replay examples/session.json examples/revised_policy.json
   cd grid && go run ./cmd/grid replay ../examples/session.json ../examples/revised_policy.json --json
   ```
4. Compile-check both runtimes:
   ```bash
   python -m compileall beacongrid
   cd grid && go build ./... && go vet ./...
   ```
5. Update documentation (`README.md`, `docs/`) and `CHANGELOG.md` when behavior
   or interfaces change.

## Style

- **Python:** target 3.11, use type hints, keep modules focused, and prefer
  small pure functions. Match the existing docstring style.
- **Go:** run `gofmt`; keep exported identifiers documented; mirror the Python
  reference's names and control flow so the two stay easy to compare.
- **JSON fixtures:** keep them minimal, realistic, and self-explanatory.

## Commit and pull-request conventions

- Write imperative, present-tense commit subjects under ~70 characters.
- Describe the change, the motivation, and how you verified it in the PR body.
- Keep pull requests focused; unrelated changes belong in separate PRs.
- Reference any related issue.

## Reporting bugs and requesting features

Open an issue using the templates under `.github/ISSUE_TEMPLATE/`. For security
issues, follow `SECURITY.md` instead of filing a public issue.

By contributing, you agree that your contributions are licensed under the
project's Apache License 2.0, and you are expected to uphold `CODE_OF_CONDUCT.md`.
