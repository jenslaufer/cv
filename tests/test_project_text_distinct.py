"""Ein Textbaustein, der unter fünf Kunden steht, sagt nichts mehr über einen.

Gemessen am 2026-09-16 über data/projects.csv: von 64 Teilsätzen standen 17
woertlich in mehr als einem Projekt. Bei den fünf juengsten Projekten machte
der geteilte Block 30–62 % der Beschreibung aus — Projekt 1 (verkaufe.immobilien,
12 Monate) trug 60 Woerter, davon 37 identisch mit vier anderen Kunden.

Die Schwelle ist 3, nicht 2, und das ist Absicht: dieselbe Arbeit bei mehreren
Kunden ist eine Tatsache und darf zweimal dastehen. Ab dem dritten Mal liest sie
sich als Kopiervorlage und verdraengt das, was das Projekt unterscheidet.

Was hier herausfiel, ist nicht verloren: jedes genannte Werkzeug steht in der
Technik-Zeile desselben Projekts (project_tech.csv), eine Zeile unter der
Beschreibung im gerenderten CV — das prueft test_removed_clauses_survive_as_tech.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MAX_PROJECTS_PER_CLAUSE = 2
MIN_WORDS = 4

DATA_DIRS = {"de": ROOT / "data", "en": ROOT / "data" / "en"}


def _clauses(desc):
    """Teilsätze, wie ein Leser sie als eigene Aussage wahrnimmt."""
    return [c.strip() for c in re.split(r"(?<=[.;])\s+", desc) if c.strip()]


def _clause_owners(data_dir):
    owners = defaultdict(list)
    with open(data_dir / "projects.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for clause in _clauses(row["desc"]):
                if len(clause.split()) >= MIN_WORDS:
                    owners[clause].append(row["id"])
    return owners


@pytest.mark.parametrize("lang", sorted(DATA_DIRS))
def test_no_clause_stands_under_three_or_more_projects(lang):
    offenders = {
        clause: ids
        for clause, ids in _clause_owners(DATA_DIRS[lang]).items()
        if len(ids) > MAX_PROJECTS_PER_CLAUSE
    }
    assert not offenders, "\n".join(
        f"{len(ids)}x (Projekte {', '.join(ids)}): {clause}"
        for clause, ids in sorted(offenders.items(), key=lambda kv: -len(kv[1]))
    )


@pytest.mark.parametrize("lang", sorted(DATA_DIRS))
def test_both_languages_carry_the_same_projects(lang):
    """Sonst faellt ein Baustein nur auf einer Seite und die CVs laufen auseinander."""
    with open(DATA_DIRS[lang] / "projects.csv", encoding="utf-8") as fh:
        ids = [row["id"] for row in csv.DictReader(fh)]
    with open(DATA_DIRS["de"] / "projects.csv", encoding="utf-8") as fh:
        de_ids = [row["id"] for row in csv.DictReader(fh)]
    assert ids == de_ids


# Werkzeug -> Projekte, die es im gestrichenen Baustein nannten (Stand vor dem Schnitt)
CLAIMED_TECH = {
    "GitLab": ["1", "2", "4", "5", "6"],
    "GitLab CI": ["1", "2", "4", "5", "6"],
    "JUnit": ["4", "5", "6"],
    "Mockito": ["4", "5", "6"],
    "TDD": ["4", "5", "6"],
}


def test_removed_clauses_survive_as_tech():
    """Der Schnitt darf kein Werkzeug aus einem Projekt entfernen."""
    with open(ROOT / "data" / "tech.csv", encoding="utf-8") as fh:
        names = {row["tech_id"]: row["tech"] for row in csv.DictReader(fh)}
    per_project = defaultdict(set)
    with open(ROOT / "data" / "project_tech.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            per_project[row["project_id"]].add(names[row["tech_id"]])
    missing = [
        f"Projekt {pid}: {tech}"
        for tech, pids in CLAIMED_TECH.items()
        for pid in pids
        if tech not in per_project[pid]
    ]
    assert not missing, "Werkzeug aus der Beschreibung gestrichen und nicht in der Technik-Zeile: " + ", ".join(missing)


@pytest.mark.parametrize("lang", sorted(DATA_DIRS))
def test_no_row_has_more_columns_than_the_header(lang):
    """Ein unmaskierter Beistrich schiebt Text in eine Spalte, die niemand rendert.

    Gefunden 2026-09-16 in data/en/projects.csv, Projekt 14: die Beschreibung war
    an ihrem Beistrich in zwei Felder zerfallen, und das ausgelieferte englische CV
    zeigte nur die halbe Zeile — ", including a single-page admin front-end." fiel
    stumm heraus, waehrend die deutsche Fassung sie trug.
    """
    with open(DATA_DIRS[lang] / "projects.csv", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    ragged = [(r[0], len(r)) for r in rows[1:] if len(r) != len(header)]
    assert not ragged, f"Zeilen mit falscher Spaltenzahl (erwartet {len(header)}): {ragged}"
