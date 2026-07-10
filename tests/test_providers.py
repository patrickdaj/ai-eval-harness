"""Unit tests for the mock provider: the tuple contract, zero cost, the keyword
heuristic, and the deliberate mechanism-implied-critical miss.

All offline — the mock path imports nothing beyond the stdlib.
"""

from __future__ import annotations

import pytest

from eval_harness import providers


def test_complete_returns_tuple_contract():
    result = providers.complete("some log line", model="mock")
    assert isinstance(result, tuple) and len(result) == 3
    text, cost, latency = result
    assert isinstance(text, str)
    assert isinstance(cost, float) and cost == 0.0
    assert isinstance(latency, float) and latency >= 0.0


@pytest.mark.parametrize(
    "line, severity",
    [
        ("CRITICAL: disk failure imminent", "critical"),
        ("kernel panic - not syncing: FATAL exception", "critical"),
        ("sshd: Failed password for root", "high"),
        ("SELinux is preventing access", "high"),
        ("app WARN retry backoff", "medium"),
        ("api rate limit exceeded", "medium"),
        ("NOTICE config reloaded", "low"),
        ("this endpoint is deprecated", "low"),
        ("just a normal heartbeat line", "info"),
    ],
)
def test_mock_keyword_heuristic(line, severity):
    text, _, _ = providers.complete(line, model="mock")
    assert text == severity


@pytest.mark.parametrize(
    "line",
    [
        "kernel: Out of memory: Killed process 8123 (java)",   # OOM kill
        "kernel: general protection fault: 0000 [#1] SMP",      # segfault
    ],
)
def test_mechanism_implied_critical_is_missed_by_design(line):
    # Critical by mechanism but never says the word — the mock falls through to
    # "info". This is the intended baseline gap the eval is meant to surface.
    text, _, _ = providers.complete(line, model="mock")
    assert text == "info"
