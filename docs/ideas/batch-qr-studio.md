# py-qr — Intelligente QR-Code Stapelverarbeitung (Batch-Studio)

## Problem Statement

Wie können wir es Nutzern ermöglichen, beliebig viele QR-Codes (z. B. YouTube-Links, URLs, Tischnummern oder vCards) aus CSV-Dateien oder der Zwischenablage in Sekunden im einheitlichen Design zu generieren und wahlweise als sauberes ZIP-Archiv oder druckfertigen A4-Etikettenbogen zu exportieren – ohne Tabellen-Frust und ohne Cloud-Zwang?

## Recommended Direction: "Smart Batch-Studio mit Dual-Export"

Eine leichtgewichtige, performante Batch-Funktion (als eigener Dialog oder Reiter), die sich nahtlos in die bestehende Architektur von `py-qr` einfügt:

### 1. Flexible Dateneingabe (Input)

* **Direktes Einfügen (Clipboard):** Ein Textfeld für Copy & Paste direkt aus Excel, Google Sheets oder Textdateien. Jede Zeile ergibt einen QR-Code (z. B. 30 YouTube-Links untereinander).
* **CSV- / Textdatei-Import:** Drag & Drop oder Datei-Auswahl. Automatische Trennzeichen-Erkennung (Komma, Semikolon, Tab).
* **Spaltenzuordnung:** Bei mehrspaltigen Daten wählt der Nutzer:
  * *Inhalts-Spalte:* URL, YouTube-Link, Text etc.
  * *Label-Spalte (optional):* Beschriftung / Dateiname (z. B. Videotitel oder Tischnummer).

### 2. Konsistentes Styling

* Alle im Generator eingestellten Gestaltungselemente (Modulformen wie Dots/Smooth, Vorder-/Hintergrundfarben, Ecken-Augen-Farbe, zentrales Emblem) werden automatisch auf den gesamten Batch angewendet.

### 3. Dual-Export (Output)

1. **ZIP-Archiv (Einzeldateien):**
   * Alle QR-Codes werden als saubere PNG- (oder SVG-) Einzeldateien generiert und in eine `.zip`-Datei gepackt.
   * Dateinamen richten sich nach der Label-Spalte oder einer sauberen Nummerierung (z. B. `01_youtube_video.png`, `02_youtube_video.png`).
2. **Druckfertiger DIN A4 Bogen (PDF):**
   * Automatische Anordnung auf Standard-Druckrastern (z. B. **3 × 8 = 24 Etiketten** pro Seite oder **2 × 4 = 8 Kärtchen** pro Seite) via `QPdfWriter`.
   * Jeder QR-Code erhält auf Wunsch eine zentrierte Textbeschriftung direkt unter dem Code.

## Key Assumptions to Validate

* [x] Auto-Erkennung von CSV-Trennzeichen (`csv.Sniffer` oder Heuristik) verarbeitet Excel-Exporte (Semikolon im DACH-Raum, Komma international) fehlerfrei.

* [x] Batch-Generierung von 100+ QR-Codes läuft in einem Hintergrund-`QThread` mit Fortschrittsbalken und bleibt unter 2 Sekunden.
* [x] Etiketten-Raster auf A4 (`QPdfWriter`) hält Standardmaße ein, sodass Ausdrucke sauber auf Klebebögen passen.

## MVP Scope

* Neuer Dialog/Menüpunkt: **"Stapelverarbeitung (Batch)..."**

* Textbereich für direkten Paste (eine Zeile = ein Code) + "CSV/TXT laden..." Button mit Zeilenzähler und Validierungsvorschau.
* Automatische Bereinigung von URLs und YouTube-Links.
* Hintergrund-Worker mit Progressbar und Abbruchmöglichkeit.
* Export als ZIP-Archiv mit PNG- oder SVG-Dateien.
* Export als druckfertiger DIN A4 PDF-Bogen (24er Etiketten oder 8er Kärtchen).

## Not Doing (and Why)

* **Keine Online-YouTube-API-Abfragen:** Keine Abhängigkeit von Google-API-Keys oder externen Servern. Wahrung der 100% Offline-First Privacy-Garantie.

* **Keine persistenten SQL-Datenbanken:** One-Shot Export im Arbeitsspeicher/Dateisystem reicht vollständig aus.
* **Keine überkomplexen Layout-Editoren:** Vordefinierte, getestete Standard-Druckraster decken typische Etiketten- und Aufsteller-Bögen ab.
