import os
import json
from functools import wraps
from uuid import uuid4
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session


db = SQL("sqlite:///getfit.db")

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
os.makedirs(app.config["PROFILE_UPLOAD_FOLDER"], exist_ok=True)
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
    """Home page for the gym app."""
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page for the gym app."""
    return render_template("dash.html")


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


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session.get("user_id")
    if request.method == "POST":
        name = request.form.get("name")
        weight = request.form.get("weight")
        height = request.form.get("height")
        fitness_goal = request.form.get("fitness_goal")
        db.execute(
            "UPDATE users SET name = ?, weight = ?, height = ?, fitness_goal = ? WHERE id = ?",
            name,
            weight,
            height,
            fitness_goal,
            user_id,
        )
        return redirect("/profile")
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    records = db.execute("SELECT * FROM pr WHERE user_id = ? ORDER BY id LIMIT 1", user_id)
    prs = records[0] if records else {"bench": None, "squat": None, "deadlift": None}
    return render_template("prof.html", user=user[0], prs=prs)


# AI assistance: GitHub Copilot helped implement profile, PR, and picture-upload routes.
@app.route("/profile/pr", methods=["POST"])
@login_required
def update_pr():
    user_id = session.get("user_id")
    exercise = request.form.get("exercise")
    weight = request.form.get("weight", type=int)
    if exercise not in {"bench", "squat", "deadlift"} or weight is None or weight <= 0:
        return redirect("/profile")

    records = db.execute("SELECT id FROM pr WHERE user_id = ? ORDER BY id LIMIT 1", user_id)
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
