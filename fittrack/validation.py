"""בדיקות תקינות לקלט של המשתמש.

כל פונקציה מחזירה רשימת הודעות שגיאה בעברית.
רשימה ריקה פירושה שהנתונים תקינים.
"""

# גבולות לגרסה הראשונה: מבוגרים בריאים, ערכים יומיומיים סבירים.
MIN_AGE = 18
MAX_AGE = 80
MIN_HEIGHT_CM = 140
MAX_HEIGHT_CM = 220
MIN_WEIGHT_KG = 40
MAX_WEIGHT_KG = 200
MIN_TRAINING_DAYS = 2
MAX_TRAINING_DAYS = 5

MIN_CALORIES = 1200
MAX_CALORIES = 4500
MIN_PROTEIN = 40
MAX_PROTEIN = 250
MIN_CARBS = 50
MAX_CARBS = 600
MIN_FAT = 25
MAX_FAT = 180

ACTIVITY_KEYS = ("sedentary", "light", "moderate", "active", "very_active")
EXPERIENCE_KEYS = ("beginner", "intermediate")
GOAL_KEYS = ("fat_loss", "maintain", "muscle_gain", "general")
SEX_KEYS = ("male", "female")


def _number(value):
    """מנסה להפוך את הקלט למספר. מחזיר None אם זה לא מספר."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_profile(data):
    """בודק את שדות הפרופיל לפני שמירה."""
    errors = []

    name = str(data.get("name", "")).strip()
    if not name:
        errors.append("צריך למלא שם, כדי שנדע איך לפנות אליך.")
    elif len(name) > 40:
        errors.append("השם ארוך מדי. עד 40 תווים מספיקים.")

    age = _number(data.get("age"))
    if age is None or age < MIN_AGE or age > MAX_AGE or int(age) != age:
        errors.append(
            f"הגיל צריך להיות מספר שלם בין {MIN_AGE} ל-{MAX_AGE}. "
            "הגרסה הזו מיועדת למבוגרים בלבד."
        )

    if data.get("sex") not in SEX_KEYS:
        errors.append("צריך לבחור מין לצורך נוסחת האנרגיה.")

    height = _number(data.get("height_cm"))
    if height is None or height < MIN_HEIGHT_CM or height > MAX_HEIGHT_CM:
        errors.append(f"הגובה צריך להיות בין {MIN_HEIGHT_CM} ל-{MAX_HEIGHT_CM} ס״מ.")

    weight = _number(data.get("weight_kg"))
    if weight is None or weight < MIN_WEIGHT_KG or weight > MAX_WEIGHT_KG:
        errors.append(f"המשקל צריך להיות בין {MIN_WEIGHT_KG} ל-{MAX_WEIGHT_KG} ק״ג.")

    if data.get("activity") not in ACTIVITY_KEYS:
        errors.append("צריך לבחור רמת פעילות.")

    if data.get("experience") not in EXPERIENCE_KEYS:
        errors.append("צריך לבחור ניסיון באימונים.")

    if data.get("goal") not in GOAL_KEYS:
        errors.append("צריך לבחור מטרה.")

    days = _number(data.get("training_days"))
    if days is None or days < MIN_TRAINING_DAYS or days > MAX_TRAINING_DAYS or int(days) != days:
        errors.append(
            f"מספר ימי האימון צריך להיות מספר שלם בין {MIN_TRAINING_DAYS} ל-{MAX_TRAINING_DAYS}."
        )

    if not data.get("acknowledged"):
        errors.append(
            "כדי להמשיך צריך לאשר שהמידע מיועד למבוגרים בריאים, "
            "ושההמלצות הן הערכה כללית ולא ייעוץ רפואי."
        )

    return errors


def validate_targets(calories, protein_g, carbs_g, fat_g):
    """בודק יעדי תזונה שהמשתמש ערך בעצמו."""
    errors = []

    calories_n = _number(calories)
    protein_n = _number(protein_g)
    carbs_n = _number(carbs_g)
    fat_n = _number(fat_g)

    if calories_n is None or calories_n < MIN_CALORIES or calories_n > MAX_CALORIES:
        errors.append(f"יעד הקלוריות צריך להיות בין {MIN_CALORIES} ל-{MAX_CALORIES}.")
    if protein_n is None or protein_n < MIN_PROTEIN or protein_n > MAX_PROTEIN:
        errors.append(f"יעד החלבון צריך להיות בין {MIN_PROTEIN} ל-{MAX_PROTEIN} גרם.")
    if carbs_n is None or carbs_n < MIN_CARBS or carbs_n > MAX_CARBS:
        errors.append(f"יעד הפחמימות צריך להיות בין {MIN_CARBS} ל-{MAX_CARBS} גרם.")
    if fat_n is None or fat_n < MIN_FAT or fat_n > MAX_FAT:
        errors.append(f"יעד השומן צריך להיות בין {MIN_FAT} ל-{MAX_FAT} גרם.")

    return errors


def macro_calorie_gap(calories, protein_g, carbs_g, fat_g):
    """מחשב את ההפרש בין הקלוריות שהוזנו לבין הקלוריות שיוצאות מהמאקרו.

    חלבון ופחמימה: 4 קלוריות לגרם. שומן: 9 קלוריות לגרם.
    """
    calories_n = _number(calories) or 0
    from_macros = (float(protein_g) * 4) + (float(carbs_g) * 4) + (float(fat_g) * 9)
    return round(from_macros - calories_n)


def validate_weight_log(log_date, weight_kg, note, today):
    """בודק רשומת משקל."""
    errors = []
    if log_date is None or log_date > today:
        errors.append("אי אפשר לשמור תאריך עתידי.")
    weight = _number(weight_kg)
    if weight is None or weight < 35 or weight > 220:
        errors.append("משקל הרשומה צריך להיות בין 35 ל-220 ק״ג.")
    if note and len(str(note)) > 200:
        errors.append("ההערה ארוכה מדי. עד 200 תווים.")
    return errors


def validate_workout_log(log_date, session_name, exercise, sets, reps, weight_kg, note, today):
    """בודק רשומת אימון."""
    errors = []
    if log_date is None or log_date > today:
        errors.append("אי אפשר לשמור תאריך עתידי.")
    if not str(session_name).strip():
        errors.append("צריך שם לאימון, למשל ״יום א — כל הגוף״.")
    elif len(str(session_name).strip()) > 60:
        errors.append("שם האימון ארוך מדי.")
    if not str(exercise).strip():
        errors.append("צריך שם לתרגיל.")
    elif len(str(exercise).strip()) > 60:
        errors.append("שם התרגיל ארוך מדי.")

    sets_n = _number(sets)
    reps_n = _number(reps)
    weight_n = _number(weight_kg)
    if sets_n is None or sets_n < 1 or sets_n > 10 or int(sets_n) != sets_n:
        errors.append("מספר הסטים צריך להיות מספר שלם בין 1 ל-10.")
    if reps_n is None or reps_n < 1 or reps_n > 50 or int(reps_n) != reps_n:
        errors.append("מספר החזרות צריך להיות מספר שלם בין 1 ל-50.")
    if weight_n is None or weight_n < 0 or weight_n > 300:
        errors.append("המשקל בתרגיל צריך להיות בין 0 ל-300 ק״ג. לתרגיל במשקל גוף אפשר לרשום 0.")
    if note and len(str(note)) > 200:
        errors.append("ההערה ארוכה מדי. עד 200 תווים.")
    return errors


def validate_nutrition_log(log_date, calories, protein_g, carbs_g, fat_g, note, today):
    """בודק רשומת תזונה יומית."""
    errors = []
    if log_date is None or log_date > today:
        errors.append("אי אפשר לשמור תאריך עתידי.")

    calories_n = _number(calories)
    protein_n = _number(protein_g)
    carbs_n = _number(carbs_g)
    fat_n = _number(fat_g)

    if calories_n is None or calories_n < 500 or calories_n > 6000:
        errors.append("הקלוריות ביומן צריכות להיות בין 500 ל-6000.")
    if protein_n is None or protein_n < 0 or protein_n > 400:
        errors.append("החלבון ביומן צריך להיות בין 0 ל-400 גרם.")
    if carbs_n is None or carbs_n < 0 or carbs_n > 800:
        errors.append("הפחמימות ביומן צריכות להיות בין 0 ל-800 גרם.")
    if fat_n is None or fat_n < 0 or fat_n > 300:
        errors.append("השומן ביומן צריך להיות בין 0 ל-300 גרם.")
    if note and len(str(note)) > 200:
        errors.append("ההערה ארוכה מדי. עד 200 תווים.")
    return errors
