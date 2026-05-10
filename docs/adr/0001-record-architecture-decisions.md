# ADR-0001: Record architecture decisions

- Status: Accepted
- Date: 2026-05-10

## Context

EvalKit is built incrementally over multiple phases (see
[`21_PHASED_ROADMAP.md`](../architecture/21_PHASED_ROADMAP.md)). Across phases, decisions
are made about technology choices, public surfaces, and tradeoffs. We need a
lightweight, durable record of why each non-obvious decision was made — both to
preserve context for future maintainers and to defeat the "fake architecture"
smell where a diagram exists but the rationale is invented after the fact.

## Decision

We record architecture decisions as ADRs in `docs/adr/`, numbered sequentially
(`NNNN-<slug>.md`), using a minimal template:

```
# ADR-NNNN: <Title>
- Status: Proposed | Accepted | Deprecated | Superseded by ADR-MMMM
- Date: YYYY-MM-DD
## Context
## Decision
## Consequences
```

ADRs are added in the same PR as the decision they describe. Reviewers reject PRs
that introduce non-obvious choices without an ADR.

## Consequences

- The repo carries a permanent, diffable trail of "why".
- New contributors can read ADRs to onboard quickly.
- Architecture diagrams in `docs/architecture/` are required to map to real
  modules; ADRs document why those modules look the way they do.
- Cost: one extra file per significant decision. Acceptable.
