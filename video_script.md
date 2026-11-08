# Mise — Round 1 video script

**Length target: 4 min 10 s** (the brief allows 3–5 min; staying under 4:30 keeps the
judges' attention and leaves room for you to speak slowly).

**What Round 1 is scored on** — the brief lists seven things. Every one of them is
answered out loud in this script, and the timestamps tell you where. Do not skip
the endpoint segment; most teams forget it and lose easy marks.

| Scored on | Covered at |
|---|---|
| The idea | 0:15 |
| The problem it solves | 0:30 |
| Who the end users are | 0:55 |
| How it helps them | 1:15 |
| Similar products + key difference | 1:50 |
| Practicality and scalability | 2:40 |
| RecipeDB / FlavorDB / CocktailDB endpoints | 3:15 |

---

## Before you record

- Record the screen at 1080p, mic close, one take per section so you can re-record a
  single block without redoing everything.
- Have the app already running and **already scanned once** so the 24h cache is warm.
  Never let the judges watch a spinner.
- Have a second browser tab open on the recipe results, so if the live scan is slow you
  cut to the results and keep talking.
- Say the team name and member names in the first 20 seconds. Judges review dozens of
  videos; make it easy to attribute.

---

## 0:00 – 0:15 · Cold open (no logo, straight to the problem)

**On screen:** a photo of a normal Indian kitchen counter — tomatoes, onions, a bowl of
curd, half a bunch of mint. Then a bin.

**Say:**

> "This is a normal Indian kitchen at six in the evening. And this — the bin — is where
> a lot of it ends up. Not because anyone planned to waste food. Because at 6:45 pm,
> the question 'what do I cook tonight?' gets answered from habit, not from what is
> actually sitting on the counter."

---

## 0:15 – 0:55 · The idea and the problem

**On screen:** the deck's slide 2 stats, then the product name.

**Say:**

> "We're Team [NAME], and we built **Mise** — a cooking copilot that reads your kitchen
> from a photograph and tells you what to cook, and more importantly, *why* it will taste
> right.
>
> The scale of the problem is not small. UNEP's Food Waste Index puts Indian household
> food waste at 78.2 million tonnes a year — 55 kilos per person. A household study in
> Telangana found 63% of households reporting leafy greens spoiling before they're used,
> and 51% cooking more than the family actually eats.
>
> So the waste isn't happening in the shop. It's happening in the last metre — the fridge,
> the counter, and that one decision."

---

## 0:55 – 1:50 · Users, and why nothing existing fixes it

**On screen:** deck slide 3, the comparison table.

**Say:**

> "Three kinds of people feel this. The working household cooking five or six dinners a
> week. The constrained eater — vegetarian, vegan, diabetic, low-sodium — who needs diet
> as a hard filter, not a suggestion. And the professional kitchen costing a menu every
> week.
>
> For all three, the tools today fail in the same two places.
>
> One: they make you *type* your pantry. SuperCook, Samsung Food, the meal-planning apps —
> all of them start with a form. Nobody fills in that form at 6:45 pm.
>
> Two: they match ingredients, and stop there. Matching alone gives you nonsense. You own
> onion, tomato and yogurt — so the app says 'make pizza'. It has no idea whether those
> things belong in a pan together.
>
> And general chatbots have the opposite problem: they'll happily invent a recipe, a
> cooking time, and a quantity, and none of it is verified."

---

## 1:50 – 2:40 · The key difference — flavour, not matching

**On screen:** deck slide 6, then the app's result card.

**Say:**

> "This is where the Foodoscope APIs change what's possible.
>
> RecipeDB gives us 118,000 real recipes across 74 countries, with methods. FlavorDB gives
> us the molecular layer — which ingredients share aroma compounds. That second layer is
> what everyone else is missing.
>
> So instead of counting matching ingredients, we score four things: are the
> dish-defining ingredients present, how much of *your* counter this dish actually uses,
> do the ingredients you own share flavour compounds, and how small the gaps are.
>
> And then we answer the question no recipe app answers — what is the *one* thing worth
> buying? Not the longest list of missing items. The single ingredient that most improves
> the flavour, ranked by shared molecules.
>
> In this result: you own ten of twelve ingredients for a Hyderabadi vegetable dum biryani.
> We don't say 'you're missing five things'. We say: add potato — it shares flavour
> molecules with four ingredients you already have."

---

## 2:40 – 3:15 · Practicality and scalability

**On screen:** deck slide 11.

**Say:**

> "Practicality, honestly. It runs on the free Starter tier. Every Foodoscope read is
> cached to disk for 24 hours and counted against a budget, so two or three calls per
> recommendation, and repeat scans cost nothing. If the API is rate-limited or the network
> drops, the identical ranking code runs over a bundled snapshot — the demo cannot break
> in the middle of a final.
>
> Diet is a hard gate, not a soft penalty. A vegetarian must never be shown chicken
> biryani; we found that bug in testing and fixed it.
>
> Scalability: the next step is pantry memory — remember the kitchen between sessions and
> prioritise what's about to spoil. That's where waste actually falls. After that, the same
> engine is an API for grocery apps and cloud kitchens: the 'one thing to add' is a purchase
> intent with a reason attached."

---

## 3:15 – 3:45 · The endpoints (do not skip this)

**On screen:** deck slide 8, endpoints visible on screen while you speak.

**Say:**

> "The Foodoscope endpoints we use, concretely.
>
> RecipeDB for retrieval — `recipebyingredient/by-ingredients-categories-title` for
> candidate recipes from the detected pantry, `recipe-bytitle` as a fallback, and
> `instructions/{recipe_id}` for the method.
>
> FlavorDB for the reasoning — `food/by-alias` for flavour pairings, which drives both the
> coherence score and the substitution suggestions, and
> `entities/by-entity-alias-readable` for an ingredient's compound profile.
>
> We also use `byutensils/utensils` to respect equipment, `recipe-diet/recipe-diet` for
> the diet gate, and the cuisine endpoint for regional depth.
>
> We're not using CocktailDB for this build."

---

## 3:45 – 4:10 · Live demo and close

**On screen:** the app. Photo → chips → results. Then the deck's closing slide.

**Say:**

> "Here it is working. I photograph the counter. It reads tomato, onion, curd, mint,
> basmati rice, ginger, garlic, green chilli, coriander, ghee — and I can correct any of
> that before it matters.
>
> Ninety minutes, vegetarian. And the top result is the biryani, with the breakdown visible:
> what I own, what the flavours are doing, what the one gap is.
>
> Anyone can match ingredients. Flavour is the part that takes the data seriously — and
> that's what we're building on."

**End card:** team name, members, repo link.

---

## Delivery notes

- **Speak slower than feels natural.** Every number you say is a number the judge is
  writing down.
- **Never say "we plan to".** Round 1 rewards a working thing. Where something isn't built,
  say "next", and keep it to one sentence.
- **The honest line is a strength.** "We found that bug in testing and fixed it" reads as
  competence, not weakness. Keep it.
- **If asked about the vision model:** it's pluggable — Gemini or OpenAI — and the app
  always asks the user to confirm what it saw. Misdetection is the fastest way to lose
  trust in a food app, so human-in-the-loop is deliberate.
