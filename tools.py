"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

# Model used for the two LLM-backed tools.
_MODEL = "llama-3.3-70b-versatile"


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _tokenize(text: str) -> list[str]:
    """Lowercase a string and split it into alphanumeric word tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    keywords = _tokenize(description or "")
    scored: list[tuple[int, dict]] = []

    for item in listings:
        # 1. Price filter (inclusive).
        if max_price is not None and item.get("price", 0) > max_price:
            continue

        # 2. Size filter — case-insensitive, token-based so "M" matches "S/M".
        if size is not None:
            wanted = size.strip().lower()
            item_size = str(item.get("size", "")).lower()
            size_tokens = re.split(r"[\s/]+", item_size)
            if wanted not in size_tokens and wanted not in item_size:
                continue

        # 3. Score by keyword overlap against the item's searchable text.
        haystack_parts = [
            item.get("title", ""),
            item.get("description", ""),
            item.get("category", ""),
            item.get("brand") or "",
            " ".join(item.get("style_tags", [])),
            " ".join(item.get("colors", [])),
        ]
        haystack = _tokenize(" ".join(haystack_parts))
        haystack_set = set(haystack)

        # Distinct keywords matched is the primary score; total occurrences
        # break ties so a more on-topic listing ranks higher.
        distinct = sum(1 for kw in set(keywords) if kw in haystack_set)
        occurrences = sum(haystack.count(kw) for kw in keywords)
        score = distinct * 1000 + occurrences

        # 4. Drop listings with no keyword overlap.
        if distinct == 0:
            continue

        scored.append((score, item))

    # 5. Sort by score, highest first.
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    # Describe the thrifted item for the prompt.
    item_desc = (
        f"{new_item.get('title', 'an item')} "
        f"(category: {new_item.get('category', 'n/a')}, "
        f"colors: {', '.join(new_item.get('colors', [])) or 'n/a'}, "
        f"style: {', '.join(new_item.get('style_tags', [])) or 'n/a'})"
    )

    items = (wardrobe or {}).get("items", [])

    if not items:
        # Empty wardrobe → general styling advice, never crash.
        prompt = (
            f"A shopper is considering buying this thrifted item:\n{item_desc}\n\n"
            "They have not entered any wardrobe items yet. Give friendly, general "
            "styling advice: what kinds of pieces pair well with it, what vibe it "
            "suits, and 1-2 example outfit ideas built around common staples. "
            "Keep it to a short paragraph or two."
        )
    else:
        # Format the wardrobe so the LLM can reference pieces by name.
        wardrobe_lines = []
        for w in items:
            wardrobe_lines.append(
                f"- {w.get('name', 'item')} "
                f"({w.get('category', 'n/a')}; "
                f"{', '.join(w.get('colors', [])) or 'n/a'})"
            )
        wardrobe_text = "\n".join(wardrobe_lines)
        prompt = (
            f"A shopper is considering buying this thrifted item:\n{item_desc}\n\n"
            f"Here is their existing wardrobe:\n{wardrobe_text}\n\n"
            "Suggest 1-2 complete outfits that combine the new item with specific "
            "named pieces from their wardrobe. Reference the wardrobe pieces by "
            "name and explain why each outfit works. Keep it concise and friendly."
        )

    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are FitFindr, a warm, knowledgeable personal stylist.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # 1. Guard against an empty / whitespace-only outfit string.
    if not outfit or not outfit.strip():
        return (
            "Couldn't generate a fit card — no outfit suggestion was provided, "
            "but this item is a great find!"
        )

    title = new_item.get("title", "this thrifted piece")
    price = new_item.get("price")
    price_str = f"${price:g}" if isinstance(price, (int, float)) else "a steal"
    platform = new_item.get("platform", "the resale app")

    prompt = (
        "Write a short, shareable OOTD-style social media caption (2-4 sentences).\n\n"
        f"Item: {title}\n"
        f"Price: {price_str}\n"
        f"Platform: {platform}\n"
        f"Outfit / styling: {outfit}\n\n"
        "Guidelines:\n"
        "- Sound casual and authentic, like a real OOTD post — not a product listing.\n"
        f"- Mention the item name, the price ({price_str}), and the platform "
        f"({platform}) naturally, once each.\n"
        "- Capture the outfit's vibe in specific terms.\n"
        "- A tasteful emoji or two is fine. Return only the caption text."
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You write fun, authentic thrift-haul captions for social media.",
            },
            {"role": "user", "content": prompt},
        ],
        # Higher temperature so repeated calls on the same input vary.
        temperature=1.0,
    )
    return response.choices[0].message.content.strip()
