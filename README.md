# cv.jenslaufer.com

Online-CV von Jens Laufer (freelance Fullstack-Entwickler), recruiter-facing.

**Die CSV-Dateien unter `data/` sind die einzige Quelle der Wahrheit.** Basis-CV und
jede zugeschnittene Variante werden daraus generiert — nichts wird von Hand editiert,
also bleibt alles synchron. Die CSVs sind tabellarisch und im Tabellenkalkulations-
Programm editierbar. `index.html` direkt zu ändern ist verboten; der Sync-Test schlägt
sonst fehl.

## Dateien

- `data/*.csv` — Quelle: Stammdaten, Konditionen, Rollen, Schwerpunkte, Kenntnisse,
  Projekthistorie, Ausbildung, Zertifikate (hier editieren). Listen-Zellen
  (Projekt-Rollen/Tech) sind mit `; ` getrennt; Kenntnisse sind eine Zeile pro Skill
  (`group,skill`).
- `index.html` — **generiert** aus `data/*.csv` (Basis-CV, druckoptimiert).
- `cv.pdf`, `cv.docx` — **generiert** (PDF via Headless-Chromium, Word aus dem Modell).
- `gen/` — der Generator (Parser, Renderer, Tailoring, Exporter, CLI).
- `tailored/<slug>/` — zugeschnittene Varianten (generiert, `noindex`, per Link teilbar).
- `examples/` — Beispiel-Ausschreibung fürs Tailoring.
- `CNAME` — GitHub-Pages-Custom-Domain.

## Workflow

```bash
pip install -r requirements.txt

# Basis-CV neu bauen, nachdem data/*.csv geändert wurde:
python -m gen build --pdf --docx

# Prüfen, dass index.html zur Quelle passt (CI-/Pre-Commit-Guard):
python -m gen check

# Auf eine Ausschreibung zuschneiden:
python -m gen tailor --job examples/job-java-backend.txt \
                     --slug java-backend-versicherung \
                     --title "Jens Laufer — Java / Spring Boot Backend" --pdf
```

`tailor` matcht die Ausschreibung gegen Projekthistorie und Skill-Vokabular aus
`data/*.csv`, behält das aktuelle Flaggschiff plus die relevantesten Projekte (neueste
zuerst) und hebt die passenden Skill-Gruppen nach vorn. Es schreibt eine
`tailored/<slug>/profile.yaml`, die von Hand verfeinert werden kann (Headline,
Pitch, Projektauswahl) — danach neu rendern:

```bash
python -m gen tailor --profile tailored/<slug>/profile.yaml --pdf
```

Eine Variante fügt **keine** neuen Fakten hinzu — sie wählt aus, ordnet und
rahmt nur. So kann ein zugeschnittener CV nie von der Quelle abweichen.

## Tests

```bash
python -m pytest -q
```

`tests/test_sync.py` erzwingt die Synchronität: `index.html` muss exakt das sein,
was `data/*.csv` rendert.

Verlinkt aus dem launch-kit `freelance`-Tenant (`cv-versand`-Autoresponder an den
`recruiters`-Verteiler).
