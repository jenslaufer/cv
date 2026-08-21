"""An umbrella tech tag must not stop where a more specific one takes over.

Measured 2026-08-21 (issue #5): every row in project_tech.csv was correct and the
sum was still wrong. Tagging walks to the most specific name available, so the
umbrella term quietly stops being assigned — `Git` last appeared on a project that
ended 08/2019 while `GitLab`/`GitHub Actions` carried the seven projects since,
and `JavaScript` last appeared 12/2014 while `Vue.js`/`Vue 3`/`React` carried nine.
A recruiter filtering for "5+ years JavaScript" gets a no out of complete data.

Backfilling the data fixes today. This file is what keeps the next GitLab-only
project from reopening the gap: it fails the moment a child tag exists without
its umbrella.

Deliberately NOT impliers: TypeScript (its own language, not hand-written JS),
GWT (Java compiled to JavaScript — the work is Java), Phonegap (the container
around that GWT app), Subversion (not Git).
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

UMBRELLAS = {
    "Git": {"GitLab", "GitLab CI", "GitHub Actions"},
    "JavaScript": {"Vue.js", "Vue 3", "React", "AngularJS", "Quasar",
                   "npm", "Grunt", "Bootstrap"},
    "AWS": {"AWS S3", "AWS EC2", "AWS VPC", "AWS SageMaker"},
}


def _rows(name):
    return list(csv.DictReader((DATA / name).open(encoding="utf-8")))


def _tags_by_project():
    tech = {r["tech_id"]: r["tech"] for r in _rows("tech.csv")}
    out = {}
    for r in _rows("project_tech.csv"):
        out.setdefault(r["project_id"], set()).add(tech[r["tech_id"]])
    return out


def _start(period):
    """Sort key from a period cell: 'seit 12/2025', '07/2024-06/2025', '2009'."""
    m = re.search(r"(\d{2})/(\d{4})", period)
    if m:
        return (int(m.group(2)), int(m.group(1)))
    return (int(re.search(r"(\d{4})", period).group(1)), 1)


def test_umbrella_and_child_names_all_exist_in_the_tech_master():
    # A rename in tech.csv would make the rule below silently cover nothing.
    known = {r["tech"] for r in _rows("tech.csv")}
    named = set(UMBRELLAS) | {c for kids in UMBRELLAS.values() for c in kids}
    assert named <= known, f"not in tech.csv: {sorted(named - known)}"


def test_umbrella_tag_is_present_wherever_a_child_tag_is():
    tags = _tags_by_project()
    titles = {r["id"]: f'{r["period"]} {r["client"]}' for r in _rows("projects.csv")}
    missing = [
        f'{titles[pid]}: {umbrella} missing, carried by {sorted(have & kids)}'
        for pid, have in tags.items()
        for umbrella, kids in UMBRELLAS.items()
        if (have & kids) and umbrella not in have
    ]
    assert not missing, "umbrella tag stops at the specific name:\n  " + "\n  ".join(missing)


def test_umbrella_reaches_the_newest_project_that_uses_it():
    # The symptom the guard above exists for, stated in dates: the newest project
    # carrying a child must also carry the umbrella, or the CV reports the whole
    # technology as abandoned in the year the child took over.
    tags = _tags_by_project()
    periods = {r["id"]: r["period"] for r in _rows("projects.csv")}
    for umbrella, kids in UMBRELLAS.items():
        users = [pid for pid, have in tags.items() if have & kids or umbrella in have]
        newest = max(users, key=lambda pid: _start(periods[pid]))
        assert umbrella in tags[newest], (
            f'{umbrella} is not tagged on its newest project '
            f'({periods[newest]}); the CV dates it to '
            f'{max((periods[p] for p in users if umbrella in tags[p]), default="never", key=_start)}'
        )
