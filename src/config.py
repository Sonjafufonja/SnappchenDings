"""Konfiguration und API-Keys."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Lade .env aus dem Projekt-Root
_root = Path(__file__).parent.parent
load_dotenv(_root / ".env")

# API Keys
KIWI_API_KEY: str = os.getenv("KIWI_API_KEY", "")
AMADEUS_API_KEY: str = os.getenv("AMADEUS_API_KEY", "")
AMADEUS_API_SECRET: str = os.getenv("AMADEUS_API_SECRET", "")

# Reise-Einstellungen
NUM_TRAVELERS: int = 2
MAX_BUDGET_PER_PERSON_PER_DAY: float = 100.0
MAX_TRIP_NIGHTS: int = 14
MIN_TRIP_NIGHTS: int = 2
MAX_SCHOOL_DAYS_SKIP: int = 2

# Kiwi.com API
KIWI_BASE_URL: str = "https://api.tequila.kiwi.com"

# DB REST API
DB_REST_BASE_URL: str = "https://v6.db.transport.rest"

# Amadeus API
AMADEUS_AUTH_URL: str = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_HOTELS_URL: str = "https://test.api.amadeus.com/v3/shopping/hotel-offers"

# Braunschweig als Start-Bahnhof
ORIGIN_CITY: str = "Braunschweig"
ORIGIN_STATION_ID: str = "8000049"  # EVA-Nummer Braunschweig Hbf

# HTTP Timeout
HTTP_TIMEOUT: float = 20.0
