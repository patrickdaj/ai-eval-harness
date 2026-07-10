## Context

The eval harness renders a run report through two paths in `src/eval_harness/eval.py`:
`_plain_report` (stdlib only) and `_rich_report` (uses `rich.table.Table`). Both build a
failures list and both pre-truncate the input log line with `r['input'][:64]` — plain text at
line ~108, rich at line ~143. The truncation is silent (no ellipsis) and drops the part of the
log that most often explains the failure.

The rich failures column is already declared with `overflow="fold"`, so rich already knows how
to wrap; the only thing defeating it is the `[:64]` slice applied before the value reaches the
table. The plain path has no width awareness at all.

## Goals / Non-Goals

**Goals:**
- Show the entire input log line for every failure in both report paths.
- Wrap long lines to the terminal width rather than truncating or letting them overflow raggedly.
- Keep the plain path dependency-free (stdlib only) and keep the rich path delegating width to `Console`.
- Preserve all metrics and the exit-code contract unchanged.

**Non-Goals:**
- Changing the summary section, colors, column set, or the failures header text.
- Adding truncation with an ellipsis (the explicit request is to show the whole line).
- Making wrapping configurable via flags/env — a single sensible default is enough.

## Decisions

- **Rich path: delete the `[:64]` slice.** Pass `r["input"]` in full to `table.add_row(...)`.
  The `overflow="fold"` column already wraps to the column width the `Console` computes from
  the terminal. No new code, no width math. Alternative (manual pre-wrapping) rejected: it
  fights rich's own layout and would double-wrap.

- **Plain path: wrap with `textwrap` against the detected terminal width.** Compute width once
  via `shutil.get_terminal_size(fallback=(80, 24)).columns` (returns 80 when not a TTY, which is
  the right default for piped output). Build the fixed prefix `    expected {e:<8} got {o:<8} | `,
  measure its visible length, and wrap the input with `textwrap.wrap(input, width=cols - len(prefix))`
  (guarding against a tiny/zero available width by flooring to a small minimum). Print the first
  wrapped segment after the prefix and each continuation segment indented by `len(prefix)` spaces
  so the log text stays left-aligned in a column.
  - Alternative — `textwrap.fill` with `subsequent_indent`: cleaner, but `fill` re-wraps the
    whole block including the prefix as if it were part of the text; using `initial_indent`/
    `subsequent_indent` with a prefix that contains dynamic-width fields is fiddlier than wrapping
    just the input and printing the prefix ourselves. Chosen approach keeps the prefix formatting
    identical to today.
  - Alternative — no wrapping, just remove the slice and let the terminal soft-wrap: rejected
    because terminal soft-wrap breaks mid-word at the exact edge and loses the aligned indent,
    making multi-failure output hard to scan.

- **Width detection lives in the plain path only.** The rich `Console` already does this
  internally; duplicating it would risk disagreeing with rich's own measurement.

## Risks / Trade-offs

- [Very long single-token lines (no spaces) may still exceed width] → `textwrap` with
  `break_long_words=True` (the default) breaks them, so nothing is lost; acceptable.
- [Non-TTY width falls back to 80] → matches conventional CLI behavior and keeps piped/CI output
  stable and diff-friendly; acceptable and arguably desirable.
- [Existing tests assert the 64-char truncation] → those assertions are now wrong by design and
  will be updated in the tasks; this is expected, not a regression.
- [README sample output shows `...` truncated lines] → update the sample so docs match behavior.

## Open Questions

- None. The change is localized to two functions with a clear, testable contract.
