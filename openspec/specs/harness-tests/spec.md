# harness-tests Specification

## Purpose

Define the offline pytest suite that exercises the eval harness end to end, covering the
scorers, providers, and eval pipeline so behavior is verifiable without network access.

## Requirements

### Requirement: Offline-runnable test suite

The project SHALL include a `tests/` directory with a pytest suite that runs fully offline
(mock provider, no network, no API key) and that is discoverable by running `pytest` from
the project root.

#### Scenario: Suite runs green offline

- **WHEN** `pytest` is run from the project root with no API key and no `litellm` installed
- **THEN** all tests are collected and pass without network access

### Requirement: Scorer coverage

The suite SHALL verify the scorer behavior: `normalize` case/whitespace/trailing-dot
handling, `exact_match` positive and negative cases, and `llm_judge` falling back to
`exact_match` in mock mode.

#### Scenario: Exact match normalizes before comparing

- **WHEN** `exact_match("Critical.", "critical")` is evaluated
- **THEN** it returns `True`

#### Scenario: Judge falls back to exact match offline

- **WHEN** `llm_judge(output, expected, model="mock")` is called
- **THEN** its result equals `exact_match(output, expected)` and no model is invoked

### Requirement: Provider coverage

The suite SHALL verify the mock provider's contract: `complete` returns a
`(text, cost, latency)` tuple, the mock cost is `0.0`, and the keyword heuristic maps
representative log lines to their expected severities (including the deliberate miss where a
mechanism-implied critical line falls through to `info`).

#### Scenario: Mock returns the tuple contract

- **WHEN** `complete("some log line", model="mock")` is called
- **THEN** it returns a 3-tuple of `(str, float, float)` with cost `0.0` and non-negative latency

#### Scenario: Mechanism-implied critical is missed by design

- **WHEN** the mock classifies a log line that is critical by mechanism but never says the word
  (e.g. an OOM kill or a segfault)
- **THEN** it returns `info`, documenting the intended baseline gap

### Requirement: Eval pipeline coverage

The suite SHALL verify the end-to-end pipeline on a small committed fixture: `load_cases`
parses JSONL, `run` produces one scored row per case, and `report` returns `True` only when
every case passes exact match.

#### Scenario: Report signals all-pass for exit code

- **WHEN** `report` is given rows where every row's `exact` is `True`
- **THEN** it returns `True` (which the entrypoint maps to exit code 0)

#### Scenario: Report signals failure when a case misses

- **WHEN** `report` is given rows where at least one row's `exact` is `False`
- **THEN** it returns `False` (which the entrypoint maps to a non-zero exit code)
