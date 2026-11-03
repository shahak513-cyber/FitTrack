"""ארבעת המסכים של FitTrack: פרופיל, תזונה, אימונים והתקדמות."""

from datetime import date

import pandas as pd
import streamlit as st

from fittrack.database import (
    add_workout,
    delete_nutrition,
    delete_weight,
    delete_workout,
    get_profile,
    list_nutrition,
    list_weights,
    list_workouts,
    save_profile,
    save_targets,
    update_profile_weight,
    upsert_nutrition,
    upsert_weight,
)
from fittrack.nutrition import TEMPLATES, build_meals, estimate_needs
from fittrack.validation import (
    macro_calorie_gap,
    validate_nutrition_log,
    validate_profile,
    validate_targets,
    validate_weight_log,
    validate_workout_log,
)
from fittrack.workouts import build_plan

SEX_LABELS = {"male": "זכר", "female": "נקבה"}
ACTIVITY_LABELS = {
    "sedentary": "יושבנית — מעט הליכה ביום",
    "light": "קלה — תנועה או אימון 1–3 פעמים בשבוע",
    "moderate": "בינונית — אימון 3–5 פעמים בשבוע",
    "active": "גבוהה — אימון כמעט כל יום",
    "very_active": "גבוהה מאוד — עבודה פיזית או שני אימונים ביום",
}
EXPERIENCE_LABELS = {
    "beginner": "מתחיל — פחות מחצי שנה",
    "intermediate": "יש ניסיון — יותר מחצי שנה",
}
GOAL_LABELS = {
    "fat_loss": "ירידה במשקל",
    "maintain": "שמירה על המשקל",
    "muscle_gain": "עלייה במסת שריר",
    "general": "כושר כללי",
}


def _show_errors(errors):
    for message in errors:
        st.error(message)


def _require_profile():
    profile = get_profile()
    if profile is None:
        st.warning("כדי להשתמש בעמוד הזה, קודם שומרים פרופיל בעמוד ״פרופיל״.")
        return None
    return profile


def _choice(label, options, labels, current):
    keys = list(options)
    index = keys.index(current) if current in keys else 0
    return st.selectbox(label, keys, index=index, format_func=lambda key: labels[key])


def page_profile():
    """טופס הפרופיל וסיכום הנתונים השמורים."""
    profile = get_profile()
    st.subheader("הפרופיל שלך")
    st.write(
        "הנתונים האלה משמשים להערכת הקלוריות ולבניית תוכנית האימון. "
        "אפשר לעדכן אותם בכל זמן."
    )

    form_key = "profile_new" if profile is None else f"profile_{profile['updated_at']}"
    with st.form(form_key):
        name = st.text_input("שם", value="" if profile is None else profile["name"])
        age_col, sex_col = st.columns(2)
        with age_col:
            age = st.number_input(
                "גיל",
                min_value=10,
                max_value=100,
                value=30 if profile is None else int(profile["age"]),
                step=1,
                help="הגרסה הזו מיועדת לגילאי 18 עד 80.",
            )
        with sex_col:
            sex = _choice(
                "מין לחישוב האנרגיה",
                SEX_LABELS,
                SEX_LABELS,
                None if profile is None else profile["sex"],
            )

        height_col, weight_col = st.columns(2)
        with height_col:
            height = st.number_input(
                "גובה (ס״מ)",
                min_value=100.0,
                max_value=250.0,
                value=170.0 if profile is None else float(profile["height_cm"]),
                step=0.5,
            )
        with weight_col:
            weight = st.number_input(
                "משקל (ק״ג)",
                min_value=30.0,
                max_value=250.0,
                value=70.0 if profile is None else float(profile["weight_kg"]),
                step=0.1,
            )

        activity = _choice(
            "רמת פעילות",
            ACTIVITY_LABELS,
            ACTIVITY_LABELS,
            None if profile is None else profile["activity"],
        )
        experience = _choice(
            "ניסיון באימונים",
            EXPERIENCE_LABELS,
            EXPERIENCE_LABELS,
            None if profile is None else profile["experience"],
        )
        goal_col, days_col = st.columns(2)
        with goal_col:
            goal = _choice(
                "מטרה",
                GOAL_LABELS,
                GOAL_LABELS,
                None if profile is None else profile["goal"],
            )
        with days_col:
            day_options = [2, 3, 4, 5]
            current_days = 3 if profile is None else int(profile["training_days"])
            training_days = st.selectbox(
                "כמה ימים בשבוע נוח לך להתאמן?",
                day_options,
                index=day_options.index(current_days) if current_days in day_options else 1,
            )

        remember_weight = st.checkbox("לרשום גם את המשקל הזה ביומן ההתקדמות של היום", value=True)
        acknowledged = st.checkbox(
            "אני מבוגר/ה בריא/ה, ומבין/ה שזו הערכה כללית ולא ייעוץ רפואי.",
            value=False if profile is None else bool(profile["acknowledged"]),
        )
        submitted = st.form_submit_button("שמירת פרופיל")

    if submitted:
        data = {
            "name": name,
            "age": age,
            "sex": sex,
            "height_cm": height,
            "weight_kg": weight,
            "activity": activity,
            "experience": experience,
            "goal": goal,
            "training_days": training_days,
            "acknowledged": acknowledged,
        }
        errors = validate_profile(data)
        if errors:
            _show_errors(errors)
        else:
            needs = estimate_needs(age, sex, height, weight, activity, goal)
            keep_custom = profile is not None and profile["targets_are_custom"]
            if keep_custom:
                data["calorie_target"] = profile["calorie_target"]
                data["protein_g"] = profile["protein_g"]
                data["carbs_g"] = profile["carbs_g"]
                data["fat_g"] = profile["fat_g"]
                data["targets_are_custom"] = True
            else:
                data["calorie_target"] = needs["calories"]
                data["protein_g"] = needs["protein_g"]
                data["carbs_g"] = needs["carbs_g"]
                data["fat_g"] = needs["fat_g"]
                data["targets_are_custom"] = False
            save_profile(data)
            if remember_weight:
                upsert_weight(date.today(), weight, "עודכן מתוך הפרופיל")
            st.success("הפרופיל נשמר במחשב הזה.")
            if keep_custom:
                st.info("יעדי התזונה שערכת ידנית נשארו כמו שהיו. אפשר לעדכן אותם בעמוד התזונה.")
            st.rerun()

    saved = get_profile()
    if saved:
        needs = estimate_needs(
            saved["age"],
            saved["sex"],
            saved["height_cm"],
            saved["weight_kg"],
            saved["activity"],
            saved["goal"],
        )
        st.markdown("### מה שמור עכשיו")
        first, second, third, fourth = st.columns(4)
        first.metric("מטרה", GOAL_LABELS[saved["goal"]])
        second.metric("ימי אימון", saved["training_days"])
        third.metric("הערכה להוצאה יומית", f"{needs['tdee']} קק״ל")
        fourth.metric("יעד קלורי שמור", f"{saved['calorie_target']} קק״ל")
        st.caption("הפירוט של הנוסחה והאפשרות לשנות יעדים נמצאים בעמוד התזונה.")


def _sync_target_inputs(profile):
    """מכניס לטופס את היעדים השמורים רק כשהפרופיל השתנה."""
    stamp = profile["updated_at"]
    if st.session_state.get("target_stamp") == stamp:
        return
    st.session_state.target_stamp = stamp
    st.session_state.calorie_target = int(profile["calorie_target"])
    st.session_state.protein_target = int(profile["protein_g"])
    st.session_state.carbs_target = int(profile["carbs_g"])
    st.session_state.fat_target = int(profile["fat_g"])


def page_nutrition():
    """מחשבון יעדים, עריכה ידנית, והצעת ארוחות."""
    profile = _require_profile()
    if profile is None:
        return

    needs = estimate_needs(
        profile["age"],
        profile["sex"],
        profile["height_cm"],
        profile["weight_kg"],
        profile["activity"],
        profile["goal"],
    )
    _sync_target_inputs(profile)

    st.subheader("מחשבון תזונה")
    st.write(
        "החישוב מתחיל מנוסחת Mifflin–St Jeor להערכת שריפה במנוחה, "
        "ואז מוסיף מקדם לפי רמת הפעילות. זו הערכה, לא בדיקה מדויקת."
    )

    bmr, tdee, suggested, factor = st.columns(4)
    bmr.metric("שריפה במנוחה (BMR)", f"{needs['bmr']}")
    tdee.metric("הוצאה יומית משוערת", f"{needs['tdee']}")
    suggested.metric("המלצת קלוריות", f"{needs['calories']}")
    factor.metric("מקדם פעילות", f"{needs['activity_factor']}")

    with st.expander("איך החישוב עובד?"):
        st.write(
            f"BMR משוער: {needs['bmr']} קלוריות ביום, לפני פעילות. "
            f"רמת הפעילות בפרופיל מכפילה את המספר ב-{needs['activity_factor']}, "
            f"ומתקבלת הוצאה יומית של בערך {needs['tdee']} קלוריות."
        )
        if profile["goal"] == "fat_loss":
            st.write("לירידה במשקל ההמלצה היא בערך 85% מההוצאה היומית, עם רף תחתון שמרני.")
        elif profile["goal"] == "muscle_gain":
            st.write("לעלייה במסת שריר ההמלצה היא בערך 110% מההוצאה היומית.")
        else:
            st.write("לשמירה על המשקל או לכושר כללי ההמלצה קרובה להוצאה היומית.")
        st.write(
            f"חלבון מומלץ: בערך {needs['protein_g']} גרם. "
            f"שומן: בערך {needs['fat_g']} גרם. "
            f"פחמימות: שאר הקלוריות, בערך {needs['carbs_g']} גרם."
        )

    st.markdown("### היעדים שלך")
    if profile["targets_are_custom"]:
        st.caption("היעדים האלה נערכו ידנית. ההמלצה המחושבת עדיין מופיעה למעלה.")
    else:
        st.caption("כרגע היעדים תואמים להמלצה המחושבת. אפשר לשנות אותם.")

    calorie_col, protein_col, carb_col, fat_col = st.columns(4)
    with calorie_col:
        calories = st.number_input("קלוריות", min_value=1200, max_value=4500, step=10, key="calorie_target")
    with protein_col:
        protein = st.number_input("חלבון (גרם)", min_value=40, max_value=250, step=1, key="protein_target")
    with carb_col:
        carbs = st.number_input("פחמימות (גרם)", min_value=50, max_value=600, step=1, key="carbs_target")
    with fat_col:
        fat = st.number_input("שומן (גרם)", min_value=25, max_value=180, step=1, key="fat_target")

    gap = macro_calorie_gap(calories, protein, carbs, fat)
    if abs(gap) >= 150:
        direction = "יותר" if gap > 0 else "פחות"
        st.warning(
            f"לפי גרמים של חלבון, פחמימות ושומן יוצאות בערך {int(calories) + gap} קלוריות, "
            f"כלומר {direction} מהיעד שהקלדת. אפשר לשמור בכל זאת."
        )

    save_col, reset_col = st.columns(2)
    with save_col:
        if st.button("שמירת היעדים"):
            errors = validate_targets(calories, protein, carbs, fat)
            if errors:
                _show_errors(errors)
            else:
                save_targets(calories, protein, carbs, fat, targets_are_custom=True)
                st.success("היעדים נשמרו.")
                st.rerun()
    with reset_col:
        if st.button("חזרה להמלצה המחושבת"):
            save_targets(
                needs["calories"],
                needs["protein_g"],
                needs["carbs_g"],
                needs["fat_g"],
                targets_are_custom=False,
            )
            st.success("היעדים חזרו להמלצה.")
            st.rerun()

    st.markdown("### הצעת ארוחות להיום")
    template_id = st.radio(
        "סגנון",
        list(TEMPLATES.keys()),
        format_func=lambda key: TEMPLATES[key]["title"],
        horizontal=True,
    )
    day = build_meals(template_id, int(calories), int(protein))
    total_col, protein_total, carb_total, fat_total = st.columns(4)
    total_col.metric("קלוריות בארוחות", day["kcal"])
    protein_total.metric("חלבון בארוחות", f"{day['protein']} ג׳")
    carb_total.metric("פחמימות בארוחות", f"{day['carbs']} ג׳")
    fat_total.metric("שומן בארוחות", f"{day['fat']} ג׳")

    for meal in day["meals"]:
        st.markdown(f"#### {meal['name']}")
        st.caption(f"בערך {meal['kcal']} קלוריות ו-{meal['protein']} גרם חלבון")
        table = pd.DataFrame(meal["items"])[["food", "grams", "kcal", "protein"]]
        table.columns = ["מזון", "כמות (גרם)", "קלוריות", "חלבון (גרם)"]
        st.dataframe(table, hide_index=True, use_container_width=True)

    for note in day["notes"]:
        st.info(note)


def page_workouts():
    """מציג תוכנית אימונים לפי הפרופיל."""
    profile = _require_profile()
    if profile is None:
        return

    st.subheader("תוכנית האימונים")
    st.write(
        f"התוכנית מותאמת למטרה ״{GOAL_LABELS[profile['goal']]}״, "
        f"לרמת הניסיון ״{EXPERIENCE_LABELS[profile['experience']]}״, "
        f"ול-{profile['training_days']} ימי אימון בשבוע."
    )
    st.caption("אפשר לבצע את האימונים בחדר כושר או בבית עם משקולות, ספסל או גומייה. בלי ציוד, בחרו את גרסת משקל הגוף שמופיעה בהסבר.")

    plan = build_plan(profile["goal"], profile["experience"], profile["training_days"])
    for note in plan["notes"]:
        st.markdown(f"- {note}")

    for day in plan["days"]:
        with st.container(border=True):
            st.markdown(f"### {day['title']}")
            st.caption(day["focus"])
            for exercise in day["exercises"]:
                st.markdown(f"**{exercise['name']}** — {exercise['sets']} סטים × {exercise['reps']}")
                st.write(exercise["tip"])


def _latest_first(rows):
    return list(reversed(rows))


def _delete_box(rows, label_builder, delete_function, button_label):
    if not rows:
        return
    recent = _latest_first(rows)[:20]
    labels = [label_builder(row) for row in recent]
    selected = st.selectbox("רשומה למחיקה", labels)
    if st.button(button_label):
        delete_function(recent[labels.index(selected)]["id"])
        st.rerun()


def page_progress():
    """יומן משקל, אימונים ותזונה, עם גרפים."""
    profile = _require_profile()
    if profile is None:
        return

    st.subheader("מעקב התקדמות")
    st.write("כל רשומה נשמרת במחשב. משקל ותזונה נשמרים פעם אחת לכל תאריך, ורשומה חדשה לאותו יום מחליפה את הקודמת.")

    weight_tab, workout_tab, food_tab = st.tabs(["משקל", "אימונים", "תזונה"])

    with weight_tab:
        _weight_section(profile)
    with workout_tab:
        _workout_section()
    with food_tab:
        _food_section(profile)


def _weight_section(profile):
    with st.form("weight_form"):
        log_day = st.date_input("תאריך", value=date.today(), max_value=date.today())
        weight = st.number_input("משקל (ק״ג)", min_value=35.0, max_value=220.0, value=float(profile["weight_kg"]), step=0.1)
        note = st.text_input("הערה", placeholder="למשל: בבוקר, לפני ארוחה")
        submitted = st.form_submit_button("שמירת משקל")
    if submitted:
        errors = validate_weight_log(log_day, weight, note, date.today())
        if errors:
            _show_errors(errors)
        else:
            upsert_weight(log_day, weight, note)
            st.success("המשקל נשמר.")
            st.rerun()

    rows = list_weights()
    if not rows:
        st.info("עדיין אין שקילות. אחרי השמירה הראשונה יופיע כאן גרף.")
        return

    first = rows[0]["weight_kg"]
    last = rows[-1]["weight_kg"]
    change = round(last - first, 1)
    sign = "+" if change > 0 else ""
    left, right = st.columns(2)
    left.metric("שקילה אחרונה", f"{last} ק״ג")
    right.metric("שינוי מאז הרשומה הראשונה", f"{sign}{change} ק״ג")

    frame = pd.DataFrame(rows)
    chart = frame.set_index("log_date")[["weight_kg"]]
    chart.columns = ["משקל (ק״ג)"]
    st.line_chart(chart, use_container_width=True)

    if st.button("לעדכן את המשקל גם בפרופיל לפי השקילה האחרונה"):
        update_profile_weight(last)
        st.success("המשקל בפרופיל עודכן. יעדי התזונה לא השתנו אוטומטית.")
        st.rerun()

    _delete_box(
        rows,
        lambda row: f"{row['log_date']} — {row['weight_kg']} ק״ג",
        delete_weight,
        "מחיקת השקילה שנבחרה",
    )


def _workout_section():
    with st.form("workout_form"):
        log_day = st.date_input("תאריך האימון", value=date.today(), max_value=date.today())
        session_name = st.text_input("שם האימון", placeholder="יום א׳ — כל הגוף")
        exercise = st.text_input("תרגיל", placeholder="סקוואט לגביע")
        sets_col, reps_col, weight_col = st.columns(3)
        with sets_col:
            sets = st.number_input("סטים", min_value=1, max_value=10, value=3, step=1)
        with reps_col:
            reps = st.number_input("חזרות בסט", min_value=1, max_value=50, value=10, step=1)
        with weight_col:
            lifted = st.number_input("משקל (ק״ג)", min_value=0.0, max_value=300.0, value=0.0, step=0.5)
        note = st.text_input("הערה לתרגיל", placeholder="הרגשה, קושי, או משהו לזכור")
        submitted = st.form_submit_button("הוספת התרגיל ליומן")

    if submitted:
        errors = validate_workout_log(
            log_day, session_name, exercise, sets, reps, lifted, note, date.today()
        )
        if errors:
            _show_errors(errors)
        else:
            add_workout(log_day, session_name, exercise, sets, reps, lifted, note)
            st.success("התרגיל נוסף ליומן.")
            st.rerun()

    rows = list_workouts()
    if not rows:
        st.info("עדיין אין אימונים ביומן. אפשר להעתיק תרגיל מעמוד האימונים ולרשום כמה סטים יצאו.")
        return

    totals = {}
    for row in rows:
        bucket = totals.setdefault(row["log_date"], {"reps": 0, "volume": 0.0})
        bucket["reps"] += row["sets"] * row["reps"]
        bucket["volume"] += row["sets"] * row["reps"] * row["weight_kg"]

    chart = pd.DataFrame(
        [{"תאריך": day, "חזרות כוללות": values["reps"]} for day, values in totals.items()]
    ).set_index("תאריך")
    st.markdown("**חזרות כוללות ביום**")
    st.caption("סכום של סטים כפול חזרות. זה עובד גם לתרגילי משקל גוף.")
    st.line_chart(chart, use_container_width=True)

    if any(values["volume"] > 0 for values in totals.values()):
        volume = pd.DataFrame(
            [{"תאריך": day, "נפח (ק״ג)": round(values["volume"], 1)} for day, values in totals.items()]
        ).set_index("תאריך")
        st.markdown("**נפח עם משקל**")
        st.caption("סטים × חזרות × משקל. תרגיל שסומן במשקל 0 לא מוסיף לנפח הזה.")
        st.line_chart(volume, use_container_width=True)

    preview = pd.DataFrame(_latest_first(rows)[:12])
    preview = preview[["log_date", "session_name", "exercise", "sets", "reps", "weight_kg"]]
    preview.columns = ["תאריך", "אימון", "תרגיל", "סטים", "חזרות", "משקל"]
    st.dataframe(preview, hide_index=True, use_container_width=True)
    _delete_box(
        rows,
        lambda row: f"{row['log_date']} — {row['exercise']} ({row['sets']}×{row['reps']})",
        delete_workout,
        "מחיקת התרגיל שנבחר",
    )


def _food_section(profile):
    with st.form("food_form"):
        log_day = st.date_input("תאריך", value=date.today(), max_value=date.today(), key="food_date")
        calories = st.number_input("קלוריות שאכלתי", min_value=0, max_value=6000, value=int(profile["calorie_target"]), step=10)
        protein_col, carb_col, fat_col = st.columns(3)
        with protein_col:
            protein = st.number_input("חלבון (גרם)", min_value=0, max_value=400, value=int(profile["protein_g"]), step=1)
        with carb_col:
            carbs = st.number_input("פחמימות (גרם)", min_value=0, max_value=800, value=int(profile["carbs_g"]), step=1)
        with fat_col:
            fat = st.number_input("שומן (גרם)", min_value=0, max_value=300, value=int(profile["fat_g"]), step=1)
        note = st.text_input("הערה", placeholder="למשל: ארוחת ערב מחוץ לבית")
        submitted = st.form_submit_button("שמירת היום")

    if submitted:
        errors = validate_nutrition_log(log_day, calories, protein, carbs, fat, note, date.today())
        if errors:
            _show_errors(errors)
        else:
            gap = macro_calorie_gap(calories, protein, carbs, fat)
            upsert_nutrition(log_day, calories, protein, carbs, fat, note)
            st.success("יום התזונה נשמר.")
            if abs(gap) >= 200:
                st.warning(
                    f"לפי המאקרו יוצאות בערך {int(calories) + gap} קלוריות, "
                    "והמספר ששמרת שונה מזה. שווה לבדוק את הסיכום."
                )
            st.rerun()

    rows = list_nutrition()
    if not rows:
        st.info("עדיין אין ימי תזונה. מספיק סיכום אחד ליום, לא צריך לרשום כל ארוחה.")
        return

    frame = pd.DataFrame(rows)
    chart = frame.set_index("log_date")[["calories", "protein_g"]].copy()
    chart["יעד קלוריות"] = int(profile["calorie_target"])
    chart.columns = ["קלוריות", "חלבון (גרם)", "יעד קלוריות"]
    st.line_chart(chart, use_container_width=True)
    st.caption("קו יעד הקלוריות הוא היעד השמור בפרופיל כרגע, גם לימים ישנים.")

    preview = pd.DataFrame(_latest_first(rows)[:12])
    preview = preview[["log_date", "calories", "protein_g", "carbs_g", "fat_g", "note"]]
    preview.columns = ["תאריך", "קלוריות", "חלבון", "פחמימות", "שומן", "הערה"]
    st.dataframe(preview, hide_index=True, use_container_width=True)
    _delete_box(
        rows,
        lambda row: f"{row['log_date']} — {row['calories']} קלוריות",
        delete_nutrition,
        "מחיקת היום שנבחר",
    )
