"""The eval harness — the ~150-line skeleton you reuse for the whole program.

Load cases → run each through a model → score → report pass rate, cost, latency.
No framework. Read every line; you own it.

    python eval.py                       # offline mock model, no key needed
    python eval.py --model claude-sonnet-5   # a real model via litellm (needs a key)

Extend it, don't replace it:
- Week 1: point it at your golden set; add a task-specific scorer.
- Week 2: add hit-rate@k / MRR scorers for RAG retrieval.
- Week 3: add a runner that drives your agent loop and scores completion.
- Week 7: validate the judge against hand labels; wire it into CI.
"""

import argparse
import json
import os
import shutil
import statistics
import sys
import textwrap
from pathlib import Path

from .providers import complete
from .scorers import exact_match, llm_judge

# The eval set lives at the project root (it's data you edit, not shipped code).
# Anchor the default to it so `python -m eval_harness` works from any directory.
DEFAULT_CASES = Path(__file__).resolve().parents[2] / "cases.jsonl"

# rich is an optional dependency: it renders the report as colored tables. If it
# isn't installed the harness falls back to plain text, so the mock path stays
# dependency-free (`python eval.py` runs with nothing but the stdlib).
try:
    import rich  # noqa: F401  (imported for availability check only)

    _RICH = True
except ImportError:
    _RICH = False

SYSTEM = (
    "Classify the severity of the log line into exactly one of: "
    "critical, high, medium, low, info. Answer with the single word only."
)


def load_cases(path: Path):
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def run(cases, model: str, *, use_judge: bool = False):
    rows = []
    for c in cases:
        output, cost, latency = complete(c["input"], model=model, system=SYSTEM)
        # The LLM judge fires a *second* API call per case. For this one-word label
        # task exact_match is the right tool and the judge is overkill (see scorers.py),
        # so it's off by default — enabling it doubles your request count, which is the
        # fast way to trip a low RPM cap. Turn it on with --judge for the Week-7 task of
        # validating the judge against your labels. Off, we reuse exact_match locally
        # (no network) so the column stays populated without spending a request.
        judge = (
            llm_judge(output, c["expected"], model=model)
            if use_judge
            else exact_match(output, c["expected"])
        )
        rows.append(
            {
                "input": c["input"],
                "expected": c["expected"],
                "output": output,
                "cost": cost,
                "latency": latency,
                "exact": exact_match(output, c["expected"]),
                "judge": judge,
            }
        )
    return rows


def _metrics(rows):
    """Reduce scored rows to the summary figures. One source of truth for the
    numbers, shared by both the plain and rich renderers."""
    n = len(rows)
    exact = sum(r["exact"] for r in rows)
    judge = sum(r["judge"] for r in rows)
    lats = sorted(r["latency"] for r in rows)
    p50 = statistics.median(lats)
    p95 = lats[min(len(lats) - 1, int(0.95 * len(lats)))]
    total_cost = sum(r["cost"] for r in rows)
    fails = [r for r in rows if not r["exact"]]
    return n, exact, judge, p50, p95, total_cost, fails


def _plain_report(rows, model: str):
    """The original plain-text report — used when rich is absent or color is off."""
    n, exact, judge, p50, p95, total_cost, fails = _metrics(rows)

    print(f"\n  model:        {model}")
    print(f"  cases:        {n}")
    print(f"  exact match:  {exact}/{n}  ({exact / n:.0%})")
    print(f"  judge pass:   {judge}/{n}  ({judge / n:.0%})")
    print(f"  total cost:   ${total_cost:.4f}")
    print(f"  latency p50:  {p50 * 1000:.0f} ms   p95: {p95 * 1000:.0f} ms")

    if fails:
        print(f"\n  failures ({len(fails)}) — read these, they say what to fix next:")
        cols = shutil.get_terminal_size(fallback=(80, 24)).columns
        for r in fails:
            prefix = f"    expected {r['expected']:<8} got {r['output']:<8} | "
            avail = max(cols - len(prefix), 20)
            # Show the whole log line, wrapping to the terminal width; continuation
            # lines are indented to sit under the log text, not the prefix.
            segments = textwrap.wrap(r["input"], width=avail) or [""]
            print(prefix + segments[0])
            for seg in segments[1:]:
                print(" " * len(prefix) + seg)
    print()


def _rich_report(rows, model: str, console):
    """Colored-table report. `console` is a rich.console.Console. Renders exactly
    the same figures as _plain_report — color carries meaning, not new data."""
    from rich.table import Table
    from rich.text import Text

    n, exact, judge, p50, p95, total_cost, fails = _metrics(rows)

    def rate_style(hits: int) -> str:
        # Green when the metric is perfect, yellow the moment it degrades.
        return "green" if hits == n else "yellow"

    summary = Table(title=f"eval · {model}", title_style="bold", show_header=False,
                    box=None, pad_edge=False)
    summary.add_column("metric", style="bold")
    summary.add_column("value")
    summary.add_row("cases", str(n))
    summary.add_row("exact match",
                    f"[{rate_style(exact)}]{exact}/{n}  ({exact / n:.0%})[/]")
    summary.add_row("judge pass",
                    f"[{rate_style(judge)}]{judge}/{n}  ({judge / n:.0%})[/]")
    summary.add_row("total cost", f"${total_cost:.4f}")
    summary.add_row("latency", f"p50 {p50 * 1000:.0f} ms   p95 {p95 * 1000:.0f} ms")
    console.print(summary)

    if fails:
        table = Table(title=f"failures ({len(fails)}) — read these, they say what to fix next",
                      title_style="bold red", header_style="bold", border_style="red")
        table.add_column("expected", style="red")
        table.add_column("got")
        table.add_column("input", overflow="fold")
        for r in fails:
            # Full input as literal Text so bracketed log tokens (e.g. "[#1]") are
            # not swallowed as rich console markup; the column's overflow="fold"
            # still wraps it to the table width.
            table.add_row(r["expected"], r["output"], Text(r["input"]))
        console.print(table)


def color_enabled(no_color: bool) -> bool:
    """Decide whether to render with rich color. Pretty tables only on an
    interactive terminal, and never when rich is missing, NO_COLOR is set, or
    --no-color is passed — so piped output and the CI gate stay clean plain text.
    """
    return (
        _RICH
        and sys.stdout.isatty()
        and not os.environ.get("NO_COLOR")
        and not no_color
    )


def report(rows, model: str, *, color: bool = False):
    """Print the run report and return True iff every case passed exact match.

    Uses rich (colored tables) when it's installed and `color` is on; otherwise
    the plain-text fallback. Both paths print the same figures and this returns
    the same boolean, so the exit-code contract is identical either way.
    """
    n, exact = len(rows), sum(r["exact"] for r in rows)
    if _RICH and color:
        from rich.console import Console

        _rich_report(rows, model, Console())
    else:
        _plain_report(rows, model)
    return exact == n


def main():
    ap = argparse.ArgumentParser(description="Minimal LLM eval harness.")
    ap.add_argument("--model", default="mock", help="'mock' (offline) or any litellm model id")
    ap.add_argument("--cases", default=DEFAULT_CASES, type=Path)
    ap.add_argument("--no-color", action="store_true",
                    help="force plain-text output (also disabled off a TTY or with NO_COLOR)")
    ap.add_argument("--judge", action="store_true",
                    help="run the LLM judge (a second API call per case). Off by default; "
                         "for this one-word task exact_match suffices and the judge just "
                         "doubles your request count against the rate limit.")
    args = ap.parse_args()

    color = color_enabled(args.no_color)

    cases = load_cases(args.cases)
    rows = run(cases, args.model, use_judge=args.judge)
    all_passed = report(rows, args.model, color=color)
    # Non-zero exit on any failure so this doubles as a CI gate (Week 7).
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
