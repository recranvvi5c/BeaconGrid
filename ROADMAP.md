# Roadmap

BeaconGrid's direction, grouped by what has shipped and what is planned. Shipped
milestones are checked.

## Shipped

- [x] **Deterministic replay core** — typed model, dependency-free loader, and a
  pure scoring kernel that produces identical results for identical inputs.
- [x] **Divergence and coverage reporting** — classified route divergence
  (`tool_switch`, `veto_shift`, `reweight`, `all_vetoed`) and policy coverage
  with fired, dormant, and veto partitions.
- [x] **Dual-runtime parity** — a Python reference package and a Go module that
  replay the same sessions to byte-compatible dossiers.
- [x] **Command-line studio** — `replay`, `diff`, `coverage`, `inspect`, and
  `validate` on both runtimes, each with JSON output and a runnable example.

## Planned

