"""
Mise — point your camera at what you have, cook something that tastes right.

FastAPI app: serves the single-page UI and three JSON endpoints.
Run:  uvicorn backend.app:app --reload --port 8000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import foodoscope
import ranking
import vision

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="Mise — computational gastronomy cooking copilot", version="1.0")


class RecommendRequest(BaseModel):
    ingredients: list[str] = Field(default_factory=list)
    minutes: int | None = None
    diet: str = "any"
    utensils: list[str] = Field(default_factory=list)
    top_k: int = 6


@app.get("/api/health")
def health():
    return {"ok": True, "foodoscope": foodoscope.status(), "vision": {
        "gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }}


@app.post("/api/scan")
async def scan(image: UploadFile = File(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Upload an image file")
    raw = await image.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 12 MB)")
    result = vision.detect(raw, image.content_type, demo_pantry=foodoscope.demo_pantry())
    return JSONResponse(result)


@app.post("/api/recommend")
def recommend(req: RecommendRequest):
    pantry = [p.strip() for p in req.ingredients if p and p.strip()]
    if not pantry:
        raise HTTPException(400, "No ingredients supplied")

    live = foodoscope.search_by_ingredients(pantry)
    source = "recipedb"
    if not live:
        # second attempt: title search on the two most "dish-defining" items
        for probe in pantry[:2]:
            live = foodoscope.recipes_by_title(probe)
            if live:
                break
    if not live:
        live = foodoscope.demo_recipes()
        source = "demo"

    results = ranking.rank(
        live,
        pantry,
        minutes=req.minutes,
        diet=req.diet,
        utensils=req.utensils,
        top_k=max(1, min(req.top_k, 12)),
    )
    if not results:
        results = ranking.rank(foodoscope.demo_recipes(), pantry, minutes=req.minutes,
                               diet=req.diet, utensils=req.utensils, top_k=req.top_k)
        source = "demo"

    return {
        "pantry": pantry,
        "source": source,
        "count": len(results),
        "recipes": results,
        "api": foodoscope.status(),
    }


@app.get("/api/substitute")
def substitute(ingredient: str):
    if not ingredient.strip():
        raise HTTPException(400, "ingredient is required")
    return ranking.substitutes(ingredient.strip().lower())


@app.get("/api/instructions/{recipe_id}")
def get_instructions(recipe_id: str):
    steps = foodoscope.instructions(recipe_id)
    if not steps:
        for rec in foodoscope.demo_recipes():
            if ranking.recipe_id(rec) == recipe_id:
                steps = rec.get("instructions", [])
                break
    return {"recipe_id": recipe_id, "steps": steps}


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
