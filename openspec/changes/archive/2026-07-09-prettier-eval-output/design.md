## Context

`report()` in `eval.py` prints the run summary and failures with a series of bare `print()`
calls in one monochrome block. The harness is run constantly and doubles as a CI gate, so two
constraints bound any change: (1) the mock path stays runnable offline with zero dependencies
(the README's explicit promise), and (2) the exit code and captured/piped output stay stable
for CI. The user wants `rich` for the pretty rendering; the design reconciles that with the
zero-dependency promise by making `rich` **optional with a plain-text fallback**.

## Goals / Non-Goals

**Goals:**
- Render the summary and failures with `rich` (colored table/panel) so the pass rate and the
  failures list are scannable at a glance.
- Keep `python eval.py` working with **no dependencies**: if `rich` isn't importable, print
  today's exact plain output.
- Suppress styling on non-terminals, under `NO_COLOR`, and with `--no-color`.
- Keep metrics and exit codes byte-for-byte equivalent to today's numbers.

**Non-Goals:**
- Making `rich` a required/core dependency (rejected: breaks the zero-dep offline promise).
- Changing what's measured, the scoring, or the eval loop.
- Progress bars, live/TUI rendering, or a JSON output mode (possible later changes).

## Decisions

**`rich` is optional, guarded by an import.** A module-level
`try: import rich … except ImportError: _RICH = False` sets availability once. `report()`
picks the renderer from `_RICH and color`. Rationale: the defining constraint of this scaffold
is the zero-dependency mock path — a hard `rich` dep would break `python eval.py` offline and
contradict the README. Chosen per the user's decision (optional + fallback) over a hard core
dependency.

**Two renderers behind one `report()` signature.** Keep the public `report(rows, model, *,
color=...) -> bool` contract; split the body into `_rich_report(...)` and `_plain_report(...)`
(the latter is today's code, essentially unchanged). `report()` returns `exact == n` in both
paths so the exit-code contract is identical. Rationale: a single decision point, both paths
provably return the same boolean, and `_plain_report` stays trivially reviewable.

**Let `rich.Console` own terminal detection; layer explicit opt-outs on top.** Compute
`color = _RICH and sys.stdout.isatty() and not os.environ.get("NO_COLOR") and not
args.no_color`, and additionally construct the `Console` with `no_color`/`force_terminal`
consistent with that. `rich` already auto-plainifies when it detects a non-tty, but we resolve
the boolean ourselves so it's deterministic and unit-testable (pass `color=False` directly).
Alternative (rely solely on rich's auto-detection) rejected — harder to test and to force off.

**Where the dependency is declared.** Today: add `rich` to `requirements.txt` as an optional
pretty extra (documented as not needed for the mock path). After `align-project-structure`
lands: a `pretty = ["rich>=13"]` (or `rich`) optional-dependency extra in `pyproject.toml`,
alongside `litellm` and `dev`. The `dev` extra SHOULD include `rich` so tests can exercise the
rich path. Whichever change lands second wires the extra into the final dep layout.

**Restrained, meaningful color.** Green = a perfect metric (100% / 0 failures), a warning color
(yellow) = degraded, red = the failures table / `expected` column so the eye lands on what to
fix. Color carries meaning, not decoration.

## Risks / Trade-offs

- **Two code paths can drift** → Keep `_plain_report` as the source of truth for the numbers;
  a test asserts rich and plain report the same metrics and the same `report()` return value.
- **ANSI leaking into CI logs / files** → Resolve `color` from `isatty()` + `NO_COLOR` +
  `--no-color`, and construct `Console` accordingly; test that disabled output contains no
  `\033`.
- **`rich` present but color disabled** → Treat `_RICH and color` as the gate; `--no-color`
  and non-tty both force the plain path even when `rich` is installed.
- **Fallback silently hides prettiness when `rich` is missing** → Acceptable and intended;
  document in the README that installing the `pretty` extra (or `rich`) enables the tables.
- **Merge overlap with `align-project-structure`** → Both touch `eval.py`/deps; keep the split
  inside `report()`/`main()`. Whichever lands second rebases the renderer location and moves
  the `rich` extra into `pyproject.toml`.

## Migration Plan

1. Add the `rich` import guard (`_RICH`) and a `--no-color` flag; resolve the `color` boolean
   in `main()` and pass it to `report()`.
2. Split `report()` into `_plain_report` (today's output) and `_rich_report` (Console + tables);
   `report()` selects on `_RICH and color` and returns `exact == n` in both.
3. Declare `rich` as an optional dependency (requirements.txt now / `pretty` extra post-restructure)
   and add it to the dev/test deps.
4. Add tests: metrics + exit-code identical across paths; no ANSI when disabled; rich path emits
   styling when forced on; failures table omitted on all-pass; import/run succeeds with `rich` absent.
5. Update the README: `--no-color`, and how to enable pretty output (`pip install rich` / the extra).

Rollback: revert; `report()` returns to the plain `print()` path with no behavioral change.

## Open Questions

- None blocking. A machine-readable `--json` output mode is a natural follow-up but is out of
  scope here.
