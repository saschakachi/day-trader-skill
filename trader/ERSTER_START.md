# Dein erster Probelauf (Windows, macOS oder Linux)

## 1. Projekt herunterladen

Öffne das GitHub-Repository `saschakachi/day-trader-skill`, klicke auf
**Code → Download ZIP**, entpacke es und öffne ein Terminal im entpackten
Projektordner. Installiere bei Bedarf Python 3.11 oder 3.12.

## 2. Offline-Selbsttest starten

Windows (PowerShell):

```powershell
py trader/first_run.py
```

macOS / Linux:

```sh
python3 trader/first_run.py
```

Erwartete Ausgabe: `"selftest": "PASS"`, ein synthetischer
Risk-PASS-Kandidat und ein BLOCK-Kandidat. Der Selbsttest verwendet nur
lokale Beispieldaten, ruft **keine** Marktdaten ab und platziert **keine**
Orders. Bei einem Fehler zeigt er `SELFTEST BLOCK`.

## 3. Danach: echter Scanner-Probelauf (noch nicht automatisch)

`trader/run_daily.py` kann den vorhandenen Yahoo-basierten ORB-Scanner
ausführen. Dafür benötigst du ein vollständiges Paper-Handelsjournal
und eine **tatsächlich überprüfte** Reconciliation-Datei. Die
Beispieldatei aus `trader/demo` darf dafür nicht als echter Nachweis
verwendet werden. Siehe `trader/ONE_COMMAND.md`.

**Wichtig:** Ein Offline-Selbsttest beweist weder profitable Strategien
noch die Richtigkeit externer Kurse. Das Projekt läuft nicht dauerhaft,
und Trade Republic ist nicht verbunden.
