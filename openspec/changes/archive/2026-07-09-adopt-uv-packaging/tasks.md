## 1. Update packaging metadata

- [x] 1.1 In `pyproject.toml`, add a PEP 735 `[dependency-groups]` section with `dev = ["pytest", "rich>=13"]`
- [x] 1.2 Remove the `dev` entry from `[project.optional-dependencies]`, keeping `litellm` and `pretty` extras unchanged
- [x] 1.3 Add a short comment noting `rich` is intentionally in both the `pretty` extra and the `dev` group (so tests exercise the colored path)
- [x] 1.4 Confirm `[build-system]` (hatchling), `[project.scripts]`, and `[tool.hatch.build.targets.wheel]` are left unchanged

## 2. Generate and commit the lockfile

- [x] 2.1 Run `uv sync` to create the project environment and generate `uv.lock`
- [x] 2.2 Run `uv sync --extra litellm --extra pretty` once to ensure extras resolve into the lock
- [x] 2.3 Verify `.gitignore` does not match `uv.lock`; ensure `.venv/` and other generated artifacts remain ignored
- [x] 2.4 Stage `uv.lock` for commit (leave `.venv/` untracked)

## 3. Update documentation

- [x] 3.1 Rewrite the README "Install" section to lead with `uv sync` (and `uv sync --extra litellm` / `--extra pretty`), keeping `pip install -e .` documented as a supported fallback
- [x] 3.2 Update the "Run it" section to `uv run python -m eval_harness` / `uv run eval-harness`, noting the plain `python -m eval_harness` still works inside the synced env
- [x] 3.3 Update the "Tests" section to `uv sync` + `uv run pytest`, keeping the pip `--group dev` fallback (was `.[dev]`; changed per PEP 735 group move)
- [x] 3.4 Update the `pyproject.toml` row in the "What's inside" table to mention the `dev` dependency group and `uv.lock`

## 4. Verify

- [x] 4.1 Run `uv run python -m eval_harness` and confirm it prints the report and exits non-zero when cases fail
- [x] 4.2 Run `uv run pytest` and confirm the full suite passes
- [x] 4.3 Confirm the `pip` fallback still works: `pip install -e . --group dev` then `pytest` (updated from `.[dev]` per PEP 735 group move)
- [x] 4.4 Run `openspec validate --change adopt-uv-packaging` and confirm it passes
