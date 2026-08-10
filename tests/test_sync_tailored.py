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
