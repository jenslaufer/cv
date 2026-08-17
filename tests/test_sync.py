"""The sync guarantee: every committed base page is exactly what data/*.csv renders.

If this fails, either the page was hand-edited (forbidden) or the CSV source
changed without rebuilding. Fix: `python3 -m gen build --lang <de|en>`. This is
the test that enforces 'die csv bleiben die Wahrheit, die müssen synchron sein'.

It loops over ``cli.BASE_PAGES`` rather than naming index.html, so a language
cannot be added with a guard that still only watches the old one — which is
precisely how the English CV shipped as data on 2026-08-14 and was still not
served on 2026-08-17.
"""
from pathlib import Path

from gen import cli, parse, render

ROOT = Path(__file__).resolve().parent.parent


def test_every_base_page_matches_source():
    for lang, (out, profile) in cli.BASE_PAGES.items():
        page = ROOT / out
        assert page.exists(), f"{out} was never built — `python3 -m gen build --lang {lang}`"
        assert page.read_text(encoding="utf-8") == render.render(
            parse.parse(lang=lang), profile, lang=lang
        ), f"{out} is out of sync with data/*.csv — run `python3 -m gen build --lang {lang}`"
