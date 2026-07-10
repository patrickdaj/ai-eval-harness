"""Tests for the eval report renderers (prettier-eval-output change).

Covers: metrics/return-value parity between the rich and plain paths, the
plain fallback emitting no ANSI, the rich path emitting styling and omitting the
failures table on an all-pass run, the color-resolution rules (TTY / NO_COLOR /
--no-color), and graceful degradation when rich is not importable.

All offline — no model, no network.
"""

from __future__ import annotations

import io
import re

import pytest

from eval_harness import eval as e

ANSI = re.compile(r"\033\[")


def _rows(all_pass: bool):
    """Two synthetic scored rows. all_pass=True → both exact; else one misses."""
    base = {"input": "kernel: Out of memory", "cost": 0.0, "latency": 0.001, "judge": True}
    return [
        {**base, "expected": "info", "output": "info", "exact": True},
        {
            **base,
            "expected": "critical",
            "output": "info" if not all_pass else "critical",
            "exact": all_pass,
        },
    ]


def _strip(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", s)


# --- 4.1 metrics + return-value parity between rich and plain -----------------

@pytest.mark.parametrize("all_pass", [True, False])
def test_return_value_matches_across_paths(all_pass, capsys, monkeypatch):
    rows = _rows(all_pass)

    plain_ret = e.report(rows, "mock", color=False)
    capsys.readouterr()

    monkeypatch.setattr(e, "_RICH", True)
    rich_ret = e.report(rows, "mock", color=True)
    capsys.readouterr()

    assert plain_ret == rich_ret == all_pass


def test_metrics_identical_across_paths():
    rows = _rows(all_pass=False)  # 1/2 exact, 50%

    import contextlib

    plain_buf = io.StringIO()
    with contextlib.redirect_stdout(plain_buf):
        e._plain_report(rows, "mock")
    plain_text = _strip(plain_buf.getvalue())

    from rich.console import Console

    rich_buf = io.StringIO()
    e._rich_report(rows, "mock", Console(file=rich_buf, force_terminal=True, width=120))
    rich_text = _strip(rich_buf.getvalue())

    # The load-bearing figures must appear in both renderings.
    for token in ["1/2", "50%", "$0.0000", "mock", "critical", "info"]:
        assert token in plain_text, f"{token!r} missing from plain report"
        assert token in rich_text, f"{token!r} missing from rich report"


# --- 4.2 disabled rendering emits no ANSI ------------------------------------

def test_plain_report_has_no_ansi(capsys):
    e.report(_rows(all_pass=False), "mock", color=False)
    out = capsys.readouterr().out
    assert not ANSI.search(out)


def test_color_false_uses_plain_even_when_rich_present(capsys, monkeypatch):
    monkeypatch.setattr(e, "_RICH", True)
    e.report(_rows(all_pass=False), "mock", color=False)
    out = capsys.readouterr().out
    assert not ANSI.search(out)


# --- 4.3 rich path emits styling; failures table omitted on all-pass ---------

def test_rich_report_emits_ansi():
    from rich.console import Console

    buf = io.StringIO()
    e._rich_report(_rows(all_pass=False), "mock",
                   Console(file=buf, force_terminal=True, width=120))
    assert ANSI.search(buf.getvalue())


def test_rich_failures_table_omitted_on_all_pass():
    from rich.console import Console

    buf = io.StringIO()
    e._rich_report(_rows(all_pass=True), "mock",
                   Console(file=buf, force_terminal=True, width=120))
    assert "failures" not in _strip(buf.getvalue())


def test_rich_failures_table_present_on_failure():
    from rich.console import Console

    buf = io.StringIO()
    e._rich_report(_rows(all_pass=False), "mock",
                   Console(file=buf, force_terminal=True, width=120))
    assert "failures" in _strip(buf.getvalue())


# --- full input log line, wrapped (wrap-failure-log-lines change) ------------

# A failing row whose input log line runs well past the old 64-char cutoff, with
# a distinctive marker past char 64 so truncation is detectable.
_LONG_TAIL = "END_OF_LOG_MARKER"
_LONG_INPUT = "kernel: " + "general protection fault " * 4 + _LONG_TAIL


def _long_fail_rows():
    base = {"cost": 0.0, "latency": 0.001, "judge": True}
    return [
        {**base, "input": _LONG_INPUT, "expected": "critical", "output": "info",
         "exact": False},
    ]


def test_plain_report_shows_full_input(capsys, monkeypatch):
    # A wide terminal: the whole line fits, so nothing wraps and nothing is cut.
    monkeypatch.setenv("COLUMNS", "200")
    e._plain_report(_long_fail_rows(), "mock")
    out = capsys.readouterr().out
    assert _LONG_INPUT in out          # full line present, verbatim
    assert _LONG_TAIL in out           # the part past char 64 survived


def test_plain_report_wraps_long_input(capsys, monkeypatch):
    # A narrow terminal forces the line onto continuation rows.
    monkeypatch.setenv("COLUMNS", "60")
    e._plain_report(_long_fail_rows(), "mock")
    out = capsys.readouterr().out

    fail_lines = [ln for ln in out.splitlines() if ln.strip()
                  and "failures (" not in ln
                  and not ln.strip().startswith(("model:", "cases:", "exact",
                                                 "judge", "total", "latency"))]
    # More than one physical line for the single failure → it wrapped.
    assert len(fail_lines) > 1
    # No physical line exceeds the terminal width.
    assert all(len(ln) <= 60 for ln in fail_lines)
    # Continuation lines are indented (no visible text at column 0).
    assert all(ln.startswith(" ") for ln in fail_lines[1:])
    # Nothing dropped: every word of the input appears across the wrapped lines.
    joined = " ".join(ln.strip() for ln in fail_lines)
    for word in _LONG_INPUT.split():
        assert word in joined


def test_rich_report_shows_full_input():
    pytest.importorskip("rich")
    from rich.console import Console

    buf = io.StringIO()
    # Wide console so the input column holds the whole line on one row.
    e._rich_report(_long_fail_rows(), "mock",
                   Console(file=buf, force_terminal=True, width=200))
    text = _strip(buf.getvalue())
    assert _LONG_TAIL in text          # not truncated at 64 chars


def test_rich_report_preserves_bracketed_tokens():
    pytest.importorskip("rich")
    from rich.console import Console

    base = {"cost": 0.0, "latency": 0.001, "judge": True}
    rows = [{**base, "input": "kernel: general protection fault: 0000 [#1] SMP",
             "expected": "critical", "output": "info", "exact": False}]
    buf = io.StringIO()
    e._rich_report(rows, "mock", Console(file=buf, force_terminal=True, width=120))
    text = _strip(buf.getvalue())
    # The bracketed token must survive verbatim, not be eaten as rich markup.
    assert "[#1]" in text


# --- color_enabled resolution (TTY / NO_COLOR / --no-color) -------------------

def test_color_enabled_true_on_tty(monkeypatch):
    monkeypatch.setattr(e, "_RICH", True)
    monkeypatch.setattr(e.sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert e.color_enabled(no_color=False) is True


def test_color_enabled_false_when_not_tty(monkeypatch):
    monkeypatch.setattr(e, "_RICH", True)
    monkeypatch.setattr(e.sys.stdout, "isatty", lambda: False, raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert e.color_enabled(no_color=False) is False


def test_color_enabled_false_with_no_color_env(monkeypatch):
    monkeypatch.setattr(e, "_RICH", True)
    monkeypatch.setattr(e.sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    assert e.color_enabled(no_color=False) is False


def test_color_enabled_false_with_flag(monkeypatch):
    monkeypatch.setattr(e, "_RICH", True)
    monkeypatch.setattr(e.sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert e.color_enabled(no_color=True) is False


def test_color_enabled_false_without_rich(monkeypatch):
    monkeypatch.setattr(e, "_RICH", False)
    monkeypatch.setattr(e.sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert e.color_enabled(no_color=False) is False


# --- 4.4 graceful degradation when rich is absent ----------------------------

def test_report_runs_without_rich(capsys, monkeypatch):
    # Simulate rich not being importable: even if color is requested, report()
    # must fall back to plain text and not raise.
    monkeypatch.setattr(e, "_RICH", False)
    ret = e.report(_rows(all_pass=True), "mock", color=True)
    out = capsys.readouterr().out
    assert ret is True
    assert not ANSI.search(out)
    assert "exact match" in out
