"""End-to-end CLI tests via subprocess.

Exercises the same flow a user runs from the README: `evalkit init` produces a
runnable scaffold, then `evalkit run` exits 0 against the bundled mock dataset,
and `evalkit list runs` / `evalkit show` reflect the result.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PYTHON = sys.executable


def _run(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "-m", "evalkit", *args],
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
        check=False,
    )


@pytest.mark.e2e
def test_init_then_run_then_show(tmp_path: Path) -> None:
    proj = tmp_path / "demo"
    db = tmp_path / "evalkit.db"

    # init
    init = _run(["init", str(proj)])
    assert init.returncode == 0, init.stderr
    assert (proj / "suite.yaml").exists()
    assert (proj / "datasets" / "sample.jsonl").exists()

    # run
    run = _run(["run", str(proj / "suite.yaml"), "--db", str(db)])
    assert run.returncode == 0, run.stderr
    assert "passed=2" in run.stdout
    assert "failed=0" in run.stdout

    # list
    listing = _run(["list", "runs", "--db", str(db)])
    assert listing.returncode == 0
    assert "starter" in listing.stdout

    # show — extract the run_id from the listing
    run_id = listing.stdout.split()[0]
    show = _run(["show", run_id, "--db", str(db)])
    assert show.returncode == 0
    assert "PASS" in show.stdout
    assert "exact_match/1.0" in show.stdout


@pytest.mark.e2e
def test_run_returns_exit_one_when_a_case_fails(tmp_path: Path) -> None:
    proj = tmp_path / "demo"
    db = tmp_path / "evalkit.db"
    proj.mkdir()
    (proj / "datasets").mkdir()
    (proj / "suite.yaml").write_text(
        "version: 1\nname: failing\ndataset: datasets/d.jsonl\n"
        "models:\n  - id: m\n    provider: mock\n    params: {}\n"
        "evaluators:\n  - name: exact_match\n",
        encoding="utf-8",
    )
    (proj / "datasets" / "d.jsonl").write_text(
        '{"case_id":"a","input":{"messages":[{"role":"user","content":"hello"}]},'
        '"expected":{"text":"WRONG"}}\n',
        encoding="utf-8",
    )

    run = _run(["run", str(proj / "suite.yaml"), "--db", str(db)])
    assert run.returncode == 1
    assert "failed=1" in run.stdout
