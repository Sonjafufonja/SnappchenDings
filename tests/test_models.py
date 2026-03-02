"""Tests für models.py."""
from __future__ import annotations

from datetime import date

import pytest

from src.models import (
    TravelWindow, TripOption, FlightResult, TrainResult,
    AccommodationResult, TripCost, Deal,
)


class TestTravelWindow:
    def test_duration_days(self):
        w = TravelWindow("Test", date(2026, 3, 23), date(2026, 4, 7), 0)
        assert w.duration_days == 16  # 23 Mär bis 7 Apr inkl. = 16 Tage

    def test_single_day(self):
        w = TravelWindow("Pfingstferien", date(2026, 5, 26), date(2026, 5, 26), 0)
        assert w.duration_days == 1

    def test_repr(self):
        w = TravelWindow("Test", date(2026, 3, 23), date(2026, 4, 7), 0)
        assert "Test" in repr(w)


class TestTripOption:
    def test_nights(self):
        window = TravelWindow("Test", date(2026, 3, 23), date(2026, 4, 7), 0)
        trip = TripOption(window=window, depart=date(2026, 3, 23), return_date=date(2026, 3, 27))
        assert trip.nights == 4

    def test_same_day_is_zero_nights(self):
        window = TravelWindow("Test", date(2026, 3, 23), date(2026, 4, 7), 0)
        trip = TripOption(window=window, depart=date(2026, 3, 23), return_date=date(2026, 3, 23))
        assert trip.nights == 0


class TestTripCost:
    def _make_costs(self, nights: int = 4, flight: float = 100.0, train: float = 50.0,
                    accom_per_night: float = 60.0, local_daily: float = 40.0) -> TripCost:
        f = FlightResult("HAM", "BUD", "Budapest", "Ungarn", "HU", flight, "", "")
        t = TrainResult("Braunschweig", "Hamburg", train)
        a = AccommodationResult("Budapest", "Ungarn", accom_per_night, nights, accom_per_night * nights)
        return TripCost(flight=f, train=t, accommodation=a,
                        local_cost_per_person_per_day=local_daily, nights=nights)

    def test_total_cost(self):
        # flight=100, train=50, accom=60*4=240, local=40*2*4=320
        costs = self._make_costs()
        expected = 100 + 50 + 240 + 320
        assert costs.total_cost == pytest.approx(expected)

    def test_cost_per_person(self):
        costs = self._make_costs()
        assert costs.cost_per_person == pytest.approx(costs.total_cost / 2)

    def test_cost_per_person_per_night(self):
        costs = self._make_costs(nights=4)
        assert costs.cost_per_person_per_night == pytest.approx(costs.cost_per_person / 4)

    def test_zero_nights_returns_inf(self):
        costs = self._make_costs(nights=0)
        assert costs.cost_per_person_per_night == float("inf")


class TestDeal:
    def test_destination_city(self):
        window = TravelWindow("Test", date(2026, 3, 23), date(2026, 4, 7), 0)
        trip = TripOption(window=window, depart=date(2026, 3, 23), return_date=date(2026, 3, 27))
        f = FlightResult("HAM", "BUD", "Budapest", "Ungarn", "HU", 100.0, "", "")
        t = TrainResult("Braunschweig", "Hamburg", 50.0)
        a = AccommodationResult("Budapest", "Ungarn", 60.0, 4, 240.0)
        costs = TripCost(flight=f, train=t, accommodation=a,
                         local_cost_per_person_per_day=40.0, nights=4)
        deal = Deal(trip=trip, costs=costs, score=75.0, rank=1)
        assert deal.destination_city == "Budapest"
        assert deal.destination_country == "Ungarn"
