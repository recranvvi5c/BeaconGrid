# Design

This document records the decisions behind BeaconGrid's shape and the
trade-offs they carry.

## Goals

- **Deterministic replay.** The same inputs must always produce the same
  dossier, so a committed session becomes a behavioral test.
- **Zero dependencies.** Run anywhere a stock Python 3.11 or Go 1.24 toolchain
  runs — CI, laptops, air-gapped review boxes.
- **Auditable scoring.** Every score is explained by the rules that produced it.
- **Two runtimes at parity.** Record in one environment, replay in another.

## Declarative policies as data

Policies are JSON, not code. Rules are `when` predicate maps plus a weight and an
optional veto. This makes a policy diffable, reviewable, and machine-generatable,
and it keeps the scoring engine a fixed, testable kernel rather than an
interpreter for arbitrary logic.

**Trade-off:** expressiveness is bounded by the predicate vocabulary. We accept
that ceiling in exchange for safety and reproducibility. Unknown predicate keys
deliberately never match, so a policy referencing a newer predicate degrades to
"no effect" rather than misbehaving on an older build.

## The scoring kernel

Score is additive: each firing non-veto rule contributes its weight. Vetoes are
absolute and short-circuit selection. We chose additive weights over a
probabilistic or learned model because the target user is a policy author who
needs to *predict and explain* outcomes, not tune a black box.

Context sensitivity enters through one lever: a `context_tag` rule scales its
weight by the maximum salience of the matching frames. This lets a single rule
express "reward this, more when the signal is strong" without a second scoring
pass.

**Trade-off:** salience scaling only applies to `context_tag`. Other predicates
are binary. Keeping a single scaling lever preserves the mental model.

## Tie-breaks are total

Ties resolve by `lowest_cost` (default), `lowest_risk`, or `first` (declaration
order), and every strategy ends by comparing the action id. A total order means
selection is never ambiguous and never runtime-dependent — essential for
