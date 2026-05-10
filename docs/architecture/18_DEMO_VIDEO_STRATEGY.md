# 18 — DEMO_VIDEO_STRATEGY.md

## Goal

A 90-second screencast that proves EvalKit works end-to-end and is the kind of tool a serious engineer built. One video, embedded in the README via animated WebP / linked YouTube.

## Script (90 seconds)

| Time | Action | Voice-over (or captions) |
|---|---|---|
| 0:00 – 0:08 | `pip install evalkit && evalkit init demo && cd demo` | "EvalKit is a CLI for evaluating LLM outputs. One install, one init, you're running." |
| 0:08 – 0:18 | Open `suite.yaml` in editor; show 20-line config. | "Suites are YAML — dataset, models, evaluators." |
| 0:18 – 0:38 | `evalkit run suite.yaml`; show progress, then green summary. | "Runs are bounded-concurrency, retried on transient errors, persisted to SQLite." |
| 0:38 – 0:50 | `evalkit show <run-id>`; show per-case table. | "Every case is reproducible from a run id." |
| 0:50 – 1:05 | Edit a model param to degrade quality; rerun; `evalkit compare baseline current`. | "The same suite catches regressions automatically." |
| 1:05 – 1:18 | Show Jaeger trace open in browser, spans labelled. | "OpenTelemetry-ready — every case is one span tree, exported wherever you collect." |
| 1:18 – 1:30 | Show GitHub PR with EvalKit CI step failing on a regression. | "Drop it into CI to gate merges." |

No intro card. No outro card. No music. The point is engineering credibility, not production value.

## Recording discipline

- Resolution: 1920×1080.
- Terminal font: large enough to read at YouTube 720p.
- One take per scene, edited with `ffmpeg` — no jump cuts that compress reality (e.g., we do not skip the actual `evalkit run` wait).
- The `make demo-video` target produces the demo project state used in the recording. Re-running the same target tomorrow produces the same state.

## Authenticity rules

- The Jaeger trace shown is the trace from the **same run** demonstrated earlier, not a stock screenshot.
- The GitHub PR shown is a real PR in a real demo repo (e.g., `evalkit-ci-demo`) with real history.
- The regression shown is reproducible: docs/demo/REGRESSION.md describes how to trigger it.
- No off-screen "magic". If a step takes 12 seconds, the video shows 12 seconds (lightly time-trimmed but never falsified).

## Hosting

- Primary: YouTube unlisted link.
- Embedded in README as an animated WebP (5–10s, looped) of the most informative scene (probably the regression `compare`).
- Link in PR description format: "[90s demo video](https://youtu.be/...)" near the top.

## What we will NOT do

- No AI voice generators.
- No "look at this beautiful UI" framing — it's a CLI; we own that.
- No fake terminal UIs (asciinema is fine; faked colors via post-processing are not).
- No "as seen on Hacker News" claims.

## When the video gets re-recorded

- Major version releases (`v1.0`, `v2.0`).
- Any change to the CLI command shown in the script.
- Any change to the report layout shown in the screen.

The video lives in `docs/demo/v1.mp4` and `docs/demo/v1.webp`; older versions are kept for traceability.
