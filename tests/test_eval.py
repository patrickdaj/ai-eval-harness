"""Unit tests for the eval pipeline: load_cases, run, and report's all-pass /
any-fail return value (which the entrypoint maps to the process exit code).

Uses the committed fixture and the offline mock model — no key, no network.
"""

from __future__ import annotations

from pathlib import Path

from eval_harness import eval as e

FIXTURE = Path(__file__).parent / "fixtures" / "cases.jsonl"


def test_load_cases_parses_jsonl():
    cases = e.load_cases(FIXTURE)
    assert len(cases) == 5
    assert all("input" in c and "expected" in c for c in cases)
    assert cases[0]["expected"] == "critical"


def test_run_yields_one_scored_row_per_case():
    cases = e.load_cases(FIXTURE)
    rows = e.run(cases, "mock")
    assert len(rows) == len(cases)
    for row in rows:
        assert set(row) >= {"input", "expected", "output", "cost", "latency", "exact", "judge"}
        assert isinstance(row["exact"], bool)


def test_run_on_fixture_has_the_known_miss():
    # 4 of 5 fixture cases pass under the mock; the OOM line is the known miss.
    rows = e.run(e.load_cases(FIXTURE), "mock")
    assert sum(r["exact"] for r in rows) == 4
    miss = [r for r in rows if not r["exact"]]
    assert len(miss) == 1 and "Out of memory" in miss[0]["input"]


def test_report_returns_false_when_a_case_misses(capsys):
    rows = e.run(e.load_cases(FIXTURE), "mock")
    result = e.report(rows, "mock")
    capsys.readouterr()
    assert result is False


def test_report_returns_true_on_all_pass(capsys):
    rows = [
        {"input": "x", "expected": "info", "output": "info",
         "cost": 0.0, "latency": 0.0, "exact": True, "judge": True},
        {"input": "y", "expected": "low", "output": "low",
         "cost": 0.0, "latency": 0.0, "exact": True, "judge": True},
    ]
    result = e.report(rows, "mock")
    capsys.readouterr()
    assert result is True
