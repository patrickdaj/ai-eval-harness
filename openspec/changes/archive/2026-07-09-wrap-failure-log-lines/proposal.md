## Why

The failures list is the whole point of the report — it's what tells you what to fix next — but every failure row truncates the input log line to 64 characters (`r['input'][:64]`), silently and with no ellipsis. The critical detail that explains the failure (an OOM message, a segfault trace, the mechanism a naive classifier missed) frequently lives past character 64 and is discarded before it ever reaches the screen. Users should see the whole log line, wrapped across terminal lines when it's too wide to fit.

## What Changes

- Stop truncating the failure input log line to 64 characters in both the plain-text and rich report paths.
- Plain-text report: print the full input, wrapping it to the terminal width so long lines continue on the next line(s) instead of being cut or overflowing raggedly. Continuation lines are indented to align under the log text, keeping the `expected … got … |` prefix readable.
- Rich report: pass the full input to the failures table; the input column already uses `overflow="fold"`, so rich wraps it within the column at the current terminal width once the pre-truncation is removed.
- Terminal width is detected via `shutil.get_terminal_size()` (with a sane fallback) for the plain path; the rich path continues to rely on the `Console`'s own width detection.

## Capabilities

### New Capabilities
<!-- None — this refines existing report-formatting behavior. -->

### Modified Capabilities
- `report-formatting`: The "Rich failures list" and "Plain-text fallback" requirements change from rendering a **truncated** input to rendering the **full** input, wrapped to the terminal width.

## Impact

- Code: `src/eval_harness/eval.py` — `_plain_report` (line ~108) and `_rich_report` (line ~143).
- Tests: `tests/test_report.py` — assertions that currently expect 64-char truncation must be updated to expect the full line and wrapping behavior.
- Docs: `README.md` — the sample failures output shows truncated lines with `...`; update to reflect wrapped full lines.
- No dependency, API, or exit-code changes. Metrics and the pass/fail contract are untouched.
