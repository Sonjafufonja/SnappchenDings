"""Berechnung aller Reisefenster basierend auf Schulferien Niedersachsen 2026."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterator

from .models import TravelWindow, TripOption
from .config import MIN_TRIP_NIGHTS, MAX_TRIP_NIGHTS

# ---------------------------------------------------------------------------
# Schulferien Niedersachsen 2026
# ---------------------------------------------------------------------------
SCHOOL_HOLIDAYS_2026: list[tuple[str, date, date]] = [
    ("Halbjahresferien",  date(2026,  2,  2), date(2026,  2,  3)),
    ("Osterferien",       date(2026,  3, 23), date(2026,  4,  7)),
    ("Pfingstferien",     date(2026,  5, 26), date(2026,  5, 26)),
    ("Sommerferien",      date(2026,  7,  2), date(2026,  8, 12)),
    ("Herbstferien",      date(2026, 10, 12), date(2026, 10, 24)),
    ("Weihnachtsferien",  date(2026, 12, 23), date(2027,  1,  9)),
]

# ---------------------------------------------------------------------------
# Brückentag-Fenster (Feiertage + max. 2 Schultage schwänzen)
# ---------------------------------------------------------------------------
BRIDGE_WINDOWS: list[tuple[str, date, date, int]] = [
    # (Name, Start, End, school_days_skipped)
    ("Tag der Arbeit (Langes WE)",    date(2026, 4, 29), date(2026, 5,  3), 2),
    ("Christi Himmelfahrt (Langes WE)", date(2026, 5, 14), date(2026, 5, 17), 1),
    ("Pfingsten + Pfingstferien",     date(2026, 5, 23), date(2026, 5, 26), 0),
]


def _is_school_day(d: date) -> bool:
    """Prüft ob ein Tag ein Schultag ist (Mo–Fr, kein Feiertag, keine Ferien)."""
    if d.weekday() >= 5:  # Sa/So
        return False
    for _, start, end in SCHOOL_HOLIDAYS_2026:
        if start <= d <= end:
            return False
    return True


def _count_school_days(start: date, end: date) -> int:
    """Zählt Schultage in einem Zeitraum."""
    count = 0
    d = start
    while d <= end:
        if _is_school_day(d):
            count += 1
        d += timedelta(days=1)
    return count


def get_travel_windows() -> list[TravelWindow]:
    """Gibt alle Reisefenster zurück (Ferien + Brückentage)."""
    windows: list[TravelWindow] = []

    # Reguläre Ferienblöcke
    for name, start, end in SCHOOL_HOLIDAYS_2026:
        windows.append(TravelWindow(
            name=name,
            start=start,
            end=end,
            school_days_skipped=0,
        ))

    # Brückentag-Fenster
    for name, start, end, skipped in BRIDGE_WINDOWS:
        windows.append(TravelWindow(
            name=name,
            start=start,
            end=end,
            school_days_skipped=skipped,
        ))

    # Sortieren nach Startdatum
    windows.sort(key=lambda w: w.start)
    return windows


def get_trip_options(window: TravelWindow) -> list[TripOption]:
    """Generiert alle sinnvollen Trip-Optionen innerhalb eines Reisefensters."""
    options: list[TripOption] = []
    max_nights = min(MAX_TRIP_NIGHTS, window.duration_days - 1)

    for nights in range(MIN_TRIP_NIGHTS, max_nights + 1):
        # Mögliche Abflugdaten innerhalb des Fensters
        latest_depart = window.end - timedelta(days=nights)
        depart = window.start
        while depart <= latest_depart:
            return_date = depart + timedelta(days=nights)
            if return_date <= window.end:
                options.append(TripOption(
                    window=window,
                    depart=depart,
                    return_date=return_date,
                ))
            depart += timedelta(days=1)

    return options
