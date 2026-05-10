# 24 — TECH_DEBT_STRATEGY.md

## Posture

Tech debt is not "things we'll fix later." It's accounted for explicitly and either (a) addressed in the same release, (b) filed with a tracking issue and acknowledged in the PR, or (c) declared an intentional non-goal. Anything else corrodes credibility.

## The smell list (binding checklist)

The user's behavioral rules and AI-code-smell list are encoded as a hard checklist run before every release tag. A `scripts/anti_smell.sh` script and a manual review must both pass.

### Automated checks

| Check | Tool | Behavior |
|---|---|---|
| TODO/FIXME in committed code | `ruff` (TD/FIX rules) | Fail on PR. Must be either fixed or moved to issues with a link. |
| Empty folders | `scripts/anti_smell.sh` | Fail on PR. |
| Unused imports / variables | `ruff` | Fail on PR. |
| Unused dependencies | `deptry` | Fail on PR. |
| Generic `except Exception:` | `ruff` (BLE rule) | Fail on PR. |
| `print()` in `src/` | `ruff` (T201 rule) | Fail on PR. Use logging. |
| `import random` in `evaluators/` | custom ruff rule | Fail on PR. Evaluators must be deterministic. |
| Files >400 lines in `src/` | `scripts/anti_smell.sh` | Warn on PR (not fail). 400+ lines requires a comment justifying. |
| Cyclomatic complexity >10 | `ruff` (C901) | Fail on PR. |
| Dead code | `vulture --min-confidence 80` | Warn on PR. |
| Dependency surface | `scripts/anti_smell.sh` | Fail if runtime deps exceed 30 (currently ~22 budgeted). |
| Image size growth | `release.yml` | Fail if image grows >10% without justification in PR description. |
| README claims | `make readme-verify` | Fail on PR. Every README command must execute. |
| Screenshot freshness | CI step | Fail if any screenshot's metadata version is more than one minor behind. |

### Manual checklist (run before each release)

A human (or Devin under explicit instruction at C8) walks through:

- [ ] No directory exists with only an `__init__.py` and zero real code.
- [ ] Every folder under `src/evalkit/` has a corresponding folder under `tests/unit/`.
- [ ] No "fake architecture" — every box in the architecture diagram corresponds to a real module.
- [ ] No "fake enterprise" — no `services/`, `factories/`, `managers/`, or `helpers/` packages.
- [ ] No duplicate abstractions — repo grep for parallel hierarchies.
- [ ] No stub functions raising `NotImplementedError` in main code paths.
- [ ] No commented-out code blocks left in.
- [ ] No "this could be improved by …" comments.
- [ ] No `# noqa` or `# type: ignore` without a one-line rationale on the same line.
- [ ] No fake metrics in README. Every number maps to `benchmarks/results.json`.
- [ ] No fake screenshots. Every image has a sibling metadata file.
- [ ] No hallucinated integrations (e.g., a "Slack integration" with one stub function).
- [ ] Every dependency listed in `pyproject.toml` is imported somewhere in `src/`.
- [ ] No "future work" section in README longer than 5 lines.
- [ ] No "we plan to" language in committed docs. Plans live in issues.

## Debt register

A single file `docs/DEBT.md` enumerates known debt:

```
| ID | Title | Created | Severity | Tracked Issue | Plan |
|---|---|---|---|---|---|
| DEBT-001 | example | 2026-05-10 | low | #42 | Address in v1.2 |
```

Entries are added when debt is incurred deliberately. The register is reviewed at every release. An entry that has sat for 3 releases without progress is escalated: either fixed, downgraded with rationale, or closed as "won't fix" with a one-line explanation.

## The "fake AI repo smell" defense

The single biggest signal of an AI-generated portfolio repo is **confidence without evidence**. We defeat it via:

1. **Reproducible README**. Every claim is a command.
2. **Honest commit history**. Iteration shows up. Squash-merging hides the right things (intermediate WIPs); it does not hide the existence of multiple PRs over multiple days.
3. **Tests that fail when broken**. The test suite is run against deliberately broken code in CI gates (mutation testing exercise during Phase 7 review).
4. **Screenshots with provenance**. `produced_at` + `evalkit_version` + `command` metadata files.
5. **Architecture diagram matches code**. ADR-0001 enforces this as a release gate.
6. **No marketing language**. Reviewers can smell it from a paragraph away.
7. **Reasonable scope**. v1 is a CLI. We do not over-promise.

## What we explicitly tolerate

We *will* leave these as debt, with explicit notes:

- SQLite-only storage (pre-meditated; documented in SPEC).
- No multi-Python version testing (we declare 3.12, only).
- Best-effort cost-USD numbers (we label them "approx").
- No Windows CI matrix (we declare Linux + macOS).

These are not pretending to exist; they are stated and bounded.

## What we do NOT tolerate

- "Coming soon" badges.
- Roadmap features in v1 docs that don't exist in v1 code.
- TODOs in committed code.
- Dependencies imported but never used.
- Test files that are 90% `assert True`.
- "@dataclass" classes that are never instantiated.
- Decorators that wrap and pass-through with no behavior.
- Configuration knobs nobody sets.
