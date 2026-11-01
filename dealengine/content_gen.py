"""Content Generation Engine — Local AI Integration.

This module generates deal descriptions using template-based generation
as the primary method, with Ollama as an optional enhancement when
available. The template approach ensures every deal has a unique,
human-sounding description without requiring a running LLM server.
"""
from __future__ import annotations

import os
import random
import re
import httpx
from typing import Dict, Any

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Template-based description generation
_ROUTE_TEMPLATES = [
    "Found a {label} fare from {origin} to {destination}: just {price} {currency} — {savings:.0f}% below median!",
    "Great {label} deal: fly {origin}→{destination} for {price} {currency}. Beat the median by {savings:.0f}%.",
    "{origin} to {destination} for {price} {currency} — a {label} fare that's {savings:.0f}% cheaper than usual.",
    "Score: {origin}→{destination} at {price} {currency}. This {label} fare beats typical prices by {savings:.0f}%.",
    "{label} alert: {origin}→{destination} round-trip for {price} {currency}, {savings:.0f}% under the norm.",
]

_PACKAGE_TEMPLATES = [
    "All-inclusive {label} escape: {destination} resort for {price} {currency} — {nights}-night stay, {savings:.0f}% off median.",
    "Package deal: {destination} all-inclusive resort, {nights} nights, {price} {currency}. A {label} price at {savings:.0f}% below normal.",
    "Unbeatable {label} package: {destination} resort, {board_type} board, {nights} nights for {price} {currency} — {savings:.0f}% discount.",
    "All-inclusive {destination} resort for {price} {currency} — {nights} nights, {board_type} board. This {label} package saves {savings:.0f}% vs median.",
    "{label} all-inclusive deal: {destination}, {nights}-night {board_type} package at {price} {currency} — {savings:.0f}% below average.",
]


def _get_label_text(label: str) -> str:
    """Convert internal label to display-friendly text."""
    label = label.lower()
    if "flash" in label:
        return "flash"
    elif "mistake" in label:
        return "glitch"
    return "price error"


def _template_fill(tmpl: str, **kwargs) -> str:
    """Fill a template string with keyword arguments."""
    try:
        return tmpl.format(**kwargs)
    except KeyError:
        return "Great travel deal found!"


def generate_deal_description(deal_data: Dict[str, Any]) -> str:
    """Generate a description using Ollama (primary) or templates (fallback).

    Tries Ollama first; falls back to template generation if unavailable.
    """
    # Try Ollama first
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": (
                        f"Write a punchy 1-sentence marketing description for this travel deal:\n"
                        f"From: {deal_data.get('origin', 'N/A')} to {deal_data.get('destination', 'N/A')}\n"
                        f"Price: {deal_data.get('price', 'N/A')} {deal_data.get('currency', 'USD')}\n"
                        f"Details: {deal_data.get('label', '')}, {deal_data.get('reasons', [])}\n"
                        f"Output ONLY the description. No quotes, no extra text."
                    ),
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.9}
                }
            )
            response.raise_for_status()
            response_text = response.json().get("response", "").strip()
            if response_text and len(response_text) > 20:
                return response_text
    except Exception as e:
        print(f"Ollama unavailable, using templates: {e}")

    # Fallback to templates
    origin = deal_data.get("origin") or deal_data.get("resort", "Unknown")
    destination = deal_data.get("destination", "Unknown")
    price = deal_data.get("price", 0)
    currency = deal_data.get("currency", "USD")
    label = deal_data.get("label", "flash")
    conf = deal_data.get("confidence", 1)
    reasons = deal_data.get("reasons", [])
    is_package = deal_data.get("is_all_inclusive", False)

    savings_pct = conf * 100
    nights = deal_data.get("nights", "")
    board_type = deal_data.get("board_type", "")

    label_text = _get_label_text(label)

    templates = _PACKAGE_TEMPLATES if is_package else _ROUTE_TEMPLATES
    tmpl = random.choice(templates)

    kwargs = {
        "origin": origin,
        "destination": destination,
        "price": price,
        "currency": currency,
        "label": label_text,
        "savings": savings_pct,
    }
    if nights:
        kwargs["nights"] = nights
    if board_type:
        kwargs["board_type"] = board_type

    description = _template_fill(tmpl, **kwargs)

    # Add reason details if available
    if reasons:
        detail = reasons[0] if isinstance(reasons, list) else str(reasons)
        detail = re.sub(r'\[.*?\]', '', detail)
        if len(detail) < 80:
            description = f"{description} ({detail})"

    return description


async def generate_with_ollama(deal_data: Dict[str, Any]) -> str:
    """Generate a description using Ollama if available.

    Falls back to template generation if Ollama is unreachable.
    """
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": (
                        f"Write a punchy 1-sentence marketing description for this travel deal:\n"
                        f"From: {deal_data.get('origin', 'N/A')} to {deal_data.get('destination', 'N/A')}\n"
                        f"Price: {deal_data.get('price', 'N/A')} {deal_data.get('currency', 'USD')}\n"
                        f"Details: {deal_data.get('label', '')}, {deal_data.get('reasons', [])}\n"
                        f"Output ONLY the description. No quotes, no extra text."
                    ),
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.9}
                }
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except Exception:
        return generate_deal_description(deal_data)


if __name__ == "__main__":
    test_deal = {
        "origin": "JFK",
        "destination": "LHR",
        "price": 286,
        "currency": "USD",
        "label": "flash",
        "confidence": 1,
        "reasons": ["71% below median (286 vs 1050)"],
    }
    print(f"Template: {generate_deal_description(test_deal)}")
