# py-qr — Reaktives Desktop QR-Studio & Reader

## Problem Statement

Wie können wir eine extrem leichtgewichtige, intuitive Desktop-Anwendung schaffen, mit der man QR-Codes ohne spürbare Latenz per Drag & Drop / Strg+V dekodiert und mit wenigen Klicks fehlerresistente QR-Codes (Text, URL, WLAN) generieren und exportieren kann – lauffähig als kompakte, portable Single-File-EXE?

## Recommended Direction: "Reactive Smart-Utility"

Eine saubere Zwei-Reiter-PySide6-Applikation ("Generieren" & "Lesen") mit Fokus auf Geschwindigkeit und Ergonomie:

- **Lesen**: Große Drop-Zone + automatische Reaktion auf `Strg+V` (Clipboard). Dekodierter Inhalt wird analysiert (URL, WLAN, vCard, Freitext) und bietet sofortige Aktionen (Browser öffnen, Passwort kopieren, Text kopieren).
- **Generieren**: Umschaltbar zwischen Freitext/URL und geführter WLAN-Maske (SSID, Passwort, WPA2/WPA3). Live-Vorschau während des Tippens. Anpassung von Vorder-/Hintergrundfarbe und Fehlerkorrektur (L/M/Q/H). Export als PNG, SVG oder direktes Kopieren des Bildes in die Zwischenablage.
- **Historie & Settings**: Kompakte Liste der letzten 20 Aktionen. Fenstergröße/Position und Dark/Light-Theme bleiben erhalten.

## Key Assumptions to Validate

- [x] `zxing-cpp` lässt sich unter Windows via PyInstaller ohne fehlende Laufzeit-DLLs als Standalone-Exe bauen.
- [x] Bilddaten aus der Windows-Zwischenablage (QClipboard / Pillow / Qt Image) lassen sich zuverlässig und ohne Qualitätsverlust an den Decoder übergeben.
- [x] Live-Rendering mit `segno` bleibt bei Textänderungen unter 50ms Reaktionszeit.

## MVP Scope (Phase 1)

- [x] PySide6 GUI mit modernem Styling, Dark/Light Theme und F11 Vollbild-Umschaltung.
- [x] QR-Generator: Freitext & WLAN-Maske, Farbwahl, Fehlerkorrektur-Level, Live-Vorschau.
- [x] QR-Export: Als PNG/SVG speichern sowie "Bild in Zwischenablage kopieren".
- [x] QR-Reader: Drag & Drop für Bilddateien, Dateiauswahl-Dialog und `Strg+V` für Clipboard-Bilder.
- [x] Smart Parser: Erkennung von URLs (Button "Öffnen") und WLAN (Buttons "SSID kopieren", "Passwort kopieren").
- [x] Lokale Historie der letzten 20 Einträge (mit "Löschen"-Option).
- [x] PyInstaller Build-Skript zur Erstellung einer portablen Single-File `.exe`.

## Phase 2 Scope (Smart Formats & Print Studio)

- [x] Erweiterte Smart-Formate: Visitenkarte (vCard 3.0), E-Mail (`mailto:`) und Geo-Standort (`geo:`).
- [x] Reader Smart-Actions: "Als .vcf speichern", "E-Mail verfassen", "In Google Maps öffnen", "In Generator laden".
- [x] Druckfertiges Kärtchen-Studio (`CardDialog` & `card_printer`): DIN A6/A4 Aufsteller mit Live-Druckvorschau, PDF- & 300 DPI PNG-Export.
- [x] Privacy & Erweiterte Historie: WLAN-Passwörter im Verlauf maskieren, Echtzeit-Suchleiste, Typ-Filter und CSV/JSON-Export.

## Not Doing

- Webcam-Live-Scanning (vermeidet OpenCV / QtMultimedia Overhead).
- Eigener Bildschirm-Snipper (Windows `Win+Shift+S` + `Strg+V` in der App ist schneller).
- Verschlüsselte Passwort-Datenbank oder Cloud-Sync (Offline-First Privacy Garantie).
