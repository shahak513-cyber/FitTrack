"""חישובי אנרגיה, יעדי מאקרו, והרכבת הצעת ארוחות.

הנוסחה היא Mifflin-St Jeor, נוסחה נפוצה להערכת BMR.
אחר כך מכפילים ברמת הפעילות כדי לקבל הערכה להוצאה היומית (TDEE).
כל המספרים כאן הם הערכות, לא מדידה אישית.
"""

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# גרם חלבון לכל ק״ג משקל גוף, לפי המטרה.
PROTEIN_PER_KG = {
    "fat_loss": 1.8,
    "maintain": 1.6,
    "muscle_gain": 1.8,
    "general": 1.6,
}

# ערכים משוערים ל-100 גרם. מותגים וצורות הכנה משנים את המספרים.
FOODS = {
    "oats": {"name": "שיבולת שועל יבשה", "kcal": 370, "protein": 13, "carbs": 60, "fat": 7},
    "milk": {"name": "חלב 3%", "kcal": 60, "protein": 3.2, "carbs": 4.6, "fat": 3.2},
    "banana": {"name": "בננה", "kcal": 89, "protein": 1.1, "carbs": 23, "fat": 0.3},
    "egg": {"name": "ביצה", "kcal": 143, "protein": 12.5, "carbs": 0.7, "fat": 9.5},
    "chicken": {"name": "חזה עוף מבושל", "kcal": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    "rice": {"name": "אורז לבן מבושל", "kcal": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
    "vegetables": {"name": "ירקות מעורבים", "kcal": 35, "protein": 2, "carbs": 6, "fat": 0.3},
    "olive_oil": {"name": "שמן זית", "kcal": 884, "protein": 0, "carbs": 0, "fat": 100},
    "white_cheese": {"name": "גבינה לבנה 5%", "kcal": 97, "protein": 9.5, "carbs": 3, "fat": 5},
    "bread": {"name": "לחם מלא", "kcal": 250, "protein": 10, "carbs": 43, "fat": 3.5},
    "tuna": {"name": "טונה במים, מסוננת", "kcal": 116, "protein": 26, "carbs": 0, "fat": 1},
    "yogurt": {"name": "יוגורט 0%", "kcal": 55, "protein": 10, "carbs": 4, "fat": 0.2},
    "apple": {"name": "תפוח", "kcal": 52, "protein": 0.3, "carbs": 14, "fat": 0.2},
    "almonds": {"name": "שקדים", "kcal": 579, "protein": 21, "carbs": 22, "fat": 50},
    "sweet_potato": {"name": "בטטה אפויה", "kcal": 90, "protein": 2, "carbs": 21, "fat": 0.2},
    "lentils": {"name": "עדשים מבושלות", "kcal": 116, "protein": 9, "carbs": 20, "fat": 0.4},
    "tahini": {"name": "טחינה גולמית", "kcal": 595, "protein": 17, "carbs": 21, "fat": 54},
}

# תבנית: ארוחות קבועות. אחר כך משנים בעיקר את מנת החלבון ואת מנת הפחמימה.
TEMPLATES = {
    "balanced": {
        "title": "יום מאוזן",
        "protein_food": "chicken",
        "carb_food": "rice",
        "meals": [
            ("ארוחת בוקר", [("oats", 50), ("milk", 200), ("banana", 100)]),
            ("ארוחת צהריים", [("chicken", 150), ("rice", 180), ("vegetables", 200), ("olive_oil", 8)]),
            ("ארוחת ערב", [("tuna", 120), ("bread", 70), ("vegetables", 150), ("white_cheese", 100)]),
            ("ביניים", [("yogurt", 150), ("apple", 120), ("almonds", 12)]),
        ],
    },
    "simple": {
        "title": "יום פשוט",
        "protein_food": "chicken",
        "carb_food": "sweet_potato",
        "meals": [
            ("ארוחת בוקר", [("egg", 120), ("bread", 60), ("vegetables", 100)]),
            ("ארוחת צהריים", [("chicken", 160), ("sweet_potato", 220), ("vegetables", 180), ("olive_oil", 10)]),
            ("ארוחת ערב", [("white_cheese", 180), ("tuna", 80), ("bread", 50), ("vegetables", 150)]),
            ("ביניים", [("yogurt", 180), ("banana", 100), ("almonds", 12)]),
        ],
    },
    "vegetarian": {
        "title": "יום צמחוני",
        "protein_food": "lentils",
        "carb_food": "rice",
        "meals": [
            ("ארוחת בוקר", [("oats", 50), ("milk", 250), ("yogurt", 150)]),
            ("ארוחת צהריים", [("lentils", 280), ("rice", 150), ("vegetables", 180), ("tahini", 15)]),
            ("ארוחת ערב", [("egg", 150), ("white_cheese", 150), ("bread", 60), ("vegetables", 180)]),
            ("ביניים", [("yogurt", 200), ("apple", 150), ("almonds", 15)]),
        ],
    },
}

# כמה גרם מותר לשנות במזונות שסוגרים את היעד, כדי שהמנות יישארו הגיוניות.
GRAM_LIMITS = {
    "chicken": (110, 280),
    "lentils": (150, 420),
    "rice": (60, 400),
    "sweet_potato": (80, 400),
    "yogurt": (80, 400),
    "bread": (30, 160),
    "olive_oil": (5, 25),
    "almonds": (8, 40),
}

# אחרי מנת הפחמימה הראשית, מקרבים את שאר הקלוריות עם מזונות שכבר נמצאים ביום.
CALORIE_TUNERS = ("bread", "olive_oil", "almonds")


def estimate_needs(age, sex, height_cm, weight_kg, activity, goal):
    """מחזיר BMR, הוצאה יומית ויעדי קלוריות ומאקרו מעוגלים."""
    weight_kg = float(weight_kg)
    height_cm = float(height_cm)
    age = float(age)

    if sex == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    tdee = bmr * ACTIVITY_FACTORS[activity]

    if goal == "fat_loss":
        calories = tdee * 0.85
    elif goal == "muscle_gain":
        calories = tdee * 1.10
    else:
        calories = tdee

    # רף תחתון שמרני, כדי שההצעה הראשונה לא תהיה נמוכה מאוד.
    minimum = 1600 if sex == "male" else 1400
    calories = max(calories, minimum)

    protein = weight_kg * PROTEIN_PER_KG[goal]
    fat = weight_kg * 0.8
    carbs = (calories - (protein * 4) - (fat * 9)) / 4

    # אם כמעט לא נשאר מקום לפחמימות, מורידים מעט את השומן.
    if carbs < 100:
        fat = weight_kg * 0.6
        carbs = (calories - (protein * 4) - (fat * 9)) / 4

    return {
        "bmr": int(round(bmr)),
        "tdee": int(round(tdee)),
        "calories": int(round(calories)),
        "protein_g": int(round(protein)),
        "carbs_g": int(round(max(carbs, 0))),
        "fat_g": int(round(fat)),
        "activity_factor": ACTIVITY_FACTORS[activity],
    }


def _round5(grams):
    """מעגל כמות גרמים ל-5 הקרובים, כדי שהמנות יהיו נוחות."""
    return int(5 * round(float(grams) / 5))


def _nutrients(food_key, grams):
    food = FOODS[food_key]
    factor = grams / 100
    return {
        "food": food["name"],
        "grams": grams,
        "kcal": int(round(food["kcal"] * factor)),
        "protein": int(round(food["protein"] * factor)),
        "carbs": int(round(food["carbs"] * factor)),
        "fat": int(round(food["fat"] * factor)),
    }


def _sum_items(items):
    totals = {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0}
    for item in items:
        for key in totals:
            totals[key] += item[key]
    return totals


def _clone_template(template):
    meals = []
    for meal_name, foods in template["meals"]:
        items = [{"key": key, "grams": grams} for key, grams in foods]
        meals.append({"name": meal_name, "items": items})
    return meals


def _find_item(meals, food_key):
    for meal in meals:
        for item in meal["items"]:
            if item["key"] == food_key:
                return item
    return None


def _set_grams(item, grams, food_key):
    low, high = GRAM_LIMITS[food_key]
    item["grams"] = min(high, max(low, _round5(grams)))


def _tune_calories(meals, item, food_key, calorie_target):
    """מזיז כמות של מזון אחד כדי להתקרב ליעד הקלוריות."""
    per_gram = FOODS[food_key]["kcal"] / 100
    if per_gram <= 0:
        return
    kcal, _protein = _precise_totals(meals)
    gap = calorie_target - kcal
    _set_grams(item, item["grams"] + (gap / per_gram), food_key)


# אם אחרי הכוונון עדיין יש יותר מדי קלוריות, מותר להקטין את המזונות האלה עד לרצפה.
SHRINK_FLOORS = {
    "tahini": 5,
    "egg": 50,
    "white_cheese": 60,
    "milk": 100,
    "oats": 30,
    "banana": 70,
    "apple": 80,
}

# אם חסרות קלוריות, מוסיפים ארוחה קצרה מהמזונות האלה, עד לתקרה.
BOOST_FOODS = (
    ("rice", 350),
    ("bread", 150),
    ("banana", 150),
    ("almonds", 35),
    ("olive_oil", 15),
)


def _shrink_extras(meals, calorie_target, protein_target):
    """מקטין מזונות דחוסים כשהיום עדיין עשיר מדי בקלוריות."""
    skipped = set()
    for _attempt in range(6):
        kcal, protein = _precise_totals(meals)
        if kcal <= calorie_target + 100:
            return
        chosen = None
        for meal in meals:
            for item in meal["items"]:
                if item["key"] in skipped:
                    continue
                floor = SHRINK_FLOORS.get(item["key"])
                if floor is None or item["grams"] <= floor:
                    continue
                density = FOODS[item["key"]]["kcal"]
                if chosen is None or density > chosen[0]:
                    chosen = (density, item)
        if chosen is None:
            return
        item = chosen[1]
        per_gram = FOODS[item["key"]]["kcal"] / 100
        protein_per_gram = FOODS[item["key"]]["protein"] / 100
        new_grams = max(
            SHRINK_FLOORS[item["key"]],
            _round5(item["grams"] - ((kcal - calorie_target) / per_gram)),
        )
        protein_loss = (item["grams"] - new_grams) * protein_per_gram
        if protein - protein_loss < protein_target - 12:
            skipped.add(item["key"])
            continue
        item["grams"] = new_grams


def _add_boost_meal(meals, calorie_target):
    """מוסיף ארוחה קצרה כשהמנות הרגילות לא מגיעות ליעד."""
    items = []
    for food_key, high in BOOST_FOODS:
        kcal, _protein = _precise_totals(meals)
        staged = sum(FOODS[item["key"]]["kcal"] * item["grams"] / 100 for item in items)
        remaining = calorie_target - (kcal + staged)
        if remaining < 100:
            break
        per_gram = FOODS[food_key]["kcal"] / 100
        grams = min(high, _round5(remaining / per_gram))
        if grams < 20:
            continue
        items.append({"key": food_key, "grams": grams})
    if items:
        meals.append({"name": "תוספת ליעד", "items": items})


def _precise_totals(meals):
    kcal = protein = 0.0
    for meal in meals:
        for item in meal["items"]:
            food = FOODS[item["key"]]
            factor = item["grams"] / 100
            kcal += food["kcal"] * factor
            protein += food["protein"] * factor
    return kcal, protein


def build_meals(template_id, calorie_target, protein_target):
    """בונה יום ארוחות ומקרב אותו ליעדי הקלוריות והחלבון.

    שאר המזונות נשארים קבועים. משנים בעיקר מנת חלבון ומנת פחמימה,
    ואם חסר חלבון מוסיפים יוגורט.
    """
    template = TEMPLATES[template_id]
    meals = _clone_template(template)

    protein_item = _find_item(meals, template["protein_food"])
    carb_item = _find_item(meals, template["carb_food"])

    kcal, protein = _precise_totals(meals)
    protein_per_gram = FOODS[template["protein_food"]]["protein"] / 100
    if protein < protein_target and protein_per_gram > 0:
        missing = protein_target - protein
        _set_grams(
            protein_item,
            protein_item["grams"] + (missing / protein_per_gram),
            template["protein_food"],
        )

    kcal, protein = _precise_totals(meals)
    if protein < protein_target - 10:
        snack = meals[-1]
        yogurt = next((item for item in snack["items"] if item["key"] == "yogurt"), None)
        missing = protein_target - protein
        extra_grams = missing / (FOODS["yogurt"]["protein"] / 100)
        if yogurt is None:
            yogurt = {"key": "yogurt", "grams": 0}
            snack["items"].append(yogurt)
            low = 0
        else:
            low = GRAM_LIMITS["yogurt"][0]
        high = GRAM_LIMITS["yogurt"][1]
        yogurt["grams"] = min(high, max(low, _round5(yogurt["grams"] + extra_grams)))

    _tune_calories(meals, carb_item, template["carb_food"], calorie_target)
    for food_key in CALORIE_TUNERS:
        tuner = _find_item(meals, food_key)
        if tuner is not None:
            _tune_calories(meals, tuner, food_key, calorie_target)
    _shrink_extras(meals, calorie_target, protein_target)
    _add_boost_meal(meals, calorie_target)

    rendered_meals = []
    day = {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0}
    for meal in meals:
        rendered_items = [_nutrients(item["key"], item["grams"]) for item in meal["items"]]
        meal_totals = _sum_items(rendered_items)
        for key in day:
            day[key] += meal_totals[key]
        rendered_meals.append(
            {
                "name": meal["name"],
                "items": rendered_items,
                "kcal": meal_totals["kcal"],
                "protein": meal_totals["protein"],
            }
        )

    notes = [
        "הכמויות והערכים משוערים לפי טבלאות תזונה כלליות. "
        "הם משתנים בין מותגים, וגם לפי בישול, שקילה ומה שנוסף לצלחת."
    ]
    calorie_gap = calorie_target - day["kcal"]
    protein_gap = protein_target - day["protein"]
    if abs(calorie_gap) >= 120:
        notes.append(
            f"סכום הארוחות יוצא בערך {day['kcal']} קלוריות, "
            f"והיעד הוא {int(calorie_target)}. נשאר פער של כ-{abs(calorie_gap)} קלוריות "
            "כדי לשמור על מנות הגיוניות."
        )
    if protein_gap >= 12:
        yogurt_grams = int(round(protein_gap / (FOODS["yogurt"]["protein"] / 100) / 10) * 10)
        notes.append(
            f"החלבון ביום הזה יוצא בערך {day['protein']} גרם מתוך יעד {int(protein_target)}. "
            f"אפשר להוסיף בערך {yogurt_grams} גרם יוגורט 0%, או מזון אחר עם כ-{protein_gap} גרם חלבון."
        )

    return {
        "title": template["title"],
        "meals": rendered_meals,
        "kcal": day["kcal"],
        "protein": day["protein"],
        "carbs": day["carbs"],
        "fat": day["fat"],
        "notes": notes,
    }
