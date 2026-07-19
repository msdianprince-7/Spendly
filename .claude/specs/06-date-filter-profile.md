# Spec: Date Filter For Profile Page

## Overview
Step 6 adds a date-range filter to the `/profile` page. Currently the summary
stats, transaction list, and category breakdown always cover a user's entire
expense history. This step lets a logged-in user narrow all three sections to
a specific date range (e.g. "this month" or a custom start/end date) using
query parameters on the existing `/profile` route, so they can review spending
for a specific period rather than all-time totals.

## Depends on
- Step 1: Database setup (`expenses.date` column exists)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 5: Backend routes for profile page (`get_expense_stats`,
  `get_expenses_by_user`, `get_category_breakdown` already query live data)

## Routes
No new routes. The existing `GET /profile` route is modified to accept two
optional query string parameters:
- `GET /profile?start=<YYYY-MM-DD>&end=<YYYY-MM-DD>` — logged-in only. Both
  params are optional; if either is missing or invalid, that side of the
  range is unbounded (falls back to all-time behavior on that side).

## Database changes
No schema changes. `expenses.date` (stored as `YYYY-MM-DD` ISO text) already
supports range comparisons via SQL `BETWEEN` / `>=` / `<=`.

Existing query helpers in `database/db.py` are extended with optional
`start_date` and `end_date` keyword arguments (default `None`, meaning
unbounded on that side):
- `get_expenses_by_user(user_id, start_date=None, end_date=None)`
- `get_expense_stats(user_id, start_date=None, end_date=None)`
- `get_category_breakdown(user_id, start_date=None, end_date=None)`

## Templates
- **Modify:** `templates/profile.html`
  - Add a small filter form above "Recent transactions" with two `<input
    type="date">` fields (`start`, `end`) and a submit button, using `GET`
    method so the range appears in the URL and is bookmarkable/shareable.
  - Pre-fill the inputs with the currently active `start`/`end` values so the
    filter persists visually after submission.
  - Add a "Clear filter" link (plain `<a>` using `url_for('profile')` with no
    query params) shown only when a filter is active.
  - No structural changes to the stats, transaction table, or category
    breakdown blocks — they keep consuming the same variable names.

## Files to change
- `app.py` — read `start`/`end` from `request.args` in the `profile()` view,
  validate them, and pass through to the three query helpers
- `database/db.py` — add optional `start_date`/`end_date` params to
  `get_expenses_by_user`, `get_expense_stats`, `get_category_breakdown`
- `templates/profile.html` — add the filter form and clear-filter link
- `static/css/profile.css` — style the new filter form using existing CSS
  variables

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL, including
  the date bounds
- Passwords hashed with werkzeug (unaffected by this step, listed per
  standing project rule)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate `start`/`end` as `YYYY-MM-DD` in `app.py` before passing to query
  helpers; silently ignore (treat as unset) a malformed or missing value
  rather than raising a 400 or 500
- If `start` is after `end`, treat the filter as invalid and fall back to
  all-time (unfiltered) results rather than erroring
- Date bounds are inclusive on both ends
- If a user has no expenses in the selected range, stats should return zeros
  and lists should be empty rather than raising exceptions
- Query helpers must build the `WHERE` clause conditionally (only adding
  `date >= ?` / `date <= ?` when the corresponding bound is provided) while
  still using `?` placeholders for every value

## Definition of done
- [ ] Visiting `/profile` with no query params shows all-time stats,
      transactions, and category breakdown exactly as before this change
- [ ] Setting `start` and `end` in the filter form and submitting updates the
      URL to `/profile?start=...&end=...` and narrows all three sections to
      that inclusive range
- [ ] As the seed user, filtering to a range containing only the "Bills"
      expenses shows a total spent equal to the sum of just those expenses
      and a top category of "Bills"
- [ ] Filtering to a date range with no matching expenses shows ₹0.00 total
      spent, 0 transactions, and an empty category breakdown — no errors
- [ ] Submitting only `start` (no `end`) includes all expenses on or after
      that date; submitting only `end` (no `start`) includes all expenses on
      or before that date
- [ ] Submitting a `start` date after the `end` date falls back to showing
      all-time results instead of erroring
- [ ] Passing a malformed date string (e.g. `start=not-a-date`) does not
      crash the page — it is treated as if that param were absent
- [ ] The date inputs are pre-filled with the active filter values after
      submission, and a "Clear filter" link appears and correctly resets to
      `/profile` with no query params
