# tests/test_tools.py
"""
Isolation tests for the three FitFindr tools.

search_listings is pure (no network) and is tested thoroughly.
suggest_outfit and create_fit_card call the Groq LLM; their tests are
skipped automatically when GROQ_API_KEY is not set so the suite still
runs offline. At least one failure-mode test per tool is included.
"""

import os

import pytest

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# LLM tests need a real API key. Skip them gracefully when it's absent.
needs_llm = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipping live LLM tests.",
)


# ── search_listings ────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    # Failure mode: nothing matches → empty list, NOT an exception.
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter_is_case_insensitive():
    # "m" should match listings sized "M", "S/M", "M/L", etc.
    results = search_listings("top", size="m", max_price=None)
    for item in results:
        size_tokens = item["size"].lower().replace("/", " ").split()
        assert "m" in size_tokens or "m" in item["size"].lower()


def test_search_results_sorted_by_relevance():
    results = search_listings("vintage denim jeans", size=None, max_price=None)
    assert len(results) >= 2
    # First result should mention at least one query keyword.
    top_text = (results[0]["title"] + " " + results[0]["description"]).lower()
    assert any(kw in top_text for kw in ("vintage", "denim", "jeans"))


# ── suggest_outfit ─────────────────────────────────────────────────────────

@needs_llm
def test_suggest_outfit_with_wardrobe():
    new_item = search_listings("vintage graphic tee", max_price=50)[0]
    result = suggest_outfit(new_item, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result.strip()) > 0


@needs_llm
def test_suggest_outfit_empty_wardrobe():
    # Failure mode: empty wardrobe → general advice, never crash / empty.
    new_item = search_listings("vintage graphic tee", max_price=50)[0]
    result = suggest_outfit(new_item, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result.strip()) > 0


# ── create_fit_card ────────────────────────────────────────────────────────

def test_create_fit_card_empty_outfit_returns_message():
    # Failure mode: empty outfit → descriptive error string, NOT an exception.
    new_item = {"title": "Cool Jacket", "price": 25.0, "platform": "depop"}
    result = create_fit_card("", new_item)
    assert isinstance(result, str)
    assert len(result.strip()) > 0
    assert "Couldn't generate" in result


def test_create_fit_card_whitespace_outfit_returns_message():
    new_item = {"title": "Cool Jacket", "price": 25.0, "platform": "depop"}
    result = create_fit_card("   \n  ", new_item)
    assert "Couldn't generate" in result


@needs_llm
def test_create_fit_card_happy_path():
    new_item = search_listings("vintage graphic tee", max_price=50)[0]
    result = create_fit_card("Pair it with baggy jeans and chunky sneakers.", new_item)
    assert isinstance(result, str)
    assert len(result.strip()) > 0
