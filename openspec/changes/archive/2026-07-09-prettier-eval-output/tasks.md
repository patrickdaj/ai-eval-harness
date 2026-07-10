## 1. Dependency & availability guard

- [x] 1.1 Declare `rich` as an optional dependency — add it to `requirements.txt` (documented as not needed for the mock path) now, or a `pretty = ["rich>=13"]` extra in `pyproject.toml` if `align-project-structure` has landed; include `rich` in the dev/test deps
- [x] 1.2 Add a module-level import guard in `eval.py`: `try: import rich … except ImportError: _RICH = False` setting an availability flag

## 2. CLI & color resolution

- [x] 2.1 Add a `--no-color` flag to the argparser in `main()`
- [x] 2.2 Resolve `color = _RICH and sys.stdout.isatty() and not os.environ.get("NO_COLOR") and not args.no_color` and pass it into `report()`

## 3. Renderers

- [x] 3.1 Keep today's plain output as `_plain_report(rows, model)` (essentially unchanged) and have `report()` delegate to it when rich/color is off
- [x] 3.2 Add `_rich_report(rows, model, *, console)` rendering the summary via a rich table/panel with outcome-based coloring (green at 100%, warning color below), preserving today's exact metric values
- [x] 3.3 In `_rich_report`, render failures as a rich table (`expected` / `got` / truncated `input`) styled to draw attention; omit it entirely when there are no failures
- [x] 3.4 Rewire `report()` to select `_rich_report` vs `_plain_report` on `_RICH and color`, constructing the `Console` consistent with the color setting, and keep returning `exact == n` in both paths (exit-code contract unchanged)

## 4. Tests & verification

- [x] 4.1 Test that rich and plain paths report identical metrics/percentages and the same `report()` return value (`True`/`False` on all-pass/any-fail)
- [x] 4.2 Test that disabled rendering (piped / `NO_COLOR` / `--no-color`) produces output with no `\033` escape sequences
- [x] 4.3 Test that the forced-on rich path emits styling and that the failures table is omitted when every case passes
- [x] 4.4 Test that the harness imports and `report()` runs without raising when `rich` is not importable (simulate the missing dependency, e.g. monkeypatch the availability flag / block the import)
- [x] 4.5 Update `README.md`: document `--no-color` and how to enable pretty output (`pip install rich` / the `pretty` extra)
- [x] 4.6 Manually run `python eval.py` with rich installed in a terminal (tables) and `python eval.py | cat` (plain), confirming exit codes still 0 on all-pass / non-zero on failure
