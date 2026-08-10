"""Language support: an English CV must be generated, never hand-written.

The rule of this repo is that data/*.csv is the only source of truth. A second
language is therefore a second *data overlay* (data/en/) plus a label pack for
the template chrome — not a hand-edited HTML file that silently drifts.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from gen import labels as _labels
from gen import parse as _parse
from gen import render as _render

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Every CSV that carries prose. tech.csv / project_tech.csv are language-neutral
# (product names) and are deliberately NOT translated.
TRANSLATED = [
    "person.csv", "konditionen.csv", "highlights.csv", "roles.csv",
    "skills.csv", "projects.csv", "project_roles.csv",
    "education.csv", "certificates.csv",
]


def test_label_packs_have_identical_keys():
    """A missing translation must fail the suite, not render a German word."""
    de = set(_labels.labels("de"))
    en = set(_labels.labels("en"))
    assert de == en, f"label keys differ: {de ^ en}"


def test_every_label_is_actually_translated():
    de, en = _labels.labels("de"), _labels.labels("en")
    same = {k for k in de if de[k] == en[k]}
    # Only proper nouns / symbols may legitimately match.
    assert same <= {"netto_suffix_none"}, f"untranslated labels: {sorted(same)}"


def test_english_overlay_exists_for_every_prose_csv():
    missing = [n for n in TRANSLATED if not (DATA / "en" / n).exists()]
    assert missing == [], f"no English overlay for: {missing}"


def test_english_overlay_has_no_extra_or_missing_projects():
    de = _parse.parse()
    en = _parse.parse(lang="en")
    assert [p["id"] for p in en["projects"]] == [p["id"] for p in de["projects"]]
    assert len(en["skills"]) == len(de["skills"])
    assert len(en["highlights"]) == len(de["highlights"])


def test_english_parse_returns_english_prose():
    en = _parse.parse(lang="en")
    flagship = next(p for p in en["projects"] if p["id"] == 0)
    assert "Harness" in flagship["title"]
    assert "Gerüst" not in flagship["desc"]
    assert "agent loop" in flagship["desc"].lower()


def test_language_neutral_tables_are_shared_not_duplicated():
    """tech.csv is product names — one copy, used by both languages."""
    assert not (DATA / "en" / "tech.csv").exists()
    assert not (DATA / "en" / "project_tech.csv").exists()
    de = _parse.parse()
    en = _parse.parse(lang="en")
    by_id_de = {p["id"]: p for p in de["projects"]}
    for p in en["projects"]:
        assert p["tech"] == by_id_de[p["id"]]["tech"]


def test_english_render_is_english_end_to_end():
    html = _render.render(_parse.parse(lang="en"), lang="en")
    assert '<html lang="en">' in html
    for word in ("Schwerpunkte", "Kenntnisse", "Projekthistorie", "Ausbildung",
                 "Zertifikate", "PDF herunterladen", "Drucken", "Verfügbar",
                 "Einsatzort", "Verifizieren"):
        assert word not in html, f"German chrome leaked into the English CV: {word}"
    for word in ("Focus", "Skills", "Project history", "Education",
                 "Certificates", "Download PDF", "Print", "Available"):
        assert word in html, f"missing English chrome: {word}"


def test_german_render_is_unchanged_in_language():
    html = _render.render(_parse.parse())
    assert '<html lang="de">' in html
    assert "Projekthistorie" in html


# --- rate: one number, on every surface -------------------------------------

def test_day_rate_is_the_only_rate_in_the_source():
    """An hourly rate next to a day rate is two prices for the same work."""
    for lang in ("de", "en"):
        kond = _parse.parse(lang=lang)["konditionen"]
        assert any("agessatz" in k or "ay rate" in k for k in kond), kond
        assert not [k for k in kond if k.startswith("Rate ")], kond


@pytest.mark.parametrize("lang,expected", [("de", "2.000 €/Tag"), ("en", "€2,000/day")])
def test_day_rate_renders(lang, expected):
    html = _render.render(_parse.parse(lang=lang), lang=lang)
    assert expected in html
    assert not re.search(r"\d+\s*€/h", html), "hourly rate still printed"


def test_footer_availability_comes_from_the_source_not_a_literal():
    """The stale 'ab 01.07.2026' survived a data fix because it was hardcoded."""
    src = (ROOT / "gen" / "render.py").read_text(encoding="utf-8")
    assert "01.07.2026" not in src
    html = _render.render(_parse.parse())
    avail = _parse.parse()["konditionen"]["Verfügbarkeit"]
    assert avail in html.rsplit("<footer>", 1)[-1]


def test_tailoring_profile_still_applies_in_english():
    profile = {"headline": "Forward Deployed Engineer", "include_projects": [0, 22]}
    html = _render.render(_parse.parse(lang="en"), profile, lang="en")
    assert "Forward Deployed Engineer" in html
    assert html.count('class="entry"') == 2
