# META — Operating manual for the portfolio

This file answers the meta-questions in the brief. It is portfolio-level, not EvalKit-specific. Treat it as the standing operating procedure for every project after Project #1.

---

## 1. How to avoid wasting Devin credits

Treat Devin as a **deterministic execution engine**, not an open-ended agent. Credits go to waste when Devin does work that should have been work for you, Claude, or Cursor.

**Use Devin for:**
- Repo scaffolding (one-time, deterministic).
- Tests, fixtures, golden files.
- CI/CD workflows.
- Dockerfiles + multi-stage build tuning.
- Refactors with explicit before/after.
- Bug fixes with a failing test attached.
- Migrations and codemods.
- Boilerplate that has a single right answer.
- Repetitive grunt across the codebase.

**Do not use Devin for:**
- Architecture decisions. Those are conversations with Claude/GPT and you, captured as ADRs. Devin only implements ratified decisions.
- Naming things. You decide; Devin types it.
- Open-ended product/UX taste calls.
- "Figure out what to build next." Phasing is decided in this doc.
- Web research that you can do in 60 seconds yourself.

**Process discipline:**
1. **Ticket every Devin run** with: goal, exact files in scope, acceptance criteria (commands + expected outputs), forbidden actions ("do not refactor X", "do not change DB schema").
2. **Three-strikes rule.** If Devin's PR fails the same check three times, the session stops. The fourth attempt is preceded by a written hypothesis: what changed in the model of the problem? Without a new hypothesis, you'll burn credits on the same failure.
3. **Cap session length.** Keep sessions short and scoped to a single phase or sub-phase. A 90-minute session with a clear deliverable is cheaper than a 6-hour session that drifts.
4. **Reuse blueprints.** The environment blueprint for one project should be the starting point for the next. Don't pay setup cost twice.
5. **Local pre-flight.** Run `make ci` locally on Devin's branch before kicking off CI. Failed CI runs that you could have caught locally are pure waste.
6. **No exploratory Devin.** "Try a few approaches" is forbidden. You decide the approach; Devin executes it.
7. **Attach evidence to every Devin task.** Logs, screenshots, repro commands. Devin's job is to *converge*, which it does faster with evidence than with prose.

---

## 2. How to avoid infinite fix loops

Fix loops happen when neither Devin nor you can locate the *root cause*, so each fix attacks a symptom.

**Hard rules:**
1. **Failing test first.** No fix lands without a test that reproduces the failure. The test goes in *first*. Without it, you're guessing.
2. **Hypothesis-or-stop.** After the second consecutive failed attempt, write down — in the PR description — a one-paragraph hypothesis of the root cause. If you can't, stop and gather more data. Do not allow a third attempt without this.
3. **Determinism over patience.** Most fix loops are caused by non-determinism: real network calls in CI, time-based logic, race conditions in async code. Fix the determinism, not the flake. EvalKit's CI uses the `mock` provider exclusively for this reason.
4. **Pin the world.** Pin Python, pin uv-lock, pin GitHub Actions to commit SHAs, pin Docker base image. Drift is the silent cause of "but it worked yesterday."
5. **Bisect when stuck.** When a fix loop has more than two attempts, stop fixing and start bisecting against the last known good commit. `git bisect` against `make ci` is unglamorous and effective.
6. **Reduce to a minimal repro.** A bug that needs the whole repo to reproduce is a bug that fix loops. Get to a 30-line repro before patching the framework.
7. **Resist patch escalation.** Don't add `try/except` to mask the symptom. Don't add `time.sleep` to mask a race. Each is a contract about how the system *should* behave; if the contract is wrong, change the contract, not the test.

**For Devin specifically:**
- Devin's branch protection: a session that fails the same check 3× must surface the failure to the user with the hypothesis, not push a fourth attempt.
- After CI fails, Devin must read CI logs (we have a tool for this) before acting. Pushing a "maybe this works" commit without reading the failure log is a fix-loop accelerator.

---

## 3. How to write good spec documents

The spec quality bar this docset is meant to set:

1. **Constraints first, then requirements, then design.** Most bad specs invert this and design something the constraints forbid.
2. **Non-goals are mandatory.** A spec without a non-goals section is a wish list. Non-goals create permission to say no.
3. **Decisions are recorded with tradeoffs.** Every non-obvious choice has a one-line rationale. ADRs for the *really* non-obvious ones.
4. **No prose where a table works better.** Tables force discipline; prose hides waffle.
5. **Every spec ends with acceptance scenarios.** "When I do X, Y happens, exit code is Z." Without this, "done" is a vibe.
6. **Specs are short.** A spec longer than ~1,500 words is poorly factored. Split it.
7. **Specs are versioned.** Edits are diffable. We don't lose decisions.
8. **A spec names what it does NOT cover.** If the runner spec doesn't talk about reports, it says so explicitly.
9. **A spec resists being a manifesto.** No mission statements. No "we believe in…". The spec is for the next engineer (often you, in 6 months).
10. **Reviewable by a smart skeptic in 10 minutes.** If a senior engineer can't grok it in 10 minutes, the spec is too long or too vague.

The 25 documents in this docset apply these rules to themselves. They're concise, evidence-shaped, and link to each other instead of duplicating.

---

## 4. How to phase implementation correctly

A phase is correctly sized when:

- It produces a **demonstrable, testable artifact** at the end.
- It can be **reverted as a unit** (one merged PR, one tag).
- It has a **single human review checkpoint**, with a clear approval question.
- It does not require future phases to be *correct* (it can be incomplete, but what exists must work).
- It is **between half a day and 1.5 days** of focused work.

Anti-patterns:

- "Foundations" phases that produce nothing demoable. Phase 0 is allowed exactly one of these.
- Phases that require parallel work in two unrelated areas (split them).
- Phases that need >3 PRs to land. The boundary was chosen wrong.
- Phases whose review is "looks good." If you can't write a 5-question checklist for the review, the phase is too vague.

The roadmap in `21_PHASED_ROADMAP.md` is calibrated to these rules. Each phase has explicit deliverables, exit criteria, and a checkpoint. Phase 0 is the only "foundations" phase; everything from Phase 1 on produces user-visible value.

---

## 5. How to maintain architectural consistency across projects

The portfolio is 10 projects (eventually). Consistency is what makes it credible as the work of one engineer rather than ten unrelated demos.

**Mandatory shared substrate** (codified in a private template repo `evalkit-template` after EvalKit ships):

- Python 3.12, uv, Ruff, Mypy strict, Pytest.
- structlog + OTel-ready (`{project}.observability` module in every project).
- pydantic-settings config.
- One exception hierarchy per project, rooted at `{Project}Error`.
- `src/{project}/` layout.
- The same `pyproject.toml` shape, the same `Makefile` targets, the same CI workflow files.
- Apache-2.0.
- The same README structure (see `17_README_STRATEGY.md`).
- The same anti-smell checklist (see `24_TECH_DEBT_STRATEGY.md`).

**Mandatory shared *interfaces*** (where projects integrate):

- Every project that emits run records emits the **same JSON shape** at the top level (run_id, started_at, status, summary). Downstream tools (TraceForge, ComplianceGraph) consume that shape uniformly.
- Every project that exposes evaluators registers them via `evalkit.evaluators` entry-points. EvalKit becomes the *evaluation substrate* for the rest of the portfolio.
- Every project's CLI uses the same exit codes (0 ok, 1 user-error-but-not-crash, 2 infra, 64 usage, 70 internal).
- Every project's logs are JSON with the same set of context keys.

**What is *not* shared:**
- Domain models (each project has its own).
- Frontend technology when applicable (chosen per project, but always "thin").
- Database schemas (each project owns its data).

**Process:**
- Before starting a project, update the template repo with anything learned in the previous one.
- Each new project starts by forking the template, not by cloning the previous project (which would carry over inappropriate domain code).

---

## 6. How to maintain production quality across the portfolio

Five disciplines, applied identically to every project:

1. **No merges without:** green CI, ≥85% test coverage, no smell-checklist failures, an updated CHANGELOG entry, an ADR for non-obvious decisions, real screenshots if README changes.
2. **Reproducibility over impressiveness.** If a number is in the README, a command is in the README. If a screenshot is in the README, a `make demo` target produces it.
3. **Deprecation has a process.** No silent removals. No "we deleted the X feature" surprises.
4. **Cadence over crunch.** A merged PR per week beats a 3-day push. Recruiters and reviewers can read commit history.
5. **Manual review is not optional.** Even on solo projects, the checkpoint pattern in `22_REVIEW_CHECKPOINTS.md` is non-negotiable. You are your own reviewer; create the seams that force a re-read pass.

Equipment:

- A shared "production checklist" in the template repo, run before every release across every project.
- A portfolio-level dashboard (eventually built on TraceForge) showing CI status, last-release date, and image sizes per project. Public on a personal site; recruiters see it.

---

## 7. How to prevent the "fake AI repo smell"

The smells, and their defenses, in priority order:

| Smell | Defense |
|---|---|
| Confident numbers, no provenance | Every README number maps to a benchmark JSON or a screenshot metadata file. |
| Architecture diagrams that don't match the code | ADR-0001 mandates diagram-code parity; release gate verifies. |
| Empty folders / placeholder files | `scripts/anti_smell.sh` fails CI on these. |
| TODOs and FIXMEs in code | Ruff TD/FIX rules fail the build. |
| README features that don't exist in code | `make readme-verify` runs every command in the README. |
| "We plan to" / "future work" filler | Roadmaps live in issues, not READMEs. |
| Marketing language ("revolutionary", "next-generation") | Anti-smell checklist; manual review. |
| Emoji-laden headers and "Made with ❤️" footers | Anti-smell checklist. |
| Test files with `assert True` or test-of-test patterns | Coverage and mutation testing during Phase 7 review. |
| Decorators / abstractions that wrap nothing | `vulture` and code review. |
| Generic boilerplate comments ("# Set up the database") | Comment policy: no diff-comments, no narration. |
| Hallucinated integrations (Slack, Jira, etc.) | Every integration must have a working `make demo` path. |
| Squash-everything history | We squash-merge but the *PR list* is preserved; rich PR descriptions show the iteration. |
| Repo with no recent activity | Cadence discipline; "hibernation" note in README if dormant. |
| Generic `services/`/`factories/`/`managers/` folders | Folder-structure doc explicitly forbids them. |

The deepest defense is **scope honesty**: the SPEC says EvalKit is a CLI for evaluating LLM outputs. It is not a "platform". It is not "enterprise-grade observability for AI applications". It is the thing it is. Reviewers respect that; they distrust everything else.

---

## 8. The 90-day plan — what I would actually do

If the goal is *highest probability of success, strongest GitHub, strongest recruiter signal, strongest consulting potential, strongest long-term leverage, realistic solo execution over 90 days*, here is exactly what I would do.

### Strategic frame

Don't build 10 unrelated tools. Build a **coherent infrastructure story** with three projects, ship them well, and write about them. Recruiters and consulting prospects buy *narrative* more than they buy *quantity*.

The story I'd tell: **"I build the substrate teams need to ship LLM features safely: evaluation, observability, and routing."** That maps to:

- **Project #1: EvalKit** — eval discipline (pytest-shaped).
- **Project #7: TraceForge** — observability for LLM apps (consumes EvalKit's OTel signals).
- **Project #3: ModelMesh** — provider-routing/orchestration gateway (registers as a Provider in EvalKit; instrumented by TraceForge).

These are the three projects where (a) the engineering is concrete enough to demonstrate without falling into "AI agent" theater, (b) they integrate with each other so the portfolio looks like a system, and (c) every senior engineer hiring for AI infra understands what they are.

The other 7 projects in your list are for *later*. **InsuranceOps and ComplianceGraph are vertical plays** — strong consulting potential but require domain specialists to verify; they are higher-ROI *after* the infra triad is shipped and you have a public reputation. **ShadowQA, AgentFlow, LocalMind, VoiceOps, DataPilot** are interesting but each carries enough novelty risk that running three serious infra plays first is the safer bet.

### Week-by-week

**Week 1 — Setup & EvalKit Phase 0–1**
- Day 1: New GitHub org, GH account hardened, signed commits, dotfiles, dev environment.
- Day 1: Clone this docset into the EvalKit repo's `docs/architecture/`.
- Days 2-3: Phase 0 (skeleton). Tag `v0.0.1`.
- Days 4-5: Phase 1 (core + mock e2e). Tag `v0.1.0`.
- Cadence: at least 1 merged PR/day. Real history, not fake.

**Week 2 — EvalKit Phase 2–4**
- Days 1-2: Phase 2 (real providers + retry).
- Day 3: Phase 3 (full evaluator suite).
- Days 4-5: Phase 4 (reports + regression).

**Week 3 — EvalKit Phase 5–7 + write**
- Days 1: Phase 5 (observability).
- Day 2: Phase 6 (release pipeline). Cut `v1.0.0-rc.1`.
- Days 3-4: Phase 7 (README, screenshots, video, benchmarks). Cut `v1.0.0`.
- Day 5: **Write a serious blog post** on EvalKit: "Why we built a pytest-shaped LLM evaluator." 1,500 words, code samples, real numbers. Post to your personal site.

**Week 4 — Distribution & feedback**
- Day 1: Submit to Show HN, /r/LocalLLaMA (relevant subset), Lobsters. Don't beg; let the work speak.
- Days 2-3: Respond to feedback, file issues, ship `v1.0.1`/`v1.1.0` for legitimate ones. Do not ship "AI-generated" patches in response to drive-by comments.
- Day 4: Reach out to 5 specific people who'd appreciate the work — eval-team engineers at AI labs, infra leads at LLM-native startups, authors of competing tools. Ask for a 15-minute critique. No pitch.
- Day 5: Phase 8 decision (dashboard) **only** if there's a real ask. Otherwise skip and start TraceForge.

**Weeks 5-7 — TraceForge (Project #7)**
- Same phased pattern.
- Key integration: TraceForge ingests OTLP from EvalKit; the combined demo shows an EvalKit run's trace tree rendered in TraceForge.
- 90-second video shows: EvalKit run → TraceForge dashboard → click into a regressed case → see the prompt/response/score in context.
- Tag `v1.0.0` end of week 7.

**Week 8 — Integration story + portfolio site**
- Build a personal portfolio site (single static page) with:
  - Hero: "AI infra triad — eval, observe, route."
  - One paragraph and one screenshot per shipped project.
  - Links to the demo videos.
  - The integration video showing both projects working together.
- Write the integration blog post: "How EvalKit + TraceForge form an evaluation feedback loop."

**Weeks 9-11 — ModelMesh (Project #3)**
- Same phased pattern.
- Build it as an MCP/API gateway with: rate limiting, routing rules, cost-aware fallback, OTel emission, exposed as an EvalKit provider.
- Three-way integration video: EvalKit runs cases through ModelMesh, TraceForge shows the routing decisions in spans.
- Tag `v1.0.0` end of week 11.

**Week 12 — Polish, distribution, consulting positioning**
- Day 1: Fix anything that's drifted in EvalKit/TraceForge while ModelMesh was being built. (Cadence matters.)
- Day 2: Update the portfolio site with the three-project story.
- Day 3: Record a 5-minute "system tour" video showing all three working together. Post to YouTube and embed.
- Day 4: Write a final positioning post: "Building AI infrastructure for solo teams." Post to your site, share.
- Day 5: Targeted outreach. Reach out to:
  - 10 hiring managers / staff engineers at companies where AI infra is a known need.
  - 3 specific consulting prospects (early-stage AI startups that need eval and observability but can't afford a platform team).
  - Don't send the same message; reference what they're working on.

### What this is NOT

- It's not 10 projects in 90 days. That's the trap. 10 weak projects ship as 0; 3 strong projects ship as 3.
- It's not viral marketing. The work has to be good enough to evaluate technically.
- It's not "I built an AI agent." Recruiters in serious AI infra orgs are tired of agent demos.
- It's not chasing trends. MCP, agents, RAG — these come and go. Eval discipline, observability, routing — these stay.

### Recruiter signal — what actually moves it

In rough order of impact:
1. **One project a senior engineer can read in 30 minutes and respect.** EvalKit alone, done well, beats a portfolio of five half-things.
2. **Real CI on a public repo with green builds over weeks.** History is hard to fake.
3. **Reproducible benchmarks in the README.** Hand-typed numbers fool no one; provenance impresses.
4. **A demo video that shows the engineer's typing, terminal, and editor habits.** This is hard to over-state. Senior engineers watch how you work.
5. **A blog post that explains *why* you made a decision and what you would change.** This is the single fastest way to demonstrate seniority.
6. **Cadence.** A repo with weekly PRs over 3 months reads as "this person ships." A repo with one giant initial commit reads as "this person had a hackathon."

### Consulting potential — what to do specifically

- After Week 8, the portfolio is concrete enough for a consulting positioning page on your site:
  - "I help AI-product teams set up evaluation, observability, and provider routing without buying a platform."
  - One paragraph per offering, with the relevant project as the credentials.
  - Pricing pages are optional; a "book a 30-minute call" link is not.
- Start a *very small* email list (5–20 subscribers from week 4–8 outreach). Send 1 thoughtful email per month. This is your highest-leverage long-term asset.
- Build a tiny "evalkit-starter" or "traceforge-starter" repo per consulting client. The starter ships with their suite/dashboard scaffolded; you charge for setup + a year of support. This is the realistic shape of solo AI-infra consulting.

### Long-term leverage — what to invest in beyond Week 12

- **Keep the three repos alive.** A repo's value to recruiters depreciates if it goes silent. One small PR per week per project keeps them looking shipped.
- **Write 1 deep technical post per month.** "What I learned shipping retry policies in EvalKit." "Why TraceForge exposes OTLP and not a custom protocol." These compound.
- **Speak when invited.** Local meetups, podcasts that match the audience. Don't seek fame; accept invitations.
- **Project #4-#10 are now optional.** If a consulting client needs ShadowQA-shaped work, ship it as a client project that becomes an open-source release. Let the market pull projects out of you, instead of pushing them.

---

## 9. Devin behavioral rules — the operationalization

The user's behavioral engineering rules ("think before coding, simplicity first, surgical changes, goal-driven execution") are operationalized as:

1. **Before any Devin coding session starts**, Devin produces a 5-line plan and waits for the user's "go". The plan names: files in scope, files out of scope, success criteria, how it will be tested.
2. **Devin states assumptions explicitly** in the PR description under "Assumptions", with the line: "Reject the PR if any of these is wrong."
3. **Devin proposes the simpler approach when one exists**, even if the user's brief implies a more complex one. The proposal is non-blocking; user approves with thumbs-up emoji or types the alternative.
4. **Devin flags scope drift**. If implementing a phase requires touching code outside the phase's declared scope, Devin stops and asks before doing it.
5. **Devin writes the test before the implementation** wherever feasible. Bug fixes always start with a failing test.
6. **Devin verifies after every phase**: `make ci` green, demo command works, screenshots regenerated, README claims still hold.
7. **Devin does not refactor unrelated code**, does not reformat unrelated files, does not rename things outside the change's purpose. All such temptations are filed as issues with `kind:chore` and a note in the PR description.

These rules are codified once in `CONTRIBUTING.md` and `.github/PULL_REQUEST_TEMPLATE.md`, so every future PR — Devin's or human's — operates under them.

---

## 10. Final word

The portfolio works if **every commit, every README sentence, every screenshot survives a skeptical 30-second scan by a senior engineer**. That is the only bar that matters. Volume, framework choice, "AI features" — all secondary. Build three things that survive that scan, write about them honestly, and the rest follows.
