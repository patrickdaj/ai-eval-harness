## 1. Build config & hygiene

- [x] 1.1 Add `.gitignore` at project root with the reference's rules (`.venv/`, `__pycache__/`, `*.pyc`, `*.egg-info/`, `.pytest_cache/`, `dist/`, `build/`)
- [x] 1.2 Add `pyproject.toml` (hatchling backend): `[project]` name `eval-harness`, version `0.1.0`, `requires-python`, description/readme/license; `[project.optional-dependencies]` with `litellm = ["litellm>=1.50"]` and `dev = ["pytest"]`; `[project.scripts]` `eval-harness = "eval_harness.eval:main"`; `[tool.hatch.build.targets.wheel] packages = ["src/eval_harness"]`
- [x] 1.3 Delete `requirements.txt` (superseded by the `litellm` extra)

## 2. Package layout

- [x] 2.1 Create `src/eval_harness/` and move `eval.py`, `providers.py`, `scorers.py` into it
- [x] 2.2 Add `src/eval_harness/__init__.py` with a docstring and `__version__ = "0.1.0"`
- [x] 2.3 Add `src/eval_harness/__main__.py` that imports and calls `eval.main` so `python -m eval_harness` runs the harness
- [x] 2.4 Convert cross-module imports to package-relative: `from .providers import complete`, `from .scorers import exact_match, llm_judge`, and the lazy `from .providers import complete` inside `llm_judge`
- [x] 2.5 Anchor the default `--cases` path to the project root so `python -m eval_harness` works from any CWD (keep `cases.jsonl` at the repo root)

## 3. Tests

- [x] 3.1 Add `tests/fixtures/cases.jsonl` — a small JSONL fixture with known pass and known-miss cases
- [x] 3.2 Add `tests/test_scorers.py` — `normalize` (case/whitespace/trailing dot), `exact_match` positive+negative, `llm_judge` mock fallback equals `exact_match`
- [x] 3.3 Add `tests/test_providers.py` — `complete("...", model="mock")` returns `(str, float, float)` with cost `0.0`; keyword heuristic hits per severity; mechanism-implied critical (OOM/segfault) returns `info`
- [x] 3.4 Add `tests/test_eval.py` — `load_cases` parses the fixture; `run` yields one scored row per case; `report` returns `True` on all-pass and `False` when a case misses
- [x] 3.5 Run `pytest` from the project root and confirm the suite passes fully offline (no key, no `litellm`)

## 4. Docs & verification

- [x] 4.1 Update `README.md`: install (`pip install -e ".[litellm]"`), run (`python -m eval_harness` / `eval-harness`), and test (`pip install -e ".[dev]" && pytest`) instructions; update the "What's inside" file table for the `src/` layout
- [x] 4.2 Verify `python -m eval_harness` and the `eval-harness` console script both print the report and exit non-zero on the two known mock failures
