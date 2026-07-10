"""Unit tests for scorers: normalize, exact_match, and the offline judge fallback.

All offline — the mock judge asks no model, so this needs no key or network.
"""

from __future__ import annotations

import pytest

from eval_harness import scorers


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Critical", "critical"),      # case
        ("  info  ", "info"),           # surrounding whitespace
        ("high.", "high"),              # trailing dot
        ("  Low. ", "low"),             # all three at once
    ],
)
def test_normalize(raw, expected):
    assert scorers.normalize(raw) == expected


def test_exact_match_positive():
    # Case, whitespace, and a trailing dot should all still match.
    assert scorers.exact_match("Critical.", "critical") is True
    assert scorers.exact_match("  INFO ", "info") is True


def test_exact_match_negative():
    assert scorers.exact_match("high", "critical") is False


def test_llm_judge_falls_back_to_exact_match_in_mock():
    # In mock mode the judge invokes no model; it must equal exact_match.
    assert scorers.llm_judge("critical", "critical", model="mock") is True
    assert scorers.llm_judge("high", "critical", model="mock") is False


def test_llm_judge_mock_matches_exact_match_exactly():
    for out, exp in [("Info.", "info"), ("low", "high"), ("  Medium ", "medium")]:
        assert scorers.llm_judge(out, exp, model="mock") == scorers.exact_match(out, exp)
