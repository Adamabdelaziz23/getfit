import os
from functools import wraps
from uuid import uuid4
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session


db = SQL("sqlite:///getfit.db")

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


@app.route("/nutrition")
@login_required
def nutrition():
    """Nutrition page placeholder."""
    return render_template("nut.html")


@app.route("/workouts")
@login_required
def workouts():
    """Workout page placeholder."""
    return render_template("work.html")


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
