## Context

`ai-eval-harness` is a flat set of scripts (`eval.py`, `providers.py`, `scorers.py`,
`cases.jsonl`, `requirements.txt`, `README.md`) that import each other by top-level module
name (`from providers import complete`) and are run as `python eval.py`. It has no tests, no
`.gitignore`, and no build config. Its sibling `agent-activity-mcp-server` — the structure
we're aligning to — uses a `src/<pkg>/` package, a hatchling `pyproject.toml` with optional
extras, a `tests/` suite with committed fixtures + helper scripts, a `scripts/` smoke test,
and a copied `.gitignore`.

A real constraint: the harness is deliberately a small, read-every-line teaching scaffold
(the README frames it as "~150 lines you own"). The restructure must preserve that legibility
and its offline-by-default, zero-dependency mock path — it should add standard structure
around the code, not rewrite the code.

## Goals / Non-Goals

**Goals:**
- Match the reference's `src/` package layout, `pyproject.toml` (hatchling), `tests/`, and
  `.gitignore`.
- Make the harness pip-installable with `python -m eval_harness` / `eval-harness` entrypoints.
- Add an offline pytest suite that locks in scorer, provider, and eval-pipeline behavior.
- Keep the mock path dependency-free and the offline run reproducible for CI.

**Non-Goals:**
- Changing eval logic, scoring math, the mock classifier's outputs, or the prompt.
- Copying MCP-specific artifacts (`.mcp.json`, server modules) — those are irrelevant here.
- Adding real-model integration tests (they need keys/network); the judge stays validated
  later in the program, not here.
- Expanding the eval set beyond the existing `cases.jsonl`.

## Decisions

**Package name `eval_harness` under `src/`.** Mirrors the reference's `src/agent_activity/`.
Distribution name `eval-harness`, import name `eval_harness`. Alternative: keep flat modules
and only add tests + `.gitignore`. Rejected because the user asked to align *structure*, and
a package is what makes install, entrypoints, and stable imports work regardless of CWD.

**Package-relative imports.** `from providers import complete` becomes `from .providers import
complete`; `from scorers import ...` becomes `from .scorers import ...`. `eval.py`'s module
name shadows the stdlib builtin `eval` only as an attribute of the package, which is safe;
we keep the filename `eval.py` for continuity but expose the CLI via `__main__.py` and a
console script so users never type the shadowed name.

**Entrypoints via `__main__.py` + console script.** Add `src/eval_harness/__main__.py` that
calls `eval.main`, and a `[project.scripts]` entry `eval-harness = "eval_harness.eval:main"`
— exactly the reference's pattern (`agent-activity = "agent_activity.server:main"`).
`python eval.py` stops working (**BREAKING**), documented in the README.

**Default `cases.jsonl` resolves independent of CWD.** Today `--cases` defaults to the
relative string `cases.jsonl`, which only works when run from the repo root. Keep `cases.jsonl`
at the repo root (it's eval *data*, edited often, not shipped code), but resolve the default
to an absolute path anchored at the project root so `python -m eval_harness` works from
anywhere. Alternative: ship `cases.jsonl` inside the package as data — rejected; the README
tells users to edit/replace it, so it belongs at the root, not in `src/`.

**`pyproject.toml` extras replace `requirements.txt`.** `litellm` moves to an optional
`[project.optional-dependencies].litellm` extra (real-model path), `pytest` to a `dev` extra
— matching the reference's `dev = ["pytest"]`. Delete `requirements.txt`; the README's
`pip install -r requirements.txt` becomes `pip install -e ".[litellm]"`.

**Tests mirror the reference's shape.** `tests/test_scorers.py`, `tests/test_providers.py`,
`tests/test_eval.py`, plus a tiny `tests/fixtures/cases.jsonl` for the pipeline test. All
offline via the mock provider. We assert the intentional baseline miss (mechanism-implied
critical → `info`) so a future "fix" to the mock can't silently change the teaching example.

## Risks / Trade-offs

- **Added ceremony vs. the "just read eval.py" ethos** → Keep modules unchanged line-for-line
  except imports; the README keeps a one-command run (`python -m eval_harness`). The structure
  wraps the scaffold; it doesn't obscure it.
- **`python eval.py` muscle memory breaks (BREAKING)** → Call it out prominently in the README
  and proposal; provide both `python -m eval_harness` and the `eval-harness` script.
- **`eval.py` module name shadows builtin `eval`** → Never referenced as a bare name; only as
  `eval_harness.eval` / a console-script target. Low risk, preserves file continuity.
- **CWD-relative default cases path could regress** → Anchor the default to the project root
  and cover it with a test that runs the loader from a different directory.

## Migration Plan

1. Create `pyproject.toml` and `.gitignore`; delete `requirements.txt`.
2. `git mv`/move the three modules into `src/eval_harness/`; add `__init__.py` (with
   `__version__`) and `__main__.py`; convert imports to relative; anchor the default cases path.
3. Add the `tests/` suite + fixture; run `pytest` (offline) to green.
4. Update `README.md` (install, run, test commands).
5. Verify `python -m eval_harness` and `eval-harness` both run and exit non-zero on the two
   known mock failures.

Rollback: revert the change; the original flat scripts are unchanged in git history.

## Open Questions

- None blocking. `scripts/` smoke test from the reference is optional and out of scope unless
  desired later.
