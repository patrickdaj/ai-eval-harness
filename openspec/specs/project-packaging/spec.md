# project-packaging Specification

## Purpose

Define how the eval harness is packaged, built, and run so it is installable as a
standard Python package with a stable import surface and command-line entrypoint.

## Requirements

### Requirement: Installable package layout

The harness SHALL be organized as a `src/eval_harness/` Python package containing the
`eval`, `providers`, and `scorers` modules, with cross-module imports expressed as
package-relative imports so the package is importable after installation.

#### Scenario: Package imports resolve after install

- **WHEN** the package is installed (e.g. `pip install -e .`) and `import eval_harness` is run
- **THEN** the `eval_harness.eval`, `eval_harness.providers`, and `eval_harness.scorers`
  modules import successfully without `sys.path` manipulation or a working-directory dependency

#### Scenario: Package exposes its version

- **WHEN** a caller reads `eval_harness.__version__`
- **THEN** it returns the package version string declared in `pyproject.toml`

### Requirement: Build configuration and dependencies

The project SHALL declare its build backend, metadata, and dependencies in a `pyproject.toml`
using the hatchling backend, replacing `requirements.txt`. Runtime use of a real model
(`litellm`) SHALL be an optional extra, and `pytest` SHALL be declared under a `dev` extra.

#### Scenario: Offline install needs no third-party runtime deps

- **WHEN** the package is installed without extras
- **THEN** the mock eval path runs using only the Python standard library, and `litellm`
  is installed only when the `litellm` extra is requested

#### Scenario: Dev extra provides the test toolchain

- **WHEN** a developer installs the `dev` extra
- **THEN** `pytest` is available to run the test suite

### Requirement: Command-line entrypoint

The harness SHALL be runnable as a module via `python -m eval_harness` and via a console
script named `eval-harness`, both invoking the eval `main()`. The default eval set SHALL
resolve to `cases.jsonl` regardless of the current working directory when not overridden.

#### Scenario: Run via module entrypoint

- **WHEN** `python -m eval_harness` is executed
- **THEN** the harness loads the default cases, runs the mock model, prints the report, and
  exits non-zero if any case fails

#### Scenario: Run via console script

- **WHEN** the installed `eval-harness` console script is executed with no arguments
- **THEN** it behaves identically to `python -m eval_harness`
