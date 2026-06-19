"""Parse the CSV source of truth (data/*.csv) into a structured model.

The CV data lives in spreadsheet-friendly CSV files under ``data/`` — that is the
single source of truth. This module turns them into plain dicts that render.py
and tailor.py consume. The model shape is the stable contract; everything
downstream is source-agnostic.

List-valued cells (project roles/tech) are stored as ``; ``-joined strings.
Skills are one row per skill (``group,skill``); groups are rebuilt in
first-appearance order.
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

LIST_SEP = "; "


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


def _split_list(cell: str) -> list[str]:
    return [p.strip() for p in (cell or "").split(LIST_SEP) if p.strip()]


def _parse_skills(data_dir: Path) -> list[dict]:
    """One row per skill -> groups in first-appearance order."""
    groups: dict[str, dict] = {}
    for r in _rows(data_dir, "skills.csv"):
        name = r["group"].strip()
        skill = (r["skill"] or "").strip()
        if not name or not skill:
            continue
        groups.setdefault(name, {"name": name, "tags": []})["tags"].append(skill)
    return list(groups.values())


def _parse_projects(data_dir: Path) -> list[dict]:
    out = []
    for r in _rows(data_dir, "projects.csv"):
        out.append({
            "id": int(r["id"]),
            "period": r["period"].strip(),
            "dur": r["dur"].strip(),
            "title": r["title"].strip(),
            "client": r["client"].strip(),
            "location": r["location"].strip(),
            "branch": r["branch"].strip(),
            "roles": _split_list(r["roles"]),
            "desc": r["desc"].strip(),
            "tech": _split_list(r["tech"]),
        })
    return out


def parse(path: str | Path | None = None) -> dict:
    """Build the CV model from the CSV source.

    ``path`` may point at an alternative data directory (used in tests);
    defaults to the repo-level ``data/``.
    """
    data_dir = Path(path) if path else DATA_DIR

    kond = _kv(data_dir, "konditionen.csv")
    onsite_pct = kond.get("Anteil Vor-Ort", "")
    remote_pct = kond.get("Anteil Remote", "")

    return {
        "person": _kv(data_dir, "person.csv"),
        "konditionen": kond,
        "onsite_pct": onsite_pct,
        "remote_pct": remote_pct,
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
