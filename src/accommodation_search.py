"""Unterkunfts-Suche via Amadeus API (primär) oder Schätzung (Fallback)."""
from __future__ import annotations

import logging
from datetime import date

import httpx

from .config import (
    AMADEUS_API_KEY, AMADEUS_API_SECRET, AMADEUS_AUTH_URL,
    AMADEUS_HOTELS_URL, HTTP_TIMEOUT, NUM_TRAVELERS,
)
from .destinations import local_daily_cost
from .models import AccommodationResult

logger = logging.getLogger(__name__)

# Amadeus Token-Cache (einfach, nicht thread-safe)
_amadeus_token: str | None = None


def _get_amadeus_token() -> str | None:
    """Holt oder erneuert den Amadeus OAuth2-Token."""
    global _amadeus_token
    if _amadeus_token:
        return _amadeus_token
    if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
        return None
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.post(
                AMADEUS_AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": AMADEUS_API_KEY,
                    "client_secret": AMADEUS_API_SECRET,
                },
            )
            r.raise_for_status()
            _amadeus_token = r.json().get("access_token")
            return _amadeus_token
    except Exception as exc:
        logger.debug("Amadeus Auth Fehler: %s", exc)
        return None


def _search_amadeus(
    city: str,
    country_code: str,
    check_in: date,
    check_out: date,
) -> float | None:
    """
    Sucht Hotelpreise über die Amadeus API.

    Returns:
        Durchschnittlicher Preis pro Nacht (1 Zimmer) oder None.
    """
    token = _get_amadeus_token()
    if not token:
        return None

    nights = (check_out - check_in).days
    if nights <= 0:
        return None

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                AMADEUS_HOTELS_URL,
                params={
                    "cityCode": city[:3].upper(),
                    "checkInDate": check_in.isoformat(),
                    "checkOutDate": check_out.isoformat(),
                    "adults": NUM_TRAVELERS,
                    "roomQuantity": 1,
                    "currency": "EUR",
                    "bestRateOnly": True,
                    "sort": "PRICE",
                    "max": 5,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.debug("Amadeus Hotel Fehler: %s", exc)
        return None

    offers = data.get("data", [])
    if not offers:
        return None

    prices = []
    for offer in offers:
        for room_offer in offer.get("offers", []):
            try:
                total = float(room_offer["price"]["total"])
                prices.append(total / nights)
            except (KeyError, ValueError):
                continue

    if not prices:
        return None

    return min(prices)


# Fallback-Preise pro Nacht (1 Zimmer, 2 Personen) nach Ländergruppe
_FALLBACK_NIGHT_PRICE: dict[str, float] = {
    # Sehr günstig
    "AL": 35, "MK": 30, "BA": 38, "RS": 35, "ME": 45, "XK": 28,
    "MD": 25, "UA": 25, "BY": 25, "AM": 35, "GE": 40, "AZ": 45,
    "TR": 35, "EG": 30, "TN": 35, "MA": 40,
    # Günstig
    "BG": 38, "RO": 40, "HU": 45, "PL": 45, "SK": 48, "CZ": 50,
    "HR": 55, "SI": 55, "LT": 45, "LV": 45, "EE": 50,
    "PT": 60, "GR": 58, "MT": 65, "CY": 65,
    # Mittel
    "ES": 70, "IT": 75, "DE": 80, "AT": 80, "CH": 110,
    "FR": 85, "NL": 85, "BE": 78, "LU": 95,
    "DK": 90, "SE": 95, "FI": 88, "NO": 110,
    "GB": 90, "IE": 90,
    "_default": 65,
}


def _fallback_price(country_code: str) -> float:
    """Schätzt den Preis pro Nacht für 1 Zimmer (2 Personen)."""
    return _FALLBACK_NIGHT_PRICE.get(country_code.upper(), _FALLBACK_NIGHT_PRICE["_default"])


def get_accommodation(
    city: str,
    country: str,
    country_code: str,
    check_in: date,
    check_out: date,
) -> AccommodationResult:
    """
    Sucht die günstigste Unterkunft für einen Trip.

    Args:
        city: Zielstadt
        country: Zielland
        country_code: ISO-2-Code des Ziellandes
        check_in: Anreisedatum
        check_out: Abreisedatum

    Returns:
        AccommodationResult mit Preis pro Nacht und Gesamtpreis.
    """
    nights = (check_out - check_in).days
    if nights <= 0:
        nights = 1

    # Primär: Amadeus API
    amadeus_price = _search_amadeus(city, country_code, check_in, check_out)
    if amadeus_price and amadeus_price > 0:
        return AccommodationResult(
            city=city,
            country=country,
            price_per_night=amadeus_price,
            nights=nights,
            total_price=amadeus_price * nights,
            source="amadeus",
        )

    # Fallback: Schätzung
    estimated = _fallback_price(country_code)
    return AccommodationResult(
        city=city,
        country=country,
        price_per_night=estimated,
        nights=nights,
        total_price=estimated * nights,
        source="estimate",
    )
