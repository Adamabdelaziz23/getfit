GETFIT
======

README prototype
----------------
This file is a working prototype for a fuller README.md. Keep it up to date as
features, setup steps, and project status change.

About
-----
GetFit is a Flask and SQLite fitness-tracking app. Users can register and log
in, edit profile details, upload a profile picture, record bench press, squat,
and deadlift personal records, view or create weekly workout routines, and
calculate nutrition targets from estimated maintenance calories.

Current features
----------------
- User registration and login with hashed passwords.
- Session-protected home, nutrition, workout, and profile pages.
- Profile editing for name, height, weight, and fitness goal.
- Profile picture uploads: choose a PNG, JPEG, or WebP (up to 5 MB) using the
    + button overlaid on the avatar; selection uploads automatically.
- Personal records saved per user for bench press, squat, and deadlift.
- Nutrition targets update from the existing calorie calculator using 15% cut,
  maintenance, and 10% bulk targets. Protein is 1.6 g/kg; remaining calories
  use a 4:3 carb-to-fat split with 4/4/9 kcal/g conversions.
- Three 7-day preset programs (Push/Pull/Legs, Upper/Lower, and Full Body), each
    showing high-intensity, high-volume, and average training options per day.
- Custom weekly routines with seven days and three training-style detail fields
    per day, saved per user.
- SQLite database access through the CS50 SQL library.

Technology
----------
- Python and Flask
- SQLite and CS50 SQL
- Flask-Session
- HTML, CSS, and JavaScript
- Bootstrap 5 loaded from a CDN

Project files
-------------
- app.py: Flask routes, authentication, profile updates, PR updates, workout routines, and image uploads.
- sql.txt: Database schema for new databases and migration reminders for existing ones.
- getfit.db: Local SQLite database. Do not commit it if it contains real user data.
- templates/: Jinja templates for the application pages.
- static/: CSS, JavaScript, and uploaded profile pictures.
- static/uploads/: Created by the app for profile picture uploads.

Run locally
-----------
From the project directory, create and activate a virtual environment, then
install the required packages:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install Flask Flask-Session cs50

Start the development server:

    python app.py

Open http://127.0.0.1:5000 in a browser. The app uses getfit.db in the project
directory. For a new database, create the schema using sql.txt before starting
the app.

Database updates
----------------
The users table includes name, fitness_goal, and profile_picture columns.
sql.txt contains commented ALTER TABLE statements for older databases. After
merging schema changes, run each required statement once against an existing
database that does not already have that column. Do not run an ALTER statement
again if the column is already present. The local getfit.db has been migrated.
Custom weekly routine details are stored as JSON in the existing workout.details
column, so the routine editor does not require another schema migration.

Do not commit getfit.db when it contains personal account data. Keep database
schema and migration instructions in source control instead.

Uploads
-------
Profile pictures are stored in static/uploads with generated filenames. The
database stores each user's current filename. Uploaded user images are local
runtime data and should not normally be committed. Use the button embedded in
the avatar to select and upload a replacement picture.

Development history
-------------------
Recent commits show these milestones:
- c06df9c: Profile logic implemented.
- 7b61358: Ignore generated files.
- 3af4978: Registration and login implemented.
- b2d6869: Initial GetFit app commit.
- 501f917: First commit.

Profile editing, PR persistence, and profile picture upload have since been
worked on in the current branch. Check git status before committing to see
which changes are still uncommitted.

Maintenance
-----------
After each feature or setup change, update this README prototype so it reflects
the current app. This can later be used to write README.md.

