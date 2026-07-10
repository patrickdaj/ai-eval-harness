# repo-hygiene Specification

## Purpose

Define version-control hygiene for the project so generated artifacts stay out of the
repository while source and eval data remain tracked.

## Requirements

### Requirement: Version-control ignore rules

The project SHALL include a `.gitignore` at its root that excludes local virtualenvs,
Python bytecode caches, packaging metadata, test caches, and build output, matching the
ignore rules used by the sibling `agent-activity-mcp-server` project.

#### Scenario: Generated artifacts are ignored

- **WHEN** a developer creates `.venv/`, `__pycache__/`, `*.pyc`, `*.egg-info/`,
  `.pytest_cache/`, `build/`, or `dist/` while working in the project
- **THEN** those paths are matched by `.gitignore` and are not shown as untracked by git

#### Scenario: Source and eval data stay tracked

- **WHEN** git status is checked after adding `.gitignore`
- **THEN** the package sources, `pyproject.toml`, `tests/`, `README.md`, and `cases.jsonl`
  remain tracked (are not ignored)
