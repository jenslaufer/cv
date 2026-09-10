"""The rate has to survive the export, not just the page.

On 2026-08-10 the two hourly rates became one day rate. The docx exporter kept
asking for the old keys, so the published cv.docx read
"Remote 95 % ·  remote /  vor Ort" — two empty slots where the price belongs,
on the one artifact that goes out by e-mail. Nothing caught it, because every
test looked at the HTML.

Today the move goes the other way (Jens, 10.09.2026: 100 EUR/h on-site,
90 EUR/h remote), so the same trap is open again in the same file. This test
reads the generated Word document, not the model that fed it.
"""
from __future__ import annotations

import pytest

from gen import exporters, parse

docx = pytest.importorskip("docx")


def _facts_line(tmp_path, lang, profile=None):
    out = tmp_path / f"cv-{lang}.docx"
    exporters.to_docx(parse.parse(lang=lang), out, profile, lang=lang)
    # the fact line is the first paragraph carrying the availability
    avail = parse.parse(lang=lang)["konditionen"]["Verfügbarkeit"]
    for p in docx.Document(str(out)).paragraphs:
        if avail in p.text:
            return p.text
    raise AssertionError(f"no fact line in {out}")


@pytest.mark.parametrize("lang,onsite,remote", [
    ("de", "100 €/h", "90 €/h"),
    ("en", "€100/h", "€90/h"),
])
def test_word_export_carries_both_rates(tmp_path, lang, onsite, remote):
    line = _facts_line(tmp_path, lang)
    assert onsite in line and remote in line, line


def test_word_export_honours_a_negotiated_rate(tmp_path):
    line = _facts_line(tmp_path, "de", {"rate": "125 €/h", "rate_label": "Stundensatz"})
    assert "125 €/h" in line, line
    assert "100 €/h" not in line and "90 €/h" not in line, line


def test_word_export_never_prints_an_empty_slot(tmp_path):
    """The 2026-08-10 symptom in one assertion: a label with nothing after it."""
    for lang in ("de", "en"):
        line = _facts_line(tmp_path, lang)
        assert "  " not in line, line
        assert not line.rstrip().endswith("·"), line


# --- the Word file is prose, not markdown source ----------------------------

def _all_text(tmp_path, lang):
    out = tmp_path / f"full-{lang}.docx"
    exporters.to_docx(parse.parse(lang=lang), out, None, lang=lang)
    return "\n".join(p.text for p in docx.Document(str(out)).paragraphs)


@pytest.mark.parametrize("lang", ["de", "en"])
def test_word_export_fills_every_template_placeholder(tmp_path, lang):
    """cv.docx shipped "~{career_years} Jahre Softwareentwicklung" for weeks.

    The HTML renderer fills {career_years} and {von}; the Word exporter never
    did, and it is the copy that goes out by e-mail — so the defect lived on
    the one surface nobody re-reads before sending it.
    """
    import re
    left = re.findall(r"\{[a-z_]+\}", _all_text(tmp_path, lang))
    assert not left, left


@pytest.mark.parametrize("lang", ["de", "en"])
def test_word_export_renders_links_as_prose(tmp_path, lang):
    """A recruiter opened Word and read "[fabrikhq.com](https://fabrikhq.com)"."""
    text = _all_text(tmp_path, lang)
    assert "](http" not in text
    assert "fabrikhq.com" in text
