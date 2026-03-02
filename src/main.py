"""Hauptlogik – Orchestrator und CLI für den Schnäppchen-Finder."""
from __future__ import annotations

import logging
import sys
from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from .travel_windows import get_travel_windows, get_trip_options
from .airports import GERMAN_AIRPORTS, AIRPORT_TRAIN_CITY
from .flight_search import search_flights
from .train_search import get_train_cost
from .accommodation_search import get_accommodation
from .deal_score import build_deal, is_within_budget
from .destinations import local_daily_cost
from .models import TripCost, Deal, FlightResult
from .config import MAX_BUDGET_PER_PERSON_PER_DAY, NUM_TRAVELERS

console = Console()
logger = logging.getLogger(__name__)

# Flaggen-Mapping (ISO-2 → Emoji)
_FLAGS: dict[str, str] = {
    "AT": "🇦🇹", "BE": "🇧🇪", "BG": "🇧🇬", "HR": "🇭🇷", "CY": "🇨🇾",
    "CZ": "🇨🇿", "DK": "🇩🇰", "EE": "🇪🇪", "FI": "🇫🇮", "FR": "🇫🇷",
    "DE": "🇩🇪", "GR": "🇬🇷", "HU": "🇭🇺", "IS": "🇮🇸", "IE": "🇮🇪",
    "IT": "🇮🇹", "LV": "🇱🇻", "LT": "🇱🇹", "LU": "🇱🇺", "MT": "🇲🇹",
    "NL": "🇳🇱", "NO": "🇳🇴", "PL": "🇵🇱", "PT": "🇵🇹", "RO": "🇷🇴",
    "SK": "🇸🇰", "SI": "🇸🇮", "ES": "🇪🇸", "SE": "🇸🇪", "CH": "🇨🇭",
    "GB": "🇬🇧", "TR": "🇹🇷", "RS": "🇷🇸", "BA": "🇧🇦", "ME": "🇲🇪",
    "AL": "🇦🇱", "MK": "🇲🇰", "GE": "🇬🇪", "AM": "🇦🇲", "AZ": "🇦🇿",
    "UA": "🇺🇦", "MD": "🇲🇩", "MA": "🇲🇦", "TN": "🇹🇳", "EG": "🇪🇬",
    "JP": "🇯🇵", "KR": "🇰🇷", "TH": "🇹🇭", "VN": "🇻🇳", "ID": "🇮🇩",
    "MY": "🇲🇾", "SG": "🇸🇬", "PH": "🇵🇭", "IN": "🇮🇳", "MX": "🇲🇽",
    "BR": "🇧🇷", "AR": "🇦🇷", "CO": "🇨🇴", "CL": "🇨🇱", "PE": "🇵🇪",
    "US": "🇺🇸", "CA": "🇨🇦", "AU": "🇦🇺", "NZ": "🇳🇿", "ZA": "🇿🇦",
    "KE": "🇰🇪", "TZ": "🇹🇿", "MZ": "🇲🇿", "MU": "🇲🇺", "CV": "🇨🇻",
}


def _flag(code: str) -> str:
    return _FLAGS.get(code.upper(), "🌍")


def _format_date(d: date) -> str:
    return d.strftime("%d.%m.%y")


def find_deals(max_results: int = 10, airports: list[str] | None = None) -> list[Deal]:
    """
    Hauptfunktion: Findet die besten Reise-Deals für Sonja.

    Args:
        max_results: Anzahl der Top-Deals die zurückgegeben werden sollen.
        airports: Liste von IATA-Codes (None = alle deutschen Flughäfen).

    Returns:
        Liste der besten Deals, sortiert nach Score (höchster zuerst).
    """
    all_deals: list[Deal] = []
    airport_list = airports or [a["iata"] for a in GERMAN_AIRPORTS]

    windows = get_travel_windows()

    with console.status("[bold green]Suche läuft…[/]"):
        for window in windows:
            trip_options = get_trip_options(window)
            if not trip_options:
                continue

            console.log(f"[cyan]{window.name}[/] – {len(trip_options)} Trip-Optionen")

            # Für jede Trip-Option: Flüge von allen Flughäfen suchen
            for trip in trip_options:
                for iata in airport_list:
                    flights = search_flights(iata, trip.depart, trip.return_date)
                    if not flights:
                        continue

                    # Nur die günstigste Verbindung pro Flughafen weiterverarbeiten
                    best_flight = min(flights, key=lambda f: f.price_total)

                    _process_flight(trip, best_flight, all_deals)

    # Filtern: Budget einhalten
    within_budget = [d for d in all_deals if is_within_budget(d.costs)]

    # Sortieren nach Score
    within_budget.sort(key=lambda d: d.score, reverse=True)

    # Rang vergeben
    for i, deal in enumerate(within_budget[:max_results], start=1):
        deal.rank = i

    return within_budget[:max_results]


def _process_flight(trip, flight: FlightResult, deals: list[Deal]) -> None:
    """Verarbeitet einen Flug: sucht Zug + Unterkunft und erstellt Deal."""
    try:
        city = AIRPORT_TRAIN_CITY.get(flight.origin_iata, flight.origin_iata)
        train = get_train_cost(city)

        accommodation = get_accommodation(
            city=flight.destination_city,
            country=flight.destination_country,
            country_code=flight.destination_country_code,
            check_in=trip.depart,
            check_out=trip.return_date,
        )

        daily_cost = local_daily_cost(flight.destination_country_code)

        costs = TripCost(
            flight=flight,
            train=train,
            accommodation=accommodation,
            local_cost_per_person_per_day=daily_cost,
            nights=trip.nights,
        )

        deal = build_deal(trip, costs)
        deals.append(deal)
    except Exception as exc:
        logger.debug("Fehler beim Verarbeiten eines Flights: %s", exc)


def print_deals(deals: list[Deal]) -> None:
    """Gibt die Top-Deals schön formatiert aus."""
    if not deals:
        console.print(
            Panel(
                "[yellow]Keine Deals gefunden. Bitte API-Keys prüfen![/]",
                title="😔 Keine Schnäppchen",
            )
        )
        return

    console.print()
    console.print(Panel(
        "[bold gold1]🏆 TOP SCHNÄPPCHEN für Sonja[/]",
        box=box.DOUBLE_EDGE,
    ))
    console.print()

    for deal in deals:
        t = deal.trip
        c = deal.costs
        f = c.flight
        flag = _flag(f.destination_country_code)

        # Score-Farbe
        if deal.score >= 70:
            score_color = "green"
        elif deal.score >= 50:
            score_color = "yellow"
        else:
            score_color = "red"

        score_str = f"[{score_color}]Score: {deal.score:.1f}[/]"
        title = (
            f"#{deal.rank}  🔥 {score_str} | "
            f"{f.destination_city} {flag}"
        )

        lines = [
            f"📅  [bold]{_format_date(t.depart)} – {_format_date(t.return_date)}[/] "
            f"({t.window.name}, {t.nights} Nächte)",
            f"✈️   {f.origin_iata} → {f.destination_iata} | "
            f"[cyan]{f.price_total:.0f}€[/] ({NUM_TRAVELERS} Pers.)",
        ]

        train_note = " (Schätzung)" if c.train.is_estimate else ""
        lines.append(
            f"🚂  Braunschweig → {c.train.destination}: "
            f"[cyan]{c.train.price_total:.0f}€[/] (Hin+Rück, {NUM_TRAVELERS} Pers.){train_note}"
        )

        accom_note = " (Schätzung)" if c.accommodation.source == "estimate" else ""
        lines.append(
            f"🏠  Hotel/Unterkunft: [cyan]{c.accommodation.price_per_night:.0f}€/Nacht[/] "
            f"= {c.accommodation.total_price:.0f}€{accom_note}"
        )

        lines.append(
            f"🍕  Vor Ort ca. [cyan]{c.local_cost_per_person_per_day:.0f}€/Tag/Pers.[/]"
        )

        lines.append(
            f"💰  GESAMT: [bold]{c.total_cost:.0f}€[/] | "
            f"PRO PERSON: [bold green]{c.cost_per_person:.0f}€[/] | "
            f"Pro Nacht/Pers: [bold]{c.cost_per_person_per_night:.2f}€[/]"
        )

        if t.window.school_days_skipped > 0:
            lines.append(
                f"🏫  [yellow]Schule geschwänzt: {t.window.school_days_skipped} Tag(e)[/]"
            )
        else:
            lines.append("🏫  Schule geschwänzt: 0 Tage")

        if f.deep_link:
            lines.append(f"🔗  [link={f.deep_link}]{f.deep_link[:60]}…[/link]")

        console.print(Panel(
            "\n".join(lines),
            title=title,
            box=box.ROUNDED,
        ))

    console.print()
    console.print(
        f"[dim]Alle Preise in EUR · Budget: max {MAX_BUDGET_PER_PERSON_PER_DAY:.0f}€/Person/Nacht · "
        f"Preise können abweichen[/dim]"
    )


def main() -> None:
    """Einstiegspunkt für die CLI."""
    logging.basicConfig(level=logging.WARNING)

    console.print(Panel(
        "[bold]🔍 SnappchenDings – Schnäppchen-Finder für Sonja[/]\n"
        "Suche die besten Reise-Deals für Schulferien 2026…",
        box=box.DOUBLE_EDGE,
    ))

    deals = find_deals(max_results=10)
    print_deals(deals)


if __name__ == "__main__":
    main()
