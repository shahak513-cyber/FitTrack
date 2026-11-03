"""שמירה וטעינה של הנתונים בקובץ SQLite מקומי.

הקובץ נוצר אוטומטית בתיקייה data/fittrack.db.
אין שרת ואין חשבון: כל המידע נשאר במחשב הזה.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# parents[1] הוא תיקיית הפרויקט, כי הקובץ נמצא בתוך fittrack/.
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "fittrack.db"


def connect():
    """פותח חיבור קצר למסד. כל פעולה פותחת וסוגרת חיבור בעצמה."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """יוצר את הטבלאות בפעם הראשונה. אם הן כבר קיימות, לא קורה כלום."""
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                sex TEXT NOT NULL,
                height_cm REAL NOT NULL,
                weight_kg REAL NOT NULL,
                activity TEXT NOT NULL,
                experience TEXT NOT NULL,
                goal TEXT NOT NULL,
                training_days INTEGER NOT NULL,
                calorie_target INTEGER NOT NULL,
                protein_g INTEGER NOT NULL,
                carbs_g INTEGER NOT NULL,
                fat_g INTEGER NOT NULL,
                targets_are_custom INTEGER NOT NULL DEFAULT 0,
                acknowledged INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weight_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date TEXT NOT NULL UNIQUE,
                weight_kg REAL NOT NULL,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS workout_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date TEXT NOT NULL,
                session_name TEXT NOT NULL,
                exercise TEXT NOT NULL,
                sets INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                weight_kg REAL NOT NULL,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS nutrition_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date TEXT NOT NULL UNIQUE,
                calories INTEGER NOT NULL,
                protein_g INTEGER NOT NULL,
                carbs_g INTEGER NOT NULL,
                fat_g INTEGER NOT NULL,
                note TEXT
            );
            """
        )


def _now():
    return datetime.now().isoformat(timespec="seconds")


def get_profile():
    """מחזיר את הפרופיל היחיד, או None אם עדיין לא נשמר פרופיל."""
    with connect() as connection:
        row = connection.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        return None
    return dict(row)


def save_profile(data):
    """שומר פרופיל אחד. שמירה חדשה מחליפה את הקודמת."""
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO profile (
                id, name, age, sex, height_cm, weight_kg, activity, experience,
                goal, training_days, calorie_target, protein_g, carbs_g, fat_g,
                targets_are_custom, acknowledged, updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                age = excluded.age,
                sex = excluded.sex,
                height_cm = excluded.height_cm,
                weight_kg = excluded.weight_kg,
                activity = excluded.activity,
                experience = excluded.experience,
                goal = excluded.goal,
                training_days = excluded.training_days,
                calorie_target = excluded.calorie_target,
                protein_g = excluded.protein_g,
                carbs_g = excluded.carbs_g,
                fat_g = excluded.fat_g,
                targets_are_custom = excluded.targets_are_custom,
                acknowledged = excluded.acknowledged,
                updated_at = excluded.updated_at
            """,
            (
                data["name"].strip(),
                int(data["age"]),
                data["sex"],
                round(float(data["height_cm"]), 1),
                round(float(data["weight_kg"]), 1),
                data["activity"],
                data["experience"],
                data["goal"],
                int(data["training_days"]),
                int(round(float(data["calorie_target"]))),
                int(round(float(data["protein_g"]))),
                int(round(float(data["carbs_g"]))),
                int(round(float(data["fat_g"]))),
                1 if data.get("targets_are_custom") else 0,
                1 if data.get("acknowledged") else 0,
                _now(),
            ),
        )


def update_profile_weight(weight_kg):
    """מעדכן רק את המשקל בפרופיל, בלי למחוק יעדים שנערכו ידנית."""
    with connect() as connection:
        connection.execute(
            "UPDATE profile SET weight_kg = ?, updated_at = ? WHERE id = 1",
            (round(float(weight_kg), 1), _now()),
        )


def save_targets(calories, protein_g, carbs_g, fat_g, targets_are_custom):
    """מעדכן את יעדי התזונה שבפרופיל."""
    with connect() as connection:
        connection.execute(
            """
            UPDATE profile
            SET calorie_target = ?, protein_g = ?, carbs_g = ?, fat_g = ?,
                targets_are_custom = ?, updated_at = ?
            WHERE id = 1
            """,
            (
                int(round(float(calories))),
                int(round(float(protein_g))),
                int(round(float(carbs_g))),
                int(round(float(fat_g))),
                1 if targets_are_custom else 0,
                _now(),
            ),
        )


def upsert_weight(log_date, weight_kg, note):
    """שומר משקל ליום. אם כבר יש רשומה לאותו יום, היא מתעדכנת."""
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO weight_logs (log_date, weight_kg, note)
            VALUES (?, ?, ?)
            ON CONFLICT(log_date) DO UPDATE SET
                weight_kg = excluded.weight_kg,
                note = excluded.note
            """,
            (log_date.isoformat(), round(float(weight_kg), 1), (note or "").strip()),
        )


def list_weights():
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM weight_logs ORDER BY log_date ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_weight(row_id):
    with connect() as connection:
        connection.execute("DELETE FROM weight_logs WHERE id = ?", (int(row_id),))


def add_workout(log_date, session_name, exercise, sets, reps, weight_kg, note):
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO workout_logs
                (log_date, session_name, exercise, sets, reps, weight_kg, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_date.isoformat(),
                session_name.strip(),
                exercise.strip(),
                int(sets),
                int(reps),
                round(float(weight_kg), 1),
                (note or "").strip(),
            ),
        )


def list_workouts():
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM workout_logs ORDER BY log_date ASC, id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_workout(row_id):
    with connect() as connection:
        connection.execute("DELETE FROM workout_logs WHERE id = ?", (int(row_id),))


def upsert_nutrition(log_date, calories, protein_g, carbs_g, fat_g, note):
    """שומר סיכום תזונה ליום. יום קיים מתעדכן במקום להכפיל רשומות."""
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO nutrition_logs
                (log_date, calories, protein_g, carbs_g, fat_g, note)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(log_date) DO UPDATE SET
                calories = excluded.calories,
                protein_g = excluded.protein_g,
                carbs_g = excluded.carbs_g,
                fat_g = excluded.fat_g,
                note = excluded.note
            """,
            (
                log_date.isoformat(),
                int(round(float(calories))),
                int(round(float(protein_g))),
                int(round(float(carbs_g))),
                int(round(float(fat_g))),
                (note or "").strip(),
            ),
        )


def list_nutrition():
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM nutrition_logs ORDER BY log_date ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_nutrition(row_id):
    with connect() as connection:
        connection.execute("DELETE FROM nutrition_logs WHERE id = ?", (int(row_id),))
