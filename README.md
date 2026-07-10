# eval-template — the harness you reuse for the whole program

This is the ~150-line eval skeleton from [Week 0, Day 5](../../docs/program/00-arm-yourself/README.md).
It's a **reference scaffold**, not a substitute for building your own: read every line,
understand it, then extend it. In the program you keep *this same harness* alive for eight
weeks — it's the thing that turns "seems good" into a number on every ship.

## Install

The harness is a small `src/eval_harness/` package. The mock path needs **no
dependencies** — install extras only for what you reach for:

```bash
pip install -e .                # offline mock path, zero third-party deps
pip install -e ".[litellm]"     # add real models via litellm (also needs a key)
pip install -e ".[pretty]"      # add rich for colored tables (see "Prettier output")
pip install -e ".[dev]"         # add the test toolchain (pytest + rich)
```

## Run it

```bash
python -m eval_harness                          # offline: a mock model, no API key, no deps
eval-harness                                    # same thing via the installed console script
python -m eval_harness --model claude-sonnet-5  # a real model via litellm (needs a key + the [litellm] extra)
python -m eval_harness --no-color               # force plain output (see "Prettier output" below)
```

Both entrypoints resolve `cases.jsonl` at the project root, so they work from any
directory. The default run is fully offline so the *harness* is verifiable before you
wire a real model — and so it can run in CI. You'll see something like:

```
  exact match:  8/10  (80%)
  judge pass:   8/10  (80%)
  total cost:   $0.0000
  latency p50:  0 ms   p95: 0 ms

  failures (2) — read these, they say what to fix next:
    expected critical got info     | kernel: Out of memory: Killed
                                     process 8123 (java)
    expected critical got info     | kernel: general protection fault:
                                     0000 [#1] SMP -- process nginx
                                     segfaulted
```

The failure log lines are shown **in full** — nothing is truncated. When a line is
wider than your terminal it wraps onto the next line(s), indented under the log text,
so the detail that explains the failure is always on screen.

**80%, not 100% — on purpose.** The mock is a naive keyword classifier that never spots
*critical* severity when a log implies it by mechanism (an OOM kill, a segfault) rather than
saying the word. That gap is the lesson: an ugly baseline is the starting point, and the
failures list is what tells you where to go. The process exits non-zero when any case fails,
so the same script doubles as a CI gate later.

## Prettier output (optional)

Install [`rich`](https://github.com/Textualize/rich) and the report renders as colored,
aligned tables — green pass rates, a red failures table — instead of plain text:

```bash
pip install -e ".[pretty]"    # optional; the harness runs fine without it
python -m eval_harness
```

`rich` is **optional on purpose**: without it (and on the offline mock path) the harness prints
the same plain text as before, so `python -m eval_harness` still needs zero dependencies. Color
only shows on an interactive terminal — it's automatically suppressed when output is piped or
redirected, when `NO_COLOR` is set, or with `--no-color` — so the CI gate and captured logs
stay clean plain text.

## Tests

```bash
pip install -e ".[dev]"    # pytest + rich (so tests exercise the colored path)
pytest
```

## What's inside

| File | Role |
|------|------|
| `cases.jsonl` | The eval set: `{input, expected}` per line. On-theme toy task — log-severity classification. Replace with your Week-1 golden set. |
| `src/eval_harness/providers.py` | `complete(prompt, model)` → `(text, cost, latency)`. `mock` is offline; anything else routes through litellm, so swapping models is one word. |
| `src/eval_harness/scorers.py` | `exact_match` (free, for labels/IDs/formats) and `llm_judge` (for free-text; falls back to exact offline until you validate it in Week 7). |
| `src/eval_harness/eval.py` | Load → run → score → report pass rate, cost, and p50/p95 latency, listing every failure. Rich tables when `[pretty]` is installed, else plain text. |
| `tests/` | Offline pytest suite (scorers, providers, eval pipeline, report formatting) with a small `fixtures/cases.jsonl`. |
| `pyproject.toml` | Package metadata, entrypoints, and optional extras (`litellm`, `pretty`, `dev`). |

## How you extend it (don't replace it)

- **Week 1** — swap `cases.jsonl` for your 30-case golden set; add a task-specific scorer; run two models and compare the cost/latency columns.
- **Week 2** — add `hit_rate@k` / `MRR` scorers for RAG retrieval.
- **Week 3** — add a runner that drives your agent loop and scores task completion.
- **Week 7** — validate `llm_judge` against 30 hand labels (measure agreement), then wire this into CI on your most-used ships.

The rule the whole program runs on applies here first: **AI can draft this; you review every
line and own it.**
