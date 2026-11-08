"""Builds the Mise Round-1 pitch deck for Foodoscope Fork IT Challenge 2026."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

NO_EFFECT = ('<a:effectLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>')


def kill_shadow(sh):
    sp = sh._element.spPr
    for el in sp.findall(qn('a:effectLst')):
        sp.remove(el)
    sp.append(parse_xml(NO_EFFECT))
    return sh

W, H = 13.333, 7.5
CREAM = RGBColor(0xFB, 0xF7, 0xF0)
INK = RGBColor(0x16, 0x18, 0x1D)
SAFF = RGBColor(0xD9, 0x62, 0x2B)
GREEN = RGBColor(0x1F, 0x4B, 0x3F)
MUTED = RGBColor(0x7A, 0x71, 0x67)
LINE = RGBColor(0xE7, 0xDF, 0xD3)
SOFT = RGBColor(0xF3, 0xEC, 0xE1)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SERIF = "Georgia"
SANS = "Arial"

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]


# ---------------------------------------------------------------- helpers
def slide(bg=CREAM):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid(); r.fill.fore_color.rgb = bg
    r.line.fill.background(); r.shadow.inherit = False
    kill_shadow(r)
    return s


def rect(s, l, t, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE, radius=None):
    sh = s.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    kill_shadow(sh)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sh.adjustments[0] = radius
        except Exception:
            pass
    return sh


def text(s, l, t, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None):
    """runs: list of (text, size, bold, color, font, space_after, italic)"""
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    first = True
    for spec in runs:
        txt, size, bold, color = spec[0], spec[1], spec[2], spec[3]
        font = spec[4] if len(spec) > 4 else SANS
        after = spec[5] if len(spec) > 5 else 6
        italic = spec[6] if len(spec) > 6 else False
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(after)
        if spacing:
            p.line_spacing = spacing
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(size); r.font.bold = bold; r.font.name = font
        r.font.color.rgb = color; r.font.italic = italic
    return tb


def eyebrow(s, txt, color=SAFF, l=0.85, t=0.62):
    text(s, l, t, 8, 0.3, [(txt.upper(), 10.5, True, color, SANS, 0)])
    rect(s, l, t + 0.30, 0.52, 0.028, fill=color)


def title(s, txt, t=1.02, size=33, color=INK, l=0.85, w=11.6):
    text(s, l, t, w, 1.5, [(txt, size, True, color, SERIF, 0)], spacing=1.02)


def footnote(s, txt, l=0.85, t=6.85, w=11.6):
    text(s, l, t, w, 0.4, [(txt, 8.5, False, MUTED, SANS, 0)])


def page_no(s, n):
    text(s, 12.15, 6.88, 0.6, 0.3, [(f"{n:02d}", 9, True, LINE, SANS, 0)], align=PP_ALIGN.RIGHT)


def rule(s, l, t, w, color=LINE, h=0.012):
    rect(s, l, t, w, h, fill=color)


# ---------------------------------------------------------------- 1 cover
s = slide()
rect(s, 0, 0, 0.34, H, fill=INK)
rect(s, 0, 0, 0.34, 2.2, fill=SAFF)

text(s, 1.15, 1.30, 9, 0.4, [("FORK IT CHALLENGE 2026  ·  ESYA'26  ·  IIIT DELHI", 10.5, True, SAFF, SANS, 0)])
text(s, 1.10, 1.85, 10.5, 1.6, [("Mise.", 96, True, INK, SERIF, 0)])
text(s, 1.15, 3.45, 9.6, 1.1, [
    ("Point your camera at your counter.\nCook something that actually tastes right.", 25, False, GREEN, SERIF, 0, True)
], spacing=1.18)
rule(s, 1.18, 4.86, 3.4, SAFF, 0.03)
text(s, 1.15, 5.10, 9.6, 0.9, [
    ("A computational-gastronomy cooking copilot built on RecipeDB and FlavorDB. "
     "It reads your kitchen from a photo, then uses flavour molecules — not guesswork — "
     "to decide what you should cook, and what one thing to add.", 12.5, False, MUTED, SANS, 0)
], spacing=1.35)
text(s, 1.15, 6.55, 5.5, 0.4, [("Team [NAME]  ·  [member 2]  ·  [member 3]  ·  [member 4]", 10, False, MUTED, SANS, 0)])

# ---------------------------------------------------------------- 2 problem
s = slide()
eyebrow(s, "The problem")
title(s, "The waste happens in the last metre,\nnot in the shop.")
text(s, 0.85, 2.50, 5.6, 1.9, [
    ("Indian households throw away 78.2 million tonnes of food a year — 55 kg per person. "
     "Globally, 19% of all food available to consumers is wasted.", 12.5, False, INK, SANS, 9),
    ("Nobody wastes food on purpose. It spoils because the decision — "
     "\u201cwhat do I cook tonight?\u201d — is made from habit, not from what is sitting there.",
     12.5, False, MUTED, SANS, 0),
], spacing=1.3)

stats = [
    ("78.2 Mt", "food wasted by Indian\nhouseholds every year"),
    ("55 kg", "wasted per person,\nper year"),
    ("63%", "of households report\nleafy greens spoiling"),
    ("51%", "cook more than the\nhousehold actually eats"),
]
x = 0.85
for i, (big, cap) in enumerate(stats):
    col = x + i * 2.95
    rect(s, col, 4.55, 2.65, 1.62, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    text(s, col + 0.24, 4.75, 2.2, 0.55, [(big, 26, True, SAFF, SERIF, 0)])
    text(s, col + 0.24, 5.35, 2.25, 0.7, [(cap, 9.5, False, MUTED, SANS, 0)], spacing=1.25)
footnote(s, "Sources: UNEP Food Waste Index Report 2024 (India: 78.2 Mt, 55 kg/capita); household study of 150 Telangana households, 2025 (spoilage and over-cooking rates).")
page_no(s, 2)

# ---------------------------------------------------------------- 3 gap
s = slide()
eyebrow(s, "Why existing apps don't fix it")
title(s, "Everyone makes you type\nyour pantry. Nobody uses flavour.")

rows = [
    ("", "SuperCook /\nSamsung Food", "Recipe sites\n& blogs", "General LLM\nchatbots", "Mise"),
    ("Knows what's in your kitchen", "You type a pantry\nlist manually", "No", "You type it", "One photo,\nyou correct it"),
    ("Recipes from a real database", "Yes", "Yes, but not\nmachine-readable", "Invents them", "RecipeDB,\n118k recipes"),
    ("Uses flavour chemistry", "No", "No", "No", "FlavorDB,\nshared molecules"),
    ("Tells you the ONE thing to buy", "No", "No", "Sometimes, unranked", "Ranked by\nflavour gain"),
    ("Handles Indian regional food", "Thin", "Recipes only", "Generic", "74 countries,\nregional cuisines"),
]
tbl_l, tbl_t, tbl_w = 0.85, 2.62, 11.62
col_w = [3.62, 2.05, 1.95, 1.95, 2.05]
row_h = [0.62, 0.78, 0.62, 0.62, 0.62, 0.62]

y = tbl_t
for ri, row in enumerate(rows):
    x = tbl_l
    for ci, cell in enumerate(row):
        is_head = ri == 0
        is_mise = ci == 4
        if is_head:
            fill = None
        elif is_mise:
            fill = SOFT
        else:
            fill = None
        if fill:
            rect(s, x, y, col_w[ci], row_h[ri], fill=fill)
        color = MUTED if is_head else (GREEN if is_mise else INK)
        bold = is_head or is_mise
        size = 9.5 if is_head else 10.5
        text(s, x + 0.14, y + 0.14, col_w[ci] - 0.24, row_h[ri] - 0.2,
             [(cell, size, bold, color, SANS, 0)], spacing=1.18)
        x += col_w[ci]
    if ri > 0:
        rule(s, tbl_l, y, tbl_w, LINE)
    y += row_h[ri]
rule(s, tbl_l, tbl_t + 0.62, tbl_w, INK, 0.02)
footnote(s, "The gap is not recipe data — it is the input (nobody photographs their kitchen) and the reasoning (nobody explains why the flavours work).")
page_no(s, 3)

# ---------------------------------------------------------------- 4 idea
s = slide()
eyebrow(s, "The idea")
title(s, "Three seconds of camera,\nnot three minutes of typing.")
steps = [
    ("01", "Shoot", "Photograph the counter, the fridge shelf, the vegetable tray. Messy is fine — the vision model returns a named ingredient list with confidences."),
    ("02", "Confirm", "The user taps off anything wrong and adds what the camera missed. Human-in-the-loop is a feature: a wrong pantry destroys trust instantly."),
    ("03", "Cook", "RecipeDB supplies real recipes; FlavorDB decides which of them will taste right with what you own — and names the single ingredient worth buying."),
]
x = 0.85
for num, head, body in steps:
    rect(s, x, 2.60, 3.68, 3.05, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    text(s, x + 0.32, 2.82, 1.2, 0.4, [(num, 11, True, SAFF, SANS, 0)])
    text(s, x + 0.32, 3.20, 3.0, 0.5, [(head, 22, True, INK, SERIF, 0)])
    text(s, x + 0.32, 3.82, 3.05, 1.6, [(body, 11.5, False, MUTED, SANS, 0)], spacing=1.35)
    x += 3.92
rect(s, 0.85, 5.90, 11.62, 0.72, fill=GREEN)
text(s, 1.12, 6.06, 11.1, 0.5, [("One line:  ", 12, True, WHITE, SANS, 0),
                               ("Mise is the shortest path from what is in your kitchen to a dish worth cooking.", 12, False, WHITE, SANS, 0)])
page_no(s, 4)

# ---------------------------------------------------------------- 5 pipeline
s = slide()
eyebrow(s, "How it works")
title(s, "The pipeline, end to end.")
boxes = [
    ("Photo", "camera input", SOFT, INK),
    ("Vision model", "names the\ningredients", SOFT, INK),
    ("User confirms", "editable chips", SOFT, INK),
    ("RecipeDB", "candidate\nrecipes", GREEN, WHITE),
    ("FlavorDB", "flavour\nscoring", GREEN, WHITE),
    ("Ranked cards", "score + why\n+ one thing to add", SAFF, WHITE),
]
bw, gap = 1.72, 0.30
x = 0.85
for i, (head, sub, fill, fg) in enumerate(boxes):
    rect(s, x, 2.72, bw, 1.30, fill=fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    text(s, x + 0.16, 2.90, bw - 0.3, 0.35, [(head, 12.5, True, fg, SANS, 0)])
    text(s, x + 0.16, 3.24, bw - 0.3, 0.6, [(sub, 9.5, False, fg, SANS, 0)], spacing=1.2)
    if i < len(boxes) - 1:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.05), Inches(3.26), Inches(0.20), Inches(0.22))
        ar.fill.solid(); ar.fill.fore_color.rgb = LINE; ar.line.fill.background(); ar.shadow.inherit = False
        kill_shadow(ar)
    x += bw + gap

notes = [
    ("Token discipline", "Every Foodoscope read is cached to disk for 24h and counted. The free Starter tier is 200 tokens — our whole demo loop runs on a warm cache, so repeat demos cost zero calls."),
    ("Never dies on stage", "If the API is unreachable or rate-limited, the identical ranking code runs over a bundled snapshot of RecipeDB-shaped data. Same logic, same UI, no broken demo."),
    ("Constraints as filters", "Diet is a hard gate, not a soft penalty — a vegetarian must never be shown chicken biryani. Time and equipment narrow the candidate set before scoring."),
]
x = 0.85
for head, body in notes:
    text(s, x, 4.45, 3.55, 0.35, [(head, 11.5, True, INK, SANS, 0)])
    text(s, x, 4.80, 3.55, 1.5, [(body, 10.5, False, MUTED, SANS, 0)], spacing=1.32)
    x += 3.92
page_no(s, 5)

# ---------------------------------------------------------------- 6 flavour science
s = slide()
eyebrow(s, "The differentiator")
title(s, "It doesn't just match. It reasons\nabout flavour.")
text(s, 0.85, 2.52, 5.85, 1.3, [
    ("Anyone can count ingredients in common. That produces nonsense — you own onion, tomato "
     "and yogurt, so \u201cmake pizza\u201d. FlavorDB gives us the molecular layer that ingredient "
     "matching is missing: which foods share aroma compounds, and therefore which swaps and "
     "additions will actually work.", 12.5, False, INK, SANS, 0)
], spacing=1.35)

rect(s, 0.85, 3.96, 5.85, 2.44, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
text(s, 1.10, 4.14, 5.4, 0.3, [("WHAT THE USER SEES", 9, True, MUTED, SANS, 0)])
text(s, 1.10, 4.46, 5.4, 0.4, [("You have 10 of 12 ingredients.", 12.5, True, INK, SANS, 0)])
text(s, 1.10, 4.82, 5.4, 0.4, [("Hyderabadi Vegetable Dum Biryani", 15, True, GREEN, SERIF, 0)])
text(s, 1.10, 5.20, 5.4, 0.35, [("Missing: potato · saffron · cardamom · cinnamon · bay leaf", 9.5, False, MUTED, SANS, 0)])
rect(s, 1.10, 5.56, 5.35, 0.68, fill=SOFT)
text(s, 1.26, 5.66, 5.05, 0.55, [("One thing to add: ", 10.5, True, SAFF, SANS, 0),
                                 ("potato — shares flavour molecules with 4 ingredients you already have.", 10.5, False, INK, SANS, 0)], spacing=1.2)

rect(s, 7.05, 2.52, 5.42, 3.82, fill=INK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
text(s, 7.35, 2.78, 4.9, 0.3, [("THE MOLECULAR LAYER", 9, True, SAFF, SANS, 0)])
text(s, 7.35, 3.16, 4.85, 2.9, [
    ("RecipeDB tells us what a dish is.", 13, True, WHITE, SANS, 10),
    ("FlavorDB tells us why it works.", 13, True, WHITE, SANS, 14),
    ("Shared compound sets turn a substitution question — \u201cI have no saffron\u201d — into a "
     "ranked, testable answer: cardamom and cinnamon share its aroma space, so the dish survives.",
     11.5, False, RGBColor(0xD8, 0xD2, 0xC8), SANS, 12),
    ("That is the layer no recipe app, and no chatbot, is using.", 11.5, True, SAFF, SANS, 0),
], spacing=1.32)
page_no(s, 6)

# ---------------------------------------------------------------- 7 scoring
s = slide()
eyebrow(s, "The ranking")
title(s, "Four signals, one number.")
parts = [
    ("30%", "Core coverage", "Are the dish-defining ingredients present? Raw coverage alone punishes a 16-ingredient biryani against a 5-ingredient omelette — so the first four ingredients carry the weight."),
    ("20%", "Counter utilisation", "How much of YOUR pantry this dish actually uses. A recipe that uses 2 of your 10 ingredients is a shopping list, not dinner."),
    ("20%", "Flavour coherence", "Mean pairwise compound overlap among the ingredients you own, from FlavorDB. Do these things belong in a pan together?"),
    ("30%", "Gap fit", "How few, and how minor, the missing pieces are — with the star ingredient weighted heaviest."),
]
x = 0.85
for pct, head, body in parts:
    rect(s, x, 2.60, 2.78, 3.30, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    text(s, x + 0.26, 2.80, 2.3, 0.5, [(pct, 27, True, SAFF, SERIF, 0)])
    text(s, x + 0.26, 3.40, 2.3, 0.4, [(head, 11.5, True, INK, SANS, 0)])
    text(s, x + 0.26, 3.82, 2.28, 1.9, [(body, 9.8, False, MUTED, SANS, 0)], spacing=1.3)
    x += 2.94
rect(s, 0.85, 6.16, 11.62, 0.52, fill=SOFT)
text(s, 1.10, 6.27, 11.2, 0.35, [("× constraint multiplier   ", 10.5, True, INK, SANS, 0),
                                ("— diet is a hard filter, time and equipment scale the score. Then a floor: no result that uses nothing you own.", 10.5, False, MUTED, SANS, 0)])
page_no(s, 7)

# ---------------------------------------------------------------- 8 endpoints
s = slide()
eyebrow(s, "Foodoscope integration")
title(s, "Exactly which endpoints we call.")
ep = [
    ("Photo \u2192 pantry", "Vision model (Gemini / OpenAI), client choice — not a Foodoscope call", MUTED),
    ("Candidate recipes", "GET /recipe2-api/recipebyingredient/by-ingredients-categories-title?includeIngredients=\u2026", GREEN),
    ("Fallback retrieval", "GET /recipe2-api/recipe-bytitle/recipeByTitle?title=\u2026", GREEN),
    ("Cooking method", "GET /recipe2-api/instructions/{recipe_id}", GREEN),
    ("Flavour pairing", "GET /flavordb/food/by-alias?food_pair=<ingredient>", SAFF),
    ("Compound profile", "GET /flavordb/entities/by-entity-alias-readable?entity_alias_readable=<ingredient>", SAFF),
    ("Equipment filter", "GET /recipe2-api/byutensils/utensils?utensils=frypan", GREEN),
    ("Diet filter", "GET /recipe2-api/recipe-diet/recipe-diet?diet=vegan", GREEN),
    ("Cuisine / region", "GET /recipe2-api/recipes_cuisine/cuisine/{region}", GREEN),
]
y = 2.55
for label, endpoint, col in ep:
    rule(s, 0.85, y, 11.62, LINE)
    text(s, 0.85, y + 0.10, 2.35, 0.3, [(label, 10.5, True, INK, SANS, 0)])
    text(s, 3.30, y + 0.11, 9.1, 0.3, [(endpoint, 9.8, False, col, "Courier New", 0)])
    y += 0.455
rule(s, 0.85, y, 11.62, LINE)
footnote(s, "Auth: Authorization: Bearer <key>. Every read is cached 24h and budget-counted against the Starter tier's 200 tokens.", t=6.85)
page_no(s, 8)

# ---------------------------------------------------------------- 9 built
s = slide()
eyebrow(s, "What already works")
title(s, "This is not a slideware idea.")
left = [
    ("Working prototype", "FastAPI service + single-page UI. Camera capture, editable pantry chips, ranked cards with score breakdown, substitution lookup, step-by-step method."),
    ("Ranking tested, not assumed", "Diet gate, time gate, core-coverage and utilisation scoring all unit-checked. Two real bugs found and fixed this week: a vegetarian filter that let chicken through, and long recipes losing to short ones."),
]
right = [
    ("Runs without the API", "Bundled snapshot + identical ranking path means the 24-hour final can never be derailed by a dead token budget or a rate limit."),
    ("Deliberately honest vision", "The app asks the user to confirm what it saw. Misdetection is the fastest way to lose trust in a food app."),
]
for col, items in ((0.85, left), (6.55, right)):
    y = 2.62
    for head, body in items:
        rect(s, col, y, 0.055, 1.42, fill=SAFF)
        text(s, col + 0.28, y + 0.02, 5.4, 0.35, [(head, 13.5, True, INK, SERIF, 0)])
        text(s, col + 0.28, y + 0.44, 5.35, 1.0, [(body, 11, False, MUTED, SANS, 0)], spacing=1.32)
        y += 1.85
page_no(s, 9)

# ---------------------------------------------------------------- 10 users
s = slide()
eyebrow(s, "Users and market")
title(s, "Who this is for, and who pays.")
users = [
    ("The 6:45 pm cook", "Working households cooking 5\u20136 dinners a week. The pain is decision fatigue plus spoilage, not lack of recipes."),
    ("The constrained eater", "Vegetarian, vegan, diabetic, low-sodium. Needs diet as a hard filter and flavour that survives restriction."),
    ("The professional kitchen", "Cloud kitchens and cafés costing menus weekly. Same engine, API-first, no consumer UI."),
]
x = 0.85
for head, body in users:
    rect(s, x, 2.58, 3.68, 1.72, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    text(s, x + 0.28, 2.78, 3.1, 0.4, [(head, 14, True, GREEN, SERIF, 0)])
    text(s, x + 0.28, 3.22, 3.1, 1.0, [(body, 10.2, False, MUTED, SANS, 0)], spacing=1.3)
    x += 3.92

text(s, 0.85, 4.58, 5.5, 0.3, [("HOW IT MAKES MONEY", 9, True, SAFF, SANS, 0)])
money = [
    ("Freemium B2C", "Free scans, paid pantry memory, meal history and multi-day planning."),
    ("Shoppable gaps", "The \u201cone thing to add\u201d is a purchase intent with a reason attached — an affiliate basket for grocery partners."),
    ("B2B API", "Menu costing and flavour-aware substitution for cloud kitchens and grocery apps, licensed on usage."),
]
x = 0.85
for head, body in money:
    text(s, x, 4.94, 3.55, 0.3, [(head, 11, True, INK, SANS, 0)])
    text(s, x, 5.26, 3.5, 1.2, [(body, 10.2, False, MUTED, SANS, 0)], spacing=1.3)
    x += 3.92
page_no(s, 10)

# ---------------------------------------------------------------- 11 scale
s = slide()
eyebrow(s, "Practicality and scalability")
title(s, "Why it survives contact\nwith real usage.")
road = [
    ("Now \u2014 the prototype", "Photo to ranked dish, diet and time constraints, flavour-based substitution, offline fallback."),
    ("Next \u2014 the pantry memory", "Remember the kitchen between sessions; prioritise what is about to spoil. This is where waste actually falls."),
    ("Then \u2014 household scale", "Multi-day planning, shopping lists that only include real gaps, regional cuisine depth from RecipeDB."),
    ("Later \u2014 the platform", "Licence the ranking engine: grocery apps, cloud kitchens, smart-kitchen hardware."),
]
y = 2.60
for i, (head, body) in enumerate(road):
    text(s, 0.85, y, 0.5, 0.3, [(f"0{i+1}", 10, True, SAFF, SANS, 0)])
    text(s, 1.42, y - 0.02, 2.75, 0.3, [(head, 11.5, True, INK, SANS, 0)])
    text(s, 4.30, y - 0.02, 5.0, 0.6, [(body, 10.5, False, MUTED, SANS, 0)], spacing=1.25)
    if i < 3:
        rule(s, 0.85, y + 0.72, 11.62, LINE)
    y += 0.92

rect(s, 9.55, 2.58, 2.92, 3.05, fill=INK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
text(s, 9.80, 2.78, 2.5, 0.3, [("COST DISCIPLINE", 8.5, True, SAFF, SANS, 0)])
text(s, 9.80, 3.12, 2.45, 2.3, [
    ("2\u20133 calls", 20, True, WHITE, SERIF, 2),
    ("per recommendation", 9, False, RGBColor(0xD8, 0xD2, 0xC8), SANS, 12),
    ("24h cache", 20, True, WHITE, SERIF, 2),
    ("kills repeat cost", 9, False, RGBColor(0xD8, 0xD2, 0xC8), SANS, 0),
], spacing=1.15)
page_no(s, 11)

# ---------------------------------------------------------------- 12 close
s = slide(bg=INK)
rect(s, 0, 0, 0.34, H, fill=SAFF)
text(s, 1.15, 1.05, 9, 0.35, [("WHY THIS ONE WINS", 10.5, True, SAFF, SANS, 0)])
text(s, 1.10, 1.50, 10.6, 1.9, [
    ("Anyone can match ingredients.\nFlavour is the part that takes\nthe data seriously.", 33, True, WHITE, SERIF, 0)
], spacing=1.12)
rule(s, 1.15, 3.62, 3.4, SAFF, 0.03)
pts = [
    ("It uses the APIs for what they are uniquely good at", "RecipeDB for verified recipes, FlavorDB for the molecular reasoning. Not a wrapper around a chatbot."),
    ("It solves a problem with a number attached", "78.2 Mt of household food waste, and a daily decision nobody wants to make."),
    ("It is buildable by this team in 24 hours", "The hard part — the ranking and the flavour layer — is already running."),
]
x = 1.15
for head, body in pts:
    text(s, x, 3.95, 3.55, 0.9, [(head, 11.5, True, WHITE, SANS, 0)], spacing=1.25)
    text(s, x, 4.72, 3.5, 1.4, [(body, 10.2, False, RGBColor(0xB8, 0xB1, 0xA6), SANS, 0)], spacing=1.32)
    x += 3.92
text(s, 1.15, 6.35, 11, 0.4, [("Team [NAME]  ·  [email]  ·  Prototype: [repo link]  ·  Built for Foodoscope Fork IT Challenge 2026", 10, False, RGBColor(0xB8, 0xB1, 0xA6), SANS, 0)])

prs.save("/scratch/work/mise/Mise_Round1_Deck.pptx")
print("saved deck with", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
