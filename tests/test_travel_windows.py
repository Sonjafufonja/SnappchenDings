"""Tests für travel_windows.py."""
from __future__ import annotations

from datetime import date

import pytest

from src.travel_windows import (
    get_travel_windows,
    get_trip_options,
    _is_school_day,
    _count_school_days,
    SCHOOL_HOLIDAYS_2026,
)
from src.models import TravelWindow


class TestSchoolDayCheck:
    def test_weekend_is_not_school_day(self):
        # Samstag
        assert not _is_school_day(date(2026, 3, 14))
        # Sonntag
        assert not _is_school_day(date(2026, 3, 15))

    def test_weekday_in_ferien_is_not_school_day(self):
        # Montag in Osterferien
        assert not _is_school_day(date(2026, 3, 23))
        assert not _is_school_day(date(2026, 4, 7))

    def test_weekday_outside_ferien_is_school_day(self):
        # Montag, kein Feiertag, keine Ferien
        assert _is_school_day(date(2026, 3, 2))
        assert _is_school_day(date(2026, 9, 7))


class TestCountSchoolDays:
    def test_zero_during_ferien(self):
        # Komplette Osterferien
        assert _count_school_days(date(2026, 3, 23), date(2026, 4, 7)) == 0

    def test_counts_correctly(self):
        # Eine normale Schulwoche (Mo–Fr)
        count = _count_school_days(date(2026, 3, 2), date(2026, 3, 6))
        assert count == 5

    def test_single_school_day(self):
        assert _count_school_days(date(2026, 3, 2), date(2026, 3, 2)) == 1


class TestGetTravelWindows:
    def test_returns_list(self):
        windows = get_travel_windows()
        assert isinstance(windows, list)
        assert len(windows) > 0

    def test_all_windows_are_travel_window(self):
        for w in get_travel_windows():
            assert isinstance(w, TravelWindow)

    def test_sorted_by_start(self):
        windows = get_travel_windows()
        starts = [w.start for w in windows]
        assert starts == sorted(starts)

    def test_includes_all_holiday_blocks(self):
        windows = get_travel_windows()
        names = [w.name for w in windows]
        assert "Osterferien" in names
        assert "Sommerferien" in names
        assert "Herbstferien" in names
        assert "Weihnachtsferien" in names

    def test_sommerferien_dates(self):
        windows = get_travel_windows()
        sommer = next(w for w in windows if w.name == "Sommerferien")
        assert sommer.start == date(2026, 7, 2)
        assert sommer.end == date(2026, 8, 12)

    def test_bridge_windows_have_school_days_skipped(self):
        windows = get_travel_windows()
        bridge = [w for w in windows if w.school_days_skipped > 0]
        assert len(bridge) > 0
        for w in bridge:
            assert w.school_days_skipped <= 2

    def test_regular_ferien_have_zero_school_days_skipped(self):
        windows = get_travel_windows()
        regular = [w for w in windows if w.name in {n for n, _, _ in SCHOOL_HOLIDAYS_2026}]
        for w in regular:
            assert w.school_days_skipped == 0


class TestGetTripOptions:
    def test_returns_list(self):
        window = TravelWindow("Test", date(2026, 7, 2), date(2026, 7, 16), 0)
        options = get_trip_options(window)
        assert isinstance(options, list)
        assert len(options) > 0

    def test_min_nights(self):
        window = TravelWindow("Test", date(2026, 7, 2), date(2026, 7, 16), 0)
        options = get_trip_options(window)
        assert all(o.nights >= 2 for o in options)

    def test_max_nights(self):
        window = TravelWindow("Test", date(2026, 7, 2), date(2026, 7, 16), 0)
        options = get_trip_options(window)
        assert all(o.nights <= 14 for o in options)

    def test_return_within_window(self):
        window = TravelWindow("Test", date(2026, 7, 2), date(2026, 7, 16), 0)
        options = get_trip_options(window)
        for o in options:
            assert o.depart >= window.start
            assert o.return_date <= window.end

    def test_short_window_limited_options(self):
        # Halbjahresferien: nur 2 Tage
        window = TravelWindow("Halbjahresferien", date(2026, 2, 2), date(2026, 2, 3), 0)
        options = get_trip_options(window)
        # Zu kurz für min_nights=2 → leer
        assert options == []

    def test_trip_option_window_reference(self):
        window = TravelWindow("Test", date(2026, 7, 2), date(2026, 7, 16), 0)
        options = get_trip_options(window)
        for o in options:
            assert o.window is window
