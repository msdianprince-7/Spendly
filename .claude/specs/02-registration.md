# Spec: Registration

## Overview
This feature implements account creation for Spendly. It adds a `POST /register`
handler that validates the signup form, hashes the password, and inserts a new
row into the `users` table. This is the first authentication feature in the
roadmap and is a prerequisite for login, logout, and any user-scoped feature
(profile, expenses).

## Depends on
Step 01 — Database setup (`database/db.py` with `get_db()`, `init_db()`,
`users` table). This is already implemented and merged.

## Routes
- `GET /register` — renders the registration form — public (already implemented, unchanged)
- `POST /register` — validates input, creates the user, and redirects to `/login` on success, or re-renders `register.html` with an error on failure — public

## Database changes
No database changes. The `users` table (id, name, email, password_hash,
created_at) already supports registration as-is. A new `database/db.py`
function, `create_user(name, email, password_hash)`, will be added to perform
the parameterized `INSERT` — no schema changes required.

## Templates
- **Create:** none
- **Modify:** `templates/register.html` — populate re-entered `name`/`email`
  values on validation failure (`value="{{ name or '' }}"`) so the user
  doesn't have to retype the whole form; no structural changes needed since
  the `{% if error %}` block and form fields already exist

## Files to change
- `app.py` — change `/register` to accept `["GET", "POST"]`, add validation
  and `create_user()` call on `POST`
- `database/db.py` — add `create_user(name, email, password_hash)` helper
- `templates/register.html` — re-populate `name`/`email` fields on error

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.generate_password_hash` is already
available (used by `seed_db()`).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders), never f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` before storage — never store plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs only in `database/db.py`, never inline in the `app.py` route
- Validate on the server even though the form has `required`/`type=email` HTML attributes (client-side validation is not trustworthy)
- Reject duplicate emails with a friendly error (catch the `UNIQUE` constraint failure — do not let it 500)
- Do not implement `/login`, `/logout`, or session handling — those are later steps; `POST /register` should redirect to `/login` (existing stub) after successful creation, without starting a session

## Definition of done
- [ ] `GET /register` still renders the form exactly as before
- [ ] Submitting valid name/email/password creates a row in `users` with a hashed (not plaintext) password
- [ ] Submitting with an email that already exists re-renders `register.html` with an error message and does not create a duplicate row
- [ ] Submitting with a missing field (name, email, or password) re-renders `register.html` with an error message and does not insert a row
- [ ] Submitting with a password under 8 characters re-renders `register.html` with an error message and does not insert a row
- [ ] On success, the browser is redirected to `/login`
- [ ] No SQL is built with string formatting/f-strings anywhere in the new code
- [ ] App still starts cleanly on port 5001 with no errors
