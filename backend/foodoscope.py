"""
Foodoscope API client — RecipeDB2 + FlavorDB.

Auth:    Authorization: Bearer <FOODOSCOPE_API_KEY>
Bases:   FOODOSCOPE_RECIPEDB_BASE  (default https://api.foodoscope.com)
         FOODOSCOPE_FLAVORDB_BASE  (default https://api.foodoscope.com/flavordb)

Token budget matters on the free Starter plan (200 tokens, 25 req/min), so every
read goes through a small TTL disk cache and a call counter. If the API is
unreachable, missing a key, or over budget, the client degrades to the bundled
demo dataset instead of raising — a live demo must never die on stage.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

RECIPEDB_BASE = os.getenv("FOODOSCOPE_RECIPEDB_BASE", "https://api.foodoscope.com").rstrip("/")
FLAVORDB_BASE = os.getenv("FOODOSCOPE_FLAVORDB_BASE", "https://api.foodoscope.com/flavordb").rstrip("/")
API_KEY = os.getenv("FOODOSCOPE_API_KEY", "").strip()

CACHE_TTL = int(os.getenv("FOODOSCOPE_CACHE_TTL", "86400"))  # 24h
MAX_LIVE_CALLS = int(os.getenv("FOODOSCOPE_MAX_CALLS", "150"))  # per process run
TIMEOUT = float(os.getenv("FOODOSCOPE_TIMEOUT", "20"))
SEARCH_PAGES = int(os.getenv("FOODOSCOPE_SEARCH_PAGES", "3"))  # candidate pages per search

_calls = {"n": 0}
_last_error: str | None = None


class BudgetExceeded(RuntimeError):
    pass


def status() -> dict[str, Any]:
    return {
        "key_present": bool(API_KEY),
        "live_calls": _calls["n"],
        "max_live_calls": MAX_LIVE_CALLS,
        "last_error": _last_error,
        "recipedb_base": RECIPEDB_BASE,
        "flavordb_base": FLAVORDB_BASE,
    }


def _cache_path(url: str, params: dict) -> Path:
    key = url + "?" + json.dumps(params, sort_keys=True)
    return CACHE_DIR / (hashlib.sha256(key.encode()).hexdigest()[:24] + ".json")


def _get(url: str, params: dict) -> Any | None:
    """Cached GET. Returns parsed JSON, or None when unavailable."""
    global _last_error
    cp = _cache_path(url, params)
    if cp.exists() and time.time() - cp.stat().st_mtime < CACHE_TTL:
        try:
            data = json.loads(cp.read_text())
            # A remembered miss ("this ingredient has no flavour entry") is as
            # good as a remembered hit — it must not cost a token next time.
            if isinstance(data, dict) and data.get("__miss__"):
                return None
            return data
        except Exception:
            pass

    if not API_KEY:
        _last_error = "no API key configured"
        return None
    if _calls["n"] >= MAX_LIVE_CALLS:
        _last_error = "live call budget exhausted"
        return None

    try:
        _calls["n"] += 1
        with httpx.Client(timeout=TIMEOUT, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json",
        }) as client:
            r = client.get(url, params=params)
        if r.status_code == 429:
            _last_error = "rate limited (429) — 25 req/min on Starter"
            return None
        if r.status_code == 404:
            # Normal, not an error: this ingredient simply has no flavour entry
            # in FlavorDB ("vegetable stock", "tomato sauce", ...). Remember the
            # miss so we don't spend a token re-asking for it on every request.
            try:
                cp.write_text(json.dumps({"__miss__": True}))
            except Exception:
                pass
            return None
        r.raise_for_status()
        payload = r.json()
        cp.write_text(json.dumps(payload))
        return payload
    except Exception as exc:  # network, auth, parse
        _last_error = f"{type(exc).__name__}: {exc}"[:200]
        return None


def _dig_list(payload: Any) -> list[dict]:
    """Foodoscope responses wrap lists in different envelopes; find the list of dicts."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "recipes", "result", "results", "hits", "items", "payload"):
            if key in payload:
                found = _dig_list(payload[key])
                if found:
                    return found
        # deepest fallback: first list-of-dicts value
        for v in payload.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


# --------------------------------------------------------------------------
# RecipeDB2
# --------------------------------------------------------------------------

def search_by_ingredients(ingredients: list[str], limit: int = 20) -> list[dict]:
    """Core call: recipes that contain these ingredients.

    GET /recipe2-api/recipebyingredient/by-ingredients-categories-title

    The API returns at most 10 recipes per page and orders them by match count,
    so page 1 alone skews heavily toward whatever the dataset ranks first
    (usually meat dishes for a pantry of onion/tomato/rice). Walking a few
    pages widens the candidate pool so the ranker — not the API's ordering —
    decides what the user sees.
    """
    if not ingredients:
        return []
    url = f"{RECIPEDB_BASE}/recipe2-api/recipebyingredient/by-ingredients-categories-title"
    out: list[dict] = []
    seen: set[str] = set()
    for page in range(1, max(1, SEARCH_PAGES) + 1):
        payload = _get(url, {
            "includeIngredients": ",".join(ingredients[:12]),
            "page": page,
            "limit": limit,
        })
        rows = _dig_list(payload)
        if not rows:
            break
        fresh = 0
        for row in rows:
            key = str(row.get("Recipe_id") or row.get("_id") or row.get("Recipe_title"))
            if key in seen:
                continue
            seen.add(key)
            out.append(row)
            fresh += 1
        if fresh == 0:
            break
    return out


def recipes_by_title(title: str, limit: int = 10) -> list[dict]:
    """GET /recipe2-api/recipe-bytitle/recipeByTitle"""
    payload = _get(
        f"{RECIPEDB_BASE}/recipe2-api/recipe-bytitle/recipeByTitle",
        {"title": title},
    )
    return _dig_list(payload)[:limit]


def instructions(recipe_id: str) -> list[str]:
    """GET /recipe2-api/instructions/{recipe_id}"""
    payload = _get(f"{RECIPEDB_BASE}/recipe2-api/instructions/{recipe_id}", {})
    if payload is None:
        return []
    if isinstance(payload, list):
        return [str(s) for s in payload]
    for key in ("data", "instructions", "steps"):
        if isinstance(payload.get(key), list):
            return [str(s) for s in payload[key]]
    return []


def recipes_by_utensil(utensil: str, limit: int = 10) -> list[dict]:
    """GET /recipe2-api/byutensils/utensils — cook only with equipment the user owns."""
    payload = _get(
        f"{RECIPEDB_BASE}/recipe2-api/byutensils/utensils",
        {"utensils": utensil, "page": 1, "limit": limit},
    )
    return _dig_list(payload)


# --------------------------------------------------------------------------
# FlavorDB
# --------------------------------------------------------------------------

def flavor_pairs(ingredient: str) -> list[str]:
    """Ingredients that share flavour molecules with `ingredient`.

    GET /flavordb/food/by-alias?food_pair=<ingredient>
    """
    payload = _get(f"{FLAVORDB_BASE}/food/by-alias", {"food_pair": ingredient})
    if payload is None:
        return []
    out: list[str] = []
    for row in _dig_list(payload):
        # Live FlavorDB answers with {"entityId":..., "topSimilarEntities":[{"entityName":...}]}
        # so "entityName" must be checked alongside the flatter legacy key names.
        for key in ("entity_alias_readable", "entityName", "entity_name",
                    "food", "name", "entity", "pair"):
            v = row.get(key)
            if isinstance(v, str) and v.strip():
                out.append(v.strip().lower())
                break
    return out


def entity(ingredient: str) -> list[dict]:
    """GET /flavordb/entities/by-entity-alias-readable — compound profile of an ingredient."""
    payload = _get(
        f"{FLAVORDB_BASE}/entities/by-entity-alias-readable",
        {"entity_alias_readable": ingredient, "page": 0, "size": 20},
    )
    return _dig_list(payload)


# --------------------------------------------------------------------------
# Demo fallback
# --------------------------------------------------------------------------

_DEMO: dict | None = None


def demo_data() -> dict:
    global _DEMO
    if _DEMO is None:
        _DEMO = json.loads((DATA_DIR / "demo_dataset.json").read_text())
    return _DEMO


def demo_recipes() -> list[dict]:
    return demo_data()["recipes"]


def demo_pairs(ingredient: str) -> list[str]:
    table = demo_data().get("flavor_pairs", {})
    return [x.lower() for x in table.get(ingredient.lower(), [])]


def demo_pantry() -> list[str]:
    return demo_data()["demo_pantry"]


def pairs_for(ingredient: str) -> tuple[list[str], str]:
    """Flavour pairs from the live API, falling back to the bundled table."""
    live = flavor_pairs(ingredient)
    if live:
        return live, "live"
    return demo_pairs(ingredient), "demo"
