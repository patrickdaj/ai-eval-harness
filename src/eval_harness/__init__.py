"""eval-harness: the ~150-line LLM eval skeleton you reuse for the whole program.

Load cases → run each through a model → score → report pass rate, cost, latency.
No framework. Read every line; you own it. See :mod:`eval_harness.eval` for the
entrypoint (``python -m eval_harness`` or the ``eval-harness`` console script).
"""

__version__ = "0.1.0"
