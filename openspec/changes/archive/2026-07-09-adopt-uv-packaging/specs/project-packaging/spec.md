## MODIFIED Requirements

### Requirement: Build configuration and dependencies

The project SHALL declare its build backend, metadata, and dependencies in a `pyproject.toml`
using the hatchling backend. `uv` SHALL be the standard workflow tool for creating the
environment and installing dependencies, and the project SHALL include a committed `uv.lock`
lockfile so installs are reproducible. Runtime use of a real model (`litellm`) and colored
output (`pretty`) SHALL remain optional extras under `[project.optional-dependencies]`. The
test toolchain (`pytest`) SHALL be declared under a PEP 735 `[dependency-groups]` `dev` group
that `uv sync` installs by default.

#### Scenario: Offline install needs no third-party runtime deps

- **WHEN** the package environment is synced without any extras (`uv sync --no-dev` or
  `pip install -e .`)
- **THEN** the mock eval path runs using only the Python standard library, and `litellm`
  is installed only when the `litellm` extra is requested

#### Scenario: Reproducible install from the lockfile

- **WHEN** a developer runs `uv sync` in a clean checkout
- **THEN** `uv` resolves and installs the exact versions pinned in the committed `uv.lock`,
  creating a project virtual environment without a separate manual venv step

#### Scenario: Dev group provides the test toolchain

- **WHEN** a developer runs `uv sync` (which installs the default `dev` dependency group)
- **THEN** `pytest` is available to run the test suite via `uv run pytest`

### Requirement: Command-line entrypoint

The harness SHALL be runnable as a module via `python -m eval_harness` and via a console
script named `eval-harness`, both invoking the eval `main()`, and both SHALL be runnable
inside the uv-managed environment via `uv run` (e.g. `uv run python -m eval_harness` or
`uv run eval-harness`). The default eval set SHALL resolve to `cases.jsonl` regardless of the
current working directory when not overridden.

#### Scenario: Run via module entrypoint

- **WHEN** `python -m eval_harness` (or `uv run python -m eval_harness`) is executed
- **THEN** the harness loads the default cases, runs the mock model, prints the report, and
  exits non-zero if any case fails

#### Scenario: Run via console script

- **WHEN** the installed `eval-harness` console script is executed with no arguments
  (directly or via `uv run eval-harness`)
- **THEN** it behaves identically to `python -m eval_harness`
