"""Tests for src/llm/usage.py — UsageCounter and ContextVar behaviour."""

import asyncio
import pytest
from contextvars import copy_context

from src.llm.usage import UsageCounter, add_tokens, start_usage_tracking, _current_counter


# ---------------------------------------------------------------------------
# Basic counter tests
# ---------------------------------------------------------------------------

def test_add_tokens_accumulates():
    counter = start_usage_tracking()
    add_tokens(100)
    add_tokens(250)
    assert counter.tokens == 350


def test_add_tokens_no_counter_does_nothing():
    """When no counter is active, add_tokens must be a safe no-op."""
    # Reset ContextVar to have no counter
    _current_counter.set(None)
    add_tokens(999)  # should not raise


def test_start_usage_tracking_returns_fresh_counter():
    counter1 = start_usage_tracking()
    add_tokens(50)
    counter2 = start_usage_tracking()  # new counter — resets for this context
    add_tokens(10)
    assert counter1.tokens == 50
    assert counter2.tokens == 10


# ---------------------------------------------------------------------------
# asyncio task: tokens from a spawned task reach the caller's counter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tokens_from_async_task_reach_caller():
    """asyncio tasks inherit the context; because UsageCounter is mutable,
    mutations inside the task are visible to the caller."""
    counter = start_usage_tracking()

    async def worker():
        add_tokens(300)

    await asyncio.gather(worker())
    assert counter.tokens == 300


# ---------------------------------------------------------------------------
# copied context: tokens from a copied context still reach caller's counter
# ---------------------------------------------------------------------------

def test_tokens_from_copied_context_reach_caller():
    """copy_context() copies the ContextVar *reference* (not the object),
    so mutations in the copy still reach the original counter."""
    counter = start_usage_tracking()

    def work_in_copy():
        add_tokens(77)

    ctx = copy_context()
    ctx.run(work_in_copy)
    assert counter.tokens == 77
