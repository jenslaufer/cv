from gen import parse, render


def test_base_render_has_all_projects():
    html = render.render(parse.parse())
    assert html.count('<article class="entry">') == 23
    assert html.count('<span class="chip">') == 10


def test_key_facts_present():
    html = render.render(parse.parse())
    for needle in ("Jens Laufer", "89 €/h", "ab 01.07.2026", "github.com/jenslaufer"):
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
