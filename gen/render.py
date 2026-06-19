"""Render the model (+ optional tailoring profile) into a self-contained CV page.

Everything visible is derived from data.md. A Profile only *selects*, *orders*
and *re-frames* (headline/pitch/highlights) — it never introduces new facts, so
tailored variants cannot drift from the source.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from . import parse as _parse

HERE = Path(__file__).resolve().parent
CSS = (HERE / "style.css").read_text(encoding="utf-8")

_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
_MD_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def md(text: str) -> str:
    """Escape, then apply a tiny safe inline-markdown subset (links, bold)."""
    out = html.escape(text or "", quote=False)
    out = _MD_LINK.sub(lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', out)
    out = _MD_BOLD.sub(r"<strong>\1</strong>", out)
    return Markup(out)


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(HERE)),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.filters["md"] = md
    return env


def _facts(data: dict) -> list[dict]:
    k = data["konditionen"]
    p = data["person"]
    return [
        {"k": "Verfügbar", "v": k.get("Verfügbarkeit", "").replace("ab ", "ab ")},
        {"k": "Einsatzort", "v": k.get("Einsatzort", "")},
        {"k": "Remote-Anteil", "v": data["remote_pct"], "small": f"Vor-Ort {data['onsite_pct']}"},
        {"k": "Satz Remote", "v": _rate(k.get("Rate Remote", "")), "small": "netto", "rate": True},
        {"k": "Satz Vor-Ort", "v": _rate(k.get("Rate Vor-Ort", "")), "small": "netto", "rate": True},
        {"k": "Standort", "v": p.get("Wohnort", ""), "small": "Deutschland"},
    ]


def _rate(raw: str) -> str:
    # "99 €/h (netto)" -> "99 €/h"
    return re.sub(r"\s*\(.*\)\s*$", "", raw).strip()


def _contact(data: dict) -> list[dict]:
    p = data["person"]
    phone = p.get("Telefon", "")
    tel = "tel:" + phone.replace(" ", "")
    pub = p.get("Sonstiges", "")
    pub_text, pub_href = pub, ""
    m = re.search(r"\((https?://[^)]+)\)", pub)
    if m:
        pub_href = m.group(1)
        pub_text = pub.split("(")[0].strip().rstrip(":").replace("Autor auf ", "") + " — Autor"
    out = [{"lbl": "Telefon", "text": phone, "href": tel}]
    out.append({"lbl": "Standort", "text": f"{p.get('Wohnort','')}, Deutschland"})
    for lbl, key in (("Website", "Website"), ("GitHub", "GitHub"),
                     ("LinkedIn", "LinkedIn"), ("Kaggle", "Kaggle")):
        url = p.get(key, "")
        if url:
            text = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
            out.append({"lbl": lbl, "text": text, "href": url, "external": True})
    if pub_href:
        out.append({"lbl": "Publikation", "text": "Towards Data Science — Autor",
                    "href": pub_href, "external": True})
    return out


def build_context(data: dict, profile: dict | None = None) -> dict:
    """Assemble the template context, applying the tailoring profile if given."""
    profile = profile or {}
    p = data["person"]

    # --- projects: select + order (facts always from data.md by id) ---
    by_id = {pr["id"]: pr for pr in data["projects"]}
    order = profile.get("include_projects")
    if order:
        projects = [by_id[i] for i in order if i in by_id]
    else:
        projects = list(data["projects"])

    # --- skills: optionally surface matched groups/tags first ---
    skills = _order_skills(data["skills"], profile.get("emphasize_skills"))

    name = p.get("Name", "")
    role_line = profile.get("headline") or p.get("Titel/Positionierung", "")
    stack_line = profile.get("stack_line") or p.get("Untertitel", "")
    pitch = profile.get("pitch") or p.get("Pitch", "")
    highlights = profile.get("highlights") or data["highlights"]
    eyebrow = profile.get("eyebrow") or "Freelancer · Softwareentwicklung"

    return {
        "title": profile.get("title") or p.get("SEO-Titel") or f"{name} — {role_line}",
        "description": profile.get("description") or pitch,
        "css": CSS,
        "noindex": profile.get("noindex", False),
        "asset_prefix": profile.get("asset_prefix", ""),
        "pdf_href": profile.get("pdf_href", "cv.pdf"),
        "pdf_download": profile.get("pdf_download", "Jens-Laufer-CV.pdf"),
        "docx_href": profile.get("docx_href", "cv.docx"),
        "docx_download": profile.get("docx_download", "Jens-Laufer-CV.docx"),
        "eyebrow": eyebrow,
        "name": name,
        "role_line": role_line,
        "stack_line": stack_line,
        "pitch": pitch,
        "facts": _facts(data),
        "highlights": highlights,
        "roles": data["roles"],
        "skills": skills,
        "projects": projects,
        "contact": _contact(data),
        "education": data["education"],
        "certificates": data["certificates"],
        "footer_left": profile.get("footer_left",
                                   "Jens Laufer · Fullstack · Data · ML · Agentic Engineering · Karlstein am Main"),
        "footer_right": profile.get("footer_right",
                                    "Verfügbar ab 01.07.2026 · weltweit · 95 % Remote"),
    }


def _order_skills(skills: list[dict], emphasize: list[str] | None) -> list[dict]:
    if not emphasize:
        return skills
    want = {e.lower() for e in emphasize}

    def score(group: dict) -> int:
        return sum(1 for t in group["tags"] if t.lower() in want)

    # stable sort: groups with matched tags first, original order preserved within
    return sorted(skills, key=lambda g: (-score(g),), reverse=False)


def render(data: dict, profile: dict | None = None) -> str:
    ctx = build_context(data, profile)
    tmpl = _env().get_template("template.html.j2")
    return tmpl.render(**ctx).rstrip() + "\n"


def render_from_source(path=None, profile: dict | None = None) -> str:
    data = _parse.parse(path) if path else _parse.parse()
    return render(data, profile)
