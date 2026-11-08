"""
Photo -> ingredient list.

Pluggable vision backend:
  * Gemini  (GEMINI_API_KEY / GOOGLE_API_KEY)  — default if present
  * OpenAI  (OPENAI_API_KEY)                   — fallback
  * demo mode (no key)                         — returns the bundled pantry so
                                                 the UI is always demonstrable

The prompt is deliberately constrained: return only food items that are clearly
visible, with a confidence, so the UI can ask the user to confirm rather than
silently inventing a pantry. Human-in-the-loop correction is a feature, not a
workaround — misdetection is the number-one trust killer in vision apps.
"""

from __future__ import annotations

import base64
import json
import os
import re

import httpx

PROMPT = """You are a kitchen vision assistant. List every distinct FOOD ingredient
visible in this image.

Rules:
- Only food items. Ignore packaging text, hands, utensils, appliances, and background.
- Use simple, common English names as they appear in recipe ingredient lists
  (e.g. "tomato", "onion", "curry leaves", "basmati rice", "yogurt", "ginger").
- Split prepared mixtures only when obvious (e.g. a bowl of chopped onions and tomatoes).
- Return at most 12 items, most confident first.

Return ONLY JSON, no prose, in this exact shape:
{"ingredients": [{"name": "tomato", "confidence": 0.94}], "notes": "optional one line"}"""


def _parse(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {"ingredients": [], "notes": "unparseable model response"}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"ingredients": [], "notes": "invalid JSON from model"}
    items = []
    for it in data.get("ingredients", [])[:12]:
        name = str(it.get("name", "")).strip().lower()
        if not name:
            continue
        try:
            conf = float(it.get("confidence", 0.7))
        except (TypeError, ValueError):
            conf = 0.7
        items.append({"name": name, "confidence": round(min(max(conf, 0.0), 1.0), 2)})
    return {"ingredients": items, "notes": str(data.get("notes", ""))[:200]}


def _gemini(image_b64: str, mime: str) -> dict | None:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    model = os.getenv("VISION_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": mime, "data": image_b64}},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 800},
    }
    try:
        with httpx.Client(timeout=45) as c:
            r = c.post(url, params={"key": key}, json=body)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        out = _parse(text)
        out["provider"] = "gemini"
        return out if out["ingredients"] else None
    except Exception as exc:
        return {"ingredients": [], "notes": f"gemini error: {type(exc).__name__}", "provider": "gemini"}


def _openai(image_b64: str, mime: str) -> dict | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
    try:
        with httpx.Client(timeout=45) as c:
            r = c.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url",
                             "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                        ],
                    }],
                },
            )
        r.raise_for_status()
        out = _parse(r.json()["choices"][0]["message"]["content"])
        out["provider"] = "openai"
        return out if out["ingredients"] else None
    except Exception as exc:
        return {"ingredients": [], "notes": f"openai error: {type(exc).__name__}", "provider": "openai"}


def detect(image_bytes: bytes, mime: str = "image/jpeg", demo_pantry: list[str] | None = None) -> dict:
    """Returns {ingredients:[{name,confidence}], provider, notes, needs_confirmation}."""
    b64 = base64.b64encode(image_bytes).decode()

    for fn in (_gemini, _openai):
        result = fn(b64, mime)
        if result and result.get("ingredients"):
            result["needs_confirmation"] = True
            return result

    pantry = demo_pantry or ["tomato", "onion", "yogurt", "mint", "basmati rice", "ginger", "green chilli"]
    return {
        "ingredients": [{"name": n, "confidence": 0.9} for n in pantry],
        "provider": "demo",
        "notes": "No vision key configured (or model unavailable) — showing the sample pantry. "
                 "Set GEMINI_API_KEY or OPENAI_API_KEY for real detection.",
        "needs_confirmation": True,
    }
