import os
import json
import math
from functools import wraps
from datetime import date, timedelta
from uuid import uuid4
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import random


with open("quotes.json", "r") as f:
    QUOTES = json.load(f)
def get_quote():
    today_str = date.today().isoformat()
    date_seed = int(today_str.replace("-", ""))
    rng = random.Random(date_seed)
    return rng.choice(QUOTES)


db = SQL("sqlite:///getfit.db")
db.execute(
    """CREATE TABLE IF NOT EXISTS weight_log (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           weight REAL NOT NULL CHECK (weight > 0),
           measured_on TEXT NOT NULL,
           recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
           UNIQUE (user_id, measured_on),
           FOREIGN KEY (user_id) REFERENCES users(id)
       )"""
)
db.execute(
    """INSERT INTO weight_log (user_id, weight, measured_on)
       SELECT id, CAST(weight AS REAL), date('now', 'localtime')
       FROM users
       WHERE weight IS NOT NULL AND CAST(weight AS REAL) > 0
         AND NOT EXISTS (
             SELECT 1 FROM weight_log WHERE weight_log.user_id = users.id
         )"""
)
db.execute(
    """CREATE TABLE IF NOT EXISTS workout_log (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           workout_name TEXT NOT NULL,
           notes TEXT,
           completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
           session_date TEXT,
           FOREIGN KEY (user_id) REFERENCES users(id)
       )"""
)
workout_log_columns = {
    row["name"] for row in db.execute("SELECT name FROM pragma_table_info('workout_log')")
}
if "session_date" not in workout_log_columns:
    db.execute("ALTER TABLE workout_log ADD COLUMN session_date TEXT")
db.execute(
    "UPDATE workout_log SET session_date = date(completed_at, 'localtime') WHERE session_date IS NULL"
)
db.execute(
    """CREATE TABLE IF NOT EXISTS exercise_log (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           session_id INTEGER NOT NULL,
           exercise_name TEXT NOT NULL,
           sets INTEGER NOT NULL,
           reps INTEGER NOT NULL,
           weight_kg REAL NOT NULL,
           FOREIGN KEY (session_id) REFERENCES workout_log(id)
       )"""
)
db.execute(
    """CREATE TABLE IF NOT EXISTS daily_nutrition (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           log_date TEXT NOT NULL,
           calories REAL NOT NULL,
           protein REAL,
           carbs REAL,
           fats REAL,
           UNIQUE (user_id, log_date),
           FOREIGN KEY (user_id) REFERENCES users(id)
       )"""
)
db.execute(
    """CREATE TABLE IF NOT EXISTS body_measurement_log (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           measured_on TEXT NOT NULL,
           body_fat REAL,
           chest REAL,
           waist REAL,
           arms REAL,
           thighs REAL,
           UNIQUE (user_id, measured_on),
           FOREIGN KEY (user_id) REFERENCES users(id)
       )"""
)
db.execute(
    """CREATE TABLE IF NOT EXISTS progress_photo (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           photo_date TEXT NOT NULL,
           filename TEXT NOT NULL,
           caption TEXT,
           FOREIGN KEY (user_id) REFERENCES users(id)
       )"""
)
db.execute(
    """CREATE TABLE IF NOT EXISTS pr_history (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           lift TEXT NOT NULL CHECK (lift IN ('bench', 'squat', 'deadlift')),
           weight_kg REAL NOT NULL,
           achieved_on TEXT NOT NULL,
           FOREIGN KEY (user_id) REFERENCES users(id)
       )"""
)
db.execute(
    """CREATE TABLE IF NOT EXISTS photo_memorial (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           before_filename TEXT NOT NULL,
           before_date TEXT NOT NULL,
           after_filename TEXT,
           after_date TEXT,
           FOREIGN KEY (user_id) REFERENCES users(id)
       )"""
)


def save_weight_reading(user_id, weight, measured_on=None):
    db.execute(
        """INSERT INTO weight_log (user_id, weight, measured_on)
           VALUES (?, ?, COALESCE(?, date('now', 'localtime')))
           ON CONFLICT(user_id, measured_on) DO UPDATE SET
               weight = excluded.weight,
               recorded_at = CURRENT_TIMESTAMP""",
        user_id,
        weight,
        measured_on,
    )


def parse_optional_number(form, field, label, minimum, maximum):
    raw_value = form.get(field, "").strip()
    if not raw_value:
        return None
    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"Enter a valid {label}.") from error
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{label.capitalize()} must be between {minimum:g} and {maximum:g}.")
    return value


def validate_progress_photo(upload):
    if upload is None or not upload.filename:
        raise ValueError("Choose a photo to upload.")

    extension = os.path.splitext(secure_filename(upload.filename))[1].lower()
    if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Upload a PNG, JPEG, or WebP photo.")

    header = upload.stream.read(12)
    upload.stream.seek(0)
    if extension == ".png":
        valid_image = header.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension in {".jpg", ".jpeg"}:
        valid_image = header.startswith(b"\xff\xd8\xff")
    else:
        valid_image = header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if not valid_image:
        raise ValueError("That file does not appear to be a valid image.")

    return f"{uuid4().hex}{extension}"


# AI assistance: GitHub Copilot helped structure the weekly workout programs.
WEEK_DAYS = (
    {"key": "monday", "name": "Monday"},
    {"key": "tuesday", "name": "Tuesday"},
    {"key": "wednesday", "name": "Wednesday"},
    {"key": "thursday", "name": "Thursday"},
    {"key": "friday", "name": "Friday"},
    {"key": "saturday", "name": "Saturday"},
    {"key": "sunday", "name": "Sunday"},
)

ROUTINE_STYLES = (
    {
        "key": "high_intensity",
        "label": "High Intensity",
        "guidance": "Compounds: 3-4 sets x 3-6 reps; accessories: 2-3 sets x 6-8 reps. Heavy, controlled loads (about 80-85% of estimated 1RM for compounds).",
    },
    {
        "key": "high_volume",
        "label": "High Volume",
        "guidance": "Compounds: 4 sets x 8-12 reps; accessories: 3-4 sets x 12-15 reps. Lighter, controlled loads (about 55-70% of estimated 1RM).",
    },
    {
        "key": "average",
        "label": "Average",
        "guidance": "Compounds: 3 sets x 6-10 reps; accessories: 3 sets x 8-12 reps. Moderate loads (about 65-75% of estimated 1RM).",
    },
)

PRESET_ROUTINES = (
    {
        "id": "push-pull-legs",
        "name": "Push / Pull / Legs",
        "description": "Six lifting days with one recovery day.",
        "days": (
            {"name": "Monday", "focus": "Push A", "exercises": ("Bench press", "Overhead press", "Incline dumbbell press", "Triceps pushdown")},
            {"name": "Tuesday", "focus": "Pull A", "exercises": ("Lat pulldown or pull-up", "Barbell row", "Face pull", "Biceps curl")},
            {"name": "Wednesday", "focus": "Legs A", "exercises": ("Barbell squat", "Romanian deadlift", "Leg press", "Calf raise")},
            {"name": "Thursday", "focus": "Push B", "exercises": ("Incline bench press", "Seated shoulder press", "Cable chest fly", "Lateral raise", "Overhead triceps extension")},
            {"name": "Friday", "focus": "Pull B", "exercises": ("Chest-supported row", "Single-arm pulldown", "Reverse fly", "Hammer curl")},
            {"name": "Saturday", "focus": "Legs B", "exercises": ("Deadlift", "Bulgarian split squat", "Hamstring curl", "Seated calf raise")},
            {"name": "Sunday", "focus": "Recovery", "rest": True, "exercises": ("Rest; optional easy walk and mobility")},
        ),
    },
    {
        "id": "upper-lower",
        "name": "Upper / Lower",
        "description": "Four lifting days, with recovery between sessions.",
        "days": (
            {"name": "Monday", "focus": "Upper A", "exercises": ("Bench press", "Barbell row", "Overhead press", "Lat pulldown", "Triceps pushdown")},
            {"name": "Tuesday", "focus": "Lower A", "exercises": ("Back squat", "Romanian deadlift", "Walking lunge", "Calf raise")},
            {"name": "Wednesday", "focus": "Recovery", "rest": True, "exercises": ("Rest; optional easy walk and mobility")},
            {"name": "Thursday", "focus": "Upper B", "exercises": ("Incline dumbbell press", "Chest-supported row", "Lateral raise", "Face pull", "Biceps curl")},
            {"name": "Friday", "focus": "Lower B", "exercises": ("Deadlift", "Front squat or goblet squat", "Hip thrust", "Hamstring curl")},
            {"name": "Saturday", "focus": "Optional Conditioning", "rest": True, "exercises": ("Optional easy cardio or mobility")},
            {"name": "Sunday", "focus": "Rest", "rest": True, "exercises": ("Rest and recover")},
        ),
    },
    {
        "id": "full-body",
        "name": "Full Body",
        "description": "Three lifting days, spaced through the week.",
        "days": (
            {"name": "Monday", "focus": "Full Body A", "exercises": ("Squat", "Bench press", "Seated row", "Romanian deadlift", "Plank")},
            {"name": "Tuesday", "focus": "Recovery", "rest": True, "exercises": ("Rest; optional easy walk and mobility")},
            {"name": "Wednesday", "focus": "Full Body B", "exercises": ("Deadlift", "Overhead press", "Lat pulldown", "Split squat", "Dead bug")},
            {"name": "Thursday", "focus": "Rest", "rest": True, "exercises": ("Rest and recover")},
            {"name": "Friday", "focus": "Full Body C", "exercises": ("Leg press", "Incline dumbbell press", "Chest-supported row", "Hip thrust", "Farmer carry")},
            {"name": "Saturday", "focus": "Optional Conditioning", "rest": True, "exercises": ("Optional easy cardio or mobility")},
            {"name": "Sunday", "focus": "Rest", "rest": True, "exercises": ("Rest and recover")},
        ),
    },
)

def login_required(f):
    """Protect routes that require an active user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["PROFILE_UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")
app.config["PROGRESS_UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads", "progress")
os.makedirs(app.config["PROFILE_UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PROGRESS_UPLOAD_FOLDER"], exist_ok=True)
Session(app)


@app.after_request
def after_request(response):
    """Ensure pages are not cached."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    daily_quote = get_quote()
    today = date.today().strftime("%A, %B %-d, %Y")
    return render_template("index.html", daily_quote=daily_quote, today=today)
    

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page for the gym app."""
    user_id = session.get("user_id")
    today = date.today()
    weight_period = request.args.get("weight_period", "month")
    if weight_period not in {"week", "month"}:
        weight_period = "month"
    weight_period_days = 7 if weight_period == "week" else 30
    weight_period_start = today - timedelta(days=weight_period_days - 1)
    workout_day_rows = db.execute(
          """SELECT session_date AS day, COUNT(*) AS sessions
           FROM workout_log
           WHERE user_id = ?
              GROUP BY session_date""",
        user_id,
    )
    sessions_by_day = {row["day"]: row["sessions"] for row in workout_day_rows}
    streak_day = today if today.isoformat() in sessions_by_day else today - timedelta(days=1)
    workout_streak = 0
    while streak_day.isoformat() in sessions_by_day:
        workout_streak += 1
        streak_day -= timedelta(days=1)

    activity_days = [
        {
            "label": (today - timedelta(days=offset)).isoformat(),
            "sessions": sessions_by_day.get((today - timedelta(days=offset)).isoformat(), 0),
        }
        for offset in range(27, -1, -1)
    ]
    active_days_count = sum(day["sessions"] > 0 for day in activity_days)
    monthly_sessions = db.execute(
        """SELECT COUNT(*) AS total FROM workout_log
           WHERE user_id = ?
                         AND strftime('%Y-%m', session_date) = strftime('%Y-%m', 'now', 'localtime')""",
        user_id,
    )[0]["total"]
    recent_rows = db.execute(
        """SELECT id, workout_name, notes, session_date AS completed_day
           FROM workout_log WHERE user_id = ?
           ORDER BY session_date DESC, completed_at DESC, id DESC LIMIT 5""",
        user_id,
    )
    recent_workouts = []
    for row in recent_rows:
        exercises = db.execute(
            "SELECT exercise_name, sets, reps, weight_kg FROM exercise_log WHERE session_id = ? ORDER BY id",
            row["id"],
        )
        exercise_details = [
            f"{exercise['exercise_name']} {exercise['sets']} x {exercise['reps']} @ {float(exercise['weight_kg']):g} kg"
            for exercise in exercises
        ]
        volume = sum(
            exercise["sets"] * exercise["reps"] * exercise["weight_kg"]
            for exercise in exercises
        )
        workout_day = date.fromisoformat(row["completed_day"])
        recent_workouts.append({
            "name": row["workout_name"],
            "details": " · ".join(exercise_details) or row["notes"] or "Workout completed",
            "date": f"{workout_day.strftime('%b')} {workout_day.day}",
            "volume": volume,
        })

    users = db.execute("SELECT weight FROM users WHERE id = ?", user_id)
    weight_rows = db.execute(
        """SELECT measured_on, weight FROM weight_log
           WHERE user_id = ?
             AND measured_on BETWEEN ? AND ?
           ORDER BY measured_on""",
        user_id,
        weight_period_start.isoformat(),
        today.isoformat(),
    )
    weight_readings = [
        {"date": date.fromisoformat(row["measured_on"]), "weight": float(row["weight"])}
        for row in weight_rows
    ]
    chart_start = weight_period_start
    chart_span = weight_period_days - 1
    chart_points = []
    chart_ticks = []
    chart_line = ""
    period_label = "last week" if weight_period == "week" else "last month"
    weight_change = f"Log another weigh-in to see your trend over the {period_label}"
    if weight_readings:
        min_weight = min(reading["weight"] for reading in weight_readings)
        max_weight = max(reading["weight"] for reading in weight_readings)
        padding = max((max_weight - min_weight) * 0.15, 0.5)
        axis_min = math.floor((min_weight - padding) * 2) / 2
        axis_max = math.ceil((max_weight + padding) * 2) / 2
        axis_range = axis_max - axis_min
        for index in range(4):
            value = axis_max - axis_range * index / 3
            chart_ticks.append({"y": 35 + index * 50, "label": f"{value:g} kg"})
        for reading in weight_readings:
            x = 48 + (reading["date"] - chart_start).days / chart_span * 636
            y = 35 + (axis_max - reading["weight"]) / axis_range * 150
            chart_points.append({
                "x": round(x, 1),
                "y": round(y, 1),
                "weight": reading["weight"],
                "label": f"{reading['date'].strftime('%b')} {reading['date'].day}",
            })
        chart_line = " ".join(f"{point['x']},{point['y']}" for point in chart_points)
        if len(weight_readings) > 1:
            delta = weight_readings[-1]["weight"] - weight_readings[0]["weight"]
            if delta > 0:
                weight_change = f"Up {delta:.1f} kg over the {period_label}"
            elif delta < 0:
                weight_change = f"Down {abs(delta):.1f} kg over the {period_label}"
            else:
                weight_change = f"No change over the {period_label}"

    chart_dates = [
        {
            "x": round(48 + offset / chart_span * 636, 1),
            "label": f"{(chart_start + timedelta(days=offset)).strftime('%b')} {(chart_start + timedelta(days=offset)).day}",
        }
        for offset in sorted({0, chart_span // 4, chart_span // 2, chart_span * 3 // 4, chart_span})
    ]
    records = db.execute(
        "SELECT bench, squat, deadlift FROM pr WHERE user_id = ? ORDER BY id LIMIT 1",
        user_id,
    )
    nutrition_goals = db.execute(
        "SELECT calories, maintain, protien, carbs, fats FROM nutrion WHERE user_id = ? ORDER BY rowid DESC LIMIT 1",
        user_id,
    )
    daily_nutrition_rows = db.execute(
        """SELECT calories, protein, carbs, fats FROM daily_nutrition
           WHERE user_id = ? AND log_date = date('now', 'localtime')""",
        user_id,
    )
    if daily_nutrition_rows:
        food_totals = daily_nutrition_rows[0]
    else:
        food_totals = db.execute(
            """SELECT COALESCE(SUM(calories), 0) AS calories,
                      COALESCE(SUM(protein), 0) AS protein,
                      COALESCE(SUM(carbs), 0) AS carbs,
                      COALESCE(SUM(fats), 0) AS fats
               FROM food_log
               WHERE user_id = ? AND date(logged_at) = date('now', 'localtime')""",
            user_id,
        )[0]
    measurement_rows = db.execute(
        "SELECT * FROM body_measurement_log WHERE user_id = ? ORDER BY measured_on",
        user_id,
    )
    body_measurement = measurement_rows[-1] if measurement_rows else {}
    measurement_fields = (
        ("body_fat", "Body fat", "%"),
        ("chest", "Chest", "cm"),
        ("waist", "Waist", "cm"),
        ("arms", "Arms", "cm"),
        ("thighs", "Thighs", "cm"),
    )
    measurement_charts = []
    for field, label, unit in measurement_fields:
        readings = [
            {"date": date.fromisoformat(row["measured_on"]), "value": float(row[field])}
            for row in measurement_rows
            if row[field] is not None
        ]
        if not readings:
            continue
        min_value = min(reading["value"] for reading in readings)
        max_value = max(reading["value"] for reading in readings)
        span_days = max((readings[-1]["date"] - readings[0]["date"]).days, 1)
        points = [
            {
                "x": round(8 + (reading["date"] - readings[0]["date"]).days / span_days * 164, 1),
                "y": round(
                    42 - ((reading["value"] - min_value) / (max_value - min_value) * 32)
                    if max_value != min_value else 26,
                    1,
                ),
                "value": reading["value"],
                "date": reading["date"].isoformat(),
            }
            for reading in readings
        ]
        measurement_charts.append({
            "name": label,
            "unit": unit,
            "latest": readings[-1]["value"],
            "latest_date": readings[-1]["date"].isoformat(),
            "min": min_value,
            "max": max_value,
            "points": points,
            "line": " ".join(f"{point['x']},{point['y']}" for point in points),
        })
    latest_body_fat = next(
        (chart["latest"] for chart in measurement_charts if chart["name"] == "Body fat"),
        None,
    )
    latest_body_fat_date = next(
        (chart["latest_date"] for chart in measurement_charts if chart["name"] == "Body fat"),
        None,
    )
    memorial_photos = db.execute(
        """SELECT id, before_filename, before_date, after_filename, after_date
           FROM photo_memorial WHERE user_id = ?
           ORDER BY before_date DESC, id DESC LIMIT 3""",
        user_id,
    )
    pr_history = db.execute(
        """SELECT lift, weight_kg, achieved_on FROM pr_history
           WHERE user_id = ? ORDER BY achieved_on DESC, id DESC LIMIT 5""",
        user_id,
    )

    current_weight = users[0]["weight"] if users else None
    pr_values = records[0] if records else {"bench": None, "squat": None, "deadlift": None}
    lift_labels = {"bench": "Bench press", "squat": "Squat", "deadlift": "Deadlift"}
    personal_records = [
        {"name": lift_labels[key], "weight": pr_values[key], "icon": key}
        for key in lift_labels
    ]
    saved_lifts = [record for record in personal_records if record["weight"] is not None]
    best_lift = max(saved_lifts, key=lambda record: record["weight"]) if saved_lifts else None

    goal = nutrition_goals[0] if nutrition_goals else {}
    calories_goal = goal.get("calories") or goal.get("maintain")
    macros = [
        {"name": "Protein", "value": food_totals["protein"] or 0, "goal": goal.get("protien"), "unit": "g", "class": "protein"},
        {"name": "Carbs", "value": food_totals["carbs"] or 0, "goal": goal.get("carbs"), "unit": "g", "class": "carbs"},
        {"name": "Fat", "value": food_totals["fats"] or 0, "goal": goal.get("fats"), "unit": "g", "class": "fat"},
    ]
    macros = [
        {**macro, "percent": min(100, round(macro["value"] * 100 / macro["goal"]))}
        for macro in macros
        if macro["goal"]
    ]
    calorie_percent = min(100, round(food_totals["calories"] * 100 / calories_goal)) if calories_goal else 0

    return render_template(
        "dash.html",
        current_weight=current_weight,
        weight_reading_count=len(weight_readings),
        weight_change=weight_change,
        weight_period=weight_period,
        weight_period_label="Last 7 days" if weight_period == "week" else "Last 30 days",
        weight_chart_points=chart_points,
        weight_chart_ticks=chart_ticks,
        weight_chart_line=chart_line,
        weight_chart_dates=chart_dates,
        body_fat=latest_body_fat,
        body_fat_date=latest_body_fat_date,
        measurement_charts=measurement_charts,
        measurements_date=body_measurement.get("measured_on"),
        memorial_photos=memorial_photos,
        pr_history=pr_history,
        personal_records=personal_records,
        best_lift=best_lift,
        food_totals=food_totals,
        calories_goal=calories_goal,
        calories_remaining=max(0, calories_goal - food_totals["calories"]) if calories_goal else None,
        calorie_percent=calorie_percent,
        macros=macros,
        workout_streak=workout_streak,
        monthly_sessions=monthly_sessions,
        activity_days=activity_days,
        active_days_count=active_days_count,
        recent_workouts=recent_workouts,
    )


@app.route("/dashboard/history")
@login_required
def dashboard_history():
    """Show dated training and calorie history."""
    user_id = session.get("user_id")
    today = date.today()
    period = request.args.get("period", "all")
    if period not in {"all", "week"}:
        period = "all"
    start_date = (today - timedelta(days=6)).isoformat() if period == "week" else None

    history_by_date = {}

    if start_date:
        session_rows = db.execute(
            """SELECT id, workout_name, notes, session_date, completed_at
               FROM workout_log
               WHERE user_id = ? AND session_date BETWEEN ? AND ?
               ORDER BY session_date DESC, completed_at DESC, id DESC""",
            user_id, start_date, today.isoformat(),
        )
        nutrition_rows = db.execute(
            """SELECT log_date AS entry_date, calories
               FROM daily_nutrition
               WHERE user_id = ? AND log_date BETWEEN ? AND ?
               ORDER BY log_date DESC""",
            user_id, start_date, today.isoformat(),
        )
        food_rows = db.execute(
            """SELECT date(logged_at) AS entry_date, SUM(calories) AS calories
               FROM food_log
               WHERE user_id = ? AND date(logged_at) BETWEEN ? AND ?
               GROUP BY date(logged_at)""",
            user_id, start_date, today.isoformat(),
        )
    else:
        session_rows = db.execute(
            """SELECT id, workout_name, notes, session_date, completed_at
               FROM workout_log
               WHERE user_id = ?
               ORDER BY session_date DESC, completed_at DESC, id DESC""",
            user_id,
        )
        nutrition_rows = db.execute(
            """SELECT log_date AS entry_date, calories
               FROM daily_nutrition WHERE user_id = ? ORDER BY log_date DESC""",
            user_id,
        )
        food_rows = db.execute(
            """SELECT date(logged_at) AS entry_date, SUM(calories) AS calories
               FROM food_log WHERE user_id = ?
               GROUP BY date(logged_at)""",
            user_id,
        )

    for row in food_rows:
        history_by_date.setdefault(row["entry_date"], {
            "date": row["entry_date"],
            "calories": row["calories"],
            "sessions": [],
        })
    for row in nutrition_rows:
        entry = history_by_date.setdefault(row["entry_date"], {
            "date": row["entry_date"],
            "calories": None,
            "sessions": [],
        })
        entry["calories"] = row["calories"]
    for row in session_rows:
        entry = history_by_date.setdefault(row["session_date"], {
            "date": row["session_date"],
            "calories": None,
            "sessions": [],
        })
        exercises = db.execute(
            """SELECT exercise_name, sets, reps FROM exercise_log
               WHERE session_id = ? ORDER BY id""",
            row["id"],
        )
        details = [
            f"{exercise['exercise_name']} · {exercise['sets']} sets × {exercise['reps']} reps"
            for exercise in exercises
        ]
        entry["sessions"].append({
            "name": row["workout_name"],
            "details": " · ".join(details) or row["notes"] or "Workout completed",
        })

    history = [
        history_by_date[entry_date]
        for entry_date in sorted(history_by_date, reverse=True)
    ]
    return render_template(
        "dashboard_history.html",
        history=history,
        period=period,
        start_date=start_date,
        end_date=today.isoformat() if start_date else None,
    )


@app.route("/dashboard/pr-history")
@login_required
def personal_record_history():
    """Show dated personal-record improvements."""
    records = db.execute(
        """SELECT lift, weight_kg, achieved_on FROM pr_history
           WHERE user_id = ? ORDER BY achieved_on DESC, id DESC""",
        session.get("user_id"),
    )
    lift_labels = {"bench": "Bench press", "squat": "Squat", "deadlift": "Deadlift"}
    return render_template(
        "pr_history.html",
        records=[
            {**record, "name": lift_labels[record["lift"]]}
            for record in records
        ],
    )


@app.route("/memorial", methods=["GET", "POST"])
@login_required
def photo_memorial():
    """Create and view before-and-after photo pairs."""
    user_id = session.get("user_id")
    if request.method == "POST":
        try:
            upload = request.files.get("before_photo")
            filename = validate_progress_photo(upload)
        except ValueError as error:
            flash(str(error))
            return redirect("/memorial")

        upload.save(os.path.join(app.config["PROGRESS_UPLOAD_FOLDER"], filename))
        db.execute(
            """INSERT INTO photo_memorial (user_id, before_filename, before_date)
               VALUES (?, ?, ?)""",
            user_id,
            filename,
            date.today().isoformat(),
        )
        flash("Before photo saved. Add the after photo whenever you are ready.")
        return redirect("/memorial")

    memorial_photos = db.execute(
        """SELECT id, before_filename, before_date, after_filename, after_date
           FROM photo_memorial WHERE user_id = ?
           ORDER BY before_date DESC, id DESC""",
        user_id,
    )
    return render_template("memorial.html", memorial_photos=memorial_photos)


@app.route("/memorial/<int:memorial_id>/after", methods=["POST"])
@login_required
def add_memorial_after_photo(memorial_id):
    """Add an after photo to one of the user's existing memorial entries."""
    user_id = session.get("user_id")
    entries = db.execute(
        """SELECT after_filename FROM photo_memorial
           WHERE id = ? AND user_id = ?""",
        memorial_id,
        user_id,
    )
    if not entries:
        flash("That memorial entry could not be found.")
        return redirect("/memorial")
    if entries[0]["after_filename"]:
        flash("An after photo has already been saved for this entry.")
        return redirect("/memorial")

    try:
        upload = request.files.get("after_photo")
        filename = validate_progress_photo(upload)
    except ValueError as error:
        flash(str(error))
        return redirect("/memorial")

    upload.save(os.path.join(app.config["PROGRESS_UPLOAD_FOLDER"], filename))
    db.execute(
        """UPDATE photo_memorial SET after_filename = ?, after_date = ?
           WHERE id = ? AND user_id = ? AND after_filename IS NULL""",
        filename,
        date.today().isoformat(),
        memorial_id,
        user_id,
    )
    flash("After photo saved.")
    return redirect("/memorial")


@app.route("/calorie-target", methods=["POST"])
@login_required
def set_calorie_target():
    """Update the signed-in user's daily calorie target."""
    user_id = session.get("user_id")
    target_input = request.form.get("calorie_target", "").strip()
    try:
        calorie_target = int(target_input)
    except ValueError:
        flash("Enter a whole-number daily calorie target.")
        return redirect("/dashboard")

    if not 1 <= calorie_target <= 20000:
        flash("Daily calorie target must be between 1 and 20,000 kcal.")
        return redirect("/dashboard")

    goal_rows = db.execute(
        "SELECT rowid FROM nutrion WHERE user_id = ? ORDER BY rowid DESC LIMIT 1",
        user_id,
    )
    if goal_rows:
        db.execute(
            "UPDATE nutrion SET calories = ? WHERE rowid = ?",
            calorie_target,
            goal_rows[0]["rowid"],
        )
    else:
        db.execute(
            "INSERT INTO nutrion (user_id, calories) VALUES (?, ?)",
            user_id,
            calorie_target,
        )

    flash("Daily calorie target saved.")
    return redirect("/dashboard")


@app.route("/calorie-intake", methods=["POST"])
@login_required
def update_calorie_intake():
    """Adjust or clear today's calorie total without losing macro totals."""
    action = request.form.get("action")
    if action not in {"adjust", "clear"}:
        flash("Choose whether to adjust or clear today's calorie intake.")
        return redirect("/dashboard")

    if action == "adjust":
        calories = request.form.get("calories", "").strip()
        try:
            calories = int(calories)
        except ValueError:
            flash("Enter a whole-number calorie intake.")
            return redirect("/dashboard")
        if not 0 <= calories <= 20000:
            flash("Calorie intake must be between 0 and 20,000 kcal.")
            return redirect("/dashboard")
    else:
        calories = 0

    user_id = session.get("user_id")
    nutrition_rows = db.execute(
        """SELECT protein, carbs, fats FROM daily_nutrition
           WHERE user_id = ? AND log_date = date('now', 'localtime')""",
        user_id,
    )
    if nutrition_rows:
        protein = nutrition_rows[0]["protein"] or 0
        carbs = nutrition_rows[0]["carbs"] or 0
        fats = nutrition_rows[0]["fats"] or 0
    else:
        food_totals = db.execute(
            """SELECT COALESCE(SUM(protein), 0) AS protein,
                      COALESCE(SUM(carbs), 0) AS carbs,
                      COALESCE(SUM(fats), 0) AS fats
               FROM food_log
               WHERE user_id = ? AND date(logged_at) = date('now', 'localtime')""",
            user_id,
        )[0]
        protein = food_totals["protein"]
        carbs = food_totals["carbs"]
        fats = food_totals["fats"]

    db.execute(
        """INSERT INTO daily_nutrition (user_id, log_date, calories, protein, carbs, fats)
           VALUES (?, date('now', 'localtime'), ?, ?, ?, ?)
           ON CONFLICT(user_id, log_date) DO UPDATE SET
               calories = excluded.calories,
               protein = excluded.protein,
               carbs = excluded.carbs,
               fats = excluded.fats""",
        user_id,
        calories,
        protein,
        carbs,
        fats,
    )

    flash("Today's calorie intake cleared." if action == "clear" else "Today's calorie intake updated.")
    return redirect("/dashboard")


@app.route("/track", methods=["GET", "POST"])
@login_required
def track_progress():
    """Record a dated training session and daily progress details."""
    user_id = session.get("user_id")
    today = date.today()

    if request.method == "GET":
        try:
            selected_day = date.fromisoformat(request.args.get("date", today.isoformat()))
        except ValueError:
            selected_day = today
        if selected_day > today:
            selected_day = today
        entry_date = selected_day.isoformat()
        nutrition_rows = db.execute(
            "SELECT * FROM daily_nutrition WHERE user_id = ? AND log_date = ?",
            user_id,
            entry_date,
        )
        measurement_rows = db.execute(
            "SELECT * FROM body_measurement_log WHERE user_id = ? AND measured_on = ?",
            user_id,
            entry_date,
        )
        weight_rows = db.execute(
            "SELECT weight FROM weight_log WHERE user_id = ? AND measured_on = ?",
            user_id,
            entry_date,
        )
        pr_rows = db.execute("SELECT * FROM pr WHERE user_id = ? ORDER BY id LIMIT 1", user_id)
        return render_template(
            "track.html",
            entry_date=entry_date,
            max_date=today.isoformat(),
            nutrition_entry=nutrition_rows[0] if nutrition_rows else {},
            measurement_entry=measurement_rows[0] if measurement_rows else {},
            weight_entry=weight_rows[0] if weight_rows else {},
            prs=pr_rows[0] if pr_rows else {"bench": None, "squat": None, "deadlift": None},
        )

    entry_date = request.form.get("entry_date", "").strip()
    try:
        selected_day = date.fromisoformat(entry_date)
        if selected_day > today:
            raise ValueError("Future dates cannot be logged.")

        workout_name = request.form.get("workout_name", "").strip()
        notes = request.form.get("session_notes", "").strip()
        if len(workout_name) > 80 or len(notes) > 500:
            raise ValueError("Session names must be under 80 characters and notes under 500.")

        exercise_names = request.form.getlist("exercise_name[]")
        exercise_sets = request.form.getlist("exercise_sets[]")
        exercise_reps = request.form.getlist("exercise_reps[]")
        exercise_weights = request.form.getlist("exercise_weight[]")
        if max(map(len, (exercise_names, exercise_sets, exercise_reps, exercise_weights)), default=0) > 15:
            raise ValueError("Log no more than 15 exercises in one session.")
        exercises = []
        row_count = max(map(len, (exercise_names, exercise_sets, exercise_reps, exercise_weights)), default=0)
        for index in range(row_count):
            values = [
                fields[index].strip() if index < len(fields) else ""
                for fields in (exercise_names, exercise_sets, exercise_reps, exercise_weights)
            ]
            if not any(values):
                continue
            name, sets_raw, reps_raw, weight_raw = values
            if not all(values) or len(name) > 100:
                raise ValueError("Complete each exercise name, set, rep, and weight field.")
            try:
                sets = int(sets_raw)
                reps = int(reps_raw)
            except ValueError as error:
                raise ValueError("Sets and reps must be whole numbers.") from error
            if not 1 <= sets <= 100 or not 1 <= reps <= 100:
                raise ValueError("Sets and reps must be between 1 and 100.")
            weight = parse_optional_number(
                {"weight": weight_raw}, "weight", "lifted weight", 0, 1000
            )
            exercises.append({"name": name, "sets": sets, "reps": reps, "weight": weight})
        if exercises and not workout_name:
            raise ValueError("Add a training session name for these exercises.")
        if notes and not workout_name:
            raise ValueError("Add a training session name for these notes.")

        nutrition_values = {
            "calories": parse_optional_number(request.form, "calories", "calories", 0, 20000),
            "protein": parse_optional_number(request.form, "protein", "protein", 0, 2000),
            "carbs": parse_optional_number(request.form, "carbs", "carbohydrates", 0, 2000),
            "fats": parse_optional_number(request.form, "fats", "fat", 0, 1000),
        }
        nutrition_entered = any(value is not None for value in nutrition_values.values())
        if nutrition_entered and nutrition_values["calories"] is None:
            raise ValueError("Enter calories when logging daily nutrition.")

        body_values = {
            "body_fat": parse_optional_number(request.form, "body_fat", "body-fat percentage", 0, 100),
            "chest": parse_optional_number(request.form, "chest", "chest measurement", 0, 500),
            "waist": parse_optional_number(request.form, "waist", "waist measurement", 0, 500),
            "arms": parse_optional_number(request.form, "arms", "arm measurement", 0, 500),
            "thighs": parse_optional_number(request.form, "thighs", "thigh measurement", 0, 500),
        }
        weight = parse_optional_number(request.form, "body_weight", "body weight", 1, 1000)
        measurements_entered = any(value is not None for value in body_values.values())

        pr_exercise = request.form.get("pr_exercise", "").strip()
        pr_weight = parse_optional_number(request.form, "pr_weight", "personal record", 1, 1000)
        if pr_exercise and pr_exercise not in {"bench", "squat", "deadlift"}:
            raise ValueError("Choose a valid lift for the personal record.")
        if bool(pr_exercise) != (pr_weight is not None):
            raise ValueError("Choose a lift and enter its new personal-record weight.")

        has_training = bool(workout_name or exercises)
        if not any((has_training, nutrition_entered, measurements_entered, weight is not None, pr_exercise)):
            raise ValueError("Add at least one progress entry before saving.")
    except ValueError as error:
        flash(str(error))
        return redirect(f"/track?date={entry_date or today.isoformat()}")

    if has_training:
        session_id = db.execute(
            "INSERT INTO workout_log (user_id, workout_name, notes, session_date) VALUES (?, ?, ?, ?)",
            user_id,
            workout_name,
            notes or None,
            entry_date,
        )
        for exercise in exercises:
            db.execute(
                "INSERT INTO exercise_log (session_id, exercise_name, sets, reps, weight_kg) VALUES (?, ?, ?, ?, ?)",
                session_id,
                exercise["name"],
                exercise["sets"],
                exercise["reps"],
                exercise["weight"],
            )

    if nutrition_entered:
        db.execute(
            """INSERT INTO daily_nutrition (user_id, log_date, calories, protein, carbs, fats)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, log_date) DO UPDATE SET
                   calories = excluded.calories, protein = excluded.protein,
                   carbs = excluded.carbs, fats = excluded.fats""",
            user_id,
            entry_date,
            nutrition_values["calories"],
            nutrition_values["protein"],
            nutrition_values["carbs"],
            nutrition_values["fats"],
        )

    if measurements_entered:
        db.execute(
            """INSERT INTO body_measurement_log
                   (user_id, measured_on, body_fat, chest, waist, arms, thighs)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, measured_on) DO UPDATE SET
                   body_fat = excluded.body_fat, chest = excluded.chest,
                   waist = excluded.waist, arms = excluded.arms, thighs = excluded.thighs""",
            user_id,
            entry_date,
            body_values["body_fat"],
            body_values["chest"],
            body_values["waist"],
            body_values["arms"],
            body_values["thighs"],
        )

    if weight is not None:
        save_weight_reading(user_id, weight, entry_date)
        latest_weight = db.execute(
            "SELECT weight, measured_on FROM weight_log WHERE user_id = ? ORDER BY measured_on DESC LIMIT 1",
            user_id,
        )[0]
        if latest_weight["measured_on"] <= entry_date:
            db.execute("UPDATE users SET weight = ? WHERE id = ?", weight, user_id)

    pr_updated = False
    if pr_exercise:
        pr_rows = db.execute(
            "SELECT id, bench, squat, deadlift FROM pr WHERE user_id = ? ORDER BY id LIMIT 1",
            user_id,
        )
        if pr_rows:
            if pr_rows[0][pr_exercise] is None or pr_weight > pr_rows[0][pr_exercise]:
                db.execute(
                    f"UPDATE pr SET {pr_exercise} = ? WHERE id = ?",
                    pr_weight,
                    pr_rows[0]["id"],
                )
                pr_updated = True
        else:
            values = {"bench": None, "squat": None, "deadlift": None}
            values[pr_exercise] = pr_weight
            db.execute(
                "INSERT INTO pr (user_id, bench, squat, deadlift) VALUES (?, ?, ?, ?)",
                user_id,
                values["bench"],
                values["squat"],
                values["deadlift"],
            )
            pr_updated = True
        if pr_updated:
            db.execute(
                """INSERT INTO pr_history (user_id, lift, weight_kg, achieved_on)
                   VALUES (?, ?, ?, ?)""",
                user_id,
                pr_exercise,
                pr_weight,
                entry_date,
            )

    flash("Daily progress saved." if not pr_exercise or pr_updated else "Progress saved. The saved personal record is already higher.")
    return redirect(f"/track?date={entry_date}")


@app.route("/nutrition")
@login_required
def nutrition():
    """Nutrition page placeholder."""
    return render_template("nut.html")


@app.route("/workouts", methods=["GET", "POST"])
@login_required
def workouts():
    """Display preset and user-created workout routines."""
    user_id = session.get("user_id")
    if request.method == "POST":
        routine_name = request.form.get("routine_name", "").strip()
        schedule = {
            day["key"]: {
                style["key"]: request.form.get(f"{day['key']}_{style['key']}", "").strip()
                for style in ROUTINE_STYLES
            }
            for day in WEEK_DAYS
        }
        has_details = any(value for day in schedule.values() for value in day.values())
        if not routine_name or len(routine_name) > 80 or not has_details:
            flash("Enter a routine name and details for at least one day and training style.")
            return redirect("/workouts")
        db.execute(
            "INSERT INTO workout (user_id, workout_name, details) VALUES (?, ?, ?)",
            user_id,
            routine_name,
            json.dumps(schedule),
        )
        flash("Routine added.")
        return redirect("/workouts")

    saved_routines = db.execute(
        "SELECT id, workout_name, details FROM workout WHERE user_id = ? ORDER BY id DESC",
        user_id,
    )
    routines = []
    for routine in saved_routines:
        try:
            schedule = json.loads(routine["details"] or "{}")
        except (TypeError, json.JSONDecodeError):
            schedule = {"monday": {"average": routine["details"] or ""}}
        if not isinstance(schedule, dict):
            schedule = {}
        days = []
        for day in WEEK_DAYS:
            day_schedule = schedule.get(day["key"], {})
            if not isinstance(day_schedule, dict):
                day_schedule = {}
            days.append({
                "name": day["name"],
                "variants": {
                    style["key"]: day_schedule.get(style["key"], "")
                    for style in ROUTINE_STYLES
                },
            })
        routines.append({
            "id": f"custom-{routine['id']}",
            "name": routine["workout_name"],
            "days": days,
            "is_custom": True,
        })
    return render_template(
        "work.html",
        preset_routines=PRESET_ROUTINES,
        custom_routines=routines,
        week_days=WEEK_DAYS,
        routine_styles=ROUTINE_STYLES,
    )


@app.route("/workouts/log", methods=["POST"])
@login_required
def log_workout():
    """Record a completed workout for the signed-in user."""
    workout_name = request.form.get("workout_name", "").strip()
    notes = request.form.get("notes", "").strip()
    if not workout_name or len(workout_name) > 80 or len(notes) > 500:
        flash("Enter a workout name up to 80 characters and notes up to 500 characters.")
        return redirect("/workouts")

    db.execute(
        "INSERT INTO workout_log (user_id, workout_name, notes, session_date) VALUES (?, ?, ?, date('now', 'localtime'))",
        session.get("user_id"),
        workout_name,
        notes or None,
    )
    flash("Workout session logged.")
    return redirect("/workouts")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session.get("user_id")
    if request.method == "POST":
        name = request.form.get("name")
        weight_input = request.form.get("weight", "").strip()
        try:
            weight = float(weight_input) if weight_input else None
        except ValueError:
            flash("Enter a valid weight in kilograms.")
            return redirect("/profile")
        if weight is not None and not 0 < weight <= 1000:
            flash("Weight must be between 0 and 1,000 kg.")
            return redirect("/profile")
        height = request.form.get("height")
        fitness_goal = request.form.get("fitness_goal")
        previous_weight = db.execute(
            "SELECT weight FROM users WHERE id = ?", user_id
        )[0]["weight"]
        db.execute(
            "UPDATE users SET name = ?, weight = ?, height = ?, fitness_goal = ? WHERE id = ?",
            name,
            weight,
            height,
            fitness_goal,
            user_id,
        )
        if weight is not None and previous_weight != weight:
            save_weight_reading(user_id, weight)
        return redirect("/profile")
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    records = db.execute("SELECT * FROM pr WHERE user_id = ? ORDER BY id LIMIT 1", user_id)
    prs = records[0] if records else {"bench": None, "squat": None, "deadlift": None}
    nutrition_goals = db.execute(
        "SELECT calories, maintain FROM nutrion WHERE user_id = ? ORDER BY rowid DESC LIMIT 1",
        user_id,
    )
    goal = nutrition_goals[0] if nutrition_goals else {}
    calories_goal = goal.get("calories") or goal.get("maintain")

    workout_days = db.execute(
        "SELECT DISTINCT session_date FROM workout_log WHERE user_id = ?",
        user_id,
    )
    sessions_by_day = {row["session_date"] for row in workout_days}
    streak_day = date.today()
    if streak_day.isoformat() not in sessions_by_day:
        streak_day -= timedelta(days=1)
    workout_streak = 0
    while streak_day.isoformat() in sessions_by_day:
        workout_streak += 1
        streak_day -= timedelta(days=1)

    return render_template(
        "prof.html",
        user=user[0],
        prs=prs,
        calories_goal=calories_goal,
        workout_streak=workout_streak,
    )


@app.route("/profile/weight", methods=["POST"])
@login_required
def log_weight():
    """Save today's weigh-in and update the user's current profile weight."""
    weight = request.form.get("weight", type=float)
    if weight is None or not 0 < weight <= 1000:
        flash("Enter a weight between 0 and 1,000 kg.")
        return redirect("/profile")

    user_id = session.get("user_id")
    db.execute("UPDATE users SET weight = ? WHERE id = ?", weight, user_id)
    save_weight_reading(user_id, weight)
    flash("Today's weigh-in was recorded.")
    return redirect("/profile")


# AI assistance: GitHub Copilot helped implement profile, PR, and picture-upload routes.
@app.route("/profile/pr", methods=["POST"])
@login_required
def update_pr():
    user_id = session.get("user_id")
    exercise = request.form.get("exercise")
    weight = request.form.get("weight", type=int)
    if exercise not in {"bench", "squat", "deadlift"} or weight is None or weight <= 0:
        return redirect("/profile")

    records = db.execute(
        "SELECT id, bench, squat, deadlift FROM pr WHERE user_id = ? ORDER BY id LIMIT 1",
        user_id,
    )
    if records:
        db.execute(f"UPDATE pr SET {exercise} = ? WHERE id = ?", weight, records[0]["id"])
    else:
        values = {"bench": None, "squat": None, "deadlift": None}
        values[exercise] = weight
        db.execute(
            "INSERT INTO pr (user_id, bench, squat, deadlift) VALUES (?, ?, ?, ?)",
            user_id,
            values["bench"],
            values["squat"],
            values["deadlift"],
        )
    db.execute(
        """INSERT INTO pr_history (user_id, lift, weight_kg, achieved_on)
           VALUES (?, ?, ?, ?)""",
        user_id,
        exercise,
        weight,
        date.today().isoformat(),
    )
    return redirect("/profile")


@app.route("/profile/picture", methods=["POST"])
@login_required
def upload_profile_picture():
    upload = request.files.get("profile_picture")
    if not upload or not upload.filename:
        flash("Choose a profile picture to upload.")
        return redirect("/profile")

    extension = os.path.splitext(secure_filename(upload.filename))[1].lower()
    if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
        flash("Upload a PNG, JPEG, or WebP image.")
        return redirect("/profile")

    header = upload.stream.read(12)
    upload.stream.seek(0)
    if extension == ".png":
        valid_image = header.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension in {".jpg", ".jpeg"}:
        valid_image = header.startswith(b"\xff\xd8\xff")
    else:
        valid_image = header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if not valid_image:
        flash("That file does not appear to be a valid image.")
        return redirect("/profile")

    filename = f"{uuid4().hex}{extension}"
    upload.save(os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename))

    user_id = session.get("user_id")
    user = db.execute("SELECT profile_picture FROM users WHERE id = ?", user_id)[0]
    db.execute("UPDATE users SET profile_picture = ? WHERE id = ?", filename, user_id)
    old_picture = user["profile_picture"]
    if old_picture and os.path.basename(old_picture) == old_picture:
        old_path = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], old_picture)
        if os.path.isfile(old_path):
            os.remove(old_path)

    flash("Profile picture updated.")
    return redirect("/profile")


@app.route("/login", methods=["GET", "POST"])
def login():
    #login a user.
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) == 1 and check_password_hash(rows[0]["password_hash"], password):
            session["user_id"] = rows[0]["id"]
        # return redirect("/")
        return redirect("/")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    #register a user.
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return render_template("register.html", error="Passwords do not match.")
        if not username or not password:
            return render_template("register.html", error="Username and password are required.")
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", username, generate_password_hash(password))
        return redirect("/login")

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log the user out."""
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
