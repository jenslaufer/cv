"""The CV leads with agentic coding and process automation, backed by full-stack years.

Jens' call (2026-11-19): recruiters must read the agent work first, the decades of
full-stack development as its foundation — in both languages.
"""
import pytest

from gen import parse


@pytest.mark.parametrize("lang,auto", [("de", "Prozessautomatisierung"), ("en", "process automation")])
def test_lead_is_agentic_coding_and_process_automation(lang, auto):
    d = parse.parse(lang=lang)
    person = d["person"]
    head = person["Titel/Positionierung"] + " " + person["Untertitel"]
    assert "Agentic Coding" in head
    assert auto.lower() in head.lower()
    # the first two highlights are the agent work, the third the full-stack foundation
    assert "Agentic Coding" in d["highlights"][0]
    assert auto.lower() in d["highlights"][1].lower()
    assert "{career_years}" in d["highlights"][2]
    # first skill group = agents, first roles = agent work
    assert d["skills"][0]["name"].startswith(("KI-Agenten", "AI agents"))
    assert "Agentic" in d["roles"][0]


def test_pitch_keeps_the_full_stack_foundation():
    p = parse.parse()["person"]["Pitch"]
    assert "Full-Stack" in p and "{career_years}" in p


def test_phone_in_masthead():
    """Jens (2026-11-19): the phone number belongs at the top, not only in the contact block."""
    from gen import render
    html = render.render(parse.parse())
    head = html.split('class="masthead"', 1)[1].split('class="pitch"', 1)[0]
    assert 'href="tel:+4915510249850"' in head
    assert "+49 15510 249850" in head
