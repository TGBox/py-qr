# py-qr — Reaktives Desktop QR-Studio & Reader

## Problem Statement

Wie können wir eine extrem leichtgewichtige, intuitive Desktop-Anwendung schaffen, mit der man QR-Codes ohne spürbare Latenz per Drag & Drop / Strg+V dekodiert und mit wenigen Klicks fehlerresistente QR-Codes (Text, URL, WLAN) generieren und exportieren kann – lauffähig als kompakte, portable Single-File-EXE?

## Recommended Direction: "Reactive Smart-Utility"

Eine saubere Zwei-Reiter-PySide6-Applikation ("Generieren" & "Lesen") mit Fokus auf Geschwindigkeit und Ergonomie:

- **Lesen**: Große Drop-Zone + automatische Reaktion auf `Strg+V` (Clipboard). Dekodierter Inhalt wird analysiert (URL, WLAN, vCard, Freitext) und bietet sofortige Aktionen (Browser öffnen, Passwort kopieren, Text kopieren).
- **Generieren**: Umschaltbar zwischen Freitext/URL und geführter WLAN-Maske (SSID, Passwort, WPA2/WPA3). Live-Vorschau während des Tippens. Anpassung von Vorder-/Hintergrundfarbe und Fehlerkorrektur (L/M/Q/H). Export als PNG, SVG oder direktes Kopieren des Bildes in die Zwischenablage.
- **Historie & Settings**: Kompakte Liste der letzten 20 Aktionen. Fenstergröße/Position und Dark/Light-Theme bleiben erhalten.

## Key Assumptions to Validate

- [ ] `zxing-cpp` lässt sich unter Windows via PyInstaller ohne fehlende Laufzeit-DLLs als Standalone-Exe bauen.
- [ ] Bilddaten aus der Windows-Zwischenablage (QClipboard / Pillow / Qt Image) lassen sich zuverlässig und ohne Qualitätsverlust an den Decoder übergeben.
- [ ] Live-Rendering mit `segno` bleibt bei Textänderungen unter 50ms Reaktionszeit.

## MVP Scope (Phase 1)

- [x] PySide6 GUI mit modernem Styling, Dark/Light Theme und F11 Vollbild-Umschaltung.
- [x] QR-Generator: Freitext & WLAN-Maske, Farbwahl, Fehlerkorrektur-Level, Live-Vorschau.
- [x] QR-Export: Als PNG/SVG speichern sowie "Bild in Zwischenablage kopieren".
- [x] QR-Reader: Drag & Drop für Bilddateien, Dateiauswahl-Dialog und `Strg+V` für Clipboard-Bilder.
- [x] Smart Parser: Erkennung von URLs (Button "Öffnen") und WLAN (Buttons "SSID kopieren", "Passwort kopieren").
- [x] Lokale Historie der letzten 20 Einträge (mit "Löschen"-Option).
- [x] PyInstaller Build-Skript zur Erstellung einer portablen Single-File `.exe`.

## Not Doing (in Phase 1)

- Webcam-Live-Scanning (vermeidet OpenCV / QtMultimedia Overhead).
- Eigener Bildschirm-Snipper (Windows `Win+Shift+S` + `Strg+V` in der App ist schneller).
- Druck-Aufsteller / DIN-Kärtchen-Generator (vorgemerkt für v2).
- Verschlüsselte Passwort-Datenbank oder Cloud-Sync.

## Open Questions

- Gibt es spezifische Farb- oder Design-Wünsche (z. B. Fluent/Windows 11 Look vs. schlichtes High-Contrast Qt)?
