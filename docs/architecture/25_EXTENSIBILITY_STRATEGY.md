# 25 — EXTENSIBILITY_STRATEGY.md

## Goal

Make the *common* extensions easy and safe; make rare extensions *possible* without forking. Avoid premature plug-in surfaces that aren't backed by use cases.

## Stable extension points (v1)

### EP1 — Custom evaluators

- Mechanism: Python entry-point group `evalkit.evaluators`.
- Contract: implement the `Evaluator` Protocol; declare `name`, `version`, `evaluate(case, response) -> Evaluation`.
- Distribution: any pip-installable package. Users `pip install evalkit-myorg-evaluators` and reference by name in suite YAML.
- Discovery: built-ins first, then entry-points. Name collisions error out with both providers' module paths.
- Versioning: an evaluator's `version` is recorded in the DB per evaluation; old runs remain interpretable when an evaluator changes.
- Example: `examples/external_evaluator/` ships a working external evaluator package as documentation and as a smoke test.

### EP2 — Custom providers

- Mechanism: same — entry-point group `evalkit.providers`.
- Contract: `Provider` Protocol with async `complete()`.
- Most users won't need this — LiteLLM covers the common providers — but the surface is there for proprietary endpoints.

### EP3 — Custom report renderers

Not in v1. Phase 8+ candidate. Until then, JSON output is the integration point — write your own renderer downstream.

## Versioning

- **Suite YAML**: `version: 1`. Future versions `version: 2` etc. are loaded by dispatch on the `version` field. No silent migrations.
- **CLI**: command names and exit codes are part of the public contract. Removing a command requires a major version bump and a deprecation cycle.
- **Database**: schema is private; all access goes through `Repo`. Migrations are committed. We do not promise hand-written SQL against the schema.
- **Python API**: `evalkit.core` Pydantic models and Protocols are stable within a major version. Internal modules (anything not re-exported from `evalkit/__init__.py`) are not.

## Migration tactics

If we ever need to change a public surface:

1. Add the new shape alongside the old one.
2. Mark the old shape deprecated (Pydantic field `deprecated=True`, CLI prints a warning).
3. Wait one minor release.
4. Remove the old shape in the next major.

CHANGELOG.md is the single source of truth for migrations.

## Reserved names

- `evalkit.*` package namespace is reserved for first-party.
- Plugins use their own namespace (`evalkit_acme_*`). The convention is documented; not enforced (we do not police PyPI).
- The `evalkit` CLI command name is reserved; subcommands are part of the public contract.

## Future hooks designed-in but not built

These are *shaped* by today's architecture so adding them later does not require breaking changes:

- **Dataset adapters**: the dataset loader is a function `load(path: Path) -> Iterator[Case]`. Adding CSV, Parquet, or HF datasets means adding loaders without touching the runner.
- **Postgres backend**: SQLAlchemy abstraction; engine URL is configurable. We don't ship Postgres support; we don't *prevent* it.
- **Streaming reports**: the `RunRecord` is built incrementally during runs already. A future "live report" needs a renderer, not a re-architecture.
- **Cost models**: provider cost calc is centralized in one module. New cost rules go in there, not scattered.

## Things we deliberately do NOT generalize

- **Suite YAML expressions**. We will not add a templating language. If you need conditionals, write a script that emits the YAML. Templating engines are how every config tool dies.
- **Plugin lifecycle hooks** (pre-run, post-run, etc.). Today there is no use case strong enough to design a stable hook surface. We add hooks when we have two real customers asking. (User isn't even plural yet — discipline.)
- **Web SPA dashboard**. If a dashboard ships, it's HTMX. We will not introduce a JS framework as a maintenance liability.
- **Generic "agent" features**. Out of scope. AgentFlow (Project #9) is the right home.

## API stability promise

> Within a major version of EvalKit, suite YAML written for v1.X will continue to validate and run on v1.X+1.
> CLI commands and exit codes are stable within a major version.
> Internal Python modules are not stable. If you need a stable Python API, raise an issue.

This is the single sentence we put in the README's "Stability" section.

## Cross-project leverage

These extensibility hooks aren't just for users — they're the seams along which **other portfolio projects integrate with EvalKit**:

- TraceForge (Project #7) consumes EvalKit's OTel signals; no API needed.
- ModelMesh (Project #3) is a provider plugin (registered via `evalkit.providers`).
- ComplianceGraph (Project #8) consumes EvalKit JSON reports as input.
- AgentFlow (Project #9) ships an evaluator plugin (`evalkit.evaluators`) for agent-quality scoring.

Designing the seams now is what makes the portfolio coherent later — without us doing any extra work in v1 of EvalKit.
