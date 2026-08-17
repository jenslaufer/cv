import re

from gen import labels, parse, render


def test_fact_grid_has_one_column_per_fact():
    """An empty sixth cell reads as a number that failed to load.

    The wide breakpoint asked for 6 columns while ``_facts()`` has returned 5
    since the two hourly rates became one day rate (2026-08-10) — so both
    published pages carried a grey empty box next to the day rate. Tying the
    number to the source means the next fact added or dropped cannot leave one
    behind: this is the same file the rate itself is measured from.
    """
    facts = render._facts(parse.parse(), labels.labels("de"))
    rule = re.search(r"\.facts\{grid-template-columns:repeat\((\d+),1fr\)\}", render.CSS)
    assert rule, "the wide fact-grid rule moved — check gen/style.css"
    assert int(rule.group(1)) == len(facts)


def test_base_render_has_all_projects():
    html = render.render(parse.parse())
    assert html.count('<article class="entry">') == 23
    assert html.count('<span class="chip">') == 10


def test_key_facts_present():
    html = render.render(parse.parse())
    for needle in ("Jens Laufer", "2.000 €/Tag", parse.parse()["konditionen"]["Verfügbarkeit"], "github.com/jenslaufer"):
        assert needle in html


def test_no_double_escaping():
    html = render.render(parse.parse())
    assert "&amp;amp;" not in html
    assert "&amp;nbsp;" not in html


def test_inline_markdown_applied():
    html = render.render(parse.parse())
    # bold lead in Schwerpunkte
    assert "<strong>~16 Jahre Fullstack-Erfahrung</strong>" in html
    # link from the flagship project description
    assert '<a href="https://fabrikhq.com">fabrikhq.com</a>' in html


def test_md_filter_escapes_unknown_markup():
    out = str(render.md("a <script> & b **bold**"))
    assert "<script>" not in out
    assert "&amp;" in out
    assert "<strong>bold</strong>" in out


def test_self_contained_document():
    html = render.render(parse.parse())
    assert html.startswith("<!DOCTYPE html>")
    assert "<style>" in html  # CSS inlined, no external stylesheet dependency
