## Why

The project is installed and run through `pip install -e .` against a hatchling
backend, with no lockfile — so environments are not reproducible and every install
resolves dependencies from scratch. Adopting [uv](https://docs.astral.sh/uv/) gives
fast, reproducible installs via a committed `uv.lock`, a single tool for creating the
environment, syncing deps, and running the harness, while keeping the zero-dependency
offline path intact.

## What Changes

- Adopt `uv` as the standard workflow tool for the project: environment creation,
  dependency sync, and running the harness/tests all go through `uv`.
- Add a committed `uv.lock` lockfile so installs are reproducible and CI is pinned.
- Move the `dev` toolchain from an optional-dependency extra to a PEP 735
  `[dependency-groups]` `dev` group, which `uv sync` installs by default. The
  `litellm` and `pretty` runtime extras stay as `[project.optional-dependencies]`.
- Keep the hatchling build backend and the existing package layout, import surface,
  and `eval-harness` console script unchanged — this is a workflow/packaging-tooling
  change, not a code change.
- Update `README.md` install/run/test commands to the `uv` equivalents
  (`uv sync`, `uv run`, `uv run --extra …`), keeping `pip install -e .` documented as
  a still-supported fallback.
- Track `uv.lock` in version control (keep `.venv/` ignored).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `project-packaging`: The build/dependency workflow requirement changes to make `uv`
  the standard tool, add a committed lockfile for reproducible installs, and move the
  `dev` toolchain to a PEP 735 dependency group (runtime extras unchanged). The
  installable layout, import surface, and command-line entrypoint requirements are
  unchanged in behavior but re-runnable via `uv`.
- `repo-hygiene`: The ignore-rules requirement changes so the `uv.lock` lockfile is
  explicitly tracked (committed), while `.venv/` and other generated artifacts stay
  ignored.

## Impact

- Dependencies: no runtime dependency changes; `uv` becomes the recommended local and
  CI toolchain. A `uv.lock` is added.
- Files: `pyproject.toml` (add `[dependency-groups]`, optional `[tool.uv]`), new
  `uv.lock`, `README.md` (commands), `.gitignore` (ensure `uv.lock` stays tracked).
- No changes to `src/eval_harness/` code, `cases.jsonl`, or test behavior.
- Users on `pip` are unaffected: `pip install -e .` and the extras continue to work.
