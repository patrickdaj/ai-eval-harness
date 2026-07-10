## Why

The eval report is a flat block of `print()` lines — pass rates, cost, latency, and the
failures list all render in the same undifferentiated monochrome text. When you run the
harness dozens of times a week (its whole point), the number that matters and the failures
that tell you what to fix don't stand out at a glance. A little visual structure — color,
a real table, a clear pass/fail signal — makes the signal pop without changing what's
measured.

## What Changes

- Render the run summary and failures list with [`rich`](https://github.com/Textualize/rich):
  a colored summary panel/table for the metrics and a bordered table for failures with
  `expected` / `got` / `input` columns.
- Make `rich` an **optional dependency with a plain-text fallback**: if `rich` isn't
  installed, `report()` prints today's exact plain output. This preserves the zero-dependency
  offline mock path — `python eval.py` still runs with no deps.
- Color-code the pass-rate metrics: green at 100%, a warning color when a metric degrades;
  highlight the failures table so it draws the eye.
- Let `rich`'s `Console` handle terminal detection (it auto-plainifies when piped/redirected),
  and honor `NO_COLOR` plus a `--no-color` flag to force plain output.
- Keep the report's **exit-code contract and the exact metrics unchanged** — this is purely
  presentation.

## Capabilities

### New Capabilities
- `report-formatting`: rich-rendered eval run summary and failures list (color + tables) with
  an automatic plain-text fallback when `rich` is absent or color is disabled.

### Modified Capabilities
<!-- No existing specs in openspec/specs/; report() currently has no spec. Nothing's requirements change. -->

## Impact

- **Code**: `eval.py` — `report()` split into a rich renderer and the existing plain renderer,
  chosen at runtime by a `rich` import guard and the color setting; `main()` gains a
  `--no-color` flag.
- **Dependencies**: new **optional** `rich` dependency (a `pretty`/`rich` extra in
  `pyproject.toml`, or `requirements.txt` today). The mock path stays dependency-free.
- **Behavior**: identical metrics and exit codes; only stdout appearance changes, and only
  when `rich` is installed and color is enabled.
- **Coordination**: overlaps with the pending `align-project-structure` change, which moves
  `eval.py` into `src/eval_harness/` and introduces `pyproject.toml` extras (the natural home
  for the `rich` extra). Whichever lands second adapts to the other's file/dep layout; no
  logic conflict.
