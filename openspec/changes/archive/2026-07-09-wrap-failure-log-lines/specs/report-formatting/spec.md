## MODIFIED Requirements

### Requirement: Rich failures list

When `rich` is available and color is enabled and at least one case fails, the report SHALL
render the failures as a `rich` table with columns for `expected`, the model output, and the
**full** input log line (not truncated), styled so it draws attention. The input column SHALL
wrap (fold) long lines within the column at the current terminal width so no log content is
lost. When no case fails, no failures table SHALL be shown.

#### Scenario: Failures render as a table

- **WHEN** one or more cases fail exact match with rich rendering active
- **THEN** a failures table is shown with one row per failure containing the expected label,
  the model output, and the full input log line

#### Scenario: Long input wraps within the column

- **WHEN** a failing case's input log line is longer than the input column's width
- **THEN** the full line is shown, wrapped across multiple lines within the input column, with
  no characters dropped

#### Scenario: No failures, no table

- **WHEN** every case passes exact match
- **THEN** no failures table or header is printed

### Requirement: Plain-text fallback

The report SHALL fall back to plain-text output equivalent to the current harness output when
`rich` is not installed. In the plain-text failures list, each failure's input log line SHALL
be printed in full (not truncated); when the line is wider than the terminal it SHALL wrap
onto continuation lines, with continuation lines indented to align under the log text. Terminal
width SHALL be detected at render time with a sane fallback when it cannot be determined.
Importing the harness and running a report SHALL NOT fail when `rich` is absent.

#### Scenario: Runs without rich installed

- **WHEN** the harness runs in an environment where `rich` is not installed
- **THEN** the report prints the plain-text summary and failures without raising, and the run
  completes normally

#### Scenario: Full input is shown

- **WHEN** a case fails and its input log line exceeds 64 characters
- **THEN** the plain-text failures list prints the entire input log line, with no characters
  dropped

#### Scenario: Long input wraps to the terminal width

- **WHEN** a failing case's input log line is wider than the terminal
- **THEN** the line continues on the next line(s), wrapped to the detected terminal width, with
  continuation lines indented to align under the log text
