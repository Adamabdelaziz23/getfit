GETFIT
======

README prototype
----------------
This short guide describes what GetFit helps users do, how its main features
work, and how to run the app locally. Keep it current as the project changes.

About
-----
GetFit is a Flask fitness-tracking app backed by SQLite. It brings workout
planning, strength records, profile details, and nutrition estimates together
so users can review their training and stay focused on their goals.

Features
--------
- Accounts: Register and log in with hashed passwords. A session keeps each
  user's pages private while they use the app.
- Home: Provides a starting point for the main fitness tools and helps users
  navigate to workouts, nutrition, and their profile.
- Profile: Lets users update their name, height, weight, and fitness goal, and
  upload a profile picture to personalize their account.
- Personal records: Stores bench press, squat, and deadlift bests per user so
  strength gains can be recorded and revisited.
- Workouts: Offers preset weekly programs and lets users build their own
  seven-day routine. Training-style options help users choose how to approach
  each day's exercises. A rest timer supports recovery between sets.
- Nutrition: Estimates calorie targets for weight loss, maintenance, or muscle
  gain. Protein and remaining macro targets are calculated from body weight
  and calorie needs to give users a practical daily guide.
- Progress dashboard: Brings weight and strength trends, workout activity,
  body measurements, a photo comparison, and nutrition goals into one view.
  Current dashboard numbers and charts are sample presentation data; they are
  not connected to saved user records.

Technology and files
--------------------
- Python, Flask, Flask-Session, SQLite, and the CS50 SQL library power the
  application and its user-specific data.
- Bootstrap 5, Jinja templates, CSS, and JavaScript provide the interface.
- app.py contains the routes, login protection, and application behavior.
- templates/ contains the pages; dash.html is the progress dashboard.
- static/ contains styles, scripts, and uploaded profile pictures.
- sql.txt documents the database schema and migration steps.
- getfit.db is the local database. Do not commit it if it contains personal
  account data.

Run locally
-----------
From the project directory, create a virtual environment and install the
dependencies:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install Flask Flask-Session cs50

Start the development server:

    python app.py

Visit http://127.0.0.1:5000. For a new database, create its schema from
sql.txt before starting the app.

Database and uploads
--------------------
The users table includes profile fields such as name, fitness goal, and profile
picture. sql.txt documents one-time ALTER TABLE statements for older databases;
only run a migration when the relevant column is missing. Custom weekly routine
details use JSON in the existing workout.details column.

Profile images are limited to PNG, JPEG, or WebP files up to 5 MB. The app
stores uploaded images in static/uploads under generated filenames and saves
the current filename for each user in the database. These uploads and any
database containing user data are local runtime data, not source files.

Maintenance
-----------
Update this prototype after feature or setup changes. Check git status before
committing so unrelated work and local user data are not included.
