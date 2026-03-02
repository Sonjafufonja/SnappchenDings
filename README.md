# SnappchenDings 🏷️

Eine **Schnäppchen-Finder App** für Sonja, die automatisch die besten Reise-Deals findet – Flüge, Zugverbindungen und Unterkünfte, passend zu den Schulferien Niedersachsen 2026.

---

## Was macht die App?

SnappchenDings durchsucht automatisch:
- **Flüge** von allen deutschen Flughäfen (via Kiwi.com Tequila API)
- **Zugverbindungen** Braunschweig → Flughafen (via DB REST API, kostenlos)
- **Unterkünfte** am Zielort (via Amadeus API oder Schätzung)

Für jeden möglichen Trip wird ein **Deal Score** (0–100) berechnet. Je höher, desto besser das Schnäppchen. Die App filtert automatisch nach dem Budget (max. 100 € pro Person pro Nacht) und zeigt die Top-Deals an.

---

## Nutzer-Profil

| Eigenschaft | Wert |
|---|---|
| Startort | Braunschweig, Niedersachsen |
| Situation | Schüler (reist nur in schulfreien Zeiten) |
| Budget | max. 100 € pro Person pro Tag |
| Reisende | 2 Personen |
| Max. Trip-Dauer | 14 Tage |
| Max. Schule schwänzen | 2 Tage |

---

## Installation

### Voraussetzungen
- Python 3.11+
- pip

### Schritte

```bash
# 1. Repository klonen
git clone https://github.com/Sonjafufonja/SnappchenDings.git
cd SnappchenDings

# 2. Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# oder: .venv\Scripts\activate  # Windows

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. API-Keys konfigurieren
cp .env.example .env
# .env mit deinen API-Keys befüllen (siehe unten)
```

---

## API-Keys

### Kiwi.com Tequila (Pflicht für echte Flugsuche)

1. Gehe zu [tequila.kiwi.com](https://tequila.kiwi.com/)
2. Registriere einen kostenlosen Account
3. Erstelle einen API-Key
4. Trage ihn in `.env` ein:

```
KIWI_API_KEY=dein_api_key_hier
```

### Amadeus (Optional, für bessere Hotelsuche)

1. Gehe zu [developers.amadeus.com](https://developers.amadeus.com/)
2. Erstelle einen kostenlosen Account (Self-Service)
3. Erstelle eine neue App → du erhältst `API Key` und `API Secret`
4. Trage sie in `.env` ein:

```
AMADEUS_API_KEY=dein_key_hier
AMADEUS_API_SECRET=dein_secret_hier
```

> **Hinweis:** Ohne API-Keys läuft die App mit Schätzwerten (kein Fehler, aber keine echten Preise).

---

## Starten

```bash
python -m src.main
```

---

## Beispiel-Output

```
╔══════════════════════════════════════╗
║  🏆 TOP SCHNÄPPCHEN für Sonja        ║
╚══════════════════════════════════════╝

╭─ #1  🔥 Score: 87.3 | Budapest 🇭🇺 ───────────────────╮
│ 📅  23.03 – 27.03 (Osterferien, 4 Nächte)              │
│ ✈️   HAM → BUD | 47€ (2 Pers.)                          │
│ 🚂  Braunschweig → Hamburg: 34€ (Hin+Rück, 2 Pers.)    │
│ 🏠  Hotel/Unterkunft: 45€/Nacht = 180€                  │
│ 🍕  Vor Ort ca. 35€/Tag/Pers.                           │
│ 💰  GESAMT: 541€ | PRO PERSON: 270€ | Pro Nacht/Pers: 67.75€│
│ 🏫  Schule geschwänzt: 0 Tage                           │
╰─────────────────────────────────────────────────────────╯
```

---

## Erklärung des Deal Scores

Der Deal Score bewertet jede Reise auf einer Skala von 0–100. **Schlechte Deals werden abgezogen**, gute bekommen keinen Bonus.

```
DEAL SCORE = 100 - Preis-Strafe - Langweilig-Strafe - Dauer-Strafe - Anreise-Strafe
```

| Komponente | Formel |
|---|---|
| **Preis-Strafe** | 0–50 Punkte, je teurer pro Nacht/Person |
| **Langweilig-Strafe** | Deutschland −40, Österreich/Schweiz −15, FR/NL/BE/DK −5, Rest 0 |
| **Dauer-Strafe** | < 2 Nächte: −15, > 10 Nächte: −5, sonst 0 |
| **Anreise-Strafe** | 0–15 Punkte, je teurer der Zug zum Flughafen |

### Beispiele
- Budapest (HU), 4 Nächte, 67€/Person/Nacht → Score ~87
- Paris (FR), 3 Nächte, 95€/Person/Nacht → Score ~42 (teuer + Langweilig-Strafe)
- Hamburg (DE), 2 Nächte → Score ~10 (Inland-Strafe)

---

## Projektstruktur

```
SnappchenDings/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── index.html                   # Einfache Web-Wunschliste (Original)
├── src/
│   ├── __init__.py
│   ├── main.py                  # Einstiegspunkt, CLI
│   ├── config.py                # Settings, API Keys
│   ├── travel_windows.py        # Schulferien & Reisefenster-Logik
│   ├── airports.py              # Alle deutschen Flughäfen
│   ├── flight_search.py         # Kiwi.com API Integration
│   ├── train_search.py          # DB REST API Integration
│   ├── accommodation_search.py  # Amadeus API + Fallback
│   ├── deal_score.py            # Deal Score Berechnung
│   ├── destinations.py          # Länderbewertung & Strafpunkte
│   └── models.py                # Dataclasses für Trip, Cost, etc.
└── tests/
    ├── __init__.py
    ├── test_travel_windows.py
    ├── test_deal_score.py
    └── test_models.py
```

---

## Tests ausführen

```bash
pytest tests/
```

---

## Tech Stack

| Paket | Zweck |
|---|---|
| `httpx` | HTTP-Requests (Kiwi, DB REST, Amadeus) |
| `python-dotenv` | API-Keys aus `.env` laden |
| `rich` | Schöne Terminal-Ausgabe |
| `pytest` | Unit-Tests |
