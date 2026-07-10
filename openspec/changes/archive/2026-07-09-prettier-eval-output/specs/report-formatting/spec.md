## ADDED Requirements

### Requirement: Rich run summary

When `rich` is available and color is enabled, the report SHALL render the run summary
(model, case count, exact-match and judge pass rates, total cost, latency p50/p95) using a
`rich` table/panel, and SHALL color-code the pass-rate metrics by outcome (e.g. green at
100%, a warning color below 100%).

#### Scenario: Summary renders as a colored table

- **WHEN** a run completes with `rich` installed and color enabled
- **THEN** the summary is rendered via `rich` with the pass-rate metrics colored by outcome

#### Scenario: Metrics values are unchanged

- **WHEN** the rich summary is rendered
- **THEN** the model, case count, pass counts, percentages, total cost, and latency figures
  are identical to those the plain report would print

### Requirement: Rich failures list

When `rich` is available and color is enabled and at least one case fails, the report SHALL
render the failures as a `rich` table with columns for `expected`, the model output, and a
truncated input, styled so it draws attention. When no case fails, no failures table SHALL be
shown.

#### Scenario: Failures render as a table

- **WHEN** one or more cases fail exact match with rich rendering active
- **THEN** a failures table is shown with one row per failure containing the expected label,
  the model output, and a truncated input

#### Scenario: No failures, no table

- **WHEN** every case passes exact match
- **THEN** no failures table or header is printed

### Requirement: Plain-text fallback

The report SHALL fall back to plain-text output equivalent to the current harness output when
`rich` is not installed. Importing the harness and running a report SHALL NOT fail when `rich`
is absent.

#### Scenario: Runs without rich installed

- **WHEN** the harness runs in an environment where `rich` is not installed
- **THEN** the report prints the plain-text summary and failures without raising, and the run
  completes normally

### Requirement: Color detection and opt-out

Color/rich rendering SHALL be suppressed in favor of plain text when stdout is not an
interactive terminal (piped or redirected), when the `NO_COLOR` environment variable is set,
or when a `--no-color` flag is passed. With rendering disabled, the output SHALL contain no
ANSI escape sequences.

#### Scenario: Piped output is plain text

- **WHEN** the harness output is piped or redirected to a file
- **THEN** no ANSI escape sequences appear in the output

#### Scenario: NO_COLOR is honored

- **WHEN** `NO_COLOR` is set in the environment
- **THEN** color/rich styling is disabled even if stdout is a terminal

#### Scenario: --no-color forces plain output

- **WHEN** the harness is run with `--no-color`
- **THEN** the report is rendered in plain text regardless of TTY status or `rich` availability

### Requirement: Unchanged exit-code contract

The pretty output SHALL NOT change the run's exit-code behavior: the process SHALL exit 0
when every case passes and non-zero when any case fails, identically to the current harness,
whether rendering uses `rich` or the plain fallback.

#### Scenario: All pass exits zero

- **WHEN** every case passes and the report is rendered (rich or plain)
- **THEN** the process exits with status 0

#### Scenario: Any failure exits non-zero

- **WHEN** at least one case fails and the report is rendered (rich or plain)
- **THEN** the process exits with a non-zero status
