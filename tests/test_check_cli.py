"""`gen check` must cover every published artifact, not just index.html.

Until 2026-08-10 it only compared index.html. That is the worst kind of guard: it
printed "in sync" while 33 tailored variants — all of them public, all of them
shared with recruiters by link — still printed a withdrawn day rate. A check that
cannot see the stale file reads exactly like a passed check.
"""
from pathlib import Path

from gen import cli

ROOT = Path(__file__).resolve().parent.parent


def test_check_passes_on_clean_tree(capsys):
    assert cli.main(["check"]) == 0


def test_check_fails_when_a_tailored_variant_is_stale(tmp_path, capsys):
    """The staleness is injected, not spelled out.

    This used to overwrite the literal "2.000 €/Tag". When the source went back
    to two hourly rates (2026-09-10) that string was gone, the victim was left
    untouched, and the test passed by asserting that a clean tree is clean —
    the exact shape of failure the guard itself exists to prevent.
    """
    victim = sorted((ROOT / "tailored").glob("*/index.html"))[0]
    original = victim.read_text(encoding="utf-8")
    assert "</body>" in original
    victim.write_text(original.replace("</body>", "<p>stale</p></body>"), encoding="utf-8")
    try:
        rc = cli.main(["check"])
    finally:
        victim.write_text(original, encoding="utf-8")
    assert rc == 1
    assert victim.parent.name in capsys.readouterr().err
