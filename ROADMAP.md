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

- [ ] **Batch replay** — replay a directory of sessions against one policy and
  emit an aggregate report with corpus-wide divergence and coverage.
- [ ] **Dossier diffing** — a first-class `bg-diff` that compares two dossiers so
  CI can fail on unexpected behavioral change.
- [ ] **Predicate pack v2** — additional predicates (numeric ranges, arg-value
  matching, frame-count thresholds) behind the same forward-compatible model.
- [ ] **HTML dossier export** — a self-contained, shareable HTML view of a
  replay for non-technical reviewers.
- [ ] **Policy linting** — static checks that flag unreachable rules, redundant
  vetoes, and always-dormant predicates before a replay is even run.
