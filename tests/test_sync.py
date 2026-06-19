"""The sync guarantee: the committed index.html is exactly what data.md renders.

If this fails, either index.html was hand-edited (forbidden) or data.md changed
without rebuilding. Fix: `python -m gen build`. This is the test that enforces
'die csv bleiben die Wahrheit, die müssen synchron sein'.
"""
from pathlib import Path

from gen import parse, render

ROOT = Path(__file__).resolve().parent.parent


def test_index_html_matches_source():
    committed = (ROOT / "index.html").read_text(encoding="utf-8")
    regenerated = render.render(parse.parse())
    assert committed == regenerated, (
        "index.html is out of sync with data.md — run `python -m gen build`"
    )
