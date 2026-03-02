"""Zugsuche Braunschweig → Flughafen via v6.db.transport.rest."""
from __future__ import annotations

import logging

import httpx

from .config import DB_REST_BASE_URL, HTTP_TIMEOUT, NUM_TRAVELERS, ORIGIN_CITY
from .models import TrainResult

logger = logging.getLogger(__name__)

# Fallback: Entfernungsschätzung Braunschweig → Flughafenstadt (km)
_DISTANCE_KM: dict[str, int] = {
    "Berlin": 230,
    "Bremen": 100,
    "Köln": 320,
    "Dresden": 380,
    "Dortmund": 280,
    "Düsseldorf": 310,
    "Erfurt": 220,
    "Friedrichshafen": 650,
    "Karlsruhe": 430,
    "Memmingen": 600,
    "Münster": 230,
    "Frankfurt": 330,
    "Westerland": 380,
    "Hannover": 55,
    "Hamburg": 170,
    "Hahn": 380,
    "Kiel": 240,
    "Leipzig": 210,
    "Lübeck": 220,
    "München": 620,
    "Kleve": 360,
    "Nürnberg": 440,
    "Paderborn": 160,
    "Saarbrücken": 500,
    "Stuttgart": 480,
}

# Preis-Schätzung: ~0.10€/km mit Sparpreis-Faktor
_PRICE_PER_KM: float = 0.10


def _estimate_price(city: str) -> float:
    """Schätzt den Zugpreis Braunschweig → Stadt (eine Richtung, 1 Person)."""
    km = _DISTANCE_KM.get(city, 400)
    return max(9.0, km * _PRICE_PER_KM)


def _search_db_rest(destination_city: str) -> tuple[float, int] | None:
    """
    Sucht eine Zugverbindung über die DB REST API.

    Returns:
        (preis_pro_person, dauer_minuten) oder None bei Fehler.
    """
    # Haltestellensuche für Origin
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            # Zielbahnhof suchen
            r = client.get(
                f"{DB_REST_BASE_URL}/locations",
                params={"query": destination_city, "results": 1},
            )
            r.raise_for_status()
            locations = r.json()
            if not locations:
                return None
            dest_id = str(locations[0]["id"])

            # Braunschweig Hbf ID: 8000049
            journeys_r = client.get(
                f"{DB_REST_BASE_URL}/journeys",
                params={
                    "from": "8000049",
                    "to": dest_id,
                    "results": 1,
                    "language": "de",
                },
            )
            journeys_r.raise_for_status()
            journeys_data = journeys_r.json()
    except httpx.HTTPError as exc:
        logger.debug("DB REST API Fehler: %s", exc)
        return None
    except Exception as exc:
        logger.debug("Unerwarteter Fehler DB REST: %s", exc)
        return None

    journeys = journeys_data.get("journeys", [])
    if not journeys:
        return None

    journey = journeys[0]

    # Preis aus der API (oft nicht verfügbar)
    price: float | None = None
    for leg in journey.get("legs", []):
        p = leg.get("price")
        if p and isinstance(p, dict):
            amount = p.get("amount")
            if amount is not None:
                price = float(amount)
                break

    # Dauer berechnen
    legs = journey.get("legs", [])
    duration_min = 0
    if legs:
        try:
            from datetime import datetime
            dep = datetime.fromisoformat(legs[0]["departure"])
            arr = datetime.fromisoformat(legs[-1]["arrival"])
            duration_min = int((arr - dep).total_seconds() / 60)
        except Exception:
            duration_min = 0

    return price, duration_min


def get_train_cost(destination_city: str) -> TrainResult:
    """
    Berechnet Zugkosten Braunschweig → Flughafenstadt (Hin+Rück, 2 Personen).

    Args:
        destination_city: Zielstadt (z.B. "Hamburg")

    Returns:
        TrainResult mit Gesamtpreis für 2 Personen (Hin+Rück).
    """
    result = _search_db_rest(destination_city)

    if result is not None:
        price_one_way, duration_min = result
        if price_one_way and price_one_way > 0:
            total = price_one_way * 2 * NUM_TRAVELERS  # Hin+Rück × 2 Personen
            return TrainResult(
                origin=ORIGIN_CITY,
                destination=destination_city,
                price_total=total,
                duration_minutes=duration_min,
                is_estimate=False,
            )

    # Fallback: Schätzung
    estimated_one_way = _estimate_price(destination_city)
    total = estimated_one_way * 2 * NUM_TRAVELERS
    return TrainResult(
        origin=ORIGIN_CITY,
        destination=destination_city,
        price_total=total,
        duration_minutes=0,
        is_estimate=True,
    )
