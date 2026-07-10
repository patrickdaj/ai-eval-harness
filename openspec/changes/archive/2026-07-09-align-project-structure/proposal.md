## Why

`ai-eval-harness` is a flat pile of scripts (`eval.py`, `providers.py`, `scorers.py`,
`requirements.txt`) with no packaging, no tests, and no `.gitignore` — while its sibling
`agent-activity-mcp-server` already uses a clean `src/` package layout, a `pyproject.toml`,
a pytest suite with fixtures, and standard ignore rules. Aligning the two makes the harness
installable, testable, and CI-ready, and gives both projects one shared shape to maintain.
The harness is meant to be kept alive and extended for eight weeks, so it needs tests that
lock in its behavior before it grows.

## What Changes

- Adopt a `src/eval_harness/` package layout: move `eval.py`, `providers.py`, `scorers.py`
  into the package and convert cross-module imports to package-relative. **BREAKING**: the
  invocation changes from `python eval.py` to `python -m eval_harness` (a console-script
  entrypoint `eval-harness` is also provided). `cases.jsonl` stays at the repo root as the
  default eval set.
- Add a `pyproject.toml` (hatchling build backend) declaring the package, the optional
  `litellm` runtime extra, and a `dev` extra pinning `pytest` — replacing `requirements.txt`.
- Add a `tests/` suite (pytest) covering `scorers` (normalize/exact_match/judge fallback),
  `providers` (mock heuristic + tuple contract), and `eval` (load/run/report/exit-code),
  plus a small committed `cases.jsonl` fixture — mirroring the reference's `tests/` + fixtures.
- Add a `.gitignore` (venv, `__pycache__`, `*.pyc`, egg-info, `.pytest_cache`, build/dist)
  copied from the reference.
- Update `README.md` to document the new run command, install, and `pytest` workflow.

## Capabilities

### New Capabilities
- `project-packaging`: `pyproject.toml` + `src/eval_harness/` package layout making the
  harness pip-installable with a console-script / `python -m` entrypoint and declared deps.
- `harness-tests`: a pytest suite (with fixtures) that verifies scorers, the mock provider,
  and the eval load/run/report/exit-code pipeline offline.
- `repo-hygiene`: a `.gitignore` that keeps virtualenvs, caches, and build artifacts out of
  version control.

### Modified Capabilities
<!-- No existing specs in openspec/specs/; nothing's requirements change. -->

## Impact

- **Code moved**: `eval.py`, `providers.py`, `scorers.py` → `src/eval_harness/`; internal
  imports (`from providers import complete`, `from scorers import ...`) become package-relative.
- **Entrypoint**: `python eval.py` → `python -m eval_harness` / `eval-harness` console script.
- **Dependencies/build**: `requirements.txt` removed in favor of `pyproject.toml` extras
  (`.[litellm]` for real models, `.[dev]` for tests). New dev dependency: `pytest`.
- **New files**: `pyproject.toml`, `.gitignore`, `tests/` (+ fixtures).
- **Docs**: `README.md` run/install/test instructions updated.
- No change to eval logic, scoring behavior, or the mock classifier's outputs.
