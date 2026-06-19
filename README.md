# cv.jenslaufer.com

Online-CV von Jens Laufer (freelance Fullstack-Entwickler), recruiter-facing.

**Die CSV-Dateien unter `data/` sind die einzige Quelle der Wahrheit.** Basis-CV und
jede zugeschnittene Variante werden daraus generiert — nichts wird von Hand editiert,
also bleibt alles synchron. Die CSVs sind tabellarisch und im Tabellenkalkulations-
Programm editierbar. `index.html` direkt zu ändern ist verboten; der Sync-Test schlägt
sonst fehl.

## Dateien

`data/*.csv` ist die Quelle (hier editieren). Das Schema ist **relational** — keine
Listen in Zellen, Projekt-Fakten in Join-Tabellen:

- `projects.csv` — eine Zeile pro Projekt (id, period, dur, title, client, location,
  branch, desc). Rollen und Tech stehen NICHT inline, sondern in Join-Tabellen.
- `tech.csv` — Master-Katalog aller eingesetzten Technologien (`tech_id,tech,category`).
- `project_tech.csv` — Verknüpfung `project_id,tech_id` (Reihenfolge = Anzeige-Reihenfolge).
- `project_roles.csv` — Verknüpfung `project_id,role`.
- `skills.csv` — die **kuratierte** Kenntnisse-Sektion (`group,skill`): eine Hand-
  Auswahl, bewusst NICHT die vollständige Projekt-Tech (ein Skill darf in mehreren
  Gruppen stehen). Getrennt von `tech.csv`, weil Highlight-Reel ≠ vollständiger Stack.
- `roles.csv` — kuratierte Top-Rollen-Zeile. `highlights.csv` — Schwerpunkte.
- `person.csv` / `konditionen.csv` — `field,value`. `education.csv` / `certificates.csv` — flach.

Eine neue Tech zu einem Projekt: Zeile in `tech.csv` (falls neu) + Zeile in
`project_tech.csv`. Der Test `test_project_tech_join_has_no_dangling_ids` fängt
verwaiste `tech_id`s ab.

**Datenherkunft:** Die Stammdaten stammen ursprünglich aus `busine1/cv` (GitLab,
R/RMarkdown, normalisiert-relational, ~2021). Dieses Repo ist das vollständige
Superset — alle Projekte von dort plus die seit 2022 dazugekommenen. `busine1/cv`
ist damit inhaltlich absorbiert.

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
