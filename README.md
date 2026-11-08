# Mise

**Point your camera at your counter. Cook something that actually tastes right.**

Mise is a computational-gastronomy cooking copilot built on Foodoscope's **RecipeDB** and
**FlavorDB** APIs. Photograph your ingredients; Mise names them, finds real recipes you can
almost cook, and ranks them with flavour science rather than ingredient counting.

Built for the **Foodoscope Fork IT Challenge 2026** (Esya'26, IIIT Delhi).

---

## Why this is different

Every pantry-to-recipe app does the same thing: match ingredient strings, return recipes.
That produces nonsense — you own onion, tomato and yogurt, so it suggests pizza.

Mise adds the molecular layer:

```
score = 0.30 × core_coverage      # are the dish-defining ingredients present?
      + 0.20 × utilisation        # how much of YOUR counter does this dish use?
      + 0.20 × flavour_coherence  # do your ingredients share aroma compounds? (FlavorDB)
      + 0.30 × gap_fit            # how few, and how minor, are the missing pieces?
      × constraint_multiplier     # diet is a hard gate; time and equipment scale the score
```

Then it answers the question no recipe app answers: **what is the one thing worth buying?**
Not the longest list of missing items — the single ingredient that most improves flavour
coherence, ranked by shared compounds.

---

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # add your Foodoscope key
./run.sh                      # http://localhost:8000
```

Or without any keys — it runs in demo mode immediately:

```bash
pip install -r requirements.txt
uvicorn backend.app:app --port 8000
```

Open <http://localhost:8000>, click the photo area, upload any image, and press
**Find what I can cook**. With no API or vision key, it uses the bundled demo pantry and
dataset so the full ranking pipeline is still exercised.

### Environment

| Variable | Purpose |
|---|---|
| `FOODOSCOPE_API_KEY` | Bearer token from your Foodoscope dashboard (Starter = 200 free tokens) |
| `FOODOSCOPE_RECIPEDB_BASE` | Default `https://api.foodoscope.com` |
| `FOODOSCOPE_FLAVORDB_BASE` | Default `https://api.foodoscope.com/flavordb` |
| `FOODOSCOPE_MAX_CALLS` | Hard cap on live calls per process run (default 150) |
| `FOODOSCOPE_CACHE_TTL` | Disk cache lifetime in seconds (default 86400) |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | Vision model for photo → ingredients |

**Confirm the base URLs against your own dashboard before the final.** The endpoint paths
below are the ones the API exposes; the host has historically also been served from the
CosyLab address, so if a call 404s, check the base first.

---

## Foodoscope endpoints used

| Purpose | Endpoint |
|---|---|
| Candidate recipes from detected pantry | `GET /recipe2-api/recipebyingredient/by-ingredients-categories-title?includeIngredients=…` |
| Fallback retrieval by dish name | `GET /recipe2-api/recipe-bytitle/recipeByTitle?title=…` |
| Step-by-step method | `GET /recipe2-api/instructions/{recipe_id}` |
| Flavour pairing / shared compounds | `GET /flavordb/food/by-alias?food_pair=<ingredient>` |
| Ingredient compound profile | `GET /flavordb/entities/by-entity-alias-readable?entity_alias_readable=<ingredient>` |
| Equipment-aware filtering | `GET /recipe2-api/byutensils/utensils?utensils=frypan` |
| Diet filtering | `GET /recipe2-api/recipe-diet/recipe-diet?diet=vegan` |
| Cuisine / region | `GET /recipe2-api/recipes_cuisine/cuisine/{region}` |

Auth: `Authorization: Bearer <FOODOSCOPE_API_KEY>`.

---

## Architecture

```
photo ──► vision.detect()        Gemini / OpenAI, returns named ingredients + confidence
             │
             ▼
      user confirms chips        (human-in-the-loop by design)
             │
             ▼
   foodoscope.search_by_ingredients()  ──► RecipeDB candidates
             │
             ▼
        ranking.rank()           ──► coverage · utilisation · flavour · gap fit
             │                        └── foodoscope.flavor_pairs() ──► FlavorDB
             ▼
      ranked cards + "one thing to add" + substitution lookup
```

| File | Role |
|---|---|
| `backend/app.py` | FastAPI routes, serves the UI |
| `backend/vision.py` | Photo → ingredients (pluggable providers, demo fallback) |
| `backend/foodoscope.py` | RecipeDB + FlavorDB client, TTL cache, call budget, demo fallback |
| `backend/ranking.py` | Scoring, diet gate, unlock suggestion, substitution |
| `frontend/index.html` | Single-page UI, no build step |
| `data/demo_dataset.json` | Offline snapshot so the demo never dies |

---

## API

```
POST /api/scan          multipart image  → {ingredients:[{name, confidence}], provider}
POST /api/recommend     JSON pantry      → {recipes:[…], source, api}
GET  /api/substitute?ingredient=saffron  → flavour-similar stand-ins
GET  /api/instructions/{recipe_id}       → method steps
GET  /api/health                         → key presence, live call count
```

---

## Design decisions worth defending

**Diet is a hard filter, not a penalty.** A soft multiplier still let a chicken biryani
through a vegetarian filter, because `"vegetarian"` is a substring of `"non-vegetarian"`.
Diet classification is now explicit.

**Long recipes are not punished for being long.** Raw coverage meant a 16-ingredient biryani
always lost to a 5-ingredient omelette. Core coverage (the first four ingredients) fixes it.

**Utilisation matters.** A recipe that uses 2 of your 10 ingredients is a shopping list,
not dinner.

**Results can be empty.** If nothing uses your counter, Mise says so instead of inventing a
match. A bad recommendation is worse than no recommendation.

**The user confirms what the camera saw.** Vision is good, not perfect. Misdetection is the
fastest way to lose trust in a food app, so the pantry is always editable before it matters.

---

## Testing

The ranking logic is the risky part, so it is exercised directly:

```bash
python3 -m pytest tests/ -q
```

Covered: diet gating across vegetarian / vegan / non-vegetarian, time constraints,
empty and nonsense pantries, substitution lookup, and the instruction endpoint.
