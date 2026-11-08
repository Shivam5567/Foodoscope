"""
Recipe ranking — this is the product's actual differentiator.

Every team will match pantry ingredients to recipes. Matching alone produces
absurd results ("you have onion, tomato, yogurt — make pizza"). Mise ranks with
flavour science on top of coverage:

    score = 0.30 * core_coverage     # are the dish-defining ingredients present
          + 0.20 * utilization       # how much of YOUR counter this dish actually uses
          + 0.20 * flavour_coherence # do the ingredients you own taste good together (FlavorDB)
          + 0.30 * missing_fit       # how few (and how minor) the gaps are
          * constraint_multiplier    # time / diet / equipment

Two deliberate design choices, both learned from testing:
  * core_coverage rather than raw coverage — otherwise a 16-ingredient biryani
    always loses to a 5-ingredient omelette just for being a real dish.
  * utilization — a recipe that uses 2 of your 10 ingredients is not "what you
    can cook", it's a shopping list.

and then answers the question no other app answers: "what ONE thing should I add
to make this dish taste right?" — chosen by flavour-molecule gain, not guesswork.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import foodoscope  # noqa: E402

# Ingredients nobody counts as "missing".
STAPLES = {
    "salt", "water", "oil", "sugar", "black pepper", "pepper", "to taste",
    "as needed", "ice", "hot water", "cold water", "cooking oil", "vegetable oil",
}

STOPWORDS = {"fresh", "chopped", "diced", "sliced", "ground", "powder", "paste",
             "large", "small", "medium", "cup", "tbsp", "tsp", "gram", "grams",
             "finely", "roughly", "optional", "to", "and", "or", "of", "the"}

_pair_cache: dict[str, set[str]] = {}


def norm(name: str) -> str:
    s = re.sub(r"\(.*?\)", " ", str(name).lower())
    s = re.sub(r"[^a-z\s]", " ", s)
    words = [w for w in s.split() if w and w not in STOPWORDS]
    return " ".join(words).strip()


def _field(rec: dict, *names: str, default: Any = None) -> Any:
    for n in names:
        if n in rec and rec[n] not in (None, "", []):
            return rec[n]
    # case-insensitive sweep
    lower = {str(k).lower(): v for k, v in rec.items()}
    for n in names:
        v = lower.get(n.lower())
        if v not in (None, "", []):
            return v
    return default


def recipe_title(rec: dict) -> str:
    return str(_field(rec, "Recipe_title", "recipe_title", "title", "name", "Recipe", default="Untitled recipe"))


def recipe_id(rec: dict) -> str:
    return str(_field(rec, "Recipe_id", "recipe_id", "id", "_id", "recipeId", default=""))


def recipe_ingredients(rec: dict) -> list[str]:
    raw = _field(rec, "ingredients", "Ingredients", "ingredient_list", "ingredients_list", default=[])
    if isinstance(raw, str):
        parts = re.split(r"[,;|\n]", raw)
    elif isinstance(raw, list):
        parts = []
        for x in raw:
            if isinstance(x, str):
                parts.append(x)
            elif isinstance(x, dict):
                parts.append(str(x.get("name") or x.get("ingredient") or x.get("ing") or ""))
    else:
        parts = []
    out, seen = [], set()
    for p in parts:
        n = norm(p)
        if n and n not in seen and len(n) > 1:
            seen.add(n)
            out.append(n)
    return out


def recipe_minutes(rec: dict) -> int | None:
    v = _field(rec, "total_time", "Total_Time", "totalTime", "time", "cook_time")
    if v is None:
        return None
    try:
        return int(float(str(v).split()[0]))
    except (ValueError, IndexError):
        return None


def _flag(rec: dict, *names: str) -> bool:
    """Read one of RecipeDB2's boolean diet flags ("0.0" / "1.0" strings)."""
    for n in names:
        v = _field(rec, n, default=None)
        if v is None:
            continue
        s = str(v).strip().lower()
        if s in ("1.0", "1", "true", "yes"):
            return True
        if s in ("0.0", "0", "false", "no"):
            return False
    return False


# Anything animal-derived. Used to infer diet when the source flags are all
# zero but are actually unreliable (Palak Paneer ships with lacto_vegetarian=0).
MEAT_TERMS = {
    "beef", "pork", "chicken", "lamb", "mutton", "veal", "turkey", "duck", "meat",
    "bacon", "sausage", "ham", "brisket", "steak", "mince", "ribs", "prosciutto",
    "fish", "salmon", "tuna", "shrimp", "prawn", "anchovy", "squid", "crab",
    "lobster", "tilapia", "cod", "sardine", "oyster", "scallop", "mussel",
    "egg", "eggs", "gelatin", "fish sauce",
}


def _has_meat(ings: list[str]) -> bool:
    for ing in ings:
        for word in ing.split():
            if word in MEAT_TERMS:
                return True
    return False


def recipe_diet(rec: dict) -> str:
    """Diet label for a recipe, from whichever field the source provides.

    RecipeDB2 does not ship a single "diet" field. It ships four separate
    boolean flags (vegan / lacto_vegetarian / ovo_vegetarian /
    ovo_lacto_vegetarian), and those flags are noisy — paneer dishes in the
    live data ship with lacto_vegetarian=0. So: honour an explicit label first,
    then the flags, and fall back to reading the ingredient list. Returning ""
    here means "unknown", which is *not* the same as "vegetarian" — an unknown
    dish is allowed through but gets no diet bonus.
    """
    explicit = str(_field(rec, "diet", "Diet", "recipe_diet", default="")).lower()
    if explicit:
        return explicit

    if _flag(rec, "vegan"):
        return "vegan"
    if _flag(rec, "ovo_lacto_vegetarian", "lacto_vegetarian", "ovo_vegetarian"):
        return "vegetarian"

    # All flags zero. Trust the ingredient list over the flags.
    if _has_meat(recipe_ingredients(rec)):
        return "non-vegetarian"
    return ""


def _pairs(ing: str) -> set[str]:
    if ing not in _pair_cache:
        got, _src = foodoscope.pairs_for(ing)
        _pair_cache[ing] = {norm(x) for x in got}
    return _pair_cache[ing]


def flavour_coherence(matched: list[str], budget: int = 4) -> tuple[float, list[str]]:
    """Mean pairwise shared-compound affinity among the ingredients the user owns."""
    if len(matched) < 2:
        return 0.0, []
    probe = matched[:budget]
    total, count, best = 0.0, 0, []
    for a in probe:
        pa = _pairs(a)
        if not pa:
            continue
        for b in matched:
            if b == a:
                continue
            count += 1
            hit = b in pa or any(b in w or w in b for w in pa if len(w) > 3)
            total += 1.0 if hit else 0.0
            if hit and a not in best:
                best.append(a)
    return (total / count if count else 0.0), best


def _constraint_multiplier(rec: dict, minutes: int | None, diet: str, utensils: list[str]) -> tuple[float, list[str]]:
    m, notes = 1.0, []
    rt = recipe_minutes(rec)
    if minutes and rt:
        if rt <= minutes:
            m *= 1.0
            notes.append(f"fits your {minutes} min")
        elif rt <= minutes * 1.5:
            m *= 0.8
            notes.append(f"slightly over ({rt} min)")
        else:
            m *= 0.45
            notes.append(f"too slow ({rt} min)")
    if diet and diet != "any":
        rd = recipe_diet(rec)
        if rd:
            compatible = (diet in rd) or (rd in diet) or (diet == "vegetarian" and "vegan" in rd)
            if not compatible:
                m *= 0.3
                notes.append(f"not {diet}")
    if utensils:
        blob = " ".join(str(_field(rec, "utensils", "Utensils", default="")).lower().split())
        if blob:
            if not any(u.lower() in blob for u in utensils):
                m *= 0.85
    return m, notes


def _diet_ok(recipe_d: str, wanted: str) -> bool:
    """Classify the recipe's diet properly.

    Naive substring tests fail here: "vegetarian" is a substring of
    "non-vegetarian", so a chicken biryani sailed through a vegetarian filter
    until this was rewritten as explicit classification.
    """
    if not recipe_d:
        return True  # unknown diet: allowed, but no diet bonus
    d = recipe_d.lower().replace("_", "-").replace(" ", "-")
    is_nonveg = ("non-vegetarian" in d) or ("nonveg" in d) or ("non-veg" in d)
    is_vegan = "vegan" in d
    is_veg = is_vegan or ("vegetarian" in d and not is_nonveg)
    if wanted == "vegetarian":
        return is_veg
    if wanted == "vegan":
        return is_vegan
    if wanted == "non-vegetarian":
        return is_nonveg
    return wanted in d


def rank(recipes: list[dict], pantry: list[str], minutes: int | None = None,
         diet: str = "any", utensils: list[str] | None = None, top_k: int = 6,
         enrich_flavour: int = 8) -> list[dict]:
    utensils = utensils or []
    pantry_n = {norm(p) for p in pantry if norm(p)}
    scored: list[dict] = []

    for rec in recipes:
        ings = recipe_ingredients(rec)
        if not ings:
            continue
        required = [i for i in ings if i not in STAPLES]
        if not required:
            continue

        # Hard diet gate: a vegetarian must never be shown a chicken dish, no
        # matter how well it scores. Soft multipliers are not enough here.
        if diet and diet != "any" and not _diet_ok(recipe_diet(rec), diet):
            continue
        rt = recipe_minutes(rec)
        if minutes and rt and rt > minutes * 2.5:
            continue  # not cookable tonight, don't waste a slot

        matched, missing = [], []
        for i in required:
            if i in pantry_n or any(i in p or p in i for p in pantry_n if len(p) > 2):
                matched.append(i)
            else:
                missing.append(i)

        # the first ingredients define the dish — they carry the score
        core = required[:4]
        core_cov = sum(1 for i in core if i in matched) / len(core) if core else 0.0
        coverage = len(matched) / len(required) if required else 0.0
        utilization = len(set(matched)) / len(pantry_n) if pantry_n else 0.0

        missing_fit = 1.0 / (1.0 + 0.25 * len(missing))
        c_mult, notes = _constraint_multiplier(rec, minutes, diet, utensils)
        star_missing = required[0] not in matched

        rec_out = {
            "id": recipe_id(rec),
            "title": recipe_title(rec),
            "cuisine": str(_field(rec, "cuisine", "Cuisine", "region", "Region", default="")),
            "minutes": recipe_minutes(rec),
            "diet": recipe_diet(rec),
            "ingredients": required,
            "matched": matched,
            "missing": missing,
            "coverage": round(coverage, 3),
            "core_coverage": round(core_cov, 3),
            "utilization": round(utilization, 3),
            "missing_fit": round(missing_fit, 3),
            "star_missing": star_missing,
            "constraints": notes,
            "_rec": rec,
        }
        scored.append(rec_out)

    # coverage-first pass, then flavour science on the strongest candidates only
    scored.sort(key=lambda r: (r["core_coverage"], r["utilization"], r["missing_fit"]), reverse=True)
    for idx, r in enumerate(scored):
        if idx < enrich_flavour:
            coh, evidence = flavour_coherence(r["matched"])
        else:
            coh, evidence = 0.0, []
        r["flavour"] = round(coh, 3)
        r["flavour_evidence"] = evidence
        base = (0.30 * r["core_coverage"]
                + 0.20 * r["utilization"]
                + 0.20 * coh
                + 0.30 * r["missing_fit"])
        r["score"] = round(100 * base * max(0.3, _mult_from_notes(r)), 1)

    # A result that uses none of your counter and none of the core ingredients is
    # not a recommendation. Better to say "nothing matches" than to invent one.
    scored = [r for r in scored if r["core_coverage"] > 0 or r["utilization"] >= 0.34]
    scored.sort(key=lambda r: r["score"], reverse=True)
    top = scored[:top_k]

    for r in top:
        if r["star_missing"] and r["missing"]:
            star = r["missing"][0]
            r["unlock"] = {
                "ingredient": star,
                "flavour_links": 0,
                "why": "this is the main ingredient of the dish — you need it before anything else",
            }
        else:
            r["unlock"] = suggest_unlock(r["matched"], r["missing"])
        r.pop("_rec", None)
    return top


def _mult_from_notes(r: dict) -> float:
    m = 1.0
    for n in r.get("constraints", []):
        if n.startswith("too slow"):
            m *= 0.45
        elif n.startswith("slightly over"):
            m *= 0.8
        elif n.startswith("not "):
            m *= 0.3
    return m


def suggest_unlock(matched: list[str], missing: list[str]) -> dict | None:
    """Which single missing ingredient most improves flavour coherence?

    For each gap, count how many owned ingredients it shares flavour molecules
    with. The best gain-per-effort suggestion is returned.
    """
    if not missing or not matched:
        return None
    best, best_gain = None, 0
    for cand in missing[:6]:
        pc = _pairs(cand)
        if not pc:
            continue
        gain = sum(1 for m in matched if m in pc or any(m in w or w in m for w in pc if len(w) > 3))
        if gain > best_gain:
            best, best_gain = cand, gain
    if not best:
        return None
    return {
        "ingredient": best,
        "flavour_links": best_gain,
        "why": f"shares flavour molecules with {best_gain} of the ingredients you already have",
    }


def substitutes(ingredient: str, limit: int = 5) -> dict:
    """Flavour-similar stand-ins for something the user is missing."""
    pairs, src = foodoscope.pairs_for(ingredient)
    pairs = [p for p in pairs if norm(p) != norm(ingredient)][:limit]
    return {
        "ingredient": ingredient,
        "substitutes": [{"name": p, "why": "shares flavour compounds"} for p in pairs],
        "source": src,
    }
