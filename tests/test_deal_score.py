"""Tests für deal_score.py."""
from __future__ import annotations

from datetime import date

import pytest

from src.deal_score import (
    price_penalty,
    duration_penalty,
    travel_penalty,
    calculate_score,
    build_deal,
    is_within_budget,
    BASE_SCORE,
)
from src.models import (
    TravelWindow, TripOption, FlightResult, TrainResult,
    AccommodationResult, TripCost, Deal,
)


def _make_costs(
    country_code: str = "HU",
    price_per_night: float = 45.0,
    nights: int = 4,
    flight_total: float = 94.0,
    train_total: float = 50.0,
    local_daily: float = 35.0,
) -> TripCost:
    flight = FlightResult(
        origin_iata="HAM",
        destination_iata="BUD",
        destination_city="Budapest",
        destination_country="Ungarn",
        destination_country_code=country_code,
        price_total=flight_total,
        departure_at="2026-03-23T10:00:00",
        return_at="2026-03-27T18:00:00",
    )
    train = TrainResult(
        origin="Braunschweig",
        destination="Hamburg",
        price_total=train_total,
        is_estimate=True,
    )
    accommodation = AccommodationResult(
        city="Budapest",
        country="Ungarn",
        price_per_night=price_per_night,
        nights=nights,
        total_price=price_per_night * nights,
    )
    return TripCost(
        flight=flight,
        train=train,
        accommodation=accommodation,
        local_cost_per_person_per_day=local_daily,
        nights=nights,
    )


def _make_trip(nights: int = 4) -> TripOption:
    window = TravelWindow("Osterferien", date(2026, 3, 23), date(2026, 4, 7), 0)
    return TripOption(window=window, depart=date(2026, 3, 23), return_date=date(2026, 3, 27))


class TestPricePenalty:
    def test_zero_for_free(self):
        assert price_penalty(0.0) == 0.0

    def test_max_for_expensive(self):
        # 100€/Person/Nacht → maximale Strafe
        assert price_penalty(100.0) == 50.0

    def test_half_for_mid(self):
        assert price_penalty(50.0) == pytest.approx(25.0, rel=0.01)

    def test_capped_at_max(self):
        assert price_penalty(200.0) == 50.0


class TestDurationPenalty:
    def test_no_penalty_for_normal(self):
        assert duration_penalty(4) == 0.0
        assert duration_penalty(2) == 0.0
        assert duration_penalty(10) == 0.0

    def test_short_trip_penalty(self):
        assert duration_penalty(1) == 15.0
        assert duration_penalty(0) == 15.0

    def test_long_trip_penalty(self):
        assert duration_penalty(11) == 5.0
        assert duration_penalty(14) == 5.0


class TestTravelPenalty:
    def test_zero_for_free(self):
        assert travel_penalty(0.0) == 0.0

    def test_max_for_expensive(self):
        assert travel_penalty(150.0) == pytest.approx(15.0, rel=0.01)

    def test_capped(self):
        assert travel_penalty(300.0) == 15.0


class TestCalculateScore:
    def test_score_in_range(self):
        trip = _make_trip()
        costs = _make_costs()
        score = calculate_score(trip, costs)
        assert 0.0 <= score <= 100.0

    def test_germany_gets_penalty(self):
        trip = _make_trip()
        costs_de = _make_costs(country_code="DE")
        costs_hu = _make_costs(country_code="HU")
        assert calculate_score(trip, costs_de) < calculate_score(trip, costs_hu)

    def test_cheap_scores_higher_than_expensive(self):
        trip = _make_trip()
        cheap = _make_costs(price_per_night=20.0, flight_total=50.0)
        expensive = _make_costs(price_per_night=90.0, flight_total=200.0)
        assert calculate_score(trip, cheap) > calculate_score(trip, expensive)

    def test_never_negative(self):
        trip = _make_trip()
        # Extreme Kosten → Score sollte nicht negativ werden
        costs = _make_costs(
            country_code="DE",
            price_per_night=200.0,
            flight_total=500.0,
            train_total=300.0,
        )
        score = calculate_score(trip, costs)
        assert score >= 0.0


class TestBuildDeal:
    def test_returns_deal(self):
        trip = _make_trip()
        costs = _make_costs()
        deal = build_deal(trip, costs)
        assert isinstance(deal, Deal)
        assert deal.trip is trip
        assert deal.costs is costs
        assert 0.0 <= deal.score <= 100.0


class TestIsWithinBudget:
    def test_within_budget(self):
        # 50€/Person/Nacht → OK
        costs = _make_costs(price_per_night=45.0, flight_total=80.0, local_daily=30.0)
        assert is_within_budget(costs)

    def test_over_budget(self):
        # Sehr teuer → über Budget
        costs = _make_costs(
            price_per_night=150.0,
            flight_total=800.0,
            train_total=200.0,
            local_daily=80.0,
            nights=3,
        )
        assert not is_within_budget(costs)
