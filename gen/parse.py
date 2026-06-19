"""Parse data.md (the single source of truth) into a structured model.

data.md stays human-friendly markdown; this module turns it into plain dicts
that render.py and tailor.py consume. Keep the parser tolerant but explicit:
a malformed section should raise, not silently drop data.
"""
from __future__ import annotations

import re
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data.md"


def _sections(text: str) -> dict[str, str]:
    """Split markdown into top-level ## sections keyed by heading."""
    out: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            if current is not None:
                out[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf).strip()
    return out


def _bullets(block: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^\s*-\s+(.*)$", block, re.M)]


def _kv(block: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for b in _bullets(block):
        if ":" in b:
            k, v = b.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _section_key(sections: dict[str, str], prefix: str) -> str:
    """Headings carry parenthetical notes; match by prefix."""
    for k in sections:
        if k.startswith(prefix):
            return k
    raise KeyError(f"section starting with {prefix!r} not found")


def _split_client_location(left: str) -> tuple[str, str]:
    """'Solytics GmbH (Remote)' -> (client, location).

    Two source shapes: 'CLIENT (LOC)' or 'CLIENT, LOC' (CLIENT may itself
    contain parentheses, e.g. 'Co-operative Group (Coop), Manchester').
    """
    s = left.strip()
    if s.endswith(")"):
        i = s.rfind("(")
        return s[:i].strip(), s[i + 1:-1].strip()
    if ", " in s:
        client, loc = s.rsplit(", ", 1)
        return client.strip(), loc.strip()
    return s, ""


def _parse_projects(block: str) -> list[dict]:
    """Parse the numbered Projekthistorie into a list of project dicts."""
    # Split on lines that begin a new numbered entry: "0. ... — Title"
    entries = re.split(r"(?m)^(?=\d+\.\s)", block)
    projects: list[dict] = []
    for raw in entries:
        raw = raw.strip()
        if not raw:
            continue
        lines = raw.splitlines()
        head = lines[0].strip()
        m = re.match(r"^(\d+)\.\s+(.*?)\s+—\s+(.*)$", head)
        if not m:
            raise ValueError(f"unparseable project header: {head!r}")
        idx, period_dur, title = m.group(1), m.group(2).strip(), m.group(3).strip()
        dm = re.match(r"^(.*?)\s*\((.*?)\)\s*$", period_dur)
        if dm:
            period, dur = dm.group(1).strip(), dm.group(2).strip()
        else:
            period, dur = period_dur, ""
        dur = dur.replace("Mon.", "Monate")

        client = location = branch = desc = ""
        roles: list[str] = []
        tech: list[str] = []
        for b in _bullets("\n".join(lines[1:])):
            if b.startswith("Kunde:"):
                rest = b[len("Kunde:"):].strip()
                left, _, branch_part = rest.partition("· Branche:")
                client, location = _split_client_location(left.strip())
                branch = branch_part.strip()
            elif b.startswith("Rollen:"):
                roles = [r.strip() for r in re.split(r"[·,]", b[len("Rollen:"):]) if r.strip()]
            elif b.startswith("Tech:"):
                tech = _split_csv(b[len("Tech:"):])
            else:
                desc = b.strip()
        projects.append({
            "id": int(idx),
            "period": period,
            "dur": dur,
            "title": title,
            "client": client,
            "location": location,
            "branch": branch,
            "roles": roles,
            "desc": desc,
            "tech": tech,
        })
    return projects


def _parse_education(block: str) -> list[dict]:
    out = []
    for b in _bullets(block):
        date, _, rest = b.partition("—")
        title, _, org = rest.strip().partition(", ")
        out.append({"date": date.strip(), "title": title.strip(), "org": org.strip()})
    return out


def _parse_certificates(block: str) -> list[dict]:
    out = []
    for b in _bullets(block):
        date, _, rest = b.partition("—")
        rest = rest.strip()
        url = ""
        um = re.search(r"\((https?://[^)]+)\)\s*$", rest)
        if um:
            url = um.group(1)
            rest = rest[:um.start()].strip()
        title, _, org = rest.partition(", ")
        out.append({"date": date.strip(), "title": title.strip(), "org": org.strip(), "url": url})
    return out


def _split_csv(text: str) -> list[str]:
    """Comma-split that ignores commas inside parentheses, e.g. 'AWS (EC2, S3)'."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return [p for p in parts if p]


def _parse_skills(block: str) -> list[dict]:
    out = []
    for b in _bullets(block):
        if ":" not in b:
            continue
        name, _, rest = b.partition(":")
        out.append({"name": name.strip(), "tags": _split_csv(rest)})
    return out


def parse(path: str | Path = DATA_FILE) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    sections = _sections(text)

    person = _kv(sections["Person"])
    kond = _kv(sections["Konditionen"])

    anteil = kond.get("Anteil Vor-Ort", "")
    onsite_pct = remote_pct = ""
    am = re.search(r"Anteil Vor-Ort:\s*([\d %]+).*Anteil Remote:\s*([\d %]+)",
                   sections["Konditionen"])
    # Konditionen stores both percentages on one bullet
    pm = re.search(r"([\d ]+%).*?Remote:\s*([\d ]+%)", sections["Konditionen"])
    if pm:
        onsite_pct, remote_pct = pm.group(1).strip(), pm.group(2).strip()

    roles = [r.strip() for r in sections["Rollen"].replace("\n", " ").split("·") if r.strip()]

    return {
        "person": person,
        "konditionen": kond,
        "onsite_pct": onsite_pct,
        "remote_pct": remote_pct,
        "roles": roles,
        "highlights": _bullets(sections[_section_key(sections, "Schwerpunkte")]),
        "skills": _parse_skills(sections[_section_key(sections, "Kenntnisse")]),
        "projects": _parse_projects(sections[_section_key(sections, "Projekthistorie")]),
        "education": _parse_education(sections["Ausbildung"]),
        "certificates": _parse_certificates(sections["Zertifikate"]),
    }
