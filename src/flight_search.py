"""Flugsuche via Kiwi.com Tequila API."""
from __future__ import annotations

import logging
from datetime import date

import httpx

from .config import KIWI_API_KEY, KIWI_BASE_URL, HTTP_TIMEOUT, NUM_TRAVELERS
from .models import FlightResult

logger = logging.getLogger(__name__)

SEARCH_ENDPOINT = f"{KIWI_BASE_URL}/v2/search"


def _make_headers() -> dict[str, str]:
    return {"apikey": KIWI_API_KEY}


def search_flights(
    origin_iata: str,
    depart_date: date,
    return_date: date,
    max_results: int = 5,
) -> list[FlightResult]:
    """
    Sucht Hin- und Rückflüge von einem deutschen Flughafen.

    Args:
        origin_iata: IATA-Code des Abflughafens (z.B. "HAM")
        depart_date: Hinflug-Datum
        return_date: Rückflug-Datum
        max_results: Maximale Anzahl Ergebnisse pro Flughafen

    Returns:
        Liste von FlightResult-Objekten, sortiert nach Preis.
    """
    if not KIWI_API_KEY:
        logger.warning("Kein KIWI_API_KEY gesetzt – Flugsuche übersprungen.")
        return []

    params = {
        "fly_from": origin_iata,
        "fly_to": "anywhere",
        "date_from": depart_date.strftime("%d/%m/%Y"),
        "date_to": depart_date.strftime("%d/%m/%Y"),
        "return_from": return_date.strftime("%d/%m/%Y"),
        "return_to": return_date.strftime("%d/%m/%Y"),
        "flight_type": "round",
        "adults": NUM_TRAVELERS,
        "curr": "EUR",
        "sort": "price",
        "limit": max_results,
        "one_for_city": 1,
        "partner_market": "de",
    }

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.get(
                SEARCH_ENDPOINT,
                params=params,
                headers=_make_headers(),
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.error("Kiwi API Fehler für %s: %s", origin_iata, exc)
        return []
    except Exception as exc:
        logger.error("Unerwarteter Fehler bei Kiwi API: %s", exc)
        return []

    results: list[FlightResult] = []
    for flight in data.get("data", []):
        country_to = flight.get("countryTo", {})
        city_to = flight.get("cityTo", "")
        country_code = country_to.get("code", "")
        country_name = country_to.get("name", "")
        destination_iata = flight.get("flyTo", "")

        # Inland-Flüge rausfiltern
        if country_code == "DE":
            continue

        price = float(flight.get("price", 0))
        deep_link = flight.get("deep_link", "")

        # Abflug- und Rückflugzeiten
        dep_str = flight.get("local_departure", "")
        ret_str = ""
        route = flight.get("route", [])
        if route:
            ret_str = route[-1].get("local_departure", "")

        results.append(FlightResult(
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            destination_city=city_to,
            destination_country=country_name,
            destination_country_code=country_code,
            price_total=price,
            departure_at=dep_str,
            return_at=ret_str,
            deep_link=deep_link,
        ))

    return results
