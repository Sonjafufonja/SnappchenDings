"""Deal Score Engine – bewertet Reise-Deals für Sonja."""
from __future__ import annotations

from .config import MAX_BUDGET_PER_PERSON_PER_DAY
from .destinations import boring_penalty
from .models import TripCost, Deal, TripOption

# Basis-Score
BASE_SCORE: float = 100.0

# Maximaler Preis-Abzug
MAX_PRICE_PENALTY: float = 50.0

# Preis-Referenz: ab diesem Preis pro Person/Nacht gibt es maximale Strafe
PRICE_PENALTY_MAX_THRESHOLD: float = MAX_BUDGET_PER_PERSON_PER_DAY

# Dauer-Strafen
SHORT_TRIP_PENALTY: float = 15.0   # < 2 Nächte
LONG_TRIP_PENALTY: float = 5.0     # > 10 Nächte
SHORT_TRIP_THRESHOLD: int = 2
LONG_TRIP_THRESHOLD: int = 10

# Anreise-Strafe: max 15 Punkte bei sehr teurer Anreise
MAX_TRAVEL_PENALTY: float = 15.0
TRAVEL_PENALTY_MAX_THRESHOLD: float = 150.0  # €, Zugkosten für 2 Personen H+R


def price_penalty(cost_per_person_per_night: float) -> float:
    """
    Preis-Strafe: Je teurer pro Nacht pro Person, desto mehr Abzug (0–50).
    """
    ratio = cost_per_person_per_night / PRICE_PENALTY_MAX_THRESHOLD
    return min(MAX_PRICE_PENALTY, MAX_PRICE_PENALTY * ratio)


def duration_penalty(nights: int) -> float:
    """Dauer-Strafe für sehr kurze oder sehr lange Trips."""
    if nights < SHORT_TRIP_THRESHOLD:
        return SHORT_TRIP_PENALTY
    if nights > LONG_TRIP_THRESHOLD:
        return LONG_TRIP_PENALTY
    return 0.0


def travel_penalty(train_cost_total: float) -> float:
    """Anreise-Strafe basierend auf den Zugkosten (0–15 Punkte)."""
    ratio = train_cost_total / TRAVEL_PENALTY_MAX_THRESHOLD
    return min(MAX_TRAVEL_PENALTY, MAX_TRAVEL_PENALTY * ratio)


def calculate_score(trip: TripOption, costs: TripCost) -> float:
    """
    Berechnet den Deal Score für einen Trip.

    DEAL SCORE = 100 - Preis-Strafe - Langweilig-Strafe - Dauer-Strafe - Anreise-Strafe

    Args:
        trip: Trip-Option mit Datum und Fenster
        costs: Kostenberechnung für den Trip

    Returns:
        Deal Score (0–100, höher = besser).
    """
    country_code = costs.flight.destination_country_code

    p_penalty = price_penalty(costs.cost_per_person_per_night)
    b_penalty = boring_penalty(country_code)
    d_penalty = duration_penalty(costs.nights)
    t_penalty = travel_penalty(costs.train.price_total)

    score = BASE_SCORE - p_penalty - b_penalty - d_penalty - t_penalty
    return max(0.0, round(score, 1))


def build_deal(trip: TripOption, costs: TripCost) -> Deal:
    """Erstellt ein Deal-Objekt mit berechnetem Score."""
    score = calculate_score(trip, costs)
    return Deal(trip=trip, costs=costs, score=score)


def is_within_budget(costs: TripCost) -> bool:
    """Prüft ob der Trip im Budget liegt (max 100€/Person/Tag)."""
    return costs.cost_per_person_per_night <= MAX_BUDGET_PER_PERSON_PER_DAY
