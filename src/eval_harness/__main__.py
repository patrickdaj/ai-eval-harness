"""Package entrypoint so ``python -m eval_harness`` runs the eval harness.

Equivalent to the ``eval-harness`` console script; both call
:func:`eval_harness.eval.main`.
"""

from .eval import main

if __name__ == "__main__":
    main()
