# Spec: Profile Page

## Overview
This feature implements the `GET /profile` route, replacing its current
placeholder string response with a real page that shows the logged-in user's
account details (name, email, member-since date). It is the first
user-scoped page in the roadmap and establishes the pattern for
login-required routes that later expense features (add/edit/delete) will
reuse.

## Depends on
- Step 01 — Database setup (`database/db.py` with `get_db()`, `init_db()`,
  `users` table). Already implemented and merged.
- Step 02 — Registration (`create_user()`). Already implemented and merged.
- Step 03 — Login and Logout (`session["user_id"]`, `session["name"]`,
  session-aware navbar). Already implemented and merged.

## Routes
- `GET /profile` — renders the profile page with the current user's account
  details — logged-in only (redirect to `GET /login` if no active session)

## Database changes
No database changes. The `users` table (id, name, email, password_hash,
created_at) already has everything needed to display a profile. A new
`database/db.py` function, `get_user_by_id(user_id)`, will be added to fetch
the current user's row — no schema changes required.

## Templates
- **Create:** `templates/profile.html` — displays the user's name, email,
  and `created_at` (formatted as a join date); extends `base.html`
- **Modify:** none

## Files to change
- `app.py` — replace the `/profile` stub with a real handler: check
  `session.get('user_id')`, redirect to `login` if absent, otherwise fetch
  the user via `get_user_by_id()` and render `profile.html`
- `database/db.py` — add `get_user_by_id(user_id)` helper

## Files to create
- `templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders), never f-strings in SQL
- Passwords hashed with werkzeug (no change needed here, but never expose
  `password_hash` to the template)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs only in `database/db.py`, never inline in the `app.py`
  route
- Do not implement `/expenses/*` routes — those are later steps
- `GET /profile` must redirect anonymous visitors to `/login`, not error or
  expose any data

## Definition of done
- [ ] Visiting `/profile` while logged out redirects to `/login`
- [ ] Visiting `/profile` while logged in renders `profile.html` with the
      correct name, email, and join date for the logged-in user
- [ ] `password_hash` is never passed into the template context
- [ ] `profile.html` extends `base.html` and uses `url_for()` for all links
- [ ] No SQL is built with string formatting/f-strings anywhere in the new
      code
- [ ] App still starts cleanly on port 5001 with no errors
