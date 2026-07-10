## Context

The harness is a `src/eval_harness/` package built with hatchling and installed via
`pip install -e .`, with runtime extras (`litellm`, `pretty`) and a `dev` extra (`pytest`,
`rich`). There is no lockfile, so installs resolve fresh each time and are not reproducible.
The offline mock path is a deliberate zero-dependency feature and must stay that way. The
machine already has `uv` 0.7 installed. This change is packaging-tooling only — no
`src/eval_harness/` code, `cases.jsonl`, or test logic changes.

## Goals / Non-Goals

**Goals:**
- Make `uv` the standard, documented way to set up, run, and test the project.
- Add a committed `uv.lock` for reproducible installs and CI pinning.
- Keep the offline mock path dependency-free.
- Preserve the existing package layout, import surface, and `eval-harness` entrypoint.
- Keep `pip install -e .` working as a fallback so nothing breaks for pip users.

**Non-Goals:**
- Switching the build backend away from hatchling.
- Changing runtime behavior, the eval pipeline, or any module code.
- Publishing to an index or setting up release automation.
- Adding new runtime dependencies.

## Decisions

**Keep hatchling as the build backend.** `uv` is a package/workflow manager, not a build
backend; it drives any PEP 517 backend. Keeping hatchling avoids touching `[build-system]`
and the wheel-packaging config that already works. Alternative considered: switch to
`uv_build` — rejected as unnecessary churn with no benefit for this package.

**Move the `dev` toolchain to a PEP 735 `[dependency-groups]` group; keep runtime extras as
optional-dependencies.** `uv sync` installs the default `dev` group automatically, which is
the idiomatic uv split between "dev tooling" and "shippable optional features." `litellm` and
`pretty` are genuine optional runtime features a consumer may want, so they stay as
`[project.optional-dependencies]` (installable via `uv sync --extra litellm` or `pip install
-e ".[litellm]"`). Alternative considered: leave `dev` as an extra — works, but then `uv sync`
would not install the test toolchain by default, losing the main ergonomic win. Note `rich`
appears both as the `pretty` extra and in the `dev` group so the colored path is exercised in
tests.

**Commit `uv.lock`.** A lockfile is only reproducible if tracked. `.venv/` stays ignored. The
current `.gitignore` does not match `uv.lock`, so no change is strictly required there, but the
repo-hygiene spec is updated to make "lockfile is tracked" an explicit requirement.

**Document `uv` first, `pip` as fallback.** README primary commands become `uv sync` /
`uv run …`; the existing `pip install -e .` lines stay as an explicitly-supported fallback so
the zero-dependency and pip stories remain true.

## Risks / Trade-offs

- **Contributors without `uv` installed** → `pip install -e .` and the extras still work and
  remain documented; `uv` is recommended, not required.
- **`uv.lock` drift / merge conflicts on a lockfile** → acceptable for a small project; `uv
  sync` regenerates deterministically and the lock pins the offline path (which has no runtime
  deps) plus opt-in extras.
- **`rich` duplicated across the `pretty` extra and `dev` group** → intentional so tests cover
  the colored renderer; documented in `pyproject.toml`.
- **PEP 735 `[dependency-groups]` requires a recent toolchain** → `uv` supports it natively and
  modern `pip` understands it; pip users who only need runtime install are unaffected.

## Migration Plan

1. Edit `pyproject.toml`: add `[dependency-groups] dev = ["pytest", "rich>=13"]`, remove the
   `dev` optional-dependency entry, keep `litellm` and `pretty` extras.
2. Run `uv sync` (and `uv sync --extra litellm --extra pretty` once) to generate `uv.lock`;
   commit the lockfile.
3. Update `README.md` install/run/test sections to `uv` commands with `pip` fallback noted.
4. Confirm `.gitignore` does not ignore `uv.lock`.
5. Verify: `uv run python -m eval_harness` produces the expected report and non-zero exit on
   failures; `uv run pytest` passes; `pip install -e ".[dev]"` + `pytest` still works.

Rollback: revert the `pyproject.toml`/README edits and delete `uv.lock`; the pip workflow is
unchanged underneath.

## Open Questions

None — machine has `uv` available and the change is additive with a preserved pip fallback.
