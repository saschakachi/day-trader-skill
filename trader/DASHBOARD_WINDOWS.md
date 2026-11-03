# Lokales Paper-Trading-Dashboard (Windows)

Diese erste Version ist eine **reine Offline-Demo**. Sie nutzt die bereits
vorhandenen synthetischen Testdaten und zeigt Risk PASS/BLOCK. Es gibt
keine Marktdatenabfragen, keine Broker-Anbindung, keine Orders und kein
Handelsjournal mit echten Trades.

## Start unter Windows

1. Den Pull Request in GitHub zusammenführen.
2. Unter **Code → Download ZIP** den aktuellen Stand herunterladen und
   entpacken (oder das Repository aktualisieren).
3. PowerShell im Projektordner öffnen.
4. Starten:

```powershell
python trader/dashboard.py
```

5. Im Browser **http://127.0.0.1:8000** öffnen.
6. Auf **Simulierten Handelstag starten** klicken.
7. Zum Beenden PowerShell auswählen und **Strg+C** drücken.

Python 3.11 genügt; keine zusätzlichen Pakete notwendig.

Der Webserver bindet ausschließlich an **127.0.0.1** (diesen PC), nicht
an das Heimnetz oder Internet. Der Knopf startet nur den lokalen
deterministischen Demo-Report. Ergebnisse werden nicht gespeichert.
Die Yahoo-Sperre (HTTP 429) wird nicht umgangen; echte Marktdaten
sind hier absichtlich nicht integriert. Die PASS-Anzeige ist keine
Handelsfreigabe und bezieht sich nur auf fiktive Daten.
