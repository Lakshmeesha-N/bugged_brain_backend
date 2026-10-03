"""Token-usage tracking for LLM calls.

A ContextVar holds a mutable UsageCounter.  Because the ContextVar stores
a *reference* to the counter object (not a copy of its value), any code that
runs in a copied context — such as LangGraph nodes or asyncio tasks — still
mutates the *same* object and the caller sees the accumulated total.
"""

from contextvars import ContextVar
from typing import Optional

# ---------------------------------------------------------------------------
# Counter
# ---------------------------------------------------------------------------


class UsageCounter:
    """Mutable token counter for one request."""

    __slots__ = ("tokens",)

    def __init__(self) -> None:
        self.tokens: int = 0


# ---------------------------------------------------------------------------
# ContextVar
# ---------------------------------------------------------------------------

_current_counter: ContextVar[Optional[UsageCounter]] = ContextVar(
    "_current_counter", default=None
)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def start_usage_tracking() -> UsageCounter:
    """Create a fresh UsageCounter, install it in the ContextVar, and return it.

    Call this at the start of a request handler *after* the limit check passes.
    The returned counter accumulates every token spent during the request.
    """
    counter = UsageCounter()
    _current_counter.set(counter)
    return counter


def add_tokens(n: int) -> None:
    """Add *n* tokens to the current counter.

    Safe to call from anywhere — including LangGraph nodes running in copied
    contexts — because all copies share the same mutable UsageCounter object.
    Does nothing if no counter has been started for this context.
    """
    counter = _current_counter.get()
    if counter is not None:
        counter.tokens += n
