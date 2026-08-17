"""The English CV must be *published*, not merely renderable.

``data/en/`` and the label packs landed on 2026-08-14 and every i18n test since
has passed — but ``gen build`` only ever wrote the German ``index.html``, so
cv.jenslaufer.com served German to every English reader. It surfaced from
outside this repo: the English work sample at jenslaufer.com/harry/en/ offers
"See the CV" and landed on a German page (Jens, 17.08. 08:25).

A language that renders in a test but is never written to disk is
indistinguishable from a language that does not exist. So the tests below are
about the *artifact on disk*, not about the renderer.
"""
from pathlib import Path

from gen import cli, parse, render

ROOT = Path(__file__).resolve().parent.parent


def _published(lang):
    """(path on disk, what data/*.csv says it should contain)."""
    out, profile = cli.BASE_PAGES[lang]
    return ROOT / out, render.render(parse.parse(lang=lang), profile, lang=lang)


def test_every_published_language_has_a_page_on_disk():
    """That the page *renders* is what test_i18n proved for three days."""
    for lang in cli.BASE_PAGES:
        path, _ = _published(lang)
        assert path.exists(), f"{lang}: {path.name} renders but was never built"


def test_the_english_page_declares_english():
    path, _ = _published("en")
    html = path.read_text(encoding="utf-8")
    assert '<html lang="en">' in html
    assert "Projekthistorie" not in html, "German chrome leaked into the English CV"


def test_check_fails_when_the_published_english_page_is_stale(capsys):
    """The guard has to see the English page too, or it ages in silence.

    Same failure mode as the tailored variants before 2026-08-10: a check that
    cannot see the stale file reads exactly like a passed check.
    """
    path, _ = _published("en")
    original = path.read_text(encoding="utf-8")
    path.write_text(original.replace("Project history", "Projekthistorie"),
                    encoding="utf-8")
    try:
        rc = cli.main(["check"])
    finally:
        path.write_text(original, encoding="utf-8")
    assert rc == 1, "check passed while the published English page was stale"
    assert "en/index.html" in capsys.readouterr().err


def test_each_language_links_to_the_other():
    """Two pages nobody can move between are one page and a rumour."""
    de = (ROOT / "index.html").read_text(encoding="utf-8")
    en = (ROOT / "en" / "index.html").read_text(encoding="utf-8")
    assert 'hreflang="en"' in de and 'href="en/"' in de
    assert 'hreflang="de"' in en and 'href="../"' in en


def test_the_english_page_resolves_its_assets_from_the_subdirectory():
    en_dir = ROOT / "en"
    html = (en_dir / "index.html").read_text(encoding="utf-8")
    assert 'href="../favicon.svg"' in html
    for name in ("cv.pdf", "cv.docx"):
        assert f'href="{name}"' in html
        assert (en_dir / name).exists(), f"en/{name} is offered for download but absent"


def test_tailored_variants_carry_no_language_switch():
    """A variant is single-language — a switch there would point at a 404."""
    for page in sorted((ROOT / "tailored").glob("*/index.html")):
        assert "hreflang" not in page.read_text(encoding="utf-8"), page.parent.name
