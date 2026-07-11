# Spec: Login and Logout

## Overview
This feature implements session-based authentication for Spendly. It adds a
`POST /login` handler that verifies email/password against the `users`
table and starts a Flask session, and implements `GET /logout` to clear that
session. It also updates the navbar in `base.html` to reflect whether a user
is signed in. This is the second authentication feature in the roadmap,
building directly on registration, and is a prerequisite for any user-scoped
page (profile, expenses).

## Depends on
- Step 01 — Database setup (`database/db.py` with `get_db()`, `init_db()`,
  `users` table). Already implemented and merged.
- Step 02 — Registration (`create_user()`, hashed passwords in `users`).
  Already implemented and merged.

## Routes
- `GET /login` — renders the login form — public (already implemented, unchanged)
- `POST /login` — validates email/password against stored hash, starts a
  session on success (redirect to `/`), or re-renders `login.html` with an
  error on failure — public
- `GET /logout` — clears the session and redirects to `/` — logged-in only
  (if no active session, just redirect to `/` rather than erroring)

## Database changes
No database changes. The `users` table (id, name, email, password_hash,
created_at) already supports login as-is. A new `database/db.py` function,
`get_user_by_email(email)`, will be added to fetch a user row for password
verification — no schema changes required.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — change hardcoded `action="/login"` to
    `action="{{ url_for('login') }}"` (CLAUDE.md forbids hardcoded URLs in
    templates)
  - `templates/base.html` — navbar conditionally shows "Sign in" / "Get
    started" for anonymous visitors, or the user's name with a "Logout" link
    (`url_for('logout')`) when `session.get('user_id')` is set

## Files to change
- `app.py` — change `/login` to accept `["GET", "POST"]`, add credential
  validation and session creation on `POST`; implement `/logout` to clear
  the session; set `app.secret_key` (required for Flask sessions)
- `database/db.py` — add `get_user_by_email(email)` helper
- `templates/login.html` — fix hardcoded form action to use `url_for()`
- `templates/base.html` — session-aware navbar

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` and
`flask.session` are already available via existing imports/Flask itself.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders), never f-strings in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never
  compare plaintext passwords
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs only in `database/db.py`, never inline in the `app.py`
  route
- Session must store only `user_id` (and optionally `name` for display) —
  never store the password or password hash in the session
- `app.secret_key` must be set (e.g. from an env var with a dev fallback) or
  `session` writes will fail
- Give a generic error ("Invalid email or password") on failed login — do
  not reveal whether the email exists or the password was wrong
- Do not implement `/profile` or `/expenses/*` routes — those are later
  steps; `POST /login` should redirect to `/` (landing page) on success,
  since `/profile` is still a stub

## Definition of done
- [ ] `GET /login` still renders the form exactly as before
- [ ] Submitting a valid email/password combination starts a session and
      redirects to `/`
- [ ] Submitting an unknown email re-renders `login.html` with a generic
      error and does not start a session
- [ ] Submitting a known email with the wrong password re-renders
      `login.html` with the same generic error and does not start a session
- [ ] Visiting `/logout` while logged in clears the session and redirects to
      `/`
- [ ] Visiting `/logout` while logged out simply redirects to `/` without
      error
- [ ] After login, the navbar shows a logout link instead of "Sign in" /
      "Get started"
- [ ] No SQL is built with string formatting/f-strings anywhere in the new
      code
- [ ] App still starts cleanly on port 5001 with no errors
