# SnappchenDings – Hosting-Anleitung

SnappchenDings ist eine **rein statische Web-App** (eine einzelne `index.html`-Datei,
kein Backend, kein Build-Schritt). Das macht das Hosting sehr einfach und
ermöglicht komplett **kostenlose** Optionen.

---

> ⚠️ **SICHERHEITSHINWEIS**  
> Teile niemals SSH-Zugangsdaten, Passwörter, API-Schlüssel oder andere Geheimnisse
> im Repository, in Issues oder Pull Requests. Füge solche Informationen grundsätzlich
> nur lokal oder über dedizierte Secrets-Manager (z. B. GitHub Actions Secrets,
> `.env`-Dateien, die in `.gitignore` eingetragen sind) ein.

---

## Inhaltsverzeichnis

1. [Kostenlose Cloud-Optionen](#1-kostenlose-cloud-optionen)
   - [GitHub Pages](#11-github-pages-empfohlen)
   - [Netlify](#12-netlify)
   - [Vercel](#13-vercel)
2. [Selbst-Hosting auf eigenem Ubuntu/Debian-Server (Apache)](#2-selbst-hosting-auf-eigenem-ubuntudebian-server-apache)
   - [Voraussetzungen](#21-voraussetzungen)
   - [Dateien übertragen](#22-dateien-übertragen)
   - [Apache Virtual Host anlegen](#23-apache-virtual-host-anlegen)
   - [TLS/HTTPS mit Let's Encrypt (Certbot)](#24-tlshttps-mit-lets-encrypt-certbot)
   - [Firewall](#25-firewall)
   - [Konfiguration prüfen und Apache neu laden](#26-konfiguration-prüfen-und-apache-neu-laden)
   - [Rollback](#27-rollback)
3. [Umgebungsvariablen / Secrets (Hinweis)](#3-umgebungsvariablen--secrets-hinweis)

---

## 1. Kostenlose Cloud-Optionen

Da die App keine Serverlogik benötigt, funktionieren alle Static-Site-Hoster
sofort und ohne Konfiguration.

### 1.1 GitHub Pages (empfohlen)

**Kostenlos**, direkt über GitHub, kein externes Konto nötig.

1. Stelle sicher, dass `index.html` im Repository-Wurzelverzeichnis liegt
   (bereits der Fall).
2. Öffne im Browser:
   `https://github.com/<DEIN-BENUTZERNAME>/SnappchenDings/settings/pages`
3. Wähle unter **Source** → **Deploy from a branch**.
4. Wähle Branch `main` und Ordner `/ (root)`, klicke **Save**.
5. Die App ist danach erreichbar unter:
   `https://<DEIN-BENUTZERNAME>.github.io/SnappchenDings/`

Kein weiterer Schritt notwendig. Bei jedem Push auf `main` wird automatisch
neu veröffentlicht.

### 1.2 Netlify

1. Erstelle ein kostenloses Konto auf [netlify.com](https://www.netlify.com).
2. Klicke **Add new site → Import an existing project** und verbinde GitHub.
3. Wähle das Repository `SnappchenDings`.
4. **Build command** und **Publish directory** leer lassen (kein Build nötig).
5. Klicke **Deploy site**.

Netlify vergibt automatisch eine `.netlify.app`-URL; eine eigene Domain lässt
sich in den Site-Einstellungen hinterlegen.

### 1.3 Vercel

1. Erstelle ein kostenloses Konto auf [vercel.com](https://vercel.com).
2. Klicke **Add New → Project**, importiere das GitHub-Repository.
3. Framework Preset: **Other** (kein Framework, kein Build).
4. Klicke **Deploy**.

---

## 2. Selbst-Hosting auf eigenem Ubuntu/Debian-Server (Apache)

Diese Anleitung geht davon aus, dass bereits **Apache 2** läuft und andere
Websites darauf gehostet werden. Der neue Virtual Host wird als **zusätzliche
Konfiguration** angelegt – bestehende Konfigurationen werden nicht verändert.

> ⚠️ Führe nach jeder Änderung an Apache-Konfigurationen immer
> `sudo apachectl configtest` aus, bevor du Apache neu lädst. Lade Apache
> nur neu (nicht restart), um laufende Verbindungen nicht zu unterbrechen.

### 2.1 Voraussetzungen

- Apache 2 ist installiert und läuft (`sudo systemctl status apache2`).
- Du hast einen DNS-Eintrag (A-Record), der deine Domain auf die Server-IP
  zeigt, **bevor** du Certbot verwendest.
- `rsync` oder `scp` ist auf deinem lokalen Rechner verfügbar.

### 2.2 Dateien übertragen

Ersetze `DEIN_BENUTZER`, `DEINE_SERVER_IP` und `example.com` durch deine
tatsächlichen Werte.

```bash
# Auf dem Server: Zielverzeichnis anlegen (sudo erforderlich, da /var/www root gehört)
ssh DEIN_BENUTZER@DEINE_SERVER_IP \
  "sudo mkdir -p /var/www/snappchendings"

# Lokal: Dateien übertragen
rsync -avz --delete \
  index.html \
  DEIN_BENUTZER@DEINE_SERVER_IP:/var/www/snappchendings/

# Auf dem Server: Berechtigungen setzen
ssh DEIN_BENUTZER@DEINE_SERVER_IP \
  "sudo chown -R www-data:www-data /var/www/snappchendings && \
   sudo chmod -R 755 /var/www/snappchendings"
```

### 2.3 Apache Virtual Host anlegen

Eine Beispiel-Konfigurationsdatei liegt unter
[`deploy/apache/snappchendings.conf`](../deploy/apache/snappchendings.conf).

```bash
# Vorlage auf den Server kopieren
scp deploy/apache/snappchendings.conf \
    DEIN_BENUTZER@DEINE_SERVER_IP:/tmp/snappchendings.conf

# Auf dem Server: Platzhalter ersetzen und aktivieren
# Hinweis: Prüfe die erzeugte Datei kurz mit `cat`, bevor du Apache neu lädst.
ssh DEIN_BENUTZER@DEINE_SERVER_IP << 'EOF'
  # Platzhalter YOUR_DOMAIN durch echte Domain ersetzen
  sed 's/YOUR_DOMAIN/example.com/g' /tmp/snappchendings.conf \
    | sudo tee /etc/apache2/sites-available/snappchendings.conf > /dev/null

  # Ergebnis kurz prüfen
  grep ServerName /etc/apache2/sites-available/snappchendings.conf

  # Konfiguration prüfen, BEVOR sie aktiviert wird
  sudo apachectl configtest

  # Nur wenn configtest "Syntax OK" meldet:
  sudo a2ensite snappchendings.conf
  sudo apachectl configtest   # nochmal prüfen
  sudo systemctl reload apache2
EOF
```

### 2.4 TLS/HTTPS mit Let's Encrypt (Certbot)

> ⚠️ Certbot verändert die Apache-Konfiguration. Führe vorher unbedingt
> `sudo apachectl configtest` aus und stelle sicher, dass der DNS-Eintrag
> bereits aktiv ist. Certbot-Fehler können vorhandene Konfigurationen nicht
> beschädigen, solange du `--apache` verwendest (Certbot nimmt nur die
> Zieldatei).

```bash
# Certbot installieren (falls noch nicht vorhanden)
sudo apt update
sudo apt install -y certbot python3-certbot-apache

# Zertifikat für deine Domain beantragen
# (ersetzt YOUR_DOMAIN durch deine tatsächliche Domain)
sudo certbot --apache -d YOUR_DOMAIN

# Certbot konfiguriert den Virtual Host automatisch für HTTPS
# und richtet eine automatische Erneuerung ein (cron / systemd timer).

# Konfiguration prüfen
sudo apachectl configtest
sudo systemctl reload apache2
```

Automatische Erneuerung testen:

```bash
sudo certbot renew --dry-run
```

### 2.5 Firewall

```bash
# UFW (Uncomplicated Firewall) – falls aktiv
sudo ufw allow 80/tcp    # HTTP (für Certbot-Challenge nötig)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw status
```

### 2.6 Konfiguration prüfen und Apache neu laden

**Immer vor dem Reload:**

```bash
sudo apachectl configtest
# Erwartete Ausgabe: "Syntax OK"

# Danach sicher neu laden (kein Restart, keine Unterbrechung):
sudo systemctl reload apache2
```

### 2.7 Rollback

Falls etwas schiefläuft, kannst du den Virtual Host sofort deaktivieren,
ohne andere Sites zu beeinflussen:

```bash
# Virtual Host deaktivieren
sudo a2dissite snappchendings.conf
sudo apachectl configtest
sudo systemctl reload apache2

# Optional: Konfigurationsdatei entfernen
sudo rm /etc/apache2/sites-available/snappchendings.conf
```

Um zur vorherigen Version der Dateien zurückzukehren:

```bash
# Auf dem Server: Verzeichnis leeren und neu befüllen
sudo rm -rf /var/www/snappchendings/*
# Dann gewünschte Version erneut mit rsync übertragen (siehe 2.2)
```

---

## 3. Umgebungsvariablen / Secrets (Hinweis)

SnappchenDings ist eine rein clientseitige App und benötigt keine
Umgebungsvariablen oder API-Schlüssel. Alle Daten verbleiben im Browser
(localStorage des Benutzers).

Sollte die App zukünftig um eine Backend-Komponente erweitert werden:

- Verwende `.env`-Dateien lokal und trage `.env` in `.gitignore` ein.
- Nutze für CI/CD Plattform-Secrets (z. B. GitHub Actions Secrets,
  Netlify Environment Variables) – niemals im Repository-Code oder in
  Commit-Messages.
- Rotiere Secrets sofort, wenn sie versehentlich committet wurden
  (`git filter-repo` oder GitHub Support kontaktieren).
