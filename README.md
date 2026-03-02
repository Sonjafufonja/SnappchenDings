# SnappchenDings

Eine Web-App zum Verwalten von Schnäppchen, Wunschartikeln und **Reise-Deals**.

## Features

### 🏷️ Wunschliste (`index.html`)
- **Wunschliste** – Füge Artikel hinzu, die du haben möchtest.
- **Hab** – Markiere Artikel als „Hab" (bereits besessen/gekauft).
- Alle Daten werden lokal im Browser gespeichert (LocalStorage).

### ✈️ Reise-Deal-Finder (`reise.html`)
- **Flugsuche** – Finde günstige Flüge über die Kiwi.com Tequila API. Ergebnisse werden nach Preis sortiert.
- **Bahnsuche** – Suche Zugverbindungen über die kostenlose DB transport.rest API (kein API-Key nötig!). Mit Autovervollständigung für Bahnhöfe.
- **Unterkünfte** – Direkte Weiterleitung zu Booking.com mit vorausgefüllten Reisedaten.
- API-Keys werden lokal im Browser gespeichert (LocalStorage).

## Verwendung

Öffne `index.html` oder `reise.html` direkt im Browser – keine Installation notwendig.

## API-Setup

### Flugsuche (Kiwi.com Tequila API)
1. Registriere dich kostenlos auf [tequila.kiwi.com](https://tequila.kiwi.com/portal/login)
2. Erstelle eine „Solution" und kopiere deinen API-Key
3. Trage den Key in der App unter ⚙️ Einstellungen ein

### Bahnsuche (DB transport.rest)
Kein Setup nötig – die API ist öffentlich und kostenlos verfügbar.

### Unterkünfte (Booking.com)
Kein Setup nötig – die Suche leitet direkt zu Booking.com weiter.
