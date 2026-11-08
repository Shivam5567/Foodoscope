"""Regression tests for the ranking logic — the risky part of Mise.

Each test here exists because a real bug was found by running it.
"""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import app  # noqa: E402

client = TestClient(app)

BIRYANI_PANTRY = ["tomato", "onion", "yogurt", "mint", "basmati rice",
                  "ginger", "garlic", "green chilli", "coriander", "ghee"]


def recommend(**kwargs):
    payload = {"top_k": 5}
    payload.update(kwargs)
    r = client.post("/api/recommend", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_health_ok():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_returns_ranked_recipes():
    data = recommend(ingredients=BIRYANI_PANTRY, minutes=90)
    assert data["count"] > 0
    scores = [r["score"] for r in data["recipes"]]
    assert scores == sorted(scores, reverse=True), "results must be sorted by score"


def test_biryani_pantry_finds_biryani():
    """Regression: a 16-ingredient biryani used to lose to a 5-ingredient omelette."""
    data = recommend(ingredients=BIRYANI_PANTRY, minutes=90, diet="vegetarian")
    titles = [r["title"] for r in data["recipes"]]
    assert any("Biryani" in t for t in titles), titles
    assert "Biryani" in titles[0]


def test_vegetarian_filter_excludes_chicken():
    """Regression: 'vegetarian' is a substring of 'non-vegetarian', so a naive
    check let a chicken biryani through a vegetarian filter."""
    data = recommend(ingredients=BIRYANI_PANTRY, minutes=90, diet="vegetarian")
    for r in data["recipes"]:
        assert "chicken" not in r["title"].lower()
        assert r["diet"] in ("vegetarian", "vegan")


def test_vegan_filter_is_strict():
    data = recommend(ingredients=["potato", "cauliflower", "onion", "ginger",
                                  "cumin", "turmeric", "tomato"], diet="vegan")
    for r in data["recipes"]:
        assert r["diet"] == "vegan"


def test_non_vegetarian_filter_excludes_vegetarian():
    data = recommend(ingredients=BIRYANI_PANTRY, diet="non-vegetarian")
    for r in data["recipes"]:
        assert "vegetarian" not in r["diet"] or r["diet"] == "non-vegetarian"


def test_time_constraint_prefers_quick_dishes():
    data = recommend(ingredients=["egg", "onion", "tomato", "green chilli", "coriander"],
                     minutes=10, top_k=3)
    assert data["recipes"][0]["minutes"] <= 15
    assert data["recipes"][0]["score"] > 60


def test_absurd_time_drops_slow_recipes():
    data = recommend(ingredients=BIRYANI_PANTRY, minutes=10)
    for r in data["recipes"]:
        assert r["minutes"] is None or r["minutes"] <= 25


def test_nonsense_pantry_returns_nothing():
    """Better to return nothing than to invent a match."""
    data = recommend(ingredients=["chocolate", "banana", "bread"], top_k=4)
    assert data["recipes"] == []


def test_empty_pantry_is_rejected():
    r = client.post("/api/recommend", json={"ingredients": []})
    assert r.status_code == 400


def test_score_components_present():
    data = recommend(ingredients=BIRYANI_PANTRY)
    r = data["recipes"][0]
    for key in ("score", "coverage", "core_coverage", "utilization",
                "flavour", "missing_fit", "matched", "missing"):
        assert key in r


def test_unlock_suggestion_is_present():
    data = recommend(ingredients=BIRYANI_PANTRY, minutes=90)
    top = data["recipes"][0]
    assert top["unlock"] is not None
    assert top["unlock"]["ingredient"] in top["missing"]


def test_substitution_lookup():
    r = client.get("/api/substitute?ingredient=saffron")
    assert r.status_code == 200
    body = r.json()
    assert body["ingredient"] == "saffron"
    assert len(body["substitutes"]) > 0
    assert "cardamom" in [s["name"] for s in body["substitutes"]]


def test_instructions_endpoint():
    r = client.get("/api/instructions/demo-001")
    assert r.status_code == 200
    assert len(r.json()["steps"]) > 0


def test_scan_without_vision_key_falls_back_to_demo():
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c6300010000050001"
    )
    r = client.post("/api/scan", files={"image": ("x.png", io.BytesIO(png), "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["ingredients"], "must never return an empty pantry"
    assert body["needs_confirmation"] is True


def test_scan_rejects_non_image():
    r = client.post("/api/scan", files={"image": ("x.txt", io.BytesIO(b"hi"), "text/plain")})
    assert r.status_code == 400
