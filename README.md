# GetFit

#### Video Demo: TODO — add the URL after recording the project video

## Description

GetFit is a fitness tracking web application built with Flask, SQLite, Jinja, and
Bootstrap. It gives users one place to plan workouts, record training and
measurements, review personal records, and keep an eye on nutrition goals. The
project grew from a simple workout and nutrition idea into a multi-page app
where saved entries are associated with the signed-in user and can be reviewed
over time.

Users can create an account, log in, and maintain a profile with their name,
height, weight, fitness goal, and profile picture. The workout page includes
weekly preset routines, custom seven-day plans, and a rest timer. The nutrition
page estimates maintenance calories from age, height, weight, and gender, then
shows example cutting, maintenance, and bulking meal plans. These estimates are
guides rather than medical or dietary advice.

The Track Your Progress page brings daily records together in one form. A user
can save a workout and its exercises, sets, reps, and loads; enter nutrition
totals; add a weigh-in and body measurements; and record a new best bench press,
squat, or deadlift. Fields are optional where possible so a user can record
only the information available that day. The dashboard summarizes weight
trends, saved personal records, recent training, workout streaks, body
measurements, progress photos, and calorie goals. Separate history pages show
dated training, calorie, and personal-record entries. The photo memorial pairs
a before photo with an after photo added later.

## Design

Flask handles routing and server-side validation, while Jinja templates render
the pages. SQLite stores accounts, routines, workouts, nutrition, measurements,
and personal records. Passwords are stored as Werkzeug password hashes rather
than plain text. A session identifies the signed-in user, and routes that
contain personal data use a login-required decorator.

The interface uses a dark background with gold accents throughout. Bootstrap
provides responsive layout and common controls; the project stylesheet adds
page-specific layouts, focus states, and restrained hover feedback. JavaScript
is used for interactions that benefit from an immediate response, such as the
rest timer, adding exercise rows, and updating nutrition estimates. Workout
routine days are represented as structured data in the database, while
date-based logs are stored in dedicated tables so they can be queried for
history and charts.

## Project Files

- `app.py` defines the Flask application, routes, authentication checks,
  validation, database queries, and upload handling.
- `templates/` contains the Jinja pages. `layout.html` is the shared shell;
  `index.html`, `work.html`, `nut.html`, and `prof.html` provide the home,
  workouts, nutrition, and profile pages. `track.html` is the daily logging
  form, and `dash.html` is the progress dashboard. The history, memorial, and
  account pages are in `dashboard_history.html`, `pr_history.html`,
  `memorial.html`, `login.html`, and `register.html`. `_memorial_pair.html` is a
  reusable before-and-after photo partial.
- `static/style.css` contains the shared theme and page styles. `static/script.js`
  handles browser-side menu, timer, calculator, profile-picture, and exercise
  row interactions. `static/w.png` is the background image.
- `quotes.json` supplies the daily home-page motivation quote.
- `sql.txt` documents the SQLite schema used by the application.
- `.gitignore` excludes the local database, virtual environments, Flask
  sessions, environment files, and uploaded profile/progress photos.

## Running Locally

Use Python 3 and SQLite. From the project directory, create and activate a
virtual environment, then install the application dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Initialize the database schema from the project directory:

```bash
sqlite3 getfit.db < sql.txt
```

Set a local secret key and start Flask:

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
flask --app app run
```

Open <http://127.0.0.1:5000> and register an account. The app creates its upload
directories and Flask session storage as needed. Do not use the development
server or a development secret key for a public production deployment.

The schema creates the base account, workout, nutrition, food logging, and
history tables. The app creates additional date-based tracking tables when it
starts. Run the tests with `python -m unittest discover -s tests -v`.

## User Data

The SQLite database and uploaded images are runtime data, not source assets.
Uploads are limited to PNG, JPEG, and WebP images up to 5 MB and are saved under
generated filenames in `static/uploads/`. They are ignored by Git; review
`git status` before submitting to ensure private database contents, photos, or
other local files are not included.
