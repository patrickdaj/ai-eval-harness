# eval-harness

A small (~150-line) LLM eval skeleton I use to turn "seems good" into a number:
load cases, run a model, score, and report pass rate / cost / latency. It's
deliberately minimal so it's easy to read end-to-end, verify, and extend for a
specific task rather than being a black box.

## Install

The harness is a small `src/eval_harness/` package managed with
[uv](https://docs.astral.sh/uv/). The mock path needs **no dependencies** — sync
extras only for what you reach for. `uv sync` creates the `.venv` and installs from
the committed `uv.lock`, so installs are reproducible:

```bash
uv sync                              # offline mock path + dev tools (pytest); zero runtime deps
uv sync --extra litellm              # add real models via litellm (also needs a key)
uv sync --extra pretty               # add rich for colored tables (see "Prettier output")
uv sync --no-dev                     # runtime only, skip the pytest dev group
```

`uv sync` installs the `dev` dependency group (pytest) by default. Prefer plain pip?
It still works — `pip install -e .`, `pip install -e ".[litellm]"`, and
`pip install -e ".[pretty]"`. The test toolchain now lives in a PEP 735 dependency
group, so install it with `pip install -e . --group dev` (pip 25.1+).

## Run it

```bash
uv run python -m eval_harness                          # offline: a mock model, no API key, no deps
uv run eval-harness                                    # same thing via the installed console script
uv run python -m eval_harness --model claude-sonnet-5  # a real model via litellm (needs a key + --extra litellm)
uv run python -m eval_harness --no-color               # force plain output (see "Prettier output" below)
```

`uv run` executes inside the synced `.venv`. Once the environment is active you can
also drop the prefix and call `python -m eval_harness` / `eval-harness` directly.

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

**80%, not 100% — on purpose.** The sample task is log-severity classification, and the
mock is a naive keyword classifier that never spots *critical* severity when a log implies
it by mechanism (an OOM kill, a segfault) rather than saying the word. That gap is the point:
a rough baseline is the starting line, and the failures list is what tells you where to go.
The process exits non-zero when any case fails, so the same script doubles as a CI gate.

## Prettier output (optional)

Install [`rich`](https://github.com/Textualize/rich) and the report renders as colored,
aligned tables — green pass rates, a red failures table — instead of plain text:

```bash
uv sync --extra pretty    # optional; the harness runs fine without it
uv run python -m eval_harness
```

`rich` is **optional on purpose**: without it (and on the offline mock path) the harness prints
the same plain text as before, so `python -m eval_harness` still needs zero dependencies. Color
only shows on an interactive terminal — it's automatically suppressed when output is piped or
redirected, when `NO_COLOR` is set, or with `--no-color` — so the CI gate and captured logs
stay clean plain text.

## Tests

```bash
uv sync              # installs the dev group (pytest + rich) by default
uv run pytest
```

Prefer pip? `pip install -e . --group dev` (pip 25.1+) then `pytest`. The `dev` group
pulls in `rich` so the tests exercise the colored report path.

## What's inside

| File | Role |
|------|------|
| `cases.jsonl` | The eval set: `{input, expected}` per line. A toy log-severity classification task — swap in your own golden set. |
| `src/eval_harness/providers.py` | `complete(prompt, model)` → `(text, cost, latency)`. `mock` is offline; anything else routes through litellm, so swapping models is one word. |
| `src/eval_harness/scorers.py` | `exact_match` (free, for labels/IDs/formats) and `llm_judge` (for free-text; falls back to exact offline until you validate it). |
| `src/eval_harness/eval.py` | Load → run → score → report pass rate, cost, and p50/p95 latency, listing every failure. Rich tables when `[pretty]` is installed, else plain text. |
| `tests/` | Offline pytest suite (scorers, providers, eval pipeline, report formatting) with a small `fixtures/cases.jsonl`. |
| `pyproject.toml` | Package metadata, entrypoints, runtime extras (`litellm`, `pretty`), and the `dev` dependency group (PEP 735) for the test toolchain. |
| `uv.lock` | Committed lockfile — `uv sync` installs these pinned versions for reproducible environments. |

## Extending it

The harness is meant to be a stable base you grow, not something you throw away per task:

- Swap `cases.jsonl` for your own golden set and add a task-specific scorer.
- Run two models and compare the cost/latency columns to make a real trade-off.
- Add retrieval scorers (`hit_rate@k` / `MRR`) if you're evaluating RAG.
- Add a runner that drives an agent loop and scores task completion.
- Validate `llm_judge` against a batch of hand labels (measure agreement) before you trust it, then wire the harness into CI on the ships you care about most.
