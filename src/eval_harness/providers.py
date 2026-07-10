"""Model providers for the eval harness.

Two paths, one signature:

- ``mock``  — a deterministic, offline heuristic. No API key, no network, no deps.
              It exists so the *harness* is verifiable end to end before you wire a
              real model (and so CI can run it). It is intentionally imperfect — a
              real baseline is never 100%, and seeing failures is the whole point.
- anything else (e.g. ``claude-sonnet-5``, ``gpt-4o``, ``ollama/llama3``) — routed
              through litellm, so swapping models is a one-word change. This is the
              cross-model interface you'll lean on in the Week-7 gauntlet.

Every provider returns the same tuple: ``(text, cost_usd, latency_s)``.
"""

import time

SEVERITIES = ["critical", "high", "medium", "low", "info"]

# Keyword → severity. Deliberately shallow: it will misjudge lines whose severity
# isn't stated in words (a segfault is critical but says no such word), which is
# exactly the kind of failure your eval should surface.
_RULES = [
    # Only fires on the *word* — so a segfault or an OOM kill (critical by mechanism,
    # but never spelled "critical") slips through to "info". That gap is the lesson.
    (("critical", "fatal", "emergency"), "critical"),
    (("failed password", "authentication failure", "denied", "selinux is preventing",
      "invalid user"), "high"),
    (("warn", "backoff", "retrying", "exceeded"), "medium"),
    (("notice", "deprecated"), "low"),
]


def _mock(prompt: str) -> str:
    text = prompt.lower()
    for needles, severity in _RULES:
        if any(n in text for n in needles):
            return severity
    return "info"


# Models that rejected `temperature` once. Newer models (Claude Sonnet 5 / Opus 4.x)
# 400 on it, and litellm's model map is too stale to drop it for us. We learn per-model
# on the first 400 and then never send it again — otherwise every case burns a wasted
# 400 request before the real call, doubling load on an already rate-limited key.
_NO_TEMPERATURE: set[str] = set()


def _retry_after(exc) -> float | None:
    """Seconds to wait per Anthropic's `retry-after` header, or None if absent.

    litellm surfaces response headers on `litellm_response_headers`; the wrapped
    httpx response (`exc.response`) is often None on the Anthropic path, so check
    both. Honoring this waits out the *actual* rate-limit window instead of a blind
    exponential guess that keeps landing inside it."""
    for headers in (
        getattr(exc, "litellm_response_headers", None),
        getattr(getattr(exc, "response", None), "headers", None),
    ):
        if headers and (ra := headers.get("retry-after")) is not None:
            try:
                return float(ra)
            except (TypeError, ValueError):
                pass
    return None


def _litellm(prompt: str, model: str, system: str | None):
    # Lazy import so the mock path needs zero dependencies.
    import litellm
    from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_exponential

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    def _wait(retry_state):
        # Prefer the server's retry-after; fall back to exponential backoff when
        # it's missing. Cap at 60s so one wait can span a full RPM window.
        return _retry_after(retry_state.outcome.exception()) or wait_exponential(
            multiplier=2, max=60
        )(retry_state)

    # Keep retrying rate limits for up to 3 minutes of wall-clock, so the run can
    # outlast a real (possibly multi-window) throttle rather than giving up after a
    # fixed count. A low tier is still the true fix (Anthropic Console → Limits) —
    # this just keeps the harness alive while you raise it.
    @retry(
        retry=retry_if_exception_type(litellm.RateLimitError),
        wait=_wait,
        stop=stop_after_delay(180),
        reraise=True,
    )
    def _call(call_kwargs):
        return litellm.completion(**call_kwargs)

    kwargs = {"model": model, "messages": messages}
    if model not in _NO_TEMPERATURE:
        kwargs["temperature"] = 0  # deterministic evals, when the model accepts it
    try:
        resp = _call(kwargs)
    except litellm.BadRequestError as e:
        if "temperature" not in str(e).lower():
            raise
        _NO_TEMPERATURE.add(model)  # remember, so later cases skip the wasted 400
        kwargs.pop("temperature", None)
        resp = _call(kwargs)
    text = resp.choices[0].message.content.strip()
    try:
        cost = litellm.completion_cost(completion_response=resp)
    except Exception:
        cost = 0.0
    return text, float(cost or 0.0)


def complete(prompt: str, model: str = "mock", system: str | None = None):
    """Run one completion. Returns (text, cost_usd, latency_s)."""
    t0 = time.perf_counter()
    if model == "mock":
        text, cost = _mock(prompt), 0.0
    else:
        text, cost = _litellm(prompt, model, system)
    return text, cost, time.perf_counter() - t0
