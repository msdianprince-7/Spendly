# Spendly — Architecture

Spendly is a Flask-based personal expense tracker, currently a scaffold/teaching
project being built incrementally.

## Stack
- **Backend**: Flask
- **Database**: SQLite, via `database/db.py` (not yet implemented)
- **Templates**: Jinja (`templates/`)
- **Frontend assets**: vanilla CSS/JS (`static/css`, `static/js`)

## Routes (`app.py`)
Implemented (render templates):
- `/` — landing page
- `/register` — registration page
- `/login` — login page

Placeholder stubs (return plain text, not yet implemented):
- `/logout` — "coming in Step 3"
- `/profile` — "coming in Step 4"
- `/expenses/add` — "coming in Step 7"
- `/expenses/<int:id>/edit` — "coming in Step 8"
- `/expenses/<int:id>/delete` — "coming in Step 9"

## Database layer (`database/db.py`)
Currently just comments describing the intended API, to be implemented in
Step 1 — Database Setup:
- `get_db()` — returns a SQLite connection with `row_factory` and foreign keys
  enabled
- `init_db()` — creates all tables using `CREATE TABLE IF NOT EXISTS`
- `seed_db()` — inserts sample data for development

## Current state
The auth-page templates and routing skeleton exist and run, but the database
layer and actual expense CRUD logic have not been implemented yet. The build
is structured as a step-by-step progression (per the code comments), with
auth (login/logout/profile) and expense management (add/edit/delete) as the
next milestones.
