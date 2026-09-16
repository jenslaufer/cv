"""The sync guarantee, extended to every tailored variant.

`test_sync.py` only guards index.html. The tailored variants are just as public —
they are shared with recruiters by link — and they went stale unnoticed: on
2026-08-10 the day rate and the availability date changed in data/*.csv, and 33 of
34 variants kept printing the withdrawn hourly rate because nothing re-rendered
them. A number is only really retracted once the artifact stops printing it.

Fix on failure: `python3 -m gen tailor --profile tailored/<slug>/profile.yaml`
(add --pdf to refresh the PDF too).
"""
from pathlib import Path

import pytest
import yaml

from gen import parse, render, tailor

ROOT = Path(__file__).resolve().parent.parent
PROFILES = sorted((ROOT / "tailored").glob("*/profile.yaml"))


def _ids(paths):
    return [p.parent.name for p in paths]


def test_there_are_tailored_variants_to_check():
    """Guard the guard: a broken glob would make every check below vacuously pass."""
    assert PROFILES, "no tailored/*/profile.yaml found — is the glob still right?"


@pytest.mark.parametrize("profile_path", PROFILES, ids=_ids(PROFILES))
def test_tailored_html_matches_source(profile_path):
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    lang = profile.get("lang", "de")
    committed = (profile_path.parent / "index.html").read_text(encoding="utf-8")
    regenerated = render.render(parse.parse(lang=lang),
                                tailor.render_profile(profile), lang=lang)
    assert committed == regenerated, (
        f"tailored/{profile_path.parent.name}/index.html is out of sync with "
        f"data/*.csv — run `python3 -m gen tailor --profile {profile_path}`"
    )


def _pdf_pairs():
    """(generated pdf, hand-named copy beside it) for every tailored variant."""
    pairs = []
    for profile_path in PROFILES:
        d = profile_path.parent
        generated = d / f"{d.name}.pdf"
        for extra in sorted(d.glob("*.pdf")):
            if extra != generated:
                pairs.append((generated, extra))
    return pairs


@pytest.mark.parametrize("generated,copy", _pdf_pairs(),
                         ids=[c.name for _, c in _pdf_pairs()])
def test_hand_named_pdf_copies_are_real_copies(generated, copy):
    """The file a recruiter gets is the renamed one, and nothing regenerates it.

    `gen tailor --pdf` writes `<slug>.pdf`. A copy renamed to something a
    recruiter can read (Jens-Laufer-CV-Java-EAI-Middleware.pdf) is invisible to
    every check here, so it ages in place: on 2026-09-16 three of them were from
    July, still printing `Go` and `Verfügbar ab 01.07.2026`. Byte equality makes
    the copy fail the moment the variant is re-rendered.

    Fix on failure: `cp <slug>.pdf <the renamed file>`.
    """
    assert generated.exists(), f"{generated.name} was never generated"
    assert copy.read_bytes() == generated.read_bytes(), (
        f"{copy.name} is not a copy of {generated.name} — it is stale; "
        f"run `cp {generated} {copy}`"
    )
