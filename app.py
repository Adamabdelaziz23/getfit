import os
from functools import wraps

from flask import Flask, redirect, render_template, request, session
from flask_session import Session

# Example database setup if you want to add it later:
# from cs50 import SQL
# from werkzeug.security import check_password_hash, generate_password_hash
# db = SQL("sqlite:///your_database.db")


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


@app.route("/profile")
@login_required
def profile():
    """Profile page placeholder."""
    return render_template("prof.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log the user in.

    Pseudocode:
    - if POST:
        - get username and password from request.form
        - query the database for that user
        - check password hash
        - if valid: session["user_id"] = user_id
        - redirect to /
    - else:
        - render login.html
    """
    if request.method == "POST":
        # username = request.form.get("username")
        # password = request.form.get("password")
        # rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        # if valid user and password matches: session["user_id"] = rows[0]["id"]
        # return redirect("/")
        return redirect("/")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a user.

    Pseudocode only for now:
    - validate username and password
    - hash the password
    - insert into users table
    - redirect to /login
    """
    if request.method == "POST":
        # username = request.form.get("username")
        # password = request.form.get("password")
        # confirmation = request.form.get("confirmation")
        # db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))
        return redirect("/login")

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log the user out."""
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
