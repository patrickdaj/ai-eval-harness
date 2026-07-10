## MODIFIED Requirements

### Requirement: Version-control ignore rules

The project SHALL include a `.gitignore` at its root that excludes local virtualenvs,
Python bytecode caches, packaging metadata, test caches, and build output. The `uv.lock`
lockfile SHALL be tracked in version control (not ignored) so that installs are reproducible
across environments.

#### Scenario: Generated artifacts are ignored

- **WHEN** a developer creates `.venv/`, `__pycache__/`, `*.pyc`, `*.egg-info/`,
  `.pytest_cache/`, `build/`, or `dist/` while working in the project
- **THEN** those paths are matched by `.gitignore` and are not shown as untracked by git

#### Scenario: Lockfile stays tracked

- **WHEN** git status is checked after `uv` generates or updates `uv.lock`
- **THEN** `uv.lock` is not matched by `.gitignore` and is tracked in version control

#### Scenario: Source and eval data stay tracked

- **WHEN** git status is checked after adding `.gitignore`
- **THEN** the package sources, `pyproject.toml`, `tests/`, `README.md`, and `cases.jsonl`
  remain tracked (are not ignored)
