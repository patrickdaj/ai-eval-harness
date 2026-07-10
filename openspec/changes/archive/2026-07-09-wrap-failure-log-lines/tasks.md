## 1. Plain-text report

- [x] 1.1 In `src/eval_harness/eval.py`, add `import shutil` and `import textwrap` (top of file, if not already present)
- [x] 1.2 In `_plain_report`, detect terminal width once via `shutil.get_terminal_size(fallback=(80, 24)).columns`
- [x] 1.3 Build the failure line prefix `    expected {expected:<8} got {output:<8} | ` and compute its length; wrap `r['input']` with `textwrap.wrap` to `max(width - len(prefix), <small floor>)`
- [x] 1.4 Print the prefix + first wrapped segment, then each continuation segment indented by `len(prefix)` spaces; handle the empty-input edge case so at least the prefix prints

## 2. Rich report

- [x] 2.1 In `_rich_report`, change `table.add_row(r["expected"], r["output"], r["input"][:64])` to pass `r["input"]` in full (drop the `[:64]` slice), relying on the existing `overflow="fold"` on the input column

## 3. Tests

- [x] 3.1 In `tests/test_report.py`, update/replace assertions that expect 64-char truncation to instead expect the full input to appear in plain output
- [x] 3.2 Add a plain-report test: a failure whose input exceeds the terminal width wraps onto continuation lines (no characters dropped, continuation lines indented)
- [x] 3.3 Add a rich-report test (skip if `rich` not installed): a long input appears in full in the rendered failures table, not truncated at 64 chars

## 4. Docs & verification

- [x] 4.1 Update the sample failures output in `README.md` so it shows full, wrapped log lines instead of truncated `...` lines
- [x] 4.2 Run `pytest` and confirm the suite passes
- [x] 4.3 Manually run `python -m eval_harness` and `python -m eval_harness --no-color` and confirm failure log lines display in full and wrap at the terminal edge
- [x] 4.4 Run `openspec validate wrap-failure-log-lines` and confirm the change validates
