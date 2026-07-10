"""Scorers: the compressed judgment of "is this output right?"

Two kinds, and knowing when to use which is the skill:

- ``exact_match`` — free, fast, narrow. Use it whenever the answer is a label, an
  ID, a number, a fixed format. Cheap enough to run on everything it can reach.
- ``llm_judge``   — scales human-ish judgment to free-text (is this summary faithful?
  is this answer helpful?) that exact match can't touch. But a judge is itself a
  model — uncalibrated it's just an opinion. Week 7 is where you validate it against
  your own labels; until then, treat its scores as provisional.

For this template's one-word task, exact_match is the right tool and the judge is
overkill — it's included wired-up so it's ready the week your outputs go free-text.
"""


def normalize(s: str) -> str:
    return s.strip().lower().strip(".")


def exact_match(output: str, expected: str) -> bool:
    return normalize(output) == normalize(expected)


def llm_judge(output: str, expected: str, model: str = "mock") -> bool:
    """Ask a model whether `output` is an acceptable answer given `expected`.

    In mock mode there's no model to ask, so it falls back to exact_match — which
    keeps the harness runnable offline. With a real `model`, it grades via the LLM;
    swap in your own rubric prompt as your task demands.
    """
    if model == "mock":
        return exact_match(output, expected)

    from .providers import complete

    prompt = (
        "You are grading a log-severity classifier.\n"
        f"Expected label: {expected}\n"
        f"Model answer:   {output}\n"
        "Is the model answer an acceptable match for the expected label? "
        "Reply with exactly 'yes' or 'no'."
    )
    verdict, _, _ = complete(prompt, model=model)
    return verdict.strip().lower().startswith("y")
