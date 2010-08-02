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
