# 20 — COMMIT_STRATEGY.md

## Conventional commits, strictly

Format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types we use: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `build`, `ci`, `perf`, `revert`. We do not use `style` (Ruff format means there is never style-only churn).

Scopes match the labels in `19_GITHUB_REPO_STRATEGY.md` (`cli`, `runner`, `storage`, `evaluators`, `observability`, `docs`, `ci`).

Subject:
- imperative mood ("add", not "added").
- ≤72 chars.
- no trailing period.

Body (when present):
- *Why*, not *what*. The diff already tells you what.
- Reference issues (`Refs #12`) and ADRs (`Refs ADR-0007`).

Footer:
- `BREAKING CHANGE: …` lines for any public-surface change.

Examples:
```
feat(runner): bound concurrency with asyncio.Semaphore

The previous implementation fanned out provider calls
without a ceiling, which caused 429 storms against
OpenAI on suites with >50 cases.

Refs #14
```

## PR sizing

Hard rules:

- **<300 lines changed (added + removed)** is the target.
- **<600 lines** is the ceiling. Larger PRs are rejected and asked to be split.
- **Generated files** (lockfiles, migrations) are excluded from the count but called out in the PR description.

## Surgical-change discipline

The user's "behavioral engineering rules" map directly to commit policy:

1. **Touch only what is required.** Lint formatting drift in unrelated files is reverted before commit. `git diff --stat` is reviewed before every commit.
2. **No drive-by refactors.** A refactor lives in its own PR with its own justification.
3. **No reformatting whole files.** Ruff format runs in pre-commit on changed files only; we do not run `ruff format .` on a diff PR.
4. **Match existing style.** Reviewer asks: would this change be obvious to someone who didn't write it? If not, it's revised.
5. **Remove only dead code introduced by your changes.** Pre-existing dead code is filed as an issue, not deleted in passing.
6. **Mention unrelated issues, don't fix them.** PR description has an "Observed but not changed" section when applicable.

## Commit cadence

- Multiple small commits per PR are fine in the branch; squashed at merge.
- Each commit on the branch should compile and pass at least lint+type. (We don't enforce per-commit pytest because that creates incentive to bundle.)
- "WIP" commits get squashed before merge. The squash merge produces one clean commit on `main`.

## What never lands on `main`

- Commits prefixed `WIP`, `tmp`, `fix later`, `???`.
- Commits with `[skip ci]` unless the PR description justifies it.
- Commits that disable a test without a tracking issue.
- Commits that add `# noqa` / `# type: ignore` without a comment explaining why.
- Commits authored under generic `noreply` identities. We use real authorship.

## Tags

- `vX.Y.Z` only.
- Tag is annotated, signed (`git tag -s`), and pushed only after `release.yml` preflight is green.
- Pre-releases use `vX.Y.Z-rc.N`.

## ADRs

When a PR makes a non-obvious architectural decision, the PR adds an ADR file under `docs/adr/NNNN-<slug>.md` using the standard template (Status, Context, Decision, Consequences). ADR-0001 is the meta-ADR establishing the practice.

## Devin-specific commit rules

- Devin commit messages must follow the same conventions as human commits.
- Devin must not amend commits. Add new commits to fix issues.
- Devin must not push to `main` directly (also enforced by branch protection).
- Devin's PR description fills the template; "I implemented X" is not acceptable as a *Why*.
- Devin sessions ending without merging must leave the branch in a state where `make ci` passes locally — partial branches are fine, broken branches are not.
