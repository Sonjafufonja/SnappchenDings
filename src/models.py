"""Datenmodelle für Trips, Kosten und Deals."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class TravelWindow:
    """Ein mögliches Reisefenster (z.B. Osterferien)."""
    name: str
    start: date
    end: date
    school_days_skipped: int = 0

    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days + 1

    def __repr__(self) -> str:
        return (
            f"TravelWindow({self.name!r}, {self.start} – {self.end}, "
            f"{self.duration_days}d, schwänzen={self.school_days_skipped})"
        )


@dataclass
class TripOption:
    """Eine konkrete Trip-Option innerhalb eines Reisefensters."""
    window: TravelWindow
    depart: date
    return_date: date

    @property
    def nights(self) -> int:
        return (self.return_date - self.depart).days

    def __repr__(self) -> str:
        return f"TripOption({self.depart} – {self.return_date}, {self.nights} Nächte)"


@dataclass
class FlightResult:
    """Ergebnis einer Flugsuche."""
    origin_iata: str
    destination_iata: str
    destination_city: str
    destination_country: str
    destination_country_code: str
    price_total: float          # Gesamtpreis für 2 Personen (Hin+Rück)
    departure_at: str
    return_at: str
    deep_link: str = ""


@dataclass
class TrainResult:
    """Ergebnis einer Zugsuche."""
    origin: str
    destination: str
    price_total: float          # Gesamtpreis für 2 Personen (Hin+Rück)
    duration_minutes: int = 0
    is_estimate: bool = False


@dataclass
class AccommodationResult:
    """Ergebnis einer Unterkunfts-Suche."""
    city: str
    country: str
    price_per_night: float      # pro Nacht (1 Zimmer, 2 Personen)
    nights: int
    total_price: float
    source: str = "estimate"    # "amadeus" | "estimate"


@dataclass
class DailyLocalCost:
    """Geschätzte Tageskosten vor Ort."""
    country_code: str
    cost_per_person_per_day: float


@dataclass
class TripCost:
    """Gesamtkostenberechnung für einen Trip (2 Personen)."""
    flight: FlightResult
    train: TrainResult
    accommodation: AccommodationResult
    local_cost_per_person_per_day: float
    nights: int

    @property
    def total_cost(self) -> float:
        local = self.local_cost_per_person_per_day * 2 * self.nights
        return (
            self.flight.price_total
            + self.train.price_total
            + self.accommodation.total_price
            + local
        )

    @property
    def cost_per_person(self) -> float:
        return self.total_cost / 2

    @property
    def cost_per_person_per_night(self) -> float:
        if self.nights == 0:
            return float("inf")
        return self.cost_per_person / self.nights


@dataclass
class Deal:
    """Ein vollständiger Deal mit Score."""
    trip: TripOption
    costs: TripCost
    score: float
    rank: int = 0

    @property
    def destination_city(self) -> str:
        return self.costs.flight.destination_city

    @property
    def destination_country(self) -> str:
        return self.costs.flight.destination_country
