"""Länderbewertung und Langweilig-Strafen für den Deal Score."""
from __future__ import annotations

# Langweilig-Strafe pro Land (ISO-2-Code)
BORING_PENALTY: dict[str, float] = {
    "DE": 40.0,   # Deutschland – tot, will keiner hin
    "AT": 15.0,   # Österreich – langweilig
    "CH": 15.0,   # Schweiz – langweilig
    "FR": 5.0,    # Frankreich – Standard
    "NL": 5.0,    # Niederlande – Standard
    "BE": 5.0,    # Belgien – Standard
    "DK": 5.0,    # Dänemark – Standard
}

# Geschätzte Tageskosten vor Ort pro Person (€) nach Ländergruppe
LOCAL_DAILY_COST: dict[str, float] = {
    # Sehr günstig
    "AL": 25, "MK": 25, "BA": 28, "RS": 28, "ME": 30, "XK": 25,
    "MD": 22, "UA": 20, "BY": 20, "AM": 25, "GE": 28, "AZ": 30,
    "TR": 30, "EG": 25, "TN": 28, "MA": 30,
    # Günstig
    "BG": 32, "RO": 32, "HU": 35, "PL": 35, "SK": 35, "CZ": 38,
    "HR": 40, "SI": 40, "LT": 35, "LV": 35, "EE": 38,
    "PT": 42, "GR": 42, "MT": 45, "CY": 45,
    # Mittel
    "ES": 48, "IT": 50, "DE": 50, "AT": 52, "CH": 75,
    "FR": 55, "NL": 55, "BE": 52, "LU": 60,
    "DK": 60, "SE": 62, "FI": 60, "NO": 75,
    "GB": 60, "IE": 60,
    # Default für alle anderen
    "_default": 45,
}


def boring_penalty(country_code: str) -> float:
    """Gibt die Langweilig-Strafe für ein Land zurück."""
    return BORING_PENALTY.get(country_code.upper(), 0.0)


def local_daily_cost(country_code: str) -> float:
    """Geschätzte Tageskosten vor Ort pro Person in €."""
    return LOCAL_DAILY_COST.get(country_code.upper(), LOCAL_DAILY_COST["_default"])
