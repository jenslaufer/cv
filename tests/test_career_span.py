"""The career figure must be derived from a date, never typed into the prose.

Until 2026-08-21 every published page said "~16 Jahre Fullstack-Erfahrung
(seit 2009)". Both halves came from the same place and both were wrong: the year
is the first row of ``projects.csv`` (05/2009, Commerzbank), the number is that
span rounded. Jens graduated 11/1997 and has worked freelance since — the
projects before 2010 were simply never recorded. So the CV answered the
"20+ years of experience?" filter, the one every agency runs before a human
reads anything, with a **No**, in all 34 published variants at once.

A typed number cannot age. These tests exist so the prose cannot hold a career
figure at all: ``person.csv`` carries ``Karrierebeginn``, the prose carries the
``{career_years}`` placeholder, and the renderer fills it. Typing the number
back in is what turns these red.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

from gen import parse, render

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("de", "en")

PUBLISHED = [ROOT / "index.html", ROOT / "en" / "index.html"]
PUBLISHED += sorted((ROOT / "tailored").glob("*/index.html"))


def _career_years(person: dict) -> int:
    month, year = person["Karrierebeginn"].split("/")
    start = dt.date(int(year), int(month), 1)
    today = dt.date.today()
    return round((today - start).days / 365.2425)


@pytest.mark.parametrize("lang", LANGS)
def test_person_csv_carries_the_career_start(lang):
    """One date, in the source of truth — not a number in a sentence."""
    person = parse.parse(lang=lang)["person"]
    assert re.fullmatch(r"\d{2}/\d{4}", person.get("Karrierebeginn", "")), (
        "person.csv needs Karrierebeginn as MM/YYYY — the career figure is "
        "computed from it, not typed"
    )


@pytest.mark.parametrize("lang", LANGS)
def test_career_start_matches_the_diploma(lang):
    """The start date is the graduation date, so two files cannot drift apart."""
    data = parse.parse(lang=lang)
    diploma = [e["date"] for e in data["education"] if "1997" in e["date"]]
    assert diploma, "education.csv lost the 1997 degree"
    assert data["person"]["Karrierebeginn"] == diploma[0]


@pytest.mark.parametrize("lang", LANGS)
def test_prose_holds_the_placeholder_not_a_number(lang):
    """A hand-typed year count is the defect — catch it in the source, not the page."""
    data = parse.parse(lang=lang)
    prose = [data["person"]["Pitch"], *data["highlights"]]
    assert any("{career_years}" in t for t in prose), (
        "no {career_years} placeholder in pitch/highlights — the career figure "
        "would be a typed number again"
    )
    for text in prose:
        assert not re.search(r"~\s*\d+\s+(Jahre|years)", text), (
            f"career figure typed into the prose instead of {{career_years}}: {text!r}"
        )


@pytest.mark.parametrize("lang", LANGS)
def test_rendered_page_shows_the_computed_figure(lang):
    """End of the chain: the page a recruiter reads carries the derived number."""
    data = parse.parse(lang=lang)
    html = render.render(data, lang=lang)
    years = _career_years(data["person"])
    assert years >= 28, f"career span computed as {years} — check Karrierebeginn"
    assert f"~{years} " in html
    assert "{career_years}" not in html, "placeholder leaked into the page"
    assert "1997" in html


@pytest.mark.parametrize("page", PUBLISHED, ids=lambda p: p.parent.name or p.name)
def test_no_published_page_starts_the_career_in_2009(page):
    """2009 is where the *project list* starts, never where the career starts.

    Project periods ("05/2009-03/2010") stay — this bans only the phrasing that
    turns the first recorded project into a career start date.
    """
    text = page.read_text(encoding="utf-8")
    hits = re.findall(r"(?:seit|since)\s+2009", text)
    assert not hits, f"{page.relative_to(ROOT)} still dates the career to 2009: {hits}"


def test_project_history_names_its_own_window():
    """23 projects from 2009 under a 29-year career reads as a contradiction.

    It is a selection, and the heading has to say so — otherwise the reader
    resolves the gap against the CV, not in its favour.
    """
    data = parse.parse()
    html = render.render(data)
    # The oldest project runs 05/2009-03/2010. Its *start* is the window; reading
    # the end date instead is a real bug this test missed once by copying it.
    earliest = min(p["period"].split("–")[0].split("/")[-1] for p in data["projects"]
                   if re.search(r"\d{2}/\d{4}", p["period"]))
    assert earliest == "2009", f"oldest project starts in {earliest} — data changed"
    heading = re.search(r'<div class="sec-head"><h2>([^<]*Projekthistorie[^<]*)</h2>', html)
    assert heading, "project section heading moved"
    assert earliest in heading.group(1), (
        f"heading {heading.group(1)!r} does not name the window it shows "
        f"(earliest project {earliest})"
    )
