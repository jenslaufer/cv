"""Parse the CSV source of truth (data/*.csv) into a structured model.

The CV data lives in spreadsheet-friendly CSV files under ``data/`` — that is the
single source of truth. This module turns them into plain dicts that render.py
and tailor.py consume. The model shape is the stable contract; everything
downstream is source-agnostic.

The schema is **relational**: project facts are normalized into join tables, so
no cell holds a ``; ``-joined list.

- ``projects.csv`` — one row per project (id, period, dur, title, client,
  location, branch, desc); roles and tech live in join tables.
- ``tech.csv`` — master tech catalog ``tech_id,tech,category`` (every distinct
  technology a project used, categorized).
- ``project_tech.csv`` — join ``project_id,tech_id`` (ordered) — a project's stack.
- ``project_roles.csv`` — join ``project_id,role`` (ordered) — a project's roles.
- ``skills.csv`` — the **curated** Skills section ``group,skill`` (a hand-picked
  highlight reel, deliberately *not* the full per-project tech; a skill may appear
  in more than one group).
- ``roles.csv`` — the curated top-level role line.
- ``person.csv`` / ``konditionen.csv`` — two-column ``field,value``.
- ``highlights.csv`` / ``education.csv`` / ``certificates.csv`` — flat tables.
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _rows(data_dir: Path, name: str) -> list[dict]:
    path = data_dir / name
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _kv(data_dir: Path, name: str) -> dict[str, str]:
    """Read a two-column field,value CSV into an ordered dict."""
    out: dict[str, str] = {}
    for r in _rows(data_dir, name):
        out[r["field"].strip()] = (r["value"] or "").strip()
    return out


def _parse_skills(data_dir: Path) -> list[dict]:
    """Curated section: one row per skill -> groups in first-appearance order."""
    groups: dict[str, dict] = {}
    for r in _rows(data_dir, "skills.csv"):
        name = r["group"].strip()
        skill = (r["skill"] or "").strip()
        if not name or not skill:
            continue
        groups.setdefault(name, {"name": name, "tags": []})["tags"].append(skill)
    return list(groups.values())


def _tech_names(data_dir: Path) -> dict[int, str]:
    return {int(r["tech_id"]): r["tech"].strip() for r in _rows(data_dir, "tech.csv")}


def _join_ordered(data_dir: Path, name: str, key: str, val: str) -> dict[int, list[str]]:
    """Read a two-column join CSV into {key_id: [val, ...]} preserving file order."""
    out: dict[int, list[str]] = {}
    for r in _rows(data_dir, name):
        out.setdefault(int(r[key]), []).append(r[val].strip())
    return out


def _parse_projects(data_dir: Path) -> list[dict]:
    tech = _tech_names(data_dir)
    proj_tech_ids = _join_ordered(data_dir, "project_tech.csv", "project_id", "tech_id")
    proj_roles = _join_ordered(data_dir, "project_roles.csv", "project_id", "role")
    out = []
    for r in _rows(data_dir, "projects.csv"):
        pid = int(r["id"])
        out.append({
            "id": pid,
            "period": r["period"].strip(),
            "dur": r["dur"].strip(),
            "title": r["title"].strip(),
            "client": r["client"].strip(),
            "location": r["location"].strip(),
            "branch": r["branch"].strip(),
            "roles": proj_roles.get(pid, []),
            "desc": r["desc"].strip(),
            "tech": [tech[int(tid)] for tid in proj_tech_ids.get(pid, [])],
        })
    return out


def parse(path: str | Path | None = None) -> dict:
    """Build the CV model from the CSV source.

    ``path`` may point at an alternative data directory (used in tests);
    defaults to the repo-level ``data/``.
    """
    data_dir = Path(path) if path else DATA_DIR

    kond = _kv(data_dir, "konditionen.csv")

    return {
        "person": _kv(data_dir, "person.csv"),
        "konditionen": kond,
        "onsite_pct": kond.get("Anteil Vor-Ort", ""),
        "remote_pct": kond.get("Anteil Remote", ""),
        "roles": [r["role"].strip() for r in _rows(data_dir, "roles.csv") if r["role"].strip()],
        "highlights": [r["highlight"] for r in _rows(data_dir, "highlights.csv") if r["highlight"].strip()],
        "skills": _parse_skills(data_dir),
        "projects": _parse_projects(data_dir),
        "education": [
            {"date": r["date"].strip(), "title": r["title"].strip(), "org": r["org"].strip()}
            for r in _rows(data_dir, "education.csv")
        ],
        "certificates": [
            {"date": r["date"].strip(), "title": r["title"].strip(),
             "org": r["org"].strip(), "url": (r["url"] or "").strip()}
            for r in _rows(data_dir, "certificates.csv")
        ],
    }
