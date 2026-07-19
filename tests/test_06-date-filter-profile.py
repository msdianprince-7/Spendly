"""Tests for Step 6: date-range filter on the /profile page.

Covers the spec at .claude/specs/06-date-filter-profile.md — the existing
GET /profile route accepts optional `start`/`end` query params (YYYY-MM-DD)
that narrow the stats, transaction list, and category breakdown to an
inclusive date range, falling back to unfiltered/all-time behavior whenever
the params are absent, malformed, or reversed (start after end).

Seed data reminder (demo user, from database/db.py seed_db):
- 8 expenses totaling ₹798.54, newest-first
- Two "Bills" expenses this month: day 5 (₹45.00) and day 6 (₹650.00),
  summing to ₹695.00 — this is the only category appearing on days 5-6
"""

from datetime import date, timedelta

from tests.conftest import login


def _today():
    return date.today()


def _iso(d):
    return d.isoformat()


class TestProfileFilterAuthGuard:
    def test_profile_with_filter_params_redirects_when_not_logged_in(self, client):
        response = client.get("/profile?start=2020-01-01&end=2020-12-31")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_profile_without_params_redirects_when_not_logged_in(self, client):
        response = client.get("/profile")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


class TestProfileFilterBaseline:
    def test_no_query_params_shows_all_time_stats(self, client, demo_user_id):
        login(client, demo_user_id)
        body = client.get("/profile").data.decode()
        assert "798.54" in body, "Expected all-time total spent unchanged"
        assert "Bills" in body
        assert ">8<" in body or "8" in body  # transaction count present somewhere

    def test_no_query_params_shows_all_eight_transactions(self, client, demo_user_id):
        login(client, demo_user_id)
        body = client.get("/profile").data.decode()
        # All eight seeded descriptions should be present when unfiltered
        for desc in [
            "Grocery run",
            "Bus fare",
            "Electricity bill",
            "Monthly rent",
            "Pharmacy",
            "Movie tickets",
            "New shoes",
            "Miscellaneous",
        ]:
            assert desc in body, f"Expected unfiltered transaction '{desc}' to appear"


class TestProfileFilterNarrowsRange:
    def test_range_covering_only_bills_expenses_shows_bills_total_and_top_category(
        self, client, demo_user_id
    ):
        login(client, demo_user_id)
        today = _today()
        start = _iso(today.replace(day=5))
        end = _iso(today.replace(day=6))
        response = client.get(f"/profile?start={start}&end={end}")
        body = response.data.decode()

        assert response.status_code == 200
        assert "695.00" in body, "Expected total spent narrowed to Bills-only sum"
        assert "Bills" in body

        # Non-Bills transactions from other days must not appear
        for desc in [
            "Grocery run",
            "Bus fare",
            "Pharmacy",
            "Movie tickets",
            "New shoes",
            "Miscellaneous",
        ]:
            assert desc not in body, f"Did not expect out-of-range transaction '{desc}'"

        # Bills transactions should appear
        assert "Electricity bill" in body
        assert "Monthly rent" in body

    def test_range_covering_only_bills_expenses_category_breakdown_is_bills_only(
        self, client, demo_user_id
    ):
        login(client, demo_user_id)
        today = _today()
        start = _iso(today.replace(day=5))
        end = _iso(today.replace(day=6))
        body = client.get(f"/profile?start={start}&end={end}").data.decode()

        assert "profile-bar-bills" in body
        for other_category_css in [
            "profile-bar-food",
            "profile-bar-transport",
            "profile-bar-health",
            "profile-bar-entertainment",
            "profile-bar-shopping",
            "profile-bar-other",
        ]:
            assert other_category_css not in body, (
                f"Did not expect category breakdown row '{other_category_css}' "
                "outside the filtered range"
            )


class TestProfileFilterEmptyResult:
    def test_range_with_no_matching_expenses_shows_zeroed_stats(
        self, client, demo_user_id
    ):
        login(client, demo_user_id)
        # Far future range guaranteed to contain no seeded expenses
        response = client.get("/profile?start=2099-01-01&end=2099-01-31")
        body = response.data.decode()

        assert response.status_code == 200
        assert "0.00" in body, "Expected ₹0.00 total spent for empty range"
        assert "Electricity bill" not in body
        assert "Monthly rent" not in body
        assert "Grocery run" not in body

    def test_range_with_no_matching_expenses_has_no_category_rows(
        self, client, demo_user_id
    ):
        login(client, demo_user_id)
        body = client.get(
            "/profile?start=2099-01-01&end=2099-01-31"
        ).data.decode()
        assert "profile-category-row" not in body


class TestProfileFilterOneSidedBounds:
    def test_start_only_includes_everything_on_or_after(self, client, demo_user_id):
        login(client, demo_user_id)
        today = _today()
        start = _iso(today.replace(day=10))
        response = client.get(f"/profile?start={start}")
        body = response.data.decode()

        assert response.status_code == 200
        # Expenses on/after day 10 should be present
        for desc in ["Pharmacy", "Movie tickets", "New shoes", "Miscellaneous"]:
            assert desc in body, f"Expected '{desc}' included with start-only filter"
        # Expenses before day 10 should be excluded
        for desc in ["Grocery run", "Bus fare", "Electricity bill", "Monthly rent"]:
            assert desc not in body, f"Did not expect '{desc}' before start bound"

    def test_end_only_includes_everything_on_or_before(self, client, demo_user_id):
        login(client, demo_user_id)
        today = _today()
        end = _iso(today.replace(day=6))
        response = client.get(f"/profile?end={end}")
        body = response.data.decode()

        assert response.status_code == 200
        # Expenses on/before day 6 should be present
        for desc in ["Grocery run", "Bus fare", "Electricity bill", "Monthly rent"]:
            assert desc in body, f"Expected '{desc}' included with end-only filter"
        # Expenses after day 6 should be excluded
        for desc in ["Pharmacy", "Movie tickets", "New shoes", "Miscellaneous"]:
            assert desc not in body, f"Did not expect '{desc}' after end bound"


class TestProfileFilterReversedRange:
    def test_start_after_end_falls_back_to_all_time(self, client, demo_user_id):
        login(client, demo_user_id)
        today = _today()
        start = _iso(today.replace(day=20))
        end = _iso(today.replace(day=1))
        response = client.get(f"/profile?start={start}&end={end}")
        body = response.data.decode()

        assert response.status_code == 200, "Reversed range must not error"
        assert "798.54" in body, "Expected all-time total when start is after end"
        for desc in [
            "Grocery run",
            "Bus fare",
            "Electricity bill",
            "Monthly rent",
            "Pharmacy",
            "Movie tickets",
            "New shoes",
            "Miscellaneous",
        ]:
            assert desc in body


class TestProfileFilterMalformedInput:
    def test_malformed_start_is_treated_as_absent(self, client, demo_user_id):
        login(client, demo_user_id)
        response = client.get("/profile?start=not-a-date")
        body = response.data.decode()

        assert response.status_code == 200, "Malformed start must not crash the page"
        assert "798.54" in body, "Malformed start should behave as unbounded start"

    def test_malformed_end_is_treated_as_absent(self, client, demo_user_id):
        login(client, demo_user_id)
        response = client.get("/profile?end=banana")
        body = response.data.decode()

        assert response.status_code == 200, "Malformed end must not crash the page"
        assert "798.54" in body, "Malformed end should behave as unbounded end"

    def test_both_malformed_falls_back_to_all_time(self, client, demo_user_id):
        login(client, demo_user_id)
        response = client.get("/profile?start=nope&end=nope-too")
        body = response.data.decode()

        assert response.status_code == 200
        assert "798.54" in body


class TestProfileFilterFormRendering:
    def test_inputs_prefilled_with_active_filter_values(self, client, demo_user_id):
        login(client, demo_user_id)
        today = _today()
        start = _iso(today.replace(day=5))
        end = _iso(today.replace(day=6))
        body = client.get(f"/profile?start={start}&end={end}").data.decode()

        assert f'value="{start}"' in body, "Expected start input pre-filled"
        assert f'value="{end}"' in body, "Expected end input pre-filled"

    def test_inputs_blank_when_no_filter_active(self, client, demo_user_id):
        login(client, demo_user_id)
        body = client.get("/profile").data.decode()

        assert 'id="start"' in body
        assert 'id="end"' in body
        assert 'value=""' in body, "Expected empty date inputs when no filter is active"

    def test_clear_filter_link_present_when_filter_active(self, client, demo_user_id):
        login(client, demo_user_id)
        today = _today()
        body = client.get(
            f"/profile?start={_iso(today.replace(day=5))}"
        ).data.decode()
        assert "Clear filter" in body

    def test_clear_filter_link_absent_when_no_filter_active(self, client, demo_user_id):
        login(client, demo_user_id)
        body = client.get("/profile").data.decode()
        assert "Clear filter" not in body

    def test_clear_filter_link_points_to_profile_with_no_query_params(
        self, client, demo_user_id
    ):
        login(client, demo_user_id)
        today = _today()
        body = client.get(
            f"/profile?start={_iso(today.replace(day=5))}&end={_iso(today.replace(day=6))}"
        ).data.decode()

        assert 'href="/profile"' in body, (
            "Expected Clear filter link to point to /profile with no query string"
        )
        assert 'href="/profile?' not in body, (
            "Clear filter link must not carry over the active query params"
        )

    def test_clear_filter_link_absent_for_empty_result_range(
        self, client, demo_user_id
    ):
        # Even when a filter yields zero rows, if start/end were validly
        # supplied the filter is still "active" and the clear link should show.
        login(client, demo_user_id)
        body = client.get(
            "/profile?start=2099-01-01&end=2099-01-31"
        ).data.decode()
        assert "Clear filter" in body


class TestProfileFilterFreshUser:
    def test_fresh_user_with_filter_params_shows_empty_state_not_error(
        self, client, fresh_user_id
    ):
        login(client, fresh_user_id, name="Fresh User")
        response = client.get("/profile?start=2020-01-01&end=2030-01-01")
        body = response.data.decode()

        assert response.status_code == 200
        assert "0.00" in body
        assert "profile-badge-" not in body
